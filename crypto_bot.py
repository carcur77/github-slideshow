#!/usr/bin/env python3
"""
Gelişmiş Kripto Analiz ve Sinyal Botu
Advanced Crypto Analysis and Signal Bot

Bu bot, farklı zaman dilimlerinde kripto para analizi yapar ve sinyal üretir.
This bot performs cryptocurrency analysis and generates signals for different timeframes.
"""

import argparse
import sys
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import time

class CryptoAnalysisBot:
    """Ana kripto analiz botu sınıfı / Main crypto analysis bot class"""
    
    def __init__(self, interval: str = '1d'):
        """
        Bot'u başlatır / Initialize the bot
        
        Args:
            interval (str): Analiz zaman dilimi / Analysis timeframe (1m, 5m, 15m, 1h, 4h, 1d)
        """
        self.interval = interval
        self.binance_base_url = "https://api.binance.com/api/v3"
        self.coingecko_base_url = "https://api.coingecko.com/api/v3"
        
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
    
    def get_binance_klines(self, symbol: str = 'BTCUSDT', limit: int = 100) -> List[List]:
        """
        Binance API'den kline verisi çeker / Fetch kline data from Binance API
        
        Args:
            symbol (str): İşlem çifti / Trading pair
            limit (int): Maksimum veri sayısı / Maximum data count
            
        Returns:
            List[List]: Kline verileri / Kline data
        """
        try:
            url = f"{self.binance_base_url}/klines"
            params = {
                'symbol': symbol,
                'interval': self.supported_intervals[self.interval],
                'limit': limit
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"Binance API hatası: {e}")
            return []
    
    def get_coingecko_data(self, coin_id: str = 'bitcoin', days: int = 30) -> Dict:
        """
        CoinGecko API'den günlük veri çeker / Fetch daily data from CoinGecko API
        
        Args:
            coin_id (str): Coin kimliği / Coin ID
            days (int): Gün sayısı / Number of days
            
        Returns:
            Dict: Fiyat verileri / Price data
        """
        try:
            url = f"{self.coingecko_base_url}/coins/{coin_id}/market_chart"
            params = {
                'vs_currency': 'usd',
                'days': days,
                'interval': 'daily'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"CoinGecko API hatası: {e}")
            return {}
    
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
            # Kısa zaman dilimleri için Binance API kullan
            print(f"📊 Binance API'den {self.interval} verileri çekiliyor...")
            klines = self.get_binance_klines(symbol)
            
            if klines:
                analysis_result['data_source'] = 'Binance API'
                # Kline formatı: [open_time, open, high, low, close, volume, ...]
                prices = [float(kline[4]) for kline in klines]  # Kapanış fiyatları
                analysis_result['prices'] = prices[-20:]  # Son 20 fiyat
                
                print(f"✅ {len(prices)} adet {self.interval} verisi alındı")
                
            else:
                print("❌ Binance API'den veri alınamadı")
                return analysis_result
                
        else:
            # Günlük analiz için CoinGecko API kullan
            print("📊 CoinGecko API'den günlük veriler çekiliyor...")
            coin_id = 'bitcoin' if symbol.startswith('BTC') else 'ethereum'
            data = self.get_coingecko_data(coin_id)
            
            if data and 'prices' in data:
                analysis_result['data_source'] = 'CoinGecko API'
                prices = [price[1] for price in data['prices']]  # Fiyat değerleri
                analysis_result['prices'] = prices[-20:]  # Son 20 fiyat
                
                print(f"✅ {len(prices)} adet günlük verisi alındı")
                
            else:
                print("❌ CoinGecko API'den veri alınamadı")
                return analysis_result
        
        # Teknik analiz hesaplamaları
        if analysis_result['prices']:
            prices = analysis_result['prices']
            current_price = prices[-1]
            
            # SMA hesaplama
            sma_20 = self.calculate_sma(prices, 20)
            sma_10 = self.calculate_sma(prices, 10)
            
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


def parse_arguments() -> argparse.Namespace:
    """Komut satırı argümanlarını ayrıştırır / Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Gelişmiş Kripto Analiz ve Sinyal Botu / Advanced Crypto Analysis and Signal Bot',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Örnekler / Examples:
  python crypto_bot.py --interval 1h
  python crypto_bot.py -t 5m --symbol ETHUSDT
  python crypto_bot.py --interactive
  python crypto_bot.py  (varsayılan: 1d)
  
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
    print("\n🤖 Gelişmiş Kripto Analiz Botu - İnteraktif Mod")
    print("🤖 Advanced Crypto Analysis Bot - Interactive Mode")
    print("="*50)
    
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
            bot = CryptoAnalysisBot(interval)
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
        bot = CryptoAnalysisBot(args.interval)
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