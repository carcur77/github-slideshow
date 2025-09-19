"""
Chart Generation Commands
Implements /chart command with dynamic visualization using Matplotlib and Plotly
"""

import discord
from discord.ext import commands
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io
import ccxt
from typing import Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ChartsCog(commands.Cog):
    """Cog for chart generation commands"""
    
    def __init__(self, bot):
        self.bot = bot
        self.exchange = ccxt.binance()
        
        # Configure matplotlib for better chart appearance
        plt.style.use('dark_background')
        plt.rcParams['figure.facecolor'] = '#2C2F33'
        plt.rcParams['axes.facecolor'] = '#36393F'
        plt.rcParams['axes.edgecolor'] = '#FFFFFF'
        plt.rcParams['text.color'] = '#FFFFFF'
        plt.rcParams['axes.labelcolor'] = '#FFFFFF'
        plt.rcParams['xtick.color'] = '#FFFFFF'
        plt.rcParams['ytick.color'] = '#FFFFFF'
    
    async def fetch_ohlcv_data(self, symbol: str, timeframe: str = '1h', limit: int = 100) -> Optional[pd.DataFrame]:
        """Fetch OHLCV data for a symbol"""
        try:
            if not symbol.endswith('USDT') and '/' not in symbol:
                symbol = f"{symbol.upper()}/USDT"
            
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return None
    
    def create_matplotlib_chart(self, df: pd.DataFrame, symbol: str, timeframe: str) -> io.BytesIO:
        """Create a matplotlib chart with technical indicators"""
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(14, 10), 
                                           gridspec_kw={'height_ratios': [3, 1, 1]})
        
        # Main price chart with indicators
        ax1.plot(df['timestamp'], df['close'], label='Price', color='#00D4AA', linewidth=2)
        
        # Calculate and plot technical indicators
        indicators = self.bot.technical_indicators
        
        # Moving Averages
        sma_20 = indicators.calculate_sma(df['close'], 20)
        sma_50 = indicators.calculate_sma(df['close'], 50)
        ema_12 = indicators.calculate_ema(df['close'], 12)
        
        ax1.plot(df['timestamp'], sma_20, label='SMA 20', color='#FF6B35', alpha=0.8)
        ax1.plot(df['timestamp'], sma_50, label='SMA 50', color='#F7931E', alpha=0.8)
        ax1.plot(df['timestamp'], ema_12, label='EMA 12', color='#FFE135', alpha=0.8)
        
        # Bollinger Bands
        bb_data = indicators.calculate_bollinger_bands(df['close'])
        ax1.plot(df['timestamp'], bb_data['upper'], label='BB Upper', color='#FF3333', alpha=0.5, linestyle='--')
        ax1.plot(df['timestamp'], bb_data['lower'], label='BB Lower', color='#FF3333', alpha=0.5, linestyle='--')
        ax1.fill_between(df['timestamp'], bb_data['upper'], bb_data['lower'], alpha=0.1, color='#FF3333')
        
        ax1.set_title(f'{symbol} - Technical Analysis Chart ({timeframe})', fontsize=16, fontweight='bold')
        ax1.set_ylabel('Price (USDT)', fontsize=12)
        ax1.legend(loc='upper left')
        ax1.grid(True, alpha=0.3)
        
        # MACD subplot
        macd_data = indicators.calculate_macd(df['close'])
        ax2.plot(df['timestamp'], macd_data['macd'], label='MACD', color='#00D4AA')
        ax2.plot(df['timestamp'], macd_data['signal'], label='Signal', color='#FF6B35')
        ax2.bar(df['timestamp'], macd_data['histogram'], label='Histogram', color='#FFE135', alpha=0.6)
        ax2.axhline(y=0, color='white', linestyle='-', alpha=0.3)
        ax2.set_ylabel('MACD', fontsize=12)
        ax2.legend(loc='upper left')
        ax2.grid(True, alpha=0.3)
        
        # Stochastic subplot
        stoch_data = indicators.calculate_stochastic(df['high'], df['low'], df['close'])
        ax3.plot(df['timestamp'], stoch_data['k'], label='%K', color='#00D4AA')
        ax3.plot(df['timestamp'], stoch_data['d'], label='%D', color='#FF6B35')
        ax3.axhline(y=80, color='red', linestyle='--', alpha=0.5, label='Overbought')
        ax3.axhline(y=20, color='green', linestyle='--', alpha=0.5, label='Oversold')
        ax3.fill_between(df['timestamp'], 80, 100, alpha=0.1, color='red')
        ax3.fill_between(df['timestamp'], 0, 20, alpha=0.1, color='green')
        ax3.set_ylabel('Stochastic', fontsize=12)
        ax3.set_xlabel('Time', fontsize=12)
        ax3.legend(loc='upper left')
        ax3.grid(True, alpha=0.3)
        ax3.set_ylim(0, 100)
        
        # Format x-axis
        for ax in [ax1, ax2, ax3]:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
            ax.xaxis.set_major_locator(mdates.HourLocator(interval=4))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        plt.tight_layout()
        
        # Save to BytesIO
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight', 
                   facecolor='#2C2F33', edgecolor='none')
        buffer.seek(0)
        plt.close()
        
        return buffer
    
    @commands.command(name='chart')
    async def generate_chart(self, ctx, symbol: str, timeframe: str = '1h', style: str = 'matplotlib'):
        """
        Generate technical analysis chart for a cryptocurrency
        Usage: /chart BTC 1h matplotlib
        Styles: matplotlib, plotly
        """
        await ctx.send(f"📊 Generating chart for {symbol.upper()}...")
        
        # Fetch market data
        df = await self.fetch_ohlcv_data(symbol, timeframe, limit=200)
        if df is None:
            await ctx.send(f"❌ Could not fetch data for {symbol.upper()}. Please check the symbol.")
            return
        
        try:
            if style.lower() == 'matplotlib':
                # Generate matplotlib chart
                chart_buffer = self.create_matplotlib_chart(df, symbol.upper(), timeframe)
                
                # Send chart as file
                chart_file = discord.File(chart_buffer, filename=f"{symbol}_chart_{timeframe}.png")
                
                # Create embed with chart info
                embed = discord.Embed(
                    title=f"📊 Technical Analysis Chart",
                    description=f"**{symbol.upper()}** - {timeframe} timeframe",
                    color=0x00ff00,
                    timestamp=datetime.now()
                )
                
                latest_price = df['close'].iloc[-1]
                price_change = ((df['close'].iloc[-1] - df['close'].iloc[-2]) / df['close'].iloc[-2]) * 100
                
                embed.add_field(
                    name="💰 Current Price",
                    value=f"${latest_price:.2f}",
                    inline=True
                )
                
                embed.add_field(
                    name="📈 24h Change",
                    value=f"{price_change:+.2f}%",
                    inline=True
                )
                
                embed.add_field(
                    name="📊 Indicators",
                    value="SMA 20/50, EMA 12, Bollinger Bands, MACD, Stochastic",
                    inline=False
                )
                
                embed.set_footer(text="Data from Binance | Chart style: Matplotlib")
                
                await ctx.send(file=chart_file, embed=embed)
                
            elif style.lower() == 'plotly':
                # Generate Plotly chart (HTML output)
                fig = self.create_plotly_chart(df, symbol.upper(), timeframe)
                
                # Save as HTML and send as file
                html_buffer = io.StringIO()
                fig.write_html(html_buffer)
                html_buffer.seek(0)
                
                html_file = discord.File(
                    io.BytesIO(html_buffer.getvalue().encode()), 
                    filename=f"{symbol}_chart_{timeframe}.html"
                )
                
                embed = discord.Embed(
                    title=f"📊 Interactive Technical Analysis Chart",
                    description=f"**{symbol.upper()}** - {timeframe} timeframe\nDownload the HTML file to view the interactive chart",
                    color=0x00ff00,
                    timestamp=datetime.now()
                )
                
                embed.set_footer(text="Data from Binance | Chart style: Plotly Interactive")
                
                await ctx.send(file=html_file, embed=embed)
            
            else:
                await ctx.send("❌ Invalid chart style. Use 'matplotlib' or 'plotly'")
                
        except Exception as e:
            logger.error(f"Error generating chart: {e}")
            await ctx.send(f"❌ Error generating chart: {str(e)}")
    
    def create_plotly_chart(self, df: pd.DataFrame, symbol: str, timeframe: str):
        """Create an interactive Plotly chart"""
        fig = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            subplot_titles=(f'{symbol} Price Chart', 'MACD', 'Stochastic Oscillator'),
            row_width=[0.2, 0.2, 0.7]
        )
        
        # Calculate indicators
        indicators = self.bot.technical_indicators
        sma_20 = indicators.calculate_sma(df['close'], 20)
        sma_50 = indicators.calculate_sma(df['close'], 50)
        bb_data = indicators.calculate_bollinger_bands(df['close'])
        macd_data = indicators.calculate_macd(df['close'])
        stoch_data = indicators.calculate_stochastic(df['high'], df['low'], df['close'])
        
        # Main price chart
        fig.add_trace(go.Scatter(x=df['timestamp'], y=df['close'], 
                                name='Price', line=dict(color='#00D4AA', width=2)), row=1, col=1)
        
        # Moving averages
        fig.add_trace(go.Scatter(x=df['timestamp'], y=sma_20, 
                                name='SMA 20', line=dict(color='#FF6B35')), row=1, col=1)
        fig.add_trace(go.Scatter(x=df['timestamp'], y=sma_50, 
                                name='SMA 50', line=dict(color='#F7931E')), row=1, col=1)
        
        # Bollinger Bands
        fig.add_trace(go.Scatter(x=df['timestamp'], y=bb_data['upper'], 
                                name='BB Upper', line=dict(color='#FF3333', dash='dash')), row=1, col=1)
        fig.add_trace(go.Scatter(x=df['timestamp'], y=bb_data['lower'], 
                                name='BB Lower', line=dict(color='#FF3333', dash='dash'), 
                                fill='tonexty', fillcolor='rgba(255,51,51,0.1)'), row=1, col=1)
        
        # MACD
        fig.add_trace(go.Scatter(x=df['timestamp'], y=macd_data['macd'], 
                                name='MACD', line=dict(color='#00D4AA')), row=2, col=1)
        fig.add_trace(go.Scatter(x=df['timestamp'], y=macd_data['signal'], 
                                name='Signal', line=dict(color='#FF6B35')), row=2, col=1)
        fig.add_trace(go.Bar(x=df['timestamp'], y=macd_data['histogram'], 
                            name='Histogram', marker_color='#FFE135', opacity=0.6), row=2, col=1)
        
        # Stochastic
        fig.add_trace(go.Scatter(x=df['timestamp'], y=stoch_data['k'], 
                                name='%K', line=dict(color='#00D4AA')), row=3, col=1)
        fig.add_trace(go.Scatter(x=df['timestamp'], y=stoch_data['d'], 
                                name='%D', line=dict(color='#FF6B35')), row=3, col=1)
        
        # Add overbought/oversold lines for Stochastic
        fig.add_hline(y=80, line_dash="dash", line_color="red", opacity=0.5, row=3, col=1)
        fig.add_hline(y=20, line_dash="dash", line_color="green", opacity=0.5, row=3, col=1)
        
        # Update layout
        fig.update_layout(
            title=f'{symbol} Technical Analysis - {timeframe}',
            template='plotly_dark',
            height=800,
            showlegend=True
        )
        
        return fig

async def setup(bot):
    await bot.add_cog(ChartsCog(bot))