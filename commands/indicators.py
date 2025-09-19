"""
Technical Indicators Commands
Implements /indicators command with MACD, Bollinger Bands, Stochastic, EMA, SMA
"""

import discord
from discord.ext import commands
import pandas as pd
import ccxt
import asyncio
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class TechnicalIndicatorsCog(commands.Cog):
    """Cog for technical indicators commands"""
    
    def __init__(self, bot):
        self.bot = bot
        self.exchange = ccxt.binance()  # Using Binance as default exchange
    
    async def fetch_ohlcv_data(self, symbol: str, timeframe: str = '1h', limit: int = 100) -> Optional[pd.DataFrame]:
        """Fetch OHLCV data for a symbol"""
        try:
            # Normalize symbol format for exchange
            if not symbol.endswith('USDT') and '/' not in symbol:
                symbol = f"{symbol.upper()}/USDT"
            
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return None
    
    @commands.command(name='indicators')
    async def technical_indicators(self, ctx, symbol: str, timeframe: str = '1h'):
        """
        Display technical indicators for a cryptocurrency
        Usage: /indicators BTC 1h
        """
        await ctx.send(f"🔄 Calculating technical indicators for {symbol.upper()}...")
        
        # Fetch market data
        df = await self.fetch_ohlcv_data(symbol, timeframe)
        if df is None:
            await ctx.send(f"❌ Could not fetch data for {symbol.upper()}. Please check the symbol.")
            return
        
        try:
            # Calculate indicators using bot's technical_indicators module
            indicators = self.bot.technical_indicators
            
            # SMA calculations
            sma_20 = indicators.calculate_sma(df['close'], 20)
            sma_50 = indicators.calculate_sma(df['close'], 50)
            
            # EMA calculations  
            ema_12 = indicators.calculate_ema(df['close'], 12)
            ema_26 = indicators.calculate_ema(df['close'], 26)
            
            # MACD calculation
            macd_data = indicators.calculate_macd(df['close'])
            
            # Bollinger Bands
            bb_data = indicators.calculate_bollinger_bands(df['close'])
            
            # Stochastic Oscillator
            stoch_data = indicators.calculate_stochastic(df['high'], df['low'], df['close'])
            
            # Get latest values
            latest_price = df['close'].iloc[-1]
            latest_sma_20 = sma_20.iloc[-1]
            latest_sma_50 = sma_50.iloc[-1]
            latest_ema_12 = ema_12.iloc[-1]
            latest_ema_26 = ema_26.iloc[-1]
            latest_macd = macd_data['macd'].iloc[-1]
            latest_signal = macd_data['signal'].iloc[-1]
            latest_bb_upper = bb_data['upper'].iloc[-1]
            latest_bb_lower = bb_data['lower'].iloc[-1]
            latest_stoch_k = stoch_data['k'].iloc[-1]
            latest_stoch_d = stoch_data['d'].iloc[-1]
            
            # Generate signals
            signals = []
            
            # MACD Signal
            if latest_macd > latest_signal:
                signals.append("🟢 MACD: Bullish")
            else:
                signals.append("🔴 MACD: Bearish")
            
            # Bollinger Bands Signal
            if latest_price > latest_bb_upper:
                signals.append("🟡 BB: Overbought")
            elif latest_price < latest_bb_lower:
                signals.append("🟢 BB: Oversold") 
            else:
                signals.append("⚪ BB: Neutral")
            
            # Stochastic Signal
            if latest_stoch_k > 80:
                signals.append("🔴 Stoch: Overbought")
            elif latest_stoch_k < 20:
                signals.append("🟢 Stoch: Oversold")
            else:
                signals.append("⚪ Stoch: Neutral")
            
            # Moving Average Signal
            if latest_price > latest_sma_20 > latest_sma_50:
                signals.append("🟢 MA: Strong Uptrend")
            elif latest_price > latest_sma_20:
                signals.append("🟡 MA: Weak Uptrend")
            else:
                signals.append("🔴 MA: Downtrend")
            
            # Create embed
            embed = discord.Embed(
                title=f"📊 Technical Indicators - {symbol.upper()}",
                description=f"Current Price: **${latest_price:.2f}**",
                color=0x00ff00 if latest_price > latest_sma_20 else 0xff0000,
                timestamp=df['timestamp'].iloc[-1]
            )
            
            # Add indicator fields
            embed.add_field(
                name="📈 Moving Averages",
                value=f"SMA 20: ${latest_sma_20:.2f}\nSMA 50: ${latest_sma_50:.2f}\nEMA 12: ${latest_ema_12:.2f}\nEMA 26: ${latest_ema_26:.2f}",
                inline=True
            )
            
            embed.add_field(
                name="📊 MACD",
                value=f"MACD: {latest_macd:.4f}\nSignal: {latest_signal:.4f}\nHistogram: {latest_macd - latest_signal:.4f}",
                inline=True
            )
            
            embed.add_field(
                name="📏 Bollinger Bands",
                value=f"Upper: ${latest_bb_upper:.2f}\nMiddle: ${bb_data['middle'].iloc[-1]:.2f}\nLower: ${latest_bb_lower:.2f}",
                inline=True
            )
            
            embed.add_field(
                name="🎯 Stochastic",
                value=f"%K: {latest_stoch_k:.2f}\n%D: {latest_stoch_d:.2f}",
                inline=True
            )
            
            embed.add_field(
                name="🚦 Signals",
                value="\n".join(signals),
                inline=False
            )
            
            embed.set_footer(text=f"Timeframe: {timeframe} | Data from Binance")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")
            await ctx.send(f"❌ Error calculating indicators: {str(e)}")

async def setup(bot):
    await bot.add_cog(TechnicalIndicatorsCog(bot))