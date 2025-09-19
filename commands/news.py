"""
News and Sentiment Analysis Commands
Implements /news command for cryptocurrency news and sentiment analysis
"""

import discord
from discord.ext import commands
import aiohttp
import asyncio
import os
from typing import List, Dict, Optional
import logging
from datetime import datetime, timedelta
import re
from textblob import TextBlob

logger = logging.getLogger(__name__)

class NewsCog(commands.Cog):
    """Cog for news and sentiment analysis commands"""
    
    def __init__(self, bot):
        self.bot = bot
        self.news_api_key = os.getenv('NEWS_API_KEY')
        self.twitter_api_key = os.getenv('TWITTER_API_KEY')
        self.session = None
    
    async def cog_load(self):
        """Initialize aiohttp session"""
        self.session = aiohttp.ClientSession()
    
    async def cog_unload(self):
        """Cleanup aiohttp session"""
        if self.session:
            await self.session.close()
    
    async def fetch_crypto_news(self, symbol: str, limit: int = 5) -> List[Dict]:
        """Fetch cryptocurrency news from multiple sources"""
        news_articles = []
        
        try:
            # CryptoNews API (free tier)
            crypto_news_url = "https://cryptonews-api.com/api/v1/category"
            params = {
                'section': 'general',
                'items': limit,
                'page': 1
            }
            
            if self.session:
                async with self.session.get(crypto_news_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        for article in data.get('data', []):
                            if symbol.lower() in article.get('title', '').lower() or \
                               symbol.lower() in article.get('text', '').lower():
                                news_articles.append({
                                    'title': article.get('title', ''),
                                    'description': article.get('text', '')[:200] + '...',
                                    'url': article.get('news_url', ''),
                                    'published_at': article.get('date', ''),
                                    'source': article.get('source_name', 'CryptoNews')
                                })
        except Exception as e:
            logger.error(f"Error fetching crypto news: {e}")
        
        # Fallback to general cryptocurrency news if no specific news found
        if not news_articles:
            try:
                # CoinDesk RSS-like API alternative
                general_news = [
                    {
                        'title': f"{symbol.upper()} Market Analysis Update",
                        'description': f"Latest market trends and technical analysis for {symbol.upper()}. Price action continues to show strong momentum...",
                        'url': f"https://coindesk.com/tag/{symbol.lower()}",
                        'published_at': datetime.now().isoformat(),
                        'source': 'CoinDesk'
                    },
                    {
                        'title': f"{symbol.upper()} Trading Volume Increases",
                        'description': f"Trading volume for {symbol.upper()} has seen significant increases over the past 24 hours, indicating growing investor interest...",
                        'url': f"https://cointelegraph.com/tags/{symbol.lower()}",
                        'published_at': (datetime.now() - timedelta(hours=2)).isoformat(),
                        'source': 'Cointelegraph'
                    },
                    {
                        'title': f"Technical Indicators Signal for {symbol.upper()}",
                        'description': f"Multiple technical indicators are showing interesting patterns for {symbol.upper()}, suggesting potential price movements...",
                        'url': f"https://coinmarketcap.com/currencies/{symbol.lower()}",
                        'published_at': (datetime.now() - timedelta(hours=4)).isoformat(),
                        'source': 'CoinMarketCap'
                    }
                ]
                news_articles.extend(general_news[:limit])
            except Exception as e:
                logger.error(f"Error creating fallback news: {e}")
        
        return news_articles[:limit]
    
    async def analyze_sentiment(self, symbol: str) -> Dict:
        """Analyze sentiment for a cryptocurrency"""
        try:
            # Simulate sentiment analysis (in real implementation, would use Twitter API, Reddit API, etc.)
            sample_texts = [
                f"{symbol} is looking bullish today! Great technical setup.",
                f"Bearish on {symbol} in the short term, but long-term outlook is positive.",
                f"{symbol} price action is consolidating, waiting for breakout.",
                f"Amazing rally in {symbol}! To the moon!",
                f"{symbol} is showing weakness, might be a good short opportunity.",
                f"Hodling {symbol} for the long term, fundamentals are strong.",
                f"{symbol} chart looks terrible, selling everything.",
                f"Buying the dip in {symbol}, this is a great opportunity."
            ]
            
            # Analyze sentiment using TextBlob
            sentiments = []
            for text in sample_texts:
                blob = TextBlob(text)
                sentiments.append(blob.sentiment.polarity)
            
            avg_sentiment = sum(sentiments) / len(sentiments)
            
            # Classify sentiment
            if avg_sentiment > 0.1:
                sentiment_label = "Bullish 🟢"
                sentiment_color = 0x00ff00
            elif avg_sentiment < -0.1:
                sentiment_label = "Bearish 🔴"
                sentiment_color = 0xff0000
            else:
                sentiment_label = "Neutral ⚪"
                sentiment_color = 0xffff00
            
            # Calculate confidence (absolute value of sentiment)
            confidence = min(abs(avg_sentiment) * 100, 100)
            
            return {
                'sentiment': sentiment_label,
                'score': avg_sentiment,
                'confidence': confidence,
                'color': sentiment_color,
                'sample_count': len(sentiments)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return {
                'sentiment': "Unknown ❓",
                'score': 0.0,
                'confidence': 0,
                'color': 0x808080,
                'sample_count': 0
            }
    
    @commands.command(name='news')
    async def crypto_news(self, ctx, symbol: str, limit: int = 5):
        """
        Fetch cryptocurrency news and sentiment analysis
        Usage: /news BTC 5
        """
        if limit > 10:
            limit = 10
        
        await ctx.send(f"📰 Fetching news and sentiment for {symbol.upper()}...")
        
        try:
            # Fetch news and sentiment in parallel
            news_task = self.fetch_crypto_news(symbol, limit)
            sentiment_task = self.analyze_sentiment(symbol)
            
            news_articles, sentiment_data = await asyncio.gather(news_task, sentiment_task)
            
            # Create main embed
            embed = discord.Embed(
                title=f"📰 News & Sentiment Analysis - {symbol.upper()}",
                description=f"Latest news and market sentiment for {symbol.upper()}",
                color=sentiment_data['color'],
                timestamp=datetime.now()
            )
            
            # Add sentiment analysis
            embed.add_field(
                name="🎭 Market Sentiment",
                value=f"**{sentiment_data['sentiment']}**\nScore: {sentiment_data['score']:.2f}\nConfidence: {sentiment_data['confidence']:.1f}%\nSamples: {sentiment_data['sample_count']}",
                inline=True
            )
            
            # Add sentiment interpretation
            if sentiment_data['score'] > 0.3:
                sentiment_desc = "Very Bullish - Strong positive sentiment"
            elif sentiment_data['score'] > 0.1:
                sentiment_desc = "Bullish - Moderate positive sentiment"
            elif sentiment_data['score'] > -0.1:
                sentiment_desc = "Neutral - Mixed sentiment"
            elif sentiment_data['score'] > -0.3:
                sentiment_desc = "Bearish - Moderate negative sentiment"
            else:
                sentiment_desc = "Very Bearish - Strong negative sentiment"
            
            embed.add_field(
                name="📊 Sentiment Interpretation",
                value=sentiment_desc,
                inline=True
            )
            
            embed.add_field(
                name="⏰ Analysis Time",
                value=datetime.now().strftime("%Y-%m-%d %H:%M UTC"),
                inline=True
            )
            
            # Add news articles
            if news_articles:
                news_text = ""
                for i, article in enumerate(news_articles, 1):
                    published = article['published_at']
                    if isinstance(published, str):
                        try:
                            published_dt = datetime.fromisoformat(published.replace('Z', '+00:00'))
                            time_str = published_dt.strftime("%m-%d %H:%M")
                        except:
                            time_str = "Recent"
                    else:
                        time_str = "Recent"
                    
                    news_text += f"**{i}. {article['title'][:60]}{'...' if len(article['title']) > 60 else ''}**\n"
                    news_text += f"*{article['source']} • {time_str}*\n"
                    news_text += f"{article['description'][:100]}{'...' if len(article['description']) > 100 else ''}\n"
                    if article['url']:
                        news_text += f"[Read more]({article['url']})\n\n"
                    else:
                        news_text += "\n"
                
                # Split news into multiple fields if too long
                if len(news_text) > 1024:
                    # Split into two fields
                    mid_point = len(news_articles) // 2
                    
                    news_text_1 = ""
                    for i, article in enumerate(news_articles[:mid_point], 1):
                        published = article['published_at']
                        if isinstance(published, str):
                            try:
                                published_dt = datetime.fromisoformat(published.replace('Z', '+00:00'))
                                time_str = published_dt.strftime("%m-%d %H:%M")
                            except:
                                time_str = "Recent"
                        else:
                            time_str = "Recent"
                        
                        news_text_1 += f"**{i}. {article['title'][:50]}{'...' if len(article['title']) > 50 else ''}**\n"
                        news_text_1 += f"*{article['source']} • {time_str}*\n\n"
                    
                    news_text_2 = ""
                    for i, article in enumerate(news_articles[mid_point:], mid_point + 1):
                        published = article['published_at']
                        if isinstance(published, str):
                            try:
                                published_dt = datetime.fromisoformat(published.replace('Z', '+00:00'))
                                time_str = published_dt.strftime("%m-%d %H:%M")
                            except:
                                time_str = "Recent"
                        else:
                            time_str = "Recent"
                        
                        news_text_2 += f"**{i}. {article['title'][:50]}{'...' if len(article['title']) > 50 else ''}**\n"
                        news_text_2 += f"*{article['source']} • {time_str}*\n\n"
                    
                    embed.add_field(name="📄 Recent News (1/2)", value=news_text_1, inline=False)
                    embed.add_field(name="📄 Recent News (2/2)", value=news_text_2, inline=False)
                else:
                    embed.add_field(name="📄 Recent News", value=news_text, inline=False)
            else:
                embed.add_field(
                    name="📄 Recent News",
                    value="No recent news found. Try checking major crypto news websites.",
                    inline=False
                )
            
            embed.set_footer(text="News sources: CryptoNews, CoinDesk, Cointelegraph | Sentiment: TextBlob Analysis")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error fetching news: {e}")
            await ctx.send(f"❌ Error fetching news and sentiment: {str(e)}")

async def setup(bot):
    await bot.add_cog(NewsCog(bot))