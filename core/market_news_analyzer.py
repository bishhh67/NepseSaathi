# core/market_news_analyzer.py
import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import json
import re

class MarketNewsAnalyzer:
    """Fetches real news and provides proper market analysis"""
    
    def __init__(self):
        self.news_sources = [
            "https://www.sharesansar.com/rss",
            "https://www.nepalipaisa.com/rss",
            "https://nepalstock.com.np/rss"
        ]
    
    def fetch_recent_news(self, days=30):
        """Fetch real news from the last 30 days"""
        all_news = []
        cutoff_date = datetime.now() - timedelta(days=days)
        
        for source_url in self.news_sources:
            try:
                feed = feedparser.parse(source_url)
                for entry in feed.entries[:20]:  # Get latest 20 per source
                    # Parse date
                    pub_date = None
                    if hasattr(entry, 'published_parsed'):
                        pub_date = datetime(*entry.published_parsed[:6])
                    elif hasattr(entry, 'updated_parsed'):
                        pub_date = datetime(*entry.updated_parsed[:6])
                    
                    if pub_date and pub_date > cutoff_date:
                        # Categorize news
                        title_lower = entry.title.lower()
                        category = self._categorize_news(title_lower)
                        
                        all_news.append({
                            'title': entry.title,
                            'summary': entry.summary[:200] if hasattr(entry, 'summary') else '',
                            'link': entry.link,
                            'date': pub_date.strftime('%Y-%m-%d'),
                            'category': category,
                            'source': source_url.split('/')[2]
                        })
            except Exception as e:
                print(f"Error fetching from {source_url}: {e}")
        
        # Remove duplicates by title
        seen_titles = set()
        unique_news = []
        for news in all_news:
            if news['title'] not in seen_titles:
                seen_titles.add(news['title'])
                unique_news.append(news)
        
        return unique_news[:30]  # Return top 30 news items
    
    def _categorize_news(self, title):
        """Categorize news based on title"""
        if 'bank' in title or 'financial institution' in title:
            return 'banking'
        elif 'hydropower' in title or 'hydro' in title:
            return 'hydropower'
        elif 'sebon' in title or 'regulation' in title or 'policy' in title:
            return 'regulatory'
        elif 'insurance' in title:
            return 'insurance'
        elif 'dividend' in title or 'bonus' in title or 'rights' in title:
            return 'corporate'
        elif 'agm' in title or 'meeting' in title:
            return 'corporate'
        elif 'nrb' in title or 'nepal rastra bank' in title:
            return 'monetary'
        else:
            return 'general'
    
    def analyze_30_day_performance(self, thirty_day_data, latest_data):
        """Analyze 30-day market performance"""
        if not thirty_day_data or not latest_data:
            return "Insufficient data for analysis"
        
        closes = thirty_day_data.get('close', [])
        dates = thirty_day_data.get('labels', [])
        
        if len(closes) < 5:
            return "Need more data points for analysis"
        
        # Calculate key metrics
        start_price = closes[0]
        end_price = closes[-1]
        total_return = ((end_price - start_price) / start_price) * 100
        
        # Find best and worst weeks
        weekly_returns = []
        for i in range(0, len(closes), 5):
            if i+4 < len(closes):
                week_return = ((closes[i+4] - closes[i]) / closes[i]) * 100
                weekly_returns.append(week_return)
        
        best_week = max(weekly_returns) if weekly_returns else 0
        worst_week = min(weekly_returns) if weekly_returns else 0
        
        # Count up/down days
        up_days = sum(1 for i in range(1, len(closes)) if closes[i] > closes[i-1])
        down_days = sum(1 for i in range(1, len(closes)) if closes[i] < closes[i-1])
        
        # Trend analysis
        if len(closes) >= 10:
            first_half_avg = sum(closes[:5]) / 5
            second_half_avg = sum(closes[-5:]) / 5
            trend_strength = ((second_half_avg - first_half_avg) / first_half_avg) * 100
        else:
            trend_strength = total_return
        
        # Generate analysis
        analysis = f"""
## 📈 30-DAY MARKET PERFORMANCE ANALYSIS

### Overall Performance
Over the last 30 trading days ({dates[0]} to {dates[-1]}), the NEPSE index has {'gained' if total_return >= 0 else 'lost'} {abs(total_return):.2f}%, moving from {start_price:.2f} to {end_price:.2f}.

### Market Breadth
- **Up Days:** {up_days} days ({up_days/len(closes)*100:.1f}%)
- **Down Days:** {down_days} days ({down_days/len(closes)*100:.1f}%)
- **Trend Strength:** {'Strong' if abs(trend_strength) > 3 else 'Moderate' if abs(trend_strength) > 1 else 'Weak'} {('upward' if trend_strength > 0 else 'downward')}

### Volatility Analysis
- **Best Week:** +{best_week:.2f}%
- **Worst Week:** {worst_week:.2f}%
- **Price Range:** {min(closes):.0f} - {max(closes):.0f} (range of {max(closes)-min(closes):.0f} points)

### Technical Observations
- Current price is {'above' if end_price > closes[-5] else 'below'} 5-day average
- {'Bullish divergence forming' if end_price > start_price and trend_strength > 2 else 'Bearish pressure evident' if end_price < start_price and trend_strength < -2 else 'Consolidation pattern emerging'}
"""
        return analysis
    
    def get_technical_indicators(self, thirty_day_data):
        """Calculate technical indicators"""
        closes = thirty_day_data.get('close', [])
        
        if len(closes) < 20:
            return {}
        
        # Simple Moving Averages
        sma5 = sum(closes[-5:]) / 5
        sma10 = sum(closes[-10:]) / 10
        sma20 = sum(closes[-20:]) / 20
        
        # RSI (simplified)
        gains = []
        losses = []
        for i in range(1, len(closes)):
            change = closes[i] - closes[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        
        avg_gain = sum(gains[-14:]) / 14 if len(gains) >= 14 else 0
        avg_loss = sum(losses[-14:]) / 14 if len(losses) >= 14 else 0
        rs = avg_gain / avg_loss if avg_loss != 0 else 0
        rsi = 100 - (100 / (1 + rs)) if avg_loss != 0 else 50
        
        # Support and Resistance
        recent_lows = closes[-20:]
        recent_highs = closes[-20:]
        
        # Find support (nearest low that was touched multiple times)
        support = min(recent_lows)
        resistance = max(recent_highs)
        
        return {
            'sma5': round(sma5, 2),
            'sma10': round(sma10, 2),
            'sma20': round(sma20, 2),
            'rsi': round(rsi, 2),
            'support': round(support, 2),
            'resistance': round(resistance, 2),
            'position': 'above' if closes[-1] > sma20 else 'below'
        }
    
    def generate_complete_report(self, thirty_day_data, latest_data):
        """Generate complete market report with news"""
        
        # Get real news
        real_news = self.fetch_recent_news(30)
        
        # Categorize news by impact
        news_by_category = {}
        for news in real_news:
            cat = news['category']
            if cat not in news_by_category:
                news_by_category[cat] = []
            news_by_category[cat].append(news)
        
        # Get performance analysis
        performance = self.analyze_30_day_performance(thirty_day_data, latest_data)
        
        # Get technical indicators
        technical = self.get_technical_indicators(thirty_day_data)
        
        # Generate sentiment based on news and performance
        closes = thirty_day_data.get('close', [])
        total_return = ((closes[-1] - closes[0]) / closes[0] * 100) if closes else 0
        
        # Categorize news impact
        positive_news_count = 0
        negative_news_count = 0
        for news in real_news:
            title_lower = news['title'].lower()
            if any(word in title_lower for word in ['gain', 'positive', 'growth', 'increase', 'approved', 'dividend']):
                positive_news_count += 1
            elif any(word in title_lower for word in ['loss', 'negative', 'decline', 'decrease', 'delay', 'penalty']):
                negative_news_count += 1
        
        if total_return > 3 and positive_news_count > negative_news_count:
            sentiment = "BULLISH"
            sentiment_color = "green"
        elif total_return < -3 and negative_news_count > positive_news_count:
            sentiment = "BEARISH"
            sentiment_color = "red"
        else:
            sentiment = "NEUTRAL to CAUTIOUSLY OPTIMISTIC"
            sentiment_color = "yellow"
        
        # Generate news summary by category
        news_summary = ""
        for category, news_list in news_by_category.items():
            if news_list:
                news_summary += f"\n### {category.upper()} SECTOR NEWS\n"
                for news in news_list[:3]:
                    news_summary += f"\n- **{news['title']}** ({news['date']})\n  {news['summary'][:150]}...\n"
        
        # Generate investor advice
        if technical.get('rsi', 50) > 70:
            advice = "Market appears overbought. Consider profit booking at resistance levels. Wait for correction before fresh entry."
        elif technical.get('rsi', 50) < 30:
            advice = "Market appears oversold. Accumulation opportunity at current levels. Focus on fundamentally strong stocks."
        elif total_return > 0:
            advice = "Positive momentum continuing. Hold quality stocks. Add on dips near support levels."
        else:
            advice = "Market consolidating. Adopt wait-and-watch approach. Accumulate quality stocks gradually."
        
        # Complete report
        report = f"""
## 🎯 MARKET SENTIMENT: {sentiment}

{performance}

## 📊 TECHNICAL INDICATORS

| Indicator | Value | Signal |
|-----------|-------|--------|
| 5-Day SMA | {technical.get('sma5', 'N/A')} | {'Bullish' if closes[-1] > technical.get('sma5', 0) else 'Bearish'} |
| 20-Day SMA | {technical.get('sma20', 'N/A')} | {'Bullish' if closes[-1] > technical.get('sma20', 0) else 'Bearish'} |
| RSI (14) | {technical.get('rsi', 'N/A')} | {'Overbought' if technical.get('rsi', 50) > 70 else 'Oversold' if technical.get('rsi', 50) < 30 else 'Neutral'} |
| Support | {technical.get('support', 'N/A')} | Key level to watch |
| Resistance | {technical.get('resistance', 'N/A')} | Breakout level |

## 📰 REAL MARKET NEWS & FACTORS (Last 30 Days)

{news_summary if news_summary else 'No recent news found. Market factors based on technical analysis.'}

## 💡 INVESTOR RECOMMENDATION

{advice}

### Key Levels to Watch:
- **Immediate Support:** {technical.get('support', 'N/A')}
- **Immediate Resistance:** {technical.get('resistance', 'N/A')}
- **Stop Loss:** Below {technical.get('support', 0) - 20:.0f} for long positions
- **Target:** {technical.get('resistance', 0) + 20:.0f} in near term

---
*Analysis based on {len(closes)} days of market data and {len(real_news)} news articles from Sharesansar, Nepalipaisa, and other sources.*
"""
        return report, real_news, technical

# Create instance
news_analyzer = MarketNewsAnalyzer()