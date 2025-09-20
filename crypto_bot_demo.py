#!/usr/bin/env python3
"""
Gelişmiş Kripto Analiz ve Sinyal Botu - Demo Versiyonu
Advanced Crypto Analysis and Signal Bot - Demo Version

Demo sürümü - API'lerin erişilemediği ortamlarda örnek verilerle çalışır.
Demo version - Works with sample data when APIs are not accessible.
"""

import argparse
import sys
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import random

class CryptoAnalysisBotDemo:
    """Demo kripto analiz botu sınıfı / Demo crypto analysis bot class"""
    
    def __init__(self, interval: str = '1d'):
        """
        Bot'u başlatır / Initialize the bot
        
        Args:
            interval (str): Analiz zaman dilimi / Analysis timeframe (1m, 5m, 15m, 1h, 4h, 1d)
        """
        self.interval = interval
        
        # Desteklenen zaman dilimleri / Supported timeframes
        self.supported_intervals = {
            '1m': '1m',
            '5m': '5m', 
            '15m': '15m',
            '1h': '1h',
            '4h': '4h',
            '1d': '1d'
        }
        
        if interval not in self.supported_intervals:
            raise ValueError(f"Desteklenmeyen zaman dilimi: {interval}. Desteklenenler: {list(self.supported_intervals.keys())}")
    
    def validate_interval(self, interval: str) -> bool:
        """Zaman dilimi formatını doğrular / Validate timeframe format"""
        return interval in self.supported_intervals
    
    def is_short_timeframe(self) -> bool:
        """Kısa zaman dilimi kontrolü (Binance API için) / Check if short timeframe (for Binance API)"""
        return self.interval in ['1m', '5m', '15m', '1h', '4h']
    
    def generate_sample_data(self, symbol: str = 'BTCUSDT', count: int = 100) -> List[float]:
        """
        Demo için örnek fiyat verisi üretir / Generate sample price data for demo
        
        Args:
            symbol (str): İşlem çifti / Trading pair
            count (int): Veri sayısı / Data count
            
        Returns:
            List[float]: Örnek fiyat verileri / Sample price data
        """
        # Başlangıç fiyatı sembolik olarak belirlenir
        base_prices = {
            'BTCUSDT': 63000,
            'ETHUSDT': 2500,
            'BNBUSDT': 580,
            'ADAUSDT': 0.35,
            'DOGEUSDT': 0.06
        }
        
        base_price = base_prices.get(symbol, 50000)
        prices = []
        current_price = base_price
        
        # Realistic price movement simulation
        for i in range(count):
            # Random walk with slight upward bias
            change_percent = random.gauss(0.001, 0.02)  # Small positive bias with 2% volatility
            current_price = current_price * (1 + change_percent)
            prices.append(current_price)
        
        return prices
    
    def calculate_sma(self, prices: List[float], period: int = 20) -> Optional[float]:
        """Basit hareketli ortalama hesaplar / Calculate Simple Moving Average"""
        if len(prices) < period:
            return None
        return sum(prices[-period:]) / period
    
    def calculate_rsi(self, prices: List[float], period: int = 14) -> Optional[float]:
        """RSI (Relative Strength Index) hesaplar / Calculate RSI"""
        if len(prices) < period + 1:
            return None
        
        gains = []
        losses = []
        
        for i in range(1, len(prices)):
            change = prices[i] - prices[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        
        if len(gains) < period:
            return None
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def perform_analysis(self, symbol: str = 'BTCUSDT') -> Dict:
        """
        Ana analiz fonksiyonu / Main analysis function
        
        Args:
            symbol (str): Analiz edilecek sembol / Symbol to analyze
            
        Returns:
            Dict: Analiz sonuçları / Analysis results
        """
        print(f"\n🔍 {symbol} için {self.interval} zaman diliminde analiz başlatılıyor...")
        print(f"🔍 Starting analysis for {symbol} on {self.interval} timeframe...")
        
        analysis_result = {
            'symbol': symbol,
            'interval': self.interval,
            'timestamp': datetime.now().isoformat(),
            'data_source': '',
            'prices': [],
            'technical_indicators': {},
            'signals': []
        }
        
        if self.is_short_timeframe():
            # Kısa zaman dilimleri için Binance API simülasyonu
            print(f"📊 Binance API simülasyonu - {self.interval} verileri oluşturuluyor...")
            prices = self.generate_sample_data(symbol, 100)
            analysis_result['data_source'] = 'Binance API (Demo Data)'
            analysis_result['prices'] = prices[-50:]  # Son 50 fiyat
            
            print(f"✅ {len(prices)} adet {self.interval} demo verisi oluşturuldu")
                
        else:
            # Günlük analiz için CoinGecko API simülasyonu
            print("📊 CoinGecko API simülasyonu - günlük veriler oluşturuluyor...")
            prices = self.generate_sample_data(symbol, 30)  # 30 günlük veri
            analysis_result['data_source'] = 'CoinGecko API (Demo Data)'
            analysis_result['prices'] = prices
            
            print(f"✅ {len(prices)} adet günlük demo verisi oluşturuldu")
        
        # Teknik analiz hesaplamaları
        if analysis_result['prices']:
            prices = analysis_result['prices']
            current_price = prices[-1]
            
            # SMA hesaplama
            sma_20 = self.calculate_sma(prices, min(20, len(prices)-1))
            sma_10 = self.calculate_sma(prices, min(10, len(prices)-1))
            
            # RSI hesaplama
            rsi = self.calculate_rsi(prices)
            
            analysis_result['technical_indicators'] = {
                'current_price': current_price,
                'sma_10': sma_10,
                'sma_20': sma_20,
                'rsi': rsi
            }
            
            # Sinyal üretimi
            signals = []
            
            if sma_10 and sma_20:
                if sma_10 > sma_20:
                    signals.append("🟢 SMA10 > SMA20: Yükseliş trendi")
                else:
                    signals.append("🔴 SMA10 < SMA20: Düşüş trendi")
            
            if rsi:
                if rsi > 70:
                    signals.append(f"⚠️ RSI {rsi:.2f}: Aşırı alım bölgesi")
                elif rsi < 30:
                    signals.append(f"💡 RSI {rsi:.2f}: Aşırı satım bölgesi")
                else:
                    signals.append(f"📊 RSI {rsi:.2f}: Normal seviye")
            
            analysis_result['signals'] = signals
        
        return analysis_result
    
    def display_results(self, analysis: Dict) -> None:
        """Analiz sonuçlarını gösterir / Display analysis results"""
        print(f"\n{'='*60}")
        print(f"📈 KRİPTO ANALİZ RAPORU / CRYPTO ANALYSIS REPORT")
        print(f"{'='*60}")
        print(f"🪙 Sembol / Symbol: {analysis['symbol']}")
        print(f"⏰ Zaman Dilimi / Timeframe: {analysis['interval']}")
        print(f"📅 Analiz Zamanı / Analysis Time: {analysis['timestamp']}")
        print(f"🔌 Veri Kaynağı / Data Source: {analysis['data_source']}")
        
        if analysis['technical_indicators']:
            indicators = analysis['technical_indicators']
            print(f"\n📊 TEKNİK GÖSTERGELER / TECHNICAL INDICATORS:")
            print(f"💰 Güncel Fiyat / Current Price: ${indicators['current_price']:.2f}")
            
            if indicators.get('sma_10'):
                print(f"📈 SMA 10: ${indicators['sma_10']:.2f}")
            if indicators.get('sma_20'):
                print(f"📈 SMA 20: ${indicators['sma_20']:.2f}")
            if indicators.get('rsi'):
                print(f"📊 RSI: {indicators['rsi']:.2f}")
        
        if analysis['signals']:
            print(f"\n🚨 SİNYALLER / SIGNALS:")
            for signal in analysis['signals']:
                print(f"  {signal}")
        
        print(f"{'='*60}")
        print(f"📝 NOT: Bu demo sürümünde örnek veriler kullanılmaktadır.")
        print(f"📝 NOTE: This demo version uses sample data.")


def parse_arguments() -> argparse.Namespace:
    """Komut satırı argümanlarını ayrıştırır / Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Gelişmiş Kripto Analiz ve Sinyal Botu - Demo / Advanced Crypto Analysis and Signal Bot - Demo',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Örnekler / Examples:
  python crypto_bot_demo.py --interval 1h
  python crypto_bot_demo.py -t 5m --symbol ETHUSDT
  python crypto_bot_demo.py --interactive
  python crypto_bot_demo.py  (varsayılan: 1d)
  
Desteklenen zaman dilimleri / Supported timeframes:
  1m, 5m, 15m, 1h, 4h, 1d
        """
    )
    
    parser.add_argument(
        '--interval', '-t',
        type=str,
        default='1d',
        help='Analiz zaman dilimi / Analysis timeframe (1m, 5m, 15m, 1h, 4h, 1d). Varsayılan: 1d'
    )
    
    parser.add_argument(
        '--symbol', '-s',
        type=str,
        default='BTCUSDT',
        help='Analiz edilecek kripto çifti / Crypto pair to analyze (default: BTCUSDT)'
    )
    
    parser.add_argument(
        '--interactive', '-i',
        action='store_true',
        help='İnteraktif mod / Interactive mode'
    )
    
    return parser.parse_args()


