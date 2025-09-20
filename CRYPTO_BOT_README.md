# Gelişmiş Kripto Analiz ve Sinyal Botu / Advanced Crypto Analysis and Signal Bot

Bu bot, farklı zaman dilimlerinde kripto para analizi yapar ve teknik sinyal üretir.
This bot performs cryptocurrency analysis in different timeframes and generates technical signals.

## Özellikler / Features

- 🕐 **Çoklu Zaman Dilimi Desteği**: 1m, 5m, 15m, 1h, 4h, 1d
- 🔌 **Çift API Entegrasyonu**: Binance (kısa vadeli) + CoinGecko (günlük)
- 📊 **Teknik Analiz**: SMA, RSI hesaplamaları
- 🚨 **Otomatik Sinyal Üretimi**: Trend ve momentum analizi
- 💻 **Komut Satırı + İnteraktif Mod**: Esnek kullanım
- 🌍 **Çift Dil Desteği**: Türkçe + İngilizce

## Kurulum / Installation

```bash
# Gereksinimler / Requirements
pip install -r requirements.txt

# Botu çalıştırmak için / To run the bot
python crypto_bot.py --help
```

## Kullanım / Usage

### Komut Satırı Modu / Command Line Mode

```bash
# Varsayılan (1 günlük Bitcoin analizi)
python crypto_bot.py

# 1 saatlik Bitcoin analizi
python crypto_bot.py --interval 1h

# 5 dakikalık Ethereum analizi
python crypto_bot.py -t 5m --symbol ETHUSDT

# 15 dakikalık analiz
python crypto_bot.py --interval 15m

# 4 saatlik analiz
python crypto_bot.py -t 4h
```

### İnteraktif Mod / Interactive Mode

```bash
python crypto_bot.py --interactive
# veya / or
python crypto_bot.py -i
```

## Desteklenen Zaman Dilimleri / Supported Timeframes

| Kısaltma | Açıklama | API Kaynağı |
|----------|----------|-------------|
| `1m` | 1 dakika | Binance |
| `5m` | 5 dakika | Binance |
| `15m` | 15 dakika | Binance |
| `1h` | 1 saat | Binance |
| `4h` | 4 saat | Binance |
| `1d` | 1 gün (varsayılan) | CoinGecko |

## Teknik Göstergeler / Technical Indicators

- **SMA (Simple Moving Average)**: 10 ve 20 periyot hareketli ortalamalar
- **RSI (Relative Strength Index)**: 14 periyot momentum osilatörü
- **Trend Analizi**: SMA çaprazlaması ile trend yönü
- **Momentum Sinyalleri**: RSI seviyelerine göre aşırı alım/satım

## API Kaynakları / API Sources

### Binance API (Kısa Vadeli / Short-term)
- **Endpoint**: `/api/v3/klines`
- **Kullanım**: 1m, 5m, 15m, 1h, 4h zaman dilimleri
- **Avantaj**: Gerçek zamanlı, yüksek frekanslı veriler

### CoinGecko API (Günlük / Daily)
- **Endpoint**: `/api/v3/coins/{id}/market_chart`
- **Kullanım**: 1d zaman dilimi
- **Avantaj**: Ücretsiz, stabil günlük veriler

## Örnek Çıktı / Sample Output

```
============================================================
📈 KRİPTO ANALİZ RAPORU / CRYPTO ANALYSIS REPORT
============================================================
🪙 Sembol / Symbol: BTCUSDT
⏰ Zaman Dilimi / Timeframe: 1h
📅 Analiz Zamanı / Analysis Time: 2024-09-20T21:30:15
🔌 Veri Kaynağı / Data Source: Binance API

📊 TEKNİK GÖSTERGELER / TECHNICAL INDICATORS:
💰 Güncel Fiyat / Current Price: $63,250.45
📈 SMA 10: $63,100.23
📈 SMA 20: $62,980.67
📊 RSI: 58.32

🚨 SİNYALLER / SIGNALS:
  🟢 SMA10 > SMA20: Yükseliş trendi
  📊 RSI 58.32: Normal seviye
============================================================
```

## Geliştirici Notları / Developer Notes

- **Varsayılan Zaman Dilimi**: 1d (günlük)
- **Hata Yönetimi**: API bağlantı sorunları için otomatik hata yakalama
- **Veri Limiti**: Performans için son 100 veri noktası
- **Timeout**: API istekleri için 10 saniye timeout

## Lisans / License

Bu proje MIT lisansı altında lisanslanmıştır.
This project is licensed under the MIT License.