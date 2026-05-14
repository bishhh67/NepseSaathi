# core/market_analysis.py
import json
from datetime import datetime, timedelta

class MarketAnalysisEngine:
    """Rule-based market analysis engine"""
    
    def __init__(self, market_data_processor):
        self.processor = market_data_processor
    
    def generate_summary(self, latest_data, thirty_day_data):
        """Generate comprehensive market summary"""
        if not latest_data:
            return "Market data temporarily unavailable."
        
        change = latest_data['percent_change']
        trend = latest_data['trend']
        
        # Calculate 30-day performance
        if thirty_day_data and len(thirty_day_data['close']) > 0:
            month_ago_close = thirty_day_data['close'][0]
            current_close = thirty_day_data['close'][-1]
            monthly_return = ((current_close - month_ago_close) / month_ago_close) * 100
        else:
            monthly_return = 0
        
        # Generate detailed summary
        if change > 1:
            sentiment = "strongly bullish"
            outlook = "positive momentum likely to continue"
        elif change > 0.3:
            sentiment = "cautiously optimistic"
            outlook = "moderate buying interest expected"
        elif change > -0.3:
            sentiment = "neutral"
            outlook = "range-bound trading expected"
        elif change > -1:
            sentiment = "cautiously bearish"
            outlook = "some profit booking likely"
        else:
            sentiment = "bearish"
            outlook = "selling pressure may persist"
        
        summary = f"""
        The NEPSE index {'gained' if change >= 0 else 'lost'} {abs(change):.2f}% in today's trading session,
        closing at {latest_data['close']:.2f}. The market sentiment appears {sentiment} with 
        {trend.lower()} momentum over the past 5 trading sessions.
        
        Over the last 30 days, the market has {'increased' if monthly_return >= 0 else 'decreased'} 
        by {abs(monthly_return):.2f}%, indicating {'strengthening' if monthly_return > 2 else 'consolidating' if abs(monthly_return) < 1 else 'weakening'} market conditions.
        
        Trading volume and turnover suggest {'active participation from institutional investors' if latest_data['turnover'] > latest_data.get('volume_avg', 0) else 'cautious retail participation'}.
        
        Outlook: {outlook}. Key support and resistance levels will be crucial in determining the next directional move.
        """
        
        return summary.strip()
    
    def generate_market_factors(self, latest_data, thirty_day_data):
        """Generate possible market factors"""
        factors = []
        change = latest_data['percent_change']
        thirty_day_return = 0
        
        if thirty_day_data and len(thirty_day_data['close']) > 1:
            month_ago = thirty_day_data['close'][0]
            current = thirty_day_data['close'][-1]
            thirty_day_return = ((current - month_ago) / month_ago) * 100
        
        # Banking sector factor (based on market movement correlation)
        if change > 0.5:
            factors.append({
                'icon': '🏦',
                'title': 'Banking Sector Strength',
                'description': 'Banking stocks showed strong buying interest, contributing significantly to index gains.',
                'impact': 'Positive'
            })
        elif change < -0.5:
            factors.append({
                'icon': '🏦',
                'title': 'Banking Sector Pressure',
                'description': 'Select profit booking in banking stocks weighed on market sentiment.',
                'impact': 'Negative'
            })
        
        # Hydropower factor
        if change > 0.3:
            factors.append({
                'icon': '💧',
                'title': 'Hydropower Momentum',
                'description': 'Hydropower stocks continued their upward trajectory on improved outlook.',
                'impact': 'Positive'
            })
        
        # Market trend factor
        if thirty_day_return > 5:
            factors.append({
                'icon': '📈',
                'title': 'Monthly Uptrend',
                'description': f'Market has gained {thirty_day_return:.1f}% over the past month, indicating strong bullish momentum.',
                'impact': 'Positive'
            })
        elif thirty_day_return < -3:
            factors.append({
                'icon': '📉',
                'title': 'Monthly Correction',
                'description': 'Technical correction phase with profit booking at higher levels.',
                'impact': 'Negative'
            })
        
        # Volume and liquidity factor
        if latest_data['turnover'] > latest_data.get('volume_avg', 0) * 1.2:
            factors.append({
                'icon': '💰',
                'title': 'High Turnover',
                'description': 'Increased market participation with robust turnover indicates strong investor interest.',
                'impact': 'Positive'
            })
        elif latest_data['turnover'] < latest_data.get('volume_avg', 0) * 0.8:
            factors.append({
                'icon': '💤',
                'title': 'Low Volume',
                'description': 'Reduced market participation suggests cautious approach from investors.',
                'impact': 'Neutral'
            })
        
        # Add technical factor
        factors.append({
            'icon': '📊',
            'title': 'Technical Levels',
            'description': f'Trading within key levels with resistance at {latest_data["high"]:.0f} and support at {latest_data["low"]:.0f}.',
            'impact': 'Neutral'
        })
        
        # Add global/macro factor
        factors.append({
            'icon': '🌍',
            'title': 'Market Sentiment',
            'description': f'Overall market breadth shows {latest_data["trend"].lower()} bias with selective buying in quality stocks.',
            'impact': 'Neutral'
        })
        
        return factors
    
    def get_key_insights(self, latest_data, thirty_day_data):
        """Generate key insights for the market snapshot"""
        insights = []
        
        if thirty_day_data:
            closes = thirty_day_data['close']
            if len(closes) >= 5:
                # Moving average trend
                ma5 = sum(closes[-5:]) / 5
                ma20 = sum(closes[-20:]) / 20 if len(closes) >= 20 else ma5
                
                if latest_data['close'] > ma5 > ma20:
                    insights.append("Golden cross pattern forming - bullish signal")
                elif latest_data['close'] < ma5 < ma20:
                    insights.append("Death cross pattern - bearish signal")
                elif latest_data['close'] > ma5:
                    insights.append("Trading above 5-day moving average - short-term positive")
                else:
                    insights.append("Trading below 5-day moving average - short-term caution")
                
                # Volatility assessment
                daily_changes = [abs(thirty_day_data['change'][i]) for i in range(len(thirty_day_data['change']))]
                avg_volatility = sum(daily_changes) / len(daily_changes)
                
                if abs(latest_data['change']) > avg_volatility * 1.5:
                    insights.append(f"Higher than average daily movement of {abs(latest_data['change']):.2f} points")
                elif abs(latest_data['change']) < avg_volatility * 0.5:
                    insights.append("Lower volatility day - consolidation phase")
        
        return insights