def interactive_mode():
    """İnteraktif mod fonksiyonu / Interactive mode function"""
    print("\n🤖 Gelişmiş Kripto Analiz Botu - İnteraktif Demo Modu")
    print("🤖 Advanced Crypto Analysis Bot - Interactive Demo Mode")
    print("="*55)
    
    while True:
        print("\nDesteklenen zaman dilimleri / Supported timeframes:")
        print("1m, 5m, 15m, 1h, 4h, 1d")
        
        interval = input("\nZaman dilimi seçin (varsayılan: 1d) / Select timeframe (default: 1d): ").strip()
        if not interval:
            interval = '1d'
        
        symbol = input("Kripto çifti (varsayılan: BTCUSDT) / Crypto pair (default: BTCUSDT): ").strip()
        if not symbol:
            symbol = 'BTCUSDT'
        
        try:
            bot = CryptoAnalysisBotDemo(interval)
            analysis = bot.perform_analysis(symbol)
            bot.display_results(analysis)
            
        except ValueError as e:
            print(f"❌ Hata: {e}")
            continue
        except Exception as e:
            print(f"❌ Beklenmeyen hata: {e}")
            continue
        
        again = input("\nBaşka analiz yapmak ister misiniz? (e/h) / Want to do another analysis? (y/n): ").strip().lower()
        if again not in ['e', 'y', 'evet', 'yes']:
            break
    
    print("\n👋 Güle güle! / Goodbye!")


def main():
    """Ana fonksiyon / Main function"""
    args = parse_arguments()
    
    if args.interactive:
        interactive_mode()
        return
    
    try:
        bot = CryptoAnalysisBotDemo(args.interval)
        analysis = bot.perform_analysis(args.symbol)
        bot.display_results(analysis)
        
    except ValueError as e:
        print(f"❌ Hata: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Beklenmeyen hata: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()