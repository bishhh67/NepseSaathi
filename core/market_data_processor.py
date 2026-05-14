# core/market_data_processor.py
import pandas as pd
import json
from datetime import datetime, timedelta
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class NEPSEMarketData:
    """Handles NEPSE market data processing from CSV"""
    
    def __init__(self):
        self.data_file = Path(__file__).parent / 'data' / 'nepse_data.csv'
        self.raw_data = None
        self.processed_data = None
        
    def load_data(self):
        """Load and preprocess CSV data"""
        try:
            if not self.data_file.exists():
                logger.error(f"Data file not found at {self.data_file}")
                return None
            
            # Read CSV file
            df = pd.read_csv(self.data_file)
            
            # Convert date column to datetime
            df['data'] = pd.to_datetime(df['data'])
            df = df.sort_values('data', ascending=False)  # Latest first
            
            self.raw_data = df
            return df
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            return None
    
    def get_last_30_days(self):
        """Get last 30 days of data"""
        if self.raw_data is None:
            self.load_data()
        
        if self.raw_data is not None:
            return self.raw_data.head(30)
        return None
    
    def get_latest_market_data(self):
        """Get the most recent trading day data"""
        df = self.get_last_30_days()
        if df is not None and len(df) > 0:
            latest = df.iloc[0]
            
            # Calculate additional metrics
            prev_day = df.iloc[1] if len(df) > 1 else None
            
            # Determine market trend (last 5 days)
            last_5_days = df.head(5)['Close'].values
            trend = "Upward" if last_5_days[0] < last_5_days[-1] else "Downward" if last_5_days[0] > last_5_days[-1] else "Stable"
            
            return {
                'date': latest['data'].strftime('%B %d, %Y'),
                'open': float(latest['Open']),
                'high': float(latest['High']),
                'low': float(latest['Low']),
                'close': float(latest['Close']),
                'change': float(latest['Change']),
                'percent_change': float(latest['Per_change_()']),
                'turnover': float(latest['Turnover']),
                'trend': trend,
                'volume_avg': float(df.head(5)['Turnover'].mean()) if len(df) >= 5 else 0
            }
        return None
    
    def get_chart_data_30_days(self):
        """Get data for 30-day chart"""
        df = self.get_last_30_days()
        if df is not None:
            # Reverse to show chronological order
            df_chrono = df.sort_values('data', ascending=True)
            
            return {
                'labels': df_chrono['data'].dt.strftime('%b %d').tolist(),
                'open': df_chrono['Open'].tolist(),
                'high': df_chrono['High'].tolist(),
                'low': df_chrono['Low'].tolist(),
                'close': df_chrono['Close'].tolist(),
                'volume': df_chrono['Turnover'].tolist(),
                'change': df_chrono['Change'].tolist(),
                'percent_change': df_chrono['Per_change_()'].tolist(),
            }
        return None
    
    def get_intraday_data(self):
        """Generate realistic intraday data from daily data"""
        latest = self.get_latest_market_data()
        if not latest:
            return None
        
        # Generate intraday points based on daily volatility
        import math
        points = []
        times = []
        
        open_val = latest['open']
        close_val = latest['close']
        high_val = latest['high']
        low_val = latest['low']
        
        # Generate 78 points (one every 5 minutes from 10 AM to 3 PM)
        for i in range(78):
            hour = 10 + (i * 5 // 60)
            minute = (i * 5) % 60
            times.append(f"{hour:02d}:{minute:02d}")
            
            # Simulate intraday movement
            progress = i / 77  # 0 to 1
            # Start at open, end at close, with peak at around 40-60% of the day
            if progress < 0.4:
                # Morning session - rise to high
                factor = progress / 0.4
                value = open_val + (high_val - open_val) * factor
            elif progress < 0.6:
                # Midday - maintain near high
                value = high_val
            else:
                # Afternoon - move toward close
                factor = (progress - 0.6) / 0.4
                value = high_val - (high_val - close_val) * factor
            
            # Add some noise
            noise = (i % 10 - 5) * (high_val - low_val) * 0.01
            value += noise
            points.append(round(value, 2))
        
        return {
            'labels': times,
            'values': points,
            'is_intraday': True
        }

# Initialize singleton
market_data = NEPSEMarketData()