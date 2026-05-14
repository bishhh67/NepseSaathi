# core/views.py
from django.shortcuts import render
from django.conf import settings
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# ============================================
# MARKET DATA PROCESSING
# ============================================

class NEPSEMarketData:
    def __init__(self):
        possible_paths = [
            Path(__file__).parent / 'data' / 'nepse_data.csv',
            Path.cwd() / 'data' / 'nepse_data.csv',
        ]
        self.data_file = None
        self.raw_data = None
        for path in possible_paths:
            if path.exists():
                self.data_file = path
                break
    
    def load_data(self):
        try:
            if not self.data_file:
                print("No CSV file found")
                return None
            df = pd.read_csv(self.data_file)
            numeric_cols = ['Open', 'High', 'Low', 'Close', 'Change', 'Per_change_()', 'Turnover']
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce')
            if 'data' in df.columns:
                df['data'] = pd.to_datetime(df['data'])
                df = df.sort_values('data', ascending=False)
            self.raw_data = df
            print(f"Data loaded successfully. Rows: {len(df)}")
            return df
        except Exception as e:
            print(f"Error loading: {e}")
            self.raw_data = None
            return None
    
    def get_last_30_days(self):
        if self.raw_data is None:
            self.load_data()
        if self.raw_data is not None and len(self.raw_data) > 0:
            return self.raw_data.head(30)
        return None
    
    def get_latest_market_data(self):
        df = self.get_last_30_days()
        if df is not None and len(df) > 0:
            latest = df.iloc[0]
            if len(df) > 1:
                if latest['Close'] > df.iloc[1]['Close']:
                    trend = "Upward"
                elif latest['Close'] < df.iloc[1]['Close']:
                    trend = "Downward"
                else:
                    trend = "Stable"
            else:
                trend = "Stable"
            
            return {
                'date': latest['data'].strftime('%B %d, %Y') if 'data' in latest else datetime.now().strftime('%B %d, %Y'),
                'open': float(latest['Open']) if 'Open' in latest else 0,
                'high': float(latest['High']) if 'High' in latest else 0,
                'low': float(latest['Low']) if 'Low' in latest else 0,
                'close': float(latest['Close']) if 'Close' in latest else 0,
                'change': float(latest['Change']) if 'Change' in latest else 0,
                'percent_change': float(latest['Per_change_()']) if 'Per_change_()' in latest else 0,
                'trend': trend
            }
        return None
    
    def get_chart_data_30_days(self):
        df = self.get_last_30_days()
        if df is not None:
            df_chrono = df.sort_values('data', ascending=True) if 'data' in df.columns else df
            return {
                'labels': df_chrono['data'].dt.strftime('%b %d').tolist() if 'data' in df_chrono.columns else [],
                'close': df_chrono['Close'].tolist() if 'Close' in df_chrono.columns else [],
                'high': df_chrono['High'].tolist() if 'High' in df_chrono.columns else [],
                'low': df_chrono['Low'].tolist() if 'Low' in df_chrono.columns else [],
            }
        return None

market_processor = NEPSEMarketData()

# ============================================
# HELPER FUNCTIONS (Hardcoded - Always works)
# ============================================

def generate_market_summary(latest_data, thirty_day_data):
    if not latest_data:
        return "Market data loading..."
    
    change = latest_data['percent_change']
    if change > 1:
        return f"🚀 The market closed strongly bullish with a gain of {latest_data['change']:.2f} points ({change:.2f}%). This significant upward movement indicates strong buying pressure across major sectors, suggesting positive investor sentiment and potential continued momentum."
    elif change > 0.3:
        return f"📈 The market showed positive momentum, closing higher by {latest_data['change']:.2f} points ({change:.2f}%). The buying interest was evident across multiple sectors, reflecting growing investor confidence."
    elif change > -0.3:
        return f"⚖️ The market remained range-bound, closing with a minor change of {latest_data['change']:.2f} points ({change:.2f}%). The sideways movement indicates indecision among market participants."
    elif change > -1:
        return f"📉 The market closed lower, dropping {latest_data['change']:.2f} points ({change:.2f}%). The selling pressure suggests cautious investor behavior."
    else:
        return f"⚠️ The market experienced a sharp decline of {latest_data['change']:.2f} points ({change:.2f}%). This bearish movement indicates widespread selling pressure."

def generate_market_factors(latest_data):
    factors = []
    change = latest_data['percent_change']
    
    if change > 0.5:
        factors.append({'icon': '🏦', 'title': 'Banking Sector', 'description': 'Strong buying interest in banking stocks driven by positive earnings expectations', 'impact': 'Positive'})
        factors.append({'icon': '💧', 'title': 'Hydropower Momentum', 'description': 'Hydropower stocks gained momentum on improved energy demand outlook', 'impact': 'Positive'})
        factors.append({'icon': '📊', 'title': 'Institutional Buying', 'description': 'Increased participation from institutional investors supported market gains', 'impact': 'Positive'})
    elif change < -0.5:
        factors.append({'icon': '💰', 'title': 'Profit Booking', 'description': 'Investors booked profits after recent gains, leading to selling pressure', 'impact': 'Negative'})
        factors.append({'icon': '🏦', 'title': 'Banking Sector Weakness', 'description': 'Select profit booking in banking stocks weighed on the index', 'impact': 'Negative'})
        factors.append({'icon': '📰', 'title': 'Regulatory Uncertainty', 'description': 'Market sentiment affected by regulatory announcements', 'impact': 'Negative'})
    else:
        factors.append({'icon': '⚖️', 'title': 'Market Consolidation', 'description': 'Market consolidated within a narrow range as buyers and sellers remained balanced', 'impact': 'Neutral'})
        factors.append({'icon': '👀', 'title': 'Wait-and-Watch Approach', 'description': 'Investors adopted cautious stance ahead of key economic data releases', 'impact': 'Neutral'})
    
    factors.append({'icon': '💧', 'title': 'Liquidity Conditions', 'description': 'Market liquidity remains adequate with stable interest rate environment', 'impact': 'Positive'})
    factors.append({'icon': '📊', 'title': 'Technical Levels', 'description': f'Trading between {latest_data["low"]:.0f} and {latest_data["high"]:.0f}', 'impact': 'Neutral'})
    
    return factors

