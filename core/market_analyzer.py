# core/market_analyzer.py
import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import json
import re

class MarketAnalyzer:
    """Fetches real news and provides proper market analysis"""
    
    def __init__(self):
        self.news_sources = [
            "https://www.sharesansar.com/rss",
            "https://www.nepalipaisa.com/rss",
        ]
    
    def fetch_recent_news(self, days=30):
        """Fetch real news from the last 30 days"""
        all_news = []
        cutoff_date = datetime.now() - timedelta(days=days)
        
        for source_url in self.news_sources:
            try:
                feed = feedparser.parse(source_url)
                for entry in feed.entries[:15]:
                    pub_date = None
                    if hasattr(entry, 'published_parsed'):
                        pub_date = datetime(*entry.published_parsed[:6])
                    elif hasattr(entry, 'updated_parsed'):
                        pub_date = datetime(*entry.updated_parsed[:6])
                    
                    if pub_date and pub_date > cutoff_date:
                        title_lower = entry.title.lower()
                        category = self._categorize_news(title_lower)
                        
                        all_news.append({
                            'title': entry.title,
                            'summary': entry.summary[:200] if hasattr(entry, 'summary') else entry.title[:150],
                            'link': entry.link,
                            'date': pub_date.strftime('%Y-%m-%d'),
                            'category': category,
                            'source': source_url.split('/')[2]
                        })
            except Exception as e:
                print(f"Error fetching from {source_url}: {e}")
        
        # Remove duplicates
        seen = set()
        unique_news = []
        for news in all_news:
            if news['title'] not in seen:
                seen.add(news['title'])
                unique_news.append(news)
        
        return unique_news[:20]
    
    def _categorize_news(self, title):
        if 'bank' in title or 'financial' in title:
            return 'banking'
        elif 'hydro' in title or 'power' in title:
            return 'hydropower'
        elif 'sebon' in title or 'regulation' in title or 'rule' in title:
            return 'regulatory'
        elif 'dividend' in title or 'bonus' in title or 'right' in title:
            return 'corporate'
        elif 'nrb' in title or 'nepal rastra' in title or 'policy' in title:
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
        
        start_price = closes[0]
        end_price = closes[-1]
        total_return = ((end_price - start_price) / start_price) * 100 if start_price != 0 else 0
        
        up_days = sum(1 for i in range(1, len(closes)) if closes[i] > closes[i-1])
        down_days = sum(1 for i in range(1, len(closes)) if closes[i] < closes[i-1])
        
        if len(closes) >= 10:
            first_half_avg = sum(closes[:5]) / 5
            second_half_avg = sum(closes[-5:]) / 5
            trend_strength = ((second_half_avg - first_half_avg) / first_half_avg) * 100 if first_half_avg != 0 else 0
        else:
            trend_strength = total_return
        
        analysis = f"""
📈 OVERALL PERFORMANCE: {total_return:+.2f}% over 30 days ({start_price:.2f} → {end_price:.2f})

📊 MARKET BREADTH: {up_days} up days vs {down_days} down days ({up_days/len(closes)*100:.0f}% positive sessions)

📉 TREND STRENGTH: {'Strong' if abs(trend_strength) > 3 else 'Moderate' if abs(trend_strength) > 1 else 'Weak'} {'upward' if trend_strength > 0 else 'downward'}

🎯 PRICE RANGE: {min(closes):.0f} - {max(closes):.0f} (range of {max(closes)-min(closes):.0f} points)
"""
        return analysis
    
    def get_technical_indicators(self, thirty_day_data):
        """Calculate technical indicators"""
        closes = thirty_day_data.get('close', [])
        
        if len(closes) < 20:
            return {
                'sma5': sum(closes[-5:]) / 5 if len(closes) >= 5 else 0,
                'sma20': 0,
                'rsi': 50,
                'support': min(closes) if closes else 0,
                'resistance': max(closes) if closes else 0,
                'position': 'neutral'
            }
        
        sma5 = sum(closes[-5:]) / 5
        sma20 = sum(closes[-20:]) / 20
        
        gains, losses = [], []
        for i in range(1, len(closes)):
            change = closes[i] - closes[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        
        avg_gain = sum(gains[-14:]) / 14 if len(gains) >= 14 else sum(gains) / len(gains) if gains else 0
        avg_loss = sum(losses[-14:]) / 14 if len(losses) >= 14 else sum(losses) / len(losses) if losses else 1
        rs = avg_gain / avg_loss if avg_loss != 0 else 1
        rsi = 100 - (100 / (1 + rs)) if avg_loss != 0 else 50
        
        support = min(closes[-20:])
        resistance = max(closes[-20:])
        
        return {
            'sma5': round(sma5, 2),
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
        
        # Get performance analysis
        performance = self.analyze_30_day_performance(thirty_day_data, latest_data)
        
        # Get technical indicators
        technical = self.get_technical_indicators(thirty_day_data)
        
        # Calculate metrics
        closes = thirty_day_data.get('close', [])
        total_return = ((closes[-1] - closes[0]) / closes[0] * 100) if closes and closes[0] != 0 else 0
        current_price = latest_data.get('close', 0)
        daily_change = latest_data.get('percent_change', 0)
        
        # Determine sentiment
        if total_return > 2 and daily_change > 0:
            sentiment = "BULLISH"
            sentiment_color = "green"
            sentiment_msg = f"Strong positive momentum with {total_return:.1f}% 30-day gain"
        elif total_return > 0:
            sentiment = "CAUTIOUSLY BULLISH"
            sentiment_color = "yellow"
            sentiment_msg = f"Positive but moderate momentum with {total_return:.1f}% gain"
        elif total_return > -2:
            sentiment = "NEUTRAL"
            sentiment_color = "gray"
            sentiment_msg = "Market consolidating with limited directional bias"
        else:
            sentiment = "BEARISH"
            sentiment_color = "red"
            sentiment_msg = f"Negative pressure with {abs(total_return):.1f}% decline"
        
        # Generate investor advice
        if technical.get('rsi', 50) > 70:
            advice = "📌 Market appears overbought. Consider booking partial profits at resistance levels. Wait for a pullback before fresh entry. Recommended action: Reduce exposure by 20-30%."
        elif technical.get('rsi', 50) < 30:
            advice = "📌 Market appears oversold. This could be a good accumulation opportunity. Focus on fundamentally strong stocks. Recommended action: Start building positions gradually."
        elif total_return > 0:
            advice = "📌 Positive momentum continuing. Hold quality stocks. Add on dips near support levels. Recommended action: Maintain 60-70% portfolio exposure."
        else:
            advice = "📌 Market consolidating. Adopt wait-and-watch approach. Recommended action: Keep 40-50% cash, accumulate quality stocks gradually on dips."
        
        # Create report
        report = f"""
## 🎯 MARKET SENTIMENT: {sentiment}

**{sentiment_msg}**

---

{performance}

---

## 📊 TECHNICAL INDICATORS

| Indicator | Value | Signal |
|-----------|-------|--------|
| 5-Day SMA | {technical.get('sma5', 'N/A')} | {'Bullish' if closes[-1] > technical.get('sma5', 0) else 'Bearish'} |
| 20-Day SMA | {technical.get('sma20', 'N/A')} | {'Bullish' if closes[-1] > technical.get('sma20', 0) else 'Bearish'} |
| RSI (14) | {technical.get('rsi', 'N/A')} | {'Overbought' if technical.get('rsi', 50) > 70 else 'Oversold' if technical.get('rsi', 50) < 30 else 'Neutral'} |
| Support | {technical.get('support', 'N/A')} | Key buying zone |
| Resistance | {technical.get('resistance', 'N/A')} | Key selling zone |

---

## 💡 INVESTMENT RECOMMENDATION

{advice}

---

### Key Levels to Watch:
- **Immediate Support:** {technical.get('support', 'N/A'):.0f}
- **Immediate Resistance:** {technical.get('resistance', 'N/A'):.0f}
- **Stop Loss:** Below {technical.get('support', 0) - 20:.0f} for long positions
- **Target:** {technical.get('resistance', 0) + 30:.0f} in near term
"""
        
        return report, real_news, technical

# Create instance
market_analyzer = MarketAnalyzer()