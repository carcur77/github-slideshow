"""
Test suite for Trading Signal Bot
"""
import unittest
import sys
import os
import asyncio
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, AsyncMock

# Add the parent directory to path to import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading_bot import TechnicalIndicators, TradingSignalBot

class TestTechnicalIndicators(unittest.TestCase):
    """Test cases for technical indicators"""
    
    def setUp(self):
        """Set up test data"""
        # Create sample price data
        np.random.seed(42)
        dates = pd.date_range(start='2023-01-01', periods=100, freq='H')
        prices = 50000 + np.cumsum(np.random.randn(100) * 100)  # Random walk around $50k
        
        self.sample_data = pd.Series(prices, index=dates)
        self.indicators = TechnicalIndicators()
    
    def test_sma_calculation(self):
        """Test Simple Moving Average calculation"""
        sma_20 = self.indicators.calculate_sma(self.sample_data, 20)
        
        # Check that SMA is calculated
        self.assertIsInstance(sma_20, pd.Series)
        self.assertEqual(len(sma_20), len(self.sample_data))
        
        # Check that first 19 values are NaN (due to window)
        self.assertTrue(pd.isna(sma_20.iloc[:19]).all())
        
        # Check that SMA values are reasonable
        self.assertFalse(pd.isna(sma_20.iloc[19:]).any())
    
    def test_ema_calculation(self):
        """Test Exponential Moving Average calculation"""
        ema_12 = self.indicators.calculate_ema(self.sample_data, 12)
        
        self.assertIsInstance(ema_12, pd.Series)
        self.assertEqual(len(ema_12), len(self.sample_data))
        
        # EMA should have fewer NaN values than SMA
        self.assertFalse(pd.isna(ema_12.iloc[1:]).any())
    
    def test_macd_calculation(self):
        """Test MACD calculation"""
        macd_data = self.indicators.calculate_macd(self.sample_data)
        
        # Check that all components are present
        self.assertIn('macd', macd_data)
        self.assertIn('signal', macd_data)
        self.assertIn('histogram', macd_data)
        
        # Check data types
        for component in macd_data.values():
            self.assertIsInstance(component, pd.Series)
            self.assertEqual(len(component), len(self.sample_data))
        
        # Check that histogram = macd - signal
        histogram_check = macd_data['macd'] - macd_data['signal']
        pd.testing.assert_series_equal(
            macd_data['histogram'].dropna(), 
            histogram_check.dropna(), 
            check_names=False
        )
    
    def test_bollinger_bands_calculation(self):
        """Test Bollinger Bands calculation"""
        bb_data = self.indicators.calculate_bollinger_bands(self.sample_data)
        
        # Check that all bands are present
        self.assertIn('upper', bb_data)
        self.assertIn('middle', bb_data)
        self.assertIn('lower', bb_data)
        
        # Check that upper > middle > lower (generally)
        valid_data = ~(pd.isna(bb_data['upper']) | pd.isna(bb_data['middle']) | pd.isna(bb_data['lower']))
        
        self.assertTrue((bb_data['upper'][valid_data] >= bb_data['middle'][valid_data]).all())
        self.assertTrue((bb_data['middle'][valid_data] >= bb_data['lower'][valid_data]).all())
    
    def test_stochastic_calculation(self):
        """Test Stochastic Oscillator calculation"""
        # Create high, low, close data
        high = self.sample_data + np.random.rand(len(self.sample_data)) * 500
        low = self.sample_data - np.random.rand(len(self.sample_data)) * 500
        close = self.sample_data
        
        stoch_data = self.indicators.calculate_stochastic(high, low, close)
        
        # Check components
        self.assertIn('k', stoch_data)
        self.assertIn('d', stoch_data)
        
        # Check that values are in valid range (0-100)
        valid_k = stoch_data['k'].dropna()
        valid_d = stoch_data['d'].dropna()
        
        self.assertTrue((valid_k >= 0).all() and (valid_k <= 100).all())
        self.assertTrue((valid_d >= 0).all() and (valid_d <= 100).all())

class TestBotComponents(unittest.TestCase):
    """Test cases for bot components"""
    
    def setUp(self):
        """Set up mock bot"""
        self.bot = Mock()
        self.bot.technical_indicators = TechnicalIndicators()
    
    def test_bot_initialization(self):
        """Test that bot initializes correctly"""
        # This test would be more meaningful with actual bot initialization
        # For now, just test that components exist
        self.assertIsNotNone(self.bot.technical_indicators)
    
    def test_technical_indicators_integration(self):
        """Test that technical indicators work in bot context"""
        # Create sample data
        sample_prices = pd.Series([100, 101, 102, 103, 104, 105] * 10)
        
        # Test that indicators can be calculated
        sma = self.bot.technical_indicators.calculate_sma(sample_prices, 5)
        self.assertIsInstance(sma, pd.Series)
        
        macd = self.bot.technical_indicators.calculate_macd(sample_prices)
        self.assertIsInstance(macd, dict)
        self.assertIn('macd', macd)

class TestDataValidation(unittest.TestCase):
    """Test cases for data validation and error handling"""
    
    def setUp(self):
        self.indicators = TechnicalIndicators()
    
    def test_empty_data_handling(self):
        """Test handling of empty data"""
        empty_series = pd.Series([])
        
        # Should not crash but return empty or NaN results
        sma = self.indicators.calculate_sma(empty_series, 10)
        self.assertTrue(sma.empty)
    
    def test_insufficient_data_handling(self):
        """Test handling of insufficient data"""
        short_series = pd.Series([1, 2, 3])  # Only 3 data points
        
        # Should handle gracefully
        sma = self.indicators.calculate_sma(short_series, 10)  # Window larger than data
        self.assertTrue(pd.isna(sma).all())
    
    def test_invalid_window_handling(self):
        """Test handling of invalid window sizes"""
        sample_data = pd.Series(range(100))
        
        # Test negative window
        with self.assertRaises((ValueError, TypeError)):
            self.indicators.calculate_sma(sample_data, -5)
        
        # Test zero window
        with self.assertRaises((ValueError, TypeError)):
            self.indicators.calculate_sma(sample_data, 0)

def run_async_test(test_func):
    """Helper to run async tests"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(test_func())
    finally:
        loop.close()

if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)