def get_key_insights(latest_data, thirty_day_data):
    insights = []
    if thirty_day_data and len(thirty_day_data['close']) >= 5:
        closes = thirty_day_data['close']
        ma5 = sum(closes[-5:]) / 5
        if latest_data['close'] > ma5:
            insights.append("📈 Trading above 5-day moving average - short-term positive signal")
        else:
            insights.append("📉 Trading below 5-day moving average - short-term caution advised")
    return insights

# ============================================
# MAIN HOME VIEW
# ============================================
def home(request):
    thirty_day_data = market_processor.get_chart_data_30_days()
    latest_data = market_processor.get_latest_market_data()
    
    tickers = [
        {"symbol": "NABIL", "change": "+2.3%"}, {"symbol": "NICA", "change": "-1.1%"},
        {"symbol": "SCB", "change": "+0.8%"}, {"symbol": "NRIC", "change": "+3.4%"},
        {"symbol": "NLG", "change": "-0.5%"}, {"symbol": "CHCL", "change": "+1.9%"},
        {"symbol": "UPPER", "change": "+4.1%"}, {"symbol": "NHPC", "change": "-0.7%"},
        {"symbol": "PCBL", "change": "+2.2%"}, {"symbol": "GBIME", "change": "+1.4%"},
    ]
    
    if latest_data and latest_data['close'] != 0:
        if latest_data['percent_change'] > 0.5:
            direction, icon, color = "Bullish", "📈", "green"
        elif latest_data['percent_change'] < -0.5:
            direction, icon, color = "Bearish", "📉", "red"
        else:
            direction, icon, color = "Sideways", "➡️", "yellow"
        
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
            'direction_icon': icon,
            'direction_color': color,
            'trend': latest_data['trend'],
            'chart_labels': json.dumps(thirty_day_data['labels']) if thirty_day_data else json.dumps([]),
            'chart_values': json.dumps(thirty_day_data['close']) if thirty_day_data else json.dumps([]),
            'insights': insights,
        }
        
        # ============================================
        # 1. HARDCODED ANALYSIS (Always works)
        # ============================================
        hardcoded_summary = generate_market_summary(latest_data, thirty_day_data)
        hardcoded_factors = generate_market_factors(latest_data)
        
        # ============================================
        # 2. MARKET ANALYZER (Technical analysis from CSV)
        # ============================================
        technical_report = None
        technical_news = []
        technical_indicators = {}
        try:
            from .market_analyzer import market_analyzer
            technical_report, technical_news, technical_indicators = market_analyzer.generate_complete_report(thirty_day_data, latest_data)
            print(f"✅ Technical analysis complete. News found: {len(technical_news)}")
        except Exception as e:
            print(f"❌ Market analyzer error: {e}")
        
        # ============================================
        # 3. DEEPSEEK AI ANALYSIS (With web search)
        # ============================================
       # In your home function, replace the AI section with:

        # ============================================
        # 3. GROQ AI ANALYSIS (Free, Fast, Detailed)
        # ============================================
        ai_context = None
        try:
            from .groq_analyzer import groq_analyzer
            ai_result = groq_analyzer.analyze_market(thirty_day_data, latest_data)
            if ai_result:
                ai_context = {
                    'analysis': ai_result.get('analysis', ''),
                    'generated_at': ai_result.get('generated_at', ''),
                    'monthly_return': ai_result.get('monthly_return', 0),
                    'rsi': ai_result.get('rsi', 50),
                    'support': ai_result.get('support', 0),
                    'resistance': ai_result.get('resistance', 0),
                    'model': ai_result.get('model', 'Groq AI'),
                }
                print("✅ Groq AI analysis complete")
            else:
                print("❌ Groq analysis returned None")
        except Exception as e:
            print(f"❌ Groq error: {e}")
        
    else:
        market_data = {
            'date': datetime.now().strftime('%B %d, %Y'),
            'open': 0, 'high': 0, 'low': 0, 'close': 0,
            'point_change': 0, 'percent_change': 0,
            'direction': 'Loading', 'direction_icon': '⏳', 'direction_color': 'gray',
            'trend': 'Loading',
            'chart_labels': json.dumps([]), 'chart_values': json.dumps([]),
            'insights': ['Place CSV file in core/data/nepse_data.csv'],
        }
        hardcoded_summary = "Waiting for data. Please place nepse_data.csv in core/data/ folder"
        hardcoded_factors = []
        technical_report = None
        technical_news = []
        technical_indicators = {}
        ai_context = None

    context = {
        "page_title": "NEPSE Sathi — Master Nepal's Stock Market",
        "tickers": tickers,
        "market_data": market_data,
        "market_summary": hardcoded_summary,
        "market_factors": hardcoded_factors,
        "market_insights": market_data.get('insights', []),
        "technical_report": technical_report,
        "technical_news": technical_news,
        "technical_indicators": technical_indicators,
        "ai_analysis": ai_context,
    }
    
    return render(request, "core/home.html", context)





def learning(request):
    return render(request, 'learning/learning.html')