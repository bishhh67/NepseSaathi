from django.shortcuts import render

from django.conf import settings

# Add these imports at the very top of your views.py
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
import logging

from .news_fetcher import news_fetcher
from .enhanced_analyzer import enhanced_analyzer

from .gemini_analyzer import gemini

logger = logging.getLogger(__name__)

# ============================================
# ADD THIS ENTIRE BLOCK - Market Data Processing
# ============================================
class NEPSEMarketData:
    """Handles NEPSE market data processing from CSV"""
    
    def __init__(self):
        possible_paths = [
            Path(__file__).parent / 'data' / 'nepse_data.csv',
            Path(__file__).parent.parent / 'data' / 'nepse_data.csv',
            Path.cwd() / 'data' / 'nepse_data.csv',
        ]
        
        self.data_file = None
        for path in possible_paths:
            if path.exists():
                self.data_file = path
                break
        
        self.raw_data = None
        
    def load_data(self):
        """Load and preprocess CSV data"""
        try:
            if not self.data_file:
                return None
            
            # Read CSV and handle commas in numbers
            df = pd.read_csv(self.data_file)
            
            # Clean numeric columns (remove commas)
            numeric_columns = ['Open', 'High', 'Low', 'Close', 'Change', 'Per_change_()', 'Turnover']
            for col in numeric_columns:
                if col in df.columns:
                    # Convert to string, remove commas, then to numeric
                    df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce')
            
            if 'data' in df.columns:
                df['data'] = pd.to_datetime(df['data'])
                df = df.sort_values('data', ascending=False)
            elif 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'])
                df = df.sort_values('Date', ascending=False)
                df.rename(columns={'Date': 'data'}, inplace=True)
            
            self.raw_data = df
            return df
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            return None
    
    def get_last_30_days(self):
        """Get last 30 days of data"""
        if self.raw_data is None:
            self.load_data()
        
        if self.raw_data is not None and len(self.raw_data) > 0:
            return self.raw_data.head(30)
        return None
    
    def get_latest_market_data(self):
        """Get the most recent trading day data"""
        df = self.get_last_30_days()
        if df is not None and len(df) > 0:
            latest = df.iloc[0]
            
            # Helper function to clean and convert numbers with commas
            def clean_float(value):
                if pd.isna(value):
                    return 0
                if isinstance(value, str):
                    value = value.replace(',', '')
                try:
                    return float(value)
                except (ValueError, TypeError):
                    return 0
            
            last_5_days = df.head(5)['Close'].values if 'Close' in df.columns else None
            trend = "Upward" if last_5_days is not None and len(last_5_days) >= 2 and last_5_days[0] < last_5_days[-1] else "Downward" if last_5_days is not None and len(last_5_days) >= 2 and last_5_days[0] > last_5_days[-1] else "Stable"
            
            return {
                'date': latest['data'].strftime('%B %d, %Y') if 'data' in latest else datetime.now().strftime('%B %d, %Y'),
                'open': clean_float(latest['Open']) if 'Open' in latest else 0,
                'high': clean_float(latest['High']) if 'High' in latest else 0,
                'low': clean_float(latest['Low']) if 'Low' in latest else 0,
                'close': clean_float(latest['Close']) if 'Close' in latest else 0,
                'change': clean_float(latest['Change']) if 'Change' in latest else 0,
                'percent_change': clean_float(latest['Per_change_()']) if 'Per_change_()' in latest else 0,
                'turnover': clean_float(latest['Turnover']) if 'Turnover' in latest else 0,
                'trend': trend,
            }
        return None
    
    def get_chart_data_30_days(self):
        """Get data for 30-day chart"""
        df = self.get_last_30_days()
        if df is not None and len(df) > 0:
            # Sort chronological order
            df_chrono = df.sort_values('data', ascending=True) if 'data' in df.columns else df
            
            # Helper function to clean values
            def clean_value(value):
                if pd.isna(value):
                    return 0
                if isinstance(value, str):
                    value = value.replace(',', '')
                try:
                    return float(value)
                except (ValueError, TypeError):
                    return 0
            
            # Clean all numeric columns
            close_values = [clean_value(v) for v in df_chrono['Close'].tolist()] if 'Close' in df_chrono.columns else []
            high_values = [clean_value(v) for v in df_chrono['High'].tolist()] if 'High' in df_chrono.columns else []
            low_values = [clean_value(v) for v in df_chrono['Low'].tolist()] if 'Low' in df_chrono.columns else []
            volume_values = [clean_value(v) for v in df_chrono['Turnover'].tolist()] if 'Turnover' in df_chrono.columns else []
            
            return {
                'labels': df_chrono['data'].dt.strftime('%b %d').tolist() if 'data' in df_chrono.columns else [f'Day {i}' for i in range(len(df_chrono))],
                'close': close_values,
                'high': high_values,
                'low': low_values,
                'volume': volume_values,
            }
        return None
    

# Initialize market processor
market_processor = NEPSEMarketData()

############################
# ============================================
# ADD THESE FUNCTIONS - Market Analysis
# ============================================

def generate_market_summary(latest_data, thirty_day_data):
    """Generate market summary"""
    if not latest_data or latest_data['close'] == 0:
        return "Market data is loading. Please ensure your CSV file is properly placed."
    
    change = latest_data['percent_change']
    trend = latest_data['trend']
    
    # Calculate 30-day performance
    monthly_return = 0
    if thirty_day_data and len(thirty_day_data.get('close', [])) > 1:
        month_ago_close = thirty_day_data['close'][0]
        current_close = thirty_day_data['close'][-1]
        if month_ago_close != 0:
            monthly_return = ((current_close - month_ago_close) / month_ago_close) * 100
    
    # Generate sentiment
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
    
    summary = f"""The NEPSE index {'gained' if change >= 0 else 'lost'} {abs(change):.2f}% in today's trading session, closing at {latest_data['close']:.2f}. The market sentiment appears {sentiment} with {trend.lower()} momentum.

Over the last 30 days, the market has {'increased' if monthly_return >= 0 else 'decreased'} by {abs(monthly_return):.2f}%. Outlook: {outlook}."""
    
    return summary


def generate_market_factors(latest_data):
    """Generate market factors"""
    factors = []
    
    if not latest_data:
        return factors
    
    change = latest_data['percent_change']
    
    if change > 0.5:
        factors.append({
            'icon': '🏦',
            'title': 'Banking Sector Strength',
            'description': 'Strong buying interest in banking stocks.',
            'impact': 'Positive'
        })
    elif change < -0.5:
        factors.append({
            'icon': '🏦',
            'title': 'Banking Sector Pressure',
            'description': 'Profit booking in banking stocks.',
            'impact': 'Negative'
        })
    else:
        factors.append({
            'icon': '🏦',
            'title': 'Banking Sector Stable',
            'description': 'Banking stocks traded in a narrow range.',
            'impact': 'Neutral'
        })
    
    factors.append({
        'icon': '💧',
        'title': 'Hydropower Activity',
        'description': 'Mixed performance with selective buying.',
        'impact': 'Neutral'
    })
    
    factors.append({
        'icon': '💰',
        'title': 'Market Liquidity',
        'description': 'Adequate liquidity supporting trading activity.',
        'impact': 'Positive'
    })
    
    factors.append({
        'icon': '📊',
        'title': 'Technical Levels',
        'description': f'Resistance at {latest_data["high"]:.0f}, support at {latest_data["low"]:.0f}.',
        'impact': 'Neutral'
    })
    
    return factors


def get_key_insights(latest_data, thirty_day_data):
    """Generate key insights"""
    insights = []
    
    if not latest_data or not thirty_day_data:
        return insights
    
    closes = thirty_day_data.get('close', [])
    if len(closes) >= 5:
        ma5 = sum(closes[-5:]) / 5
        if latest_data['close'] > ma5:
            insights.append("📈 Trading above 5-day moving average - positive signal")
        else:
            insights.append("📉 Trading below 5-day moving average - caution advised")
    
    return insights


# Add this entire function BEFORE your home function in views.py

def prepare_market_data_for_ai(thirty_day_data, latest_data):
    """Format market data for AI consumption"""
    if not thirty_day_data or not latest_data:
        return None
    
    closes = thirty_day_data.get('close', [])
    dates = thirty_day_data.get('labels', [])
    
    if not closes or len(closes) < 5:
        return None
    
    # Calculate moving averages
    ma5 = sum(closes[-5:]) / 5 if len(closes) >= 5 else closes[-1]
    ma10 = sum(closes[-10:]) / 10 if len(closes) >= 10 else ma5
    ma20 = sum(closes[-20:]) / 20 if len(closes) >= 20 else ma10
    
    # Calculate volatility
    daily_returns = []
    for i in range(1, len(closes)):
        if closes[i-1] != 0:
            ret = (closes[i] - closes[i-1]) / closes[i-1] * 100
            daily_returns.append(ret)
    
    volatility = sum(daily_returns) / len(daily_returns) if daily_returns else 0
    
    # Find support and resistance levels
    support = min(closes[-10:]) if len(closes) >= 10 else min(closes)
    resistance = max(closes[-10:]) if len(closes) >= 10 else max(closes)
    
    # Calculate weekly performance
    weekly_changes = []
    for i in range(0, len(closes), 5):
        if i+4 < len(closes):
            week_change = (closes[i+4] - closes[i]) / closes[i] * 100 if closes[i] != 0 else 0
            weekly_changes.append(week_change)
    
    return {
        "date_range": {
            "start": dates[0] if dates else "N/A",
            "end": dates[-1] if dates else "N/A",
            "days": len(closes)
        },
        "latest_day": {
            "date": latest_data.get('date'),
            "close": latest_data.get('close'),
            "change_percent": latest_data.get('percent_change'),
            "change_points": latest_data.get('point_change'),
            "high": latest_data.get('high'),
            "low": latest_data.get('low'),
            "volume": latest_data.get('turnover', 0)
        },
        "thirty_day_stats": {
            "highest_close": max(closes),
            "lowest_close": min(closes),
            "average_close": sum(closes) / len(closes),
            "total_return_percent": ((closes[-1] - closes[0]) / closes[0] * 100) if closes[0] != 0 else 0,
            "volatility_percent": abs(volatility),
            "uptrend_days": sum(1 for i in range(1, len(closes)) if closes[i] > closes[i-1]),
            "downtrend_days": sum(1 for i in range(1, len(closes)) if closes[i] < closes[i-1])
        },
        "technical_indicators": {
            "ma5": round(ma5, 2),
            "ma10": round(ma10, 2),
            "ma20": round(ma20, 2),
            "support_level": round(support, 2),
            "resistance_level": round(resistance, 2),
            "position_vs_ma5": "above" if latest_data.get('close', 0) > ma5 else "below",
            "weekly_changes": [round(w, 2) for w in weekly_changes[-4:]]
        }
    }

################################
def home(request):
    # Get market data from CSV
    thirty_day_data = market_processor.get_chart_data_30_days()
    latest_data = market_processor.get_latest_market_data()
    
    # Your existing tickers data
    tickers = [
        {"symbol": "NABIL", "change": "+2.3%"},
        {"symbol": "NICA", "change": "-1.1%"},
        {"symbol": "SCB", "change": "+0.8%"},
        {"symbol": "NRIC", "change": "+3.4%"},
        {"symbol": "NLG", "change": "-0.5%"},
        {"symbol": "CHCL", "change": "+1.9%"},
        {"symbol": "UPPER", "change": "+4.1%"},
        {"symbol": "NHPC", "change": "-0.7%"},
        {"symbol": "PCBL", "change": "+2.2%"},
        {"symbol": "GBIME", "change": "+1.4%"},
    ]
    
    # Process market data for display
    if latest_data and latest_data['close'] != 0:
        # Determine market direction
        if latest_data['percent_change'] > 0.5:
            direction = "Bullish"
            direction_icon = "📈"
            direction_color = "green"
        elif latest_data['percent_change'] < -0.5:
            direction = "Bearish"
            direction_icon = "📉"
            direction_color = "red"
        else:
            direction = "Sideways"
            direction_icon = "➡️"
            direction_color = "yellow"
        
        insights = get_key_insights(latest_data, thirty_day_data)
        
        market_data = {
            'date': latest_data['date'],
            'open': latest_data['open'],
            'high': latest_data['high'],
            'low': latest_data['low'],
            'close': latest_data['close'],
            'point_change': latest_data['change'],
            'percent_change': latest_data['percent_change'],
            'direction': direction,
            'direction_icon': direction_icon,
            'direction_color': direction_color,
            'trend': latest_data['trend'],
            'chart_labels': json.dumps(thirty_day_data['labels']) if thirty_day_data else json.dumps([]),
            'chart_values': json.dumps(thirty_day_data['close']) if thirty_day_data else json.dumps([]),
            'insights': insights,
        }
        
        # Import the enhanced analyzers
        from .news_fetcher import news_fetcher
        from .enhanced_analyzer import enhanced_analyzer
        
        # Fetch real news from websites
        print("Fetching news from Sharesansar, Nepalipaisa, NEPSE Alpha...")
        real_news = news_fetcher.fetch_all_news()
        print(f"Found {len(real_news)} news articles")
        
        # Get enhanced detailed analysis
        detailed_analysis = enhanced_analyzer.analyze_market(thirty_day_data, latest_data, real_news)
        
        summary = "Comprehensive market analysis based on 30-day technical data and real news"
        
        # Create factors from analysis
        factors = []
        
        # Add technical factors
        factors.append({
            'icon': '📊',
            'title': 'Technical Position',
            'description': f"Price is {detailed_analysis['key_levels'].get('position', 'neutral')} 20-day MA. RSI: {detailed_analysis['key_levels'].get('rsi', 50):.1f}",
            'impact': 'Technical'
        })
        
        factors.append({
            'icon': '🎯',
            'title': 'Key Levels',
            'description': f"Support: {detailed_analysis['key_levels'].get('support', 0):.0f} | Resistance: {detailed_analysis['key_levels'].get('resistance', 0):.0f}",
            'impact': 'Technical'
        })
        
        factors.append({
            'icon': '📈',
            'title': '30-Day Performance',
            'description': f"Return: {((latest_data['close'] - thirty_day_data['close'][0]) / thirty_day_data['close'][0] * 100):.2f}% over 30 days",
            'impact': 'Performance'
        })
        
        # Add news-based factors from categorized news
        if detailed_analysis.get('categorized_news'):
            for cat, news_list in list(detailed_analysis['categorized_news'].items())[:3]:
                icon_map = {
                    'SEBON/Regulatory': '📜',
                    'NRB/Monetary Policy': '💰',
                    'Banking Sector': '🏦',
                    'Hydropower': '💧',
                    'Corporate Actions': '🏢',
                    'IPO/FPO': '🚀',
                    'General Market': '📰'
                }
                if news_list:
                    factors.append({
                        'icon': icon_map.get(cat, '📰'),
                        'title': f"{cat}",
                        'description': news_list[0]['title'][:80] if news_list else 'No recent news',
                        'impact': 'News Driven'
                    })
        
        # Store comprehensive analysis for template
        ai_context = {
            'sentiment': detailed_analysis.get('sentiment', 'NEUTRAL'),
            'sentiment_detail': detailed_analysis.get('sentiment_detail', ''),
            'technical_analysis': detailed_analysis.get('technical_analysis', ''),
            'market_drivers': detailed_analysis.get('market_drivers', []),
            'weekly_outlook': detailed_analysis.get('weekly_outlook', ''),
            'investment_recommendation': detailed_analysis.get('investment_recommendation', ''),
            'key_levels': detailed_analysis.get('key_levels', {}),
            'categorized_news': detailed_analysis.get('categorized_news', {}),
            'top_news': real_news[:10],
            'news_count': len(real_news),
            'reasons': detailed_analysis.get('market_drivers', [])[:5],
            'technical_view': f"Support: {detailed_analysis.get('key_levels', {}).get('support', 0):.0f}, Resistance: {detailed_analysis.get('key_levels', {}).get('resistance', 0):.0f}. RSI: {detailed_analysis.get('key_levels', {}).get('rsi', 50):.1f}",
            'investor_advice': detailed_analysis.get('investment_recommendation', '').split('**Strategy**')[-1][:300] if '**Strategy**' in detailed_analysis.get('investment_recommendation', '') else detailed_analysis.get('investment_recommendation', ''),
            'next_week_outlook': detailed_analysis.get('weekly_outlook', '')[:200]
        }
        
    else:
        market_data = {
            'date': datetime.now().strftime('%B %d, %Y'),
            'open': 0,
            'high': 0,
            'low': 0,
            'close': 0,
            'point_change': 0,
            'percent_change': 0,
            'direction': 'Loading',
            'direction_icon': '⏳',
            'direction_color': 'gray',
            'trend': 'Loading',
            'chart_labels': json.dumps([]),
            'chart_values': json.dumps([]),
            'insights': ['Place CSV file in core/data/nepse_data.csv'],
        }
        summary = "📊 Waiting for data. Please place nepse_data.csv in core/data/ folder"
        factors = []
        ai_context = None

    context = {
        "page_title": "NEPSE Sathi — Master Nepal's Stock Market",
        "tickers": tickers,
        "market_data": market_data,
        "market_summary": summary,
        "market_factors": factors,
        "market_insights": market_data.get('insights', []),
        "ai_analysis": ai_context,
    }
    
    return render(request, "core/home.html", context)
#####################

def learning(request):
    return render(request, 'learning/learning.html')

