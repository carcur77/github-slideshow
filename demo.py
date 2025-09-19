#!/usr/bin/env python3
"""
Trading Signal Bot Demo
Demonstrates core functionality without Discord dependencies
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class TechnicalIndicators:
    """Technical indicators calculation engine"""
    
    @staticmethod
    def calculate_sma(data: pd.Series, window: int) -> pd.Series:
        """Calculate Simple Moving Average"""
        return data.rolling(window=window).mean()
    
    @staticmethod  
    def calculate_ema(data: pd.Series, window: int) -> pd.Series:
        """Calculate Exponential Moving Average"""
        return data.ewm(span=window).mean()
    
    @staticmethod
    def calculate_macd(data: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> dict:
        """Calculate MACD indicator"""
        ema_fast = TechnicalIndicators.calculate_ema(data, fast)
        ema_slow = TechnicalIndicators.calculate_ema(data, slow)
        macd_line = ema_fast - ema_slow
        signal_line = TechnicalIndicators.calculate_ema(macd_line, signal)
        histogram = macd_line - signal_line
        
        return {
            'macd': macd_line,
            'signal': signal_line, 
            'histogram': histogram
        }
    
    @staticmethod
    def calculate_bollinger_bands(data: pd.Series, window: int = 20, std_dev: int = 2) -> dict:
        """Calculate Bollinger Bands"""
        sma = TechnicalIndicators.calculate_sma(data, window)
        std = data.rolling(window=window).std()
        
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        
        return {
            'upper': upper_band,
            'middle': sma,
            'lower': lower_band
        }
    
    @staticmethod
    def calculate_stochastic(high: pd.Series, low: pd.Series, close: pd.Series, 
                           k_window: int = 14, d_window: int = 3) -> dict:
        """Calculate Stochastic Oscillator"""
        lowest_low = low.rolling(window=k_window).min()
        highest_high = high.rolling(window=k_window).max()
        
        k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low))
        d_percent = k_percent.rolling(window=d_window).mean()
        
        return {
            'k': k_percent,
            'd': d_percent
        }

def generate_sample_data(days: int = 30) -> pd.DataFrame:
    """Generate realistic sample cryptocurrency price data"""
    np.random.seed(42)
    
    # Generate timestamps
    start_date = datetime.now() - timedelta(days=days)
    timestamps = pd.date_range(start=start_date, periods=days*24, freq='H')
    
    # Generate price data using random walk with trend
    price_changes = np.random.normal(0.001, 0.02, len(timestamps))  # Small positive drift with volatility
    prices = [50000]  # Starting price of $50,000
    
    for change in price_changes[1:]:
        new_price = prices[-1] * (1 + change)
        prices.append(max(new_price, 1000))  # Prevent negative prices
    
    # Generate volume data
    volumes = np.random.lognormal(10, 0.5, len(timestamps))
    
    # Generate OHLC data
    df = pd.DataFrame({
        'timestamp': timestamps,
        'close': prices
    })
    
    # Generate high and low based on close
    df['high'] = df['close'] * (1 + np.random.uniform(0, 0.02, len(df)))
    df['low'] = df['close'] * (1 - np.random.uniform(0, 0.02, len(df)))
    df['open'] = df['close'].shift(1).fillna(df['close'].iloc[0])
    df['volume'] = volumes
    
    return df

def analyze_signals(df: pd.DataFrame, indicators: TechnicalIndicators) -> dict:
    """Analyze trading signals based on technical indicators"""
    
    # Calculate indicators
    sma_20 = indicators.calculate_sma(df['close'], 20)
    sma_50 = indicators.calculate_sma(df['close'], 50)
    ema_12 = indicators.calculate_ema(df['close'], 12)
    
    macd_data = indicators.calculate_macd(df['close'])
    bb_data = indicators.calculate_bollinger_bands(df['close'])
    stoch_data = indicators.calculate_stochastic(df['high'], df['low'], df['close'])
    
    # Get latest values
    latest_price = df['close'].iloc[-1]
    latest_sma_20 = sma_20.iloc[-1]
    latest_sma_50 = sma_50.iloc[-1]
    latest_macd = macd_data['macd'].iloc[-1]
    latest_signal = macd_data['signal'].iloc[-1]
    latest_bb_upper = bb_data['upper'].iloc[-1]
    latest_bb_lower = bb_data['lower'].iloc[-1]
    latest_stoch_k = stoch_data['k'].iloc[-1]
    
    # Generate signals
    signals = []
    signal_strength = 0
    
    # MACD Signal
    if latest_macd > latest_signal:
        signals.append("🟢 MACD: Bullish")
        signal_strength += 1
    else:
        signals.append("🔴 MACD: Bearish")
        signal_strength -= 1
    
    # Bollinger Bands Signal
    if latest_price > latest_bb_upper:
        signals.append("🟡 BB: Overbought")
        signal_strength -= 0.5
    elif latest_price < latest_bb_lower:
        signals.append("🟢 BB: Oversold (Buy opportunity)")
        signal_strength += 1
    else:
        signals.append("⚪ BB: Neutral")
    
    # Stochastic Signal
    if latest_stoch_k > 80:
        signals.append("🔴 Stoch: Overbought")
        signal_strength -= 0.5
    elif latest_stoch_k < 20:
        signals.append("🟢 Stoch: Oversold (Buy opportunity)")
        signal_strength += 1
    else:
        signals.append("⚪ Stoch: Neutral")
    
    # Moving Average Signal
    if latest_price > latest_sma_20 > latest_sma_50:
        signals.append("🟢 MA: Strong Uptrend")
        signal_strength += 2
    elif latest_price > latest_sma_20:
        signals.append("🟡 MA: Weak Uptrend")
        signal_strength += 0.5
    else:
        signals.append("🔴 MA: Downtrend")
        signal_strength -= 1
    
    # Overall signal
    if signal_strength >= 2:
        overall_signal = "🚀 STRONG BUY"
    elif signal_strength >= 1:
        overall_signal = "🟢 BUY"
    elif signal_strength <= -2:
        overall_signal = "📉 STRONG SELL"
    elif signal_strength <= -1:
        overall_signal = "🔴 SELL"
    else:
        overall_signal = "⚪ HOLD"
    
    return {
        'signals': signals,
        'overall_signal': overall_signal,
        'signal_strength': signal_strength,
        'latest_price': latest_price,
        'indicators': {
            'sma_20': latest_sma_20,
            'sma_50': latest_sma_50,
            'ema_12': ema_12.iloc[-1],
            'macd': latest_macd,
            'bb_upper': latest_bb_upper,
            'bb_lower': latest_bb_lower,
            'stoch_k': latest_stoch_k
        }
    }

def create_chart(df: pd.DataFrame, indicators: TechnicalIndicators, save_path: str = None):
    """Create a technical analysis chart"""
    
    plt.style.use('dark_background')
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(14, 10), 
                                       gridspec_kw={'height_ratios': [3, 1, 1]})
    
    # Main price chart
    ax1.plot(df['timestamp'], df['close'], label='Price', color='#00D4AA', linewidth=2)
    
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
    
    ax1.set_title('Cryptocurrency Technical Analysis Demo', fontsize=16, fontweight='bold')
    ax1.set_ylabel('Price (USD)', fontsize=12)
    ax1.legend(loc='upper left')
    ax1.grid(True, alpha=0.3)
    
    # MACD
    macd_data = indicators.calculate_macd(df['close'])
    ax2.plot(df['timestamp'], macd_data['macd'], label='MACD', color='#00D4AA')
    ax2.plot(df['timestamp'], macd_data['signal'], label='Signal', color='#FF6B35')
    ax2.bar(df['timestamp'], macd_data['histogram'], label='Histogram', color='#FFE135', alpha=0.6, width=0.02)
    ax2.axhline(y=0, color='white', linestyle='-', alpha=0.3)
    ax2.set_ylabel('MACD', fontsize=12)
    ax2.legend(loc='upper left')
    ax2.grid(True, alpha=0.3)
    
    # Stochastic
    stoch_data = indicators.calculate_stochastic(df['high'], df['low'], df['close'])
    ax3.plot(df['timestamp'], stoch_data['k'], label='%K', color='#00D4AA')
    ax3.plot(df['timestamp'], stoch_data['d'], label='%D', color='#FF6B35')
    ax3.axhline(y=80, color='red', linestyle='--', alpha=0.5, label='Overbought')
    ax3.axhline(y=20, color='green', linestyle='--', alpha=0.5, label='Oversold')
    ax3.fill_between(df['timestamp'], 80, 100, alpha=0.1, color='red')
    ax3.fill_between(df['timestamp'], 0, 20, alpha=0.1, color='green')
    ax3.set_ylabel('Stochastic %', fontsize=12)
    ax3.set_xlabel('Time', fontsize=12)
    ax3.legend(loc='upper left')
    ax3.grid(True, alpha=0.3)
    ax3.set_ylim(0, 100)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='#2C2F33')
        print(f"📊 Chart saved to: {save_path}")
    
    return fig

def main():
    """Main demo function"""
    print("🤖 Trading Signal Bot Demo")
    print("=" * 50)
    
    # Initialize components
    indicators = TechnicalIndicators()
    
    # Generate sample data
    print("📈 Generating sample cryptocurrency data...")
    df = generate_sample_data(30)  # 30 days of hourly data
    print(f"✅ Generated {len(df)} data points")
    
    # Analyze signals
    print("\n🔍 Analyzing technical indicators...")
    analysis = analyze_signals(df, indicators)
    
    # Display results
    print(f"\n💰 Current Price: ${analysis['latest_price']:,.2f}")
    print(f"🚦 Overall Signal: {analysis['overall_signal']}")
    print(f"💪 Signal Strength: {analysis['signal_strength']:.1f}")
    
    print("\n📊 Individual Signals:")
    for signal in analysis['signals']:
        print(f"   {signal}")
    
    print("\n📈 Technical Indicators:")
    indicators_data = analysis['indicators']
    print(f"   SMA 20: ${indicators_data['sma_20']:,.2f}")
    print(f"   SMA 50: ${indicators_data['sma_50']:,.2f}")
    print(f"   EMA 12: ${indicators_data['ema_12']:,.2f}")
    print(f"   MACD: {indicators_data['macd']:.4f}")
    print(f"   BB Upper: ${indicators_data['bb_upper']:,.2f}")
    print(f"   BB Lower: ${indicators_data['bb_lower']:,.2f}")
    print(f"   Stochastic %K: {indicators_data['stoch_k']:.2f}")
    
    # Create and display chart
    print("\n📊 Generating technical analysis chart...")
    try:
        chart_path = "/tmp/technical_analysis_demo.png"
        fig = create_chart(df, indicators, chart_path)
        plt.show()
    except Exception as e:
        print(f"⚠️  Chart generation failed: {e}")
        print("📊 Chart would be displayed here in a full environment")
    
    print("\n✨ Demo completed successfully!")
    print("\n🔧 In the full Discord bot, you would use commands like:")
    print("   /indicators BTC 1h")
    print("   /chart BTC 1h matplotlib")
    print("   /news BTC 5")
    print("   /predict BTC 1h")
    print("   /onchain BTC whale")

if __name__ == "__main__":
    main()