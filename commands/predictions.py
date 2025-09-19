"""
AI Market Predictions Commands
Implements AI-based market predictions using historical data and technical indicators
"""

import discord
from discord.ext import commands
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import ccxt
from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

class PredictionsCog(commands.Cog):
    """Cog for AI-based market predictions"""
    
    def __init__(self, bot):
        self.bot = bot
        self.exchange = ccxt.binance()
        self.models = {}  # Cache for trained models
        self.scalers = {}  # Cache for data scalers
    
    async def fetch_extended_data(self, symbol: str, timeframe: str = '1h', limit: int = 500) -> Optional[pd.DataFrame]:
        """Fetch extended historical data for training"""
        try:
            if not symbol.endswith('USDT') and '/' not in symbol:
                symbol = f"{symbol.upper()}/USDT"
            
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
        except Exception as e:
            logger.error(f"Error fetching extended data for {symbol}: {e}")
            return None
    
    def create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create features for ML model"""
        features_df = df.copy()
        
        # Technical indicators as features
        indicators = self.bot.technical_indicators
        
        # Moving averages
        features_df['sma_5'] = indicators.calculate_sma(df['close'], 5)
        features_df['sma_10'] = indicators.calculate_sma(df['close'], 10)
        features_df['sma_20'] = indicators.calculate_sma(df['close'], 20)
        features_df['sma_50'] = indicators.calculate_sma(df['close'], 50)
        features_df['ema_12'] = indicators.calculate_ema(df['close'], 12)
        features_df['ema_26'] = indicators.calculate_ema(df['close'], 26)
        
        # MACD
        macd_data = indicators.calculate_macd(df['close'])
        features_df['macd'] = macd_data['macd']
        features_df['macd_signal'] = macd_data['signal']
        features_df['macd_histogram'] = macd_data['histogram']
        
        # Bollinger Bands
        bb_data = indicators.calculate_bollinger_bands(df['close'])
        features_df['bb_upper'] = bb_data['upper']
        features_df['bb_middle'] = bb_data['middle']
        features_df['bb_lower'] = bb_data['lower']
        features_df['bb_width'] = bb_data['upper'] - bb_data['lower']
        features_df['bb_position'] = (df['close'] - bb_data['lower']) / (bb_data['upper'] - bb_data['lower'])
        
        # Stochastic
        stoch_data = indicators.calculate_stochastic(df['high'], df['low'], df['close'])
        features_df['stoch_k'] = stoch_data['k']
        features_df['stoch_d'] = stoch_data['d']
        
        # Price-based features
        features_df['price_change'] = df['close'].pct_change()
        features_df['high_low_ratio'] = df['high'] / df['low']
        features_df['close_open_ratio'] = df['close'] / df['open']
        features_df['volume_sma'] = indicators.calculate_sma(df['volume'], 20)
        features_df['volume_ratio'] = df['volume'] / features_df['volume_sma']
        
        # Lag features
        for lag in [1, 2, 3, 5]:
            features_df[f'close_lag_{lag}'] = df['close'].shift(lag)
            features_df[f'volume_lag_{lag}'] = df['volume'].shift(lag)
            features_df[f'price_change_lag_{lag}'] = features_df['price_change'].shift(lag)
        
        # Volatility features
        features_df['volatility_10'] = df['close'].rolling(10).std()
        features_df['volatility_20'] = df['close'].rolling(20).std()
        
        # Hour of day (cyclical encoding)
        features_df['hour'] = features_df['timestamp'].dt.hour
        features_df['hour_sin'] = np.sin(2 * np.pi * features_df['hour'] / 24)
        features_df['hour_cos'] = np.cos(2 * np.pi * features_df['hour'] / 24)
        
        # Day of week
        features_df['day_of_week'] = features_df['timestamp'].dt.dayofweek
        features_df['day_sin'] = np.sin(2 * np.pi * features_df['day_of_week'] / 7)
        features_df['day_cos'] = np.cos(2 * np.pi * features_df['day_of_week'] / 7)
        
        return features_df
    
    async def train_prediction_model(self, symbol: str, timeframe: str = '1h') -> Tuple[Optional[RandomForestRegressor], Optional[StandardScaler], Dict]:
        """Train ML model for price prediction"""
        try:
            # Fetch extended historical data
            df = await self.fetch_extended_data(symbol, timeframe, limit=1000)
            if df is None or len(df) < 100:
                return None, None, {'error': 'Insufficient data for training'}
            
            # Create features
            features_df = self.create_features(df)
            
            # Define feature columns (exclude non-feature columns)
            exclude_cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
            feature_cols = [col for col in features_df.columns if col not in exclude_cols]
            
            # Prepare data
            X = features_df[feature_cols].dropna()
            
            # Target: next period's close price
            y = features_df['close'].shift(-1).dropna()
            
            # Align X and y
            min_len = min(len(X), len(y))
            X = X.iloc[:min_len]
            y = y.iloc[:min_len]
            
            if len(X) < 50:
                return None, None, {'error': 'Insufficient clean data for training'}
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # Train Random Forest model
            model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42,
                n_jobs=-1
            )
            
            model.fit(X_train_scaled, y_train)
            
            # Evaluate model
            train_pred = model.predict(X_train_scaled)
            test_pred = model.predict(X_test_scaled)
            
            train_mae = mean_absolute_error(y_train, train_pred)
            test_mae = mean_absolute_error(y_test, test_pred)
            train_r2 = r2_score(y_train, train_pred)
            test_r2 = r2_score(y_test, test_pred)
            
            metrics = {
                'train_mae': train_mae,
                'test_mae': test_mae,
                'train_r2': train_r2,
                'test_r2': test_r2,
                'feature_count': len(feature_cols),
                'training_samples': len(X_train),
                'test_samples': len(X_test)
            }
            
            # Cache model and scaler
            model_key = f"{symbol}_{timeframe}"
            self.models[model_key] = model
            self.scalers[model_key] = scaler
            
            return model, scaler, metrics
            
        except Exception as e:
            logger.error(f"Error training prediction model: {e}")
            return None, None, {'error': str(e)}
    
    async def make_prediction(self, symbol: str, timeframe: str = '1h') -> Dict:
        """Make price prediction using trained model"""
        try:
            model_key = f"{symbol}_{timeframe}"
            
            # Check if model exists in cache
            if model_key not in self.models:
                await ctx.send("🔄 Training AI model... This may take a moment.")
                model, scaler, metrics = await self.train_prediction_model(symbol, timeframe)
                if model is None:
                    return {'error': metrics.get('error', 'Failed to train model')}
            else:
                model = self.models[model_key]
                scaler = self.scalers[model_key]
                metrics = {'cached': True}
            
            # Fetch recent data for prediction
            df = await self.fetch_extended_data(symbol, timeframe, limit=200)
            if df is None:
                return {'error': 'Failed to fetch recent data'}
            
            # Create features for latest data point
            features_df = self.create_features(df)
            
            # Get feature columns (same as training)
            exclude_cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
            feature_cols = [col for col in features_df.columns if col not in exclude_cols]
            
            # Prepare latest features
            latest_features = features_df[feature_cols].iloc[-1:].dropna(axis=1)
            
            # Handle missing features (fill with mean or 0)
            for col in feature_cols:
                if col not in latest_features.columns:
                    latest_features[col] = 0
            
            # Ensure feature order matches training
            latest_features = latest_features.reindex(columns=feature_cols, fill_value=0)
            
            # Scale features
            latest_features_scaled = scaler.transform(latest_features)
            
            # Make prediction
            prediction = model.predict(latest_features_scaled)[0]
            current_price = df['close'].iloc[-1]
            
            # Calculate prediction metrics
            price_change = prediction - current_price
            price_change_pct = (price_change / current_price) * 100
            
            # Calculate confidence based on model performance
            if 'test_r2' in metrics:
                confidence = max(0, min(100, metrics['test_r2'] * 100))
            else:
                confidence = 75  # Default confidence for cached models
            
            # Determine signal
            if price_change_pct > 2:
                signal = "Strong Buy 🟢"
                signal_emoji = "🚀"
            elif price_change_pct > 0.5:
                signal = "Buy 🟢"
                signal_emoji = "📈"
            elif price_change_pct < -2:
                signal = "Strong Sell 🔴"
                signal_emoji = "📉"
            elif price_change_pct < -0.5:
                signal = "Sell 🔴"
                signal_emoji = "⬇️"
            else:
                signal = "Hold ⚪"
                signal_emoji = "➡️"
            
            return {
                'current_price': current_price,
                'predicted_price': prediction,
                'price_change': price_change,
                'price_change_pct': price_change_pct,
                'confidence': confidence,
                'signal': signal,
                'signal_emoji': signal_emoji,
                'timeframe': timeframe,
                'metrics': metrics
            }
            
        except Exception as e:
            logger.error(f"Error making prediction: {e}")
            return {'error': str(e)}
    
    @commands.command(name='predict')
    async def ai_prediction(self, ctx, symbol: str, timeframe: str = '1h'):
        """
        Generate AI-based price predictions
        Usage: /predict BTC 1h
        """
        await ctx.send(f"🤖 Generating AI prediction for {symbol.upper()}...")
        
        try:
            # Make prediction
            prediction_data = await self.make_prediction(symbol, timeframe)
            
            if 'error' in prediction_data:
                await ctx.send(f"❌ Error generating prediction: {prediction_data['error']}")
                return
            
            # Create prediction embed
            embed = discord.Embed(
                title=f"🤖 AI Market Prediction - {symbol.upper()}",
                description=f"Machine learning-based price prediction for {symbol.upper()}",
                color=0x00ff00 if prediction_data['price_change_pct'] > 0 else 0xff0000,
                timestamp=datetime.now()
            )
            
            # Current vs Predicted Price
            embed.add_field(
                name="💰 Current Price",
                value=f"${prediction_data['current_price']:.4f}",
                inline=True
            )
            
            embed.add_field(
                name="🔮 Predicted Price",
                value=f"${prediction_data['predicted_price']:.4f}",
                inline=True
            )
            
            embed.add_field(
                name="📊 Price Change",
                value=f"{prediction_data['price_change']:+.4f} ({prediction_data['price_change_pct']:+.2f}%)",
                inline=True
            )
            
            # AI Signal
            embed.add_field(
                name="🚦 AI Signal",
                value=f"{prediction_data['signal_emoji']} {prediction_data['signal']}",
                inline=True
            )
            
            embed.add_field(
                name="🎯 Confidence Level",
                value=f"{prediction_data['confidence']:.1f}%",
                inline=True
            )
            
            embed.add_field(
                name="⏱️ Timeframe",
                value=f"Next {timeframe} period",
                inline=True
            )
            
            # Model performance (if available)
            if 'test_r2' in prediction_data['metrics']:
                metrics = prediction_data['metrics']
                model_info = f"**Model Performance:**\n"
                model_info += f"R² Score: {metrics['test_r2']:.3f}\n"
                model_info += f"Test MAE: ${metrics['test_mae']:.4f}\n"
                model_info += f"Features: {metrics['feature_count']}\n"
                model_info += f"Training Samples: {metrics['training_samples']}"
                
                embed.add_field(
                    name="🏆 Model Metrics",
                    value=model_info,
                    inline=False
                )
            
            # Add interpretation
            if prediction_data['confidence'] > 80:
                confidence_desc = "High confidence - Model shows strong predictive performance"
            elif prediction_data['confidence'] > 60:
                confidence_desc = "Moderate confidence - Consider alongside other analysis"
            else:
                confidence_desc = "Low confidence - Use with caution, model uncertainty is high"
            
            embed.add_field(
                name="💡 Interpretation",
                value=confidence_desc,
                inline=False
            )
            
            # Risk disclaimer
            embed.add_field(
                name="⚠️ Disclaimer",
                value="AI predictions are based on historical data and technical indicators. Past performance does not guarantee future results. Always conduct your own research.",
                inline=False
            )
            
            embed.set_footer(text=f"Model: Random Forest | Features: Technical Indicators + Price History")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in AI prediction command: {e}")
            await ctx.send(f"❌ Error generating AI prediction: {str(e)}")
    
    @commands.command(name='model_info')
    async def model_info(self, ctx, symbol: str, timeframe: str = '1h'):
        """
        Display information about the AI model for a symbol
        Usage: /model_info BTC 1h
        """
        model_key = f"{symbol}_{timeframe}"
        
        if model_key not in self.models:
            await ctx.send(f"📝 No trained model found for {symbol.upper()} ({timeframe}). Use `/predict {symbol} {timeframe}` to train a model first.")
            return
        
        embed = discord.Embed(
            title=f"🤖 AI Model Information - {symbol.upper()}",
            description=f"Details about the trained model for {symbol.upper()} ({timeframe})",
            color=0x0099ff,
            timestamp=datetime.now()
        )
        
        model = self.models[model_key]
        
        # Model parameters
        embed.add_field(
            name="🛠️ Model Type",
            value="Random Forest Regressor",
            inline=True
        )
        
        embed.add_field(
            name="🌳 Trees",
            value=str(model.n_estimators),
            inline=True
        )
        
        embed.add_field(
            name="📏 Max Depth",
            value=str(model.max_depth),
            inline=True
        )
        
        # Feature importance (top 10)
        if hasattr(model, 'feature_importances_'):
            try:
                # Get feature names (this is simplified - in real implementation you'd track feature names)
                feature_names = [f"Feature_{i}" for i in range(len(model.feature_importances_))]
                importances = model.feature_importances_
                
                # Get top 10 most important features
                top_indices = np.argsort(importances)[-10:][::-1]
                top_features = [(feature_names[i], importances[i]) for i in top_indices]
                
                feature_text = "\n".join([f"{name}: {importance:.3f}" for name, importance in top_features[:5]])
                
                embed.add_field(
                    name="🎯 Top Features",
                    value=feature_text,
                    inline=False
                )
            except:
                pass
        
        embed.set_footer(text="Model cached in memory | Use /predict to refresh")
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(PredictionsCog(bot))