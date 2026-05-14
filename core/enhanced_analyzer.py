# core/enhanced_analyzer.py
import json
from datetime import datetime

class EnhancedMarketAnalyzer:
    """Provides detailed market analysis with real news"""
    
    def __init__(self):
        pass
    
    def analyze_market(self, thirty_day_data, latest_data, news_items):
        """Generate comprehensive market analysis"""
        
        closes = thirty_day_data.get('close', [])
        dates = thirty_day_data.get('labels', [])
        highs = thirty_day_data.get('high', [])
        lows = thirty_day_data.get('low', [])
        
        if len(closes) < 10:
            return self.get_basic_analysis(latest_data)
        
        # Calculate detailed metrics
        start_price = closes[0]
        end_price = closes[-1]
        total_return = ((end_price - start_price) / start_price) * 100
        
        # Daily returns
        daily_returns = []
        for i in range(1, len(closes)):
            ret = (closes[i] - closes[i-1]) / closes[i-1] * 100
            daily_returns.append(ret)
        
        avg_daily_return = sum(daily_returns) / len(daily_returns)
        volatility = (sum((r - avg_daily_return) ** 2 for r in daily_returns) / len(daily_returns)) ** 0.5
        
        # Best and worst days
        best_day = max(daily_returns)
        worst_day = min(daily_returns)
        
        # Moving averages
        ma5 = sum(closes[-5:]) / 5
        ma10 = sum(closes[-10:]) / 10 if len(closes) >= 10 else ma5
        ma20 = sum(closes[-20:]) / 20 if len(closes) >= 20 else ma10
        
        # RSI calculation
        gains = [r for r in daily_returns if r > 0]
        losses = [abs(r) for r in daily_returns if r < 0]
        avg_gain = sum(gains[-14:]) / 14 if len(gains) >= 14 else sum(gains) / len(gains) if gains else 0
        avg_loss = sum(losses[-14:]) / 14 if len(losses) >= 14 else sum(losses) / len(losses) if losses else 1
        rs = avg_gain / avg_loss if avg_loss > 0 else 1
        rsi = 100 - (100 / (1 + rs))
        
        # Trend analysis
        if len(closes) >= 20:
            first_decade_avg = sum(closes[:10]) / 10
            last_decade_avg = sum(closes[-10:]) / 10
            trend_strength = ((last_decade_avg - first_decade_avg) / first_decade_avg) * 100
        else:
            trend_strength = total_return
        
        # Support and Resistance levels
        recent_lows = lows[-20:] if len(lows) >= 20 else lows
        recent_highs = highs[-20:] if len(highs) >= 20 else highs
        support = min(recent_lows)
        resistance = max(recent_highs)
        
        # Volume analysis
        volumes = thirty_day_data.get('volume', [])
        if volumes:
            avg_volume = sum(volumes[-10:]) / 10 if len(volumes) >= 10 else sum(volumes) / len(volumes)
            current_volume = volumes[-1] if volumes else 0
            volume_trend = "above" if current_volume > avg_volume * 1.2 else "below" if current_volume < avg_volume * 0.8 else "at"
        else:
            volume_trend = "N/A"
        
        # Generate market sentiment based on data
        if total_return > 5 and rsi < 70:
            sentiment = "STRONGLY BULLISH"
            sentiment_detail = "Strong upward momentum with room for further gains"
        elif total_return > 2 and trend_strength > 0:
            sentiment = "BULLISH"
            sentiment_detail = "Positive momentum with institutional participation"
        elif total_return > -2 and abs(trend_strength) < 2:
            sentiment = "NEUTRAL"
            sentiment_detail = "Range-bound market with consolidation"
        elif total_return > -5:
            sentiment = "CAUTIOUSLY BEARISH"
            sentiment_detail = "Mild selling pressure, support levels holding"
        else:
            sentiment = "BEARISH"
            sentiment_detail = "Strong downward pressure, wait for reversal signals"
        
        # Categorize news by impact
        categorized_news = self.categorize_news(news_items)
        
        # Generate detailed analysis sections
        technical_analysis = self.generate_technical_analysis(
            closes, ma5, ma10, ma20, rsi, support, resistance, 
            total_return, volatility, best_day, worst_day, volume_trend
        )
        
        market_drivers = self.generate_market_drivers(
            total_return, rsi, trend_strength, volume_trend, categorized_news
        )
        
        weekly_outlook = self.generate_weekly_outlook(
            sentiment, rsi, support, resistance, total_return, trend_strength
        )
        
        investment_recommendation = self.generate_recommendation(
            sentiment, rsi, support, resistance, total_return
        )
        
        return {
            'sentiment': sentiment,
            'sentiment_detail': sentiment_detail,
            'technical_analysis': technical_analysis,
            'market_drivers': market_drivers,
            'weekly_outlook': weekly_outlook,
            'investment_recommendation': investment_recommendation,
            'key_levels': {
                'support': support,
                'resistance': resistance,
                'ma5': ma5,
                'ma20': ma20,
                'rsi': round(rsi, 2)
            },
            'categorized_news': categorized_news,
            'top_news': news_items[:10]
        }
    
    def categorize_news(self, news_items):
        """Categorize news items by impact"""
        categories = {
            'SEBON/Regulatory': [],
            'NRB/Monetary Policy': [],
            'Banking Sector': [],
            'Hydropower': [],
            'Corporate Actions': [],
            'IPO/FPO': [],
            'General Market': []
        }
        
        for news in news_items:
            title_lower = news['title'].lower()
            if 'sebon' in title_lower or 'regulation' in title_lower or 'rule' in title_lower:
                categories['SEBON/Regulatory'].append(news)
            elif 'nrb' in title_lower or 'nepal rastra' in title_lower or 'policy' in title_lower or 'interest' in title_lower:
                categories['NRB/Monetary Policy'].append(news)
            elif 'bank' in title_lower or 'finance' in title_lower or 'microfinance' in title_lower:
                categories['Banking Sector'].append(news)
            elif 'hydro' in title_lower or 'power' in title_lower or 'energy' in title_lower:
                categories['Hydropower'].append(news)
            elif 'dividend' in title_lower or 'bonus' in title_lower or 'right' in title_lower or 'agm' in title_lower:
                categories['Corporate Actions'].append(news)
            elif 'ipo' in title_lower or 'fpo' in title_lower or 'public issue' in title_lower:
                categories['IPO/FPO'].append(news)
            else:
                categories['General Market'].append(news)
        
        return {k: v for k, v in categories.items() if v}
    
    def generate_technical_analysis(self, closes, ma5, ma10, ma20, rsi, support, resistance, 
                                     total_return, volatility, best_day, worst_day, volume_trend):
        """Generate detailed technical analysis"""
        
        current_price = closes[-1]
        
        # Determine position relative to moving averages
        if current_price > ma5 > ma10 > ma20:
            ma_signal = "Golden Cross pattern forming - STRONG BULLISH"
        elif current_price > ma20 and current_price < ma5:
            ma_signal = "Short-term correction within uptrend - BULLISH"
        elif current_price < ma5 < ma10 < ma20:
            ma_signal = "Death Cross pattern - BEARISH"
        elif current_price < ma20 and current_price > ma5:
            ma_signal = "Short-term recovery attempt - CAUTIOUSLY BULLISH"
        else:
            ma_signal = "Mixed signals - NEUTRAL"
        
        # RSI interpretation
        if rsi > 70:
            rsi_signal = f"Overbought (RSI: {rsi:.1f}) - Expect consolidation or pullback"
        elif rsi < 30:
            rsi_signal = f"Oversold (RSI: {rsi:.1f}) - Potential bounce opportunity"
        elif rsi > 50:
            rsi_signal = f"Bullish momentum (RSI: {rsi:.1f}) - Buying interest present"
        else:
            rsi_signal = f"Bearish momentum (RSI: {rsi:.1f}) - Selling pressure exists"
        
        analysis = f"""
📈 **Trend Analysis**: The market has {'gained' if total_return >= 0 else 'lost'} {abs(total_return):.2f}% over the last 30 days. 
Daily volatility stands at {volatility:.2f}%, with the best day gaining {best_day:.2f}% and worst day losing {abs(worst_day):.2f}%.

📊 **Moving Average Analysis**: 
- Current Price: {current_price:.2f}
- 5-Day MA: {ma5:.2f} (Price is {'above' if current_price > ma5 else 'below'})
- 10-Day MA: {ma10:.2f}
- 20-Day MA: {ma20:.2f}
Signal: {ma_signal}

🔄 **RSI Analysis**: {rsi_signal}

🎯 **Support & Resistance**:
- Immediate Support: {support:.2f} (Strong buying interest expected at this level)
- Immediate Resistance: {resistance:.2f} (Profit booking likely at this level)
- Range Width: {resistance - support:.0f} points

📦 **Volume Analysis**: Volume is {volume_trend} average levels, indicating {'strong participation' if volume_trend == 'above' else 'cautious participation' if volume_trend == 'below' else 'normal activity'}.
"""
        return analysis
    
    def generate_market_drivers(self, total_return, rsi, trend_strength, volume_trend, categorized_news):
        """Generate detailed market drivers"""
        
        drivers = []
        
        # Technical drivers
        drivers.append(f"**Technical Momentum**: {'Strong' if abs(total_return) > 5 else 'Moderate' if abs(total_return) > 2 else 'Weak'} {'upward' if total_return > 0 else 'downward'} movement with {abs(trend_strength):.1f}% trend strength over 30 days.")
        
        drivers.append(f"**RSI Indicator**: {'Overbought conditions suggest caution' if rsi > 70 else 'Oversold levels indicate value buying opportunity' if rsi < 30 else 'Neutral RSI allows balanced position taking'} (Current RSI: {rsi:.1f})")
        
        drivers.append(f"**Volume Analysis**: {volume_trend.upper()} average volume suggests {'institutional participation' if volume_trend == 'above' else 'retail-driven activity' if volume_trend == 'below' else 'balanced market participation'}")
        
        # News-based drivers
        if 'SEBON/Regulatory' in categorized_news:
            drivers.append(f"**Regulatory Environment**: Recent SEBON announcements are influencing market sentiment. Key regulatory news includes {categorized_news['SEBON/Regulatory'][0]['title'][:100]}...")
        
        if 'NRB/Monetary Policy' in categorized_news:
            drivers.append(f"**Monetary Policy Impact**: NRB's policy stance and interest rate environment are key market drivers. {categorized_news['NRB/Monetary Policy'][0]['title'][:100]}...")
        
        if 'Banking Sector' in categorized_news:
            drivers.append(f"**Banking Sector Lead**: Banking stocks are showing leadership with recent news: {categorized_news['Banking Sector'][0]['title'][:100]}...")
        
        if 'Hydropower' in categorized_news:
            drivers.append(f"**Hydropower Momentum**: Energy sector gaining attention. {categorized_news['Hydropower'][0]['title'][:100]}...")
        
        # General driver if no news
        if not any(categorized_news.values()):
            drivers.append("**Market Sentiment**: General market sentiment is driven by technical factors and global cues. Watch for breakout above resistance or breakdown below support for directional clarity.")
        
        return drivers
    
    def generate_weekly_outlook(self, sentiment, rsi, support, resistance, total_return, trend_strength):
        """Generate detailed weekly outlook"""
        
        if rsi > 70:
            short_term = "Market is in overbought territory. Expect profit booking in the next 2-3 sessions. Key support to watch is {:.0f}.".format(support)
            medium_term = "Correction likely before next leg up. Accumulate on dips near {:.0f} level.".format(support)
        elif rsi < 30:
            short_term = "Market is oversold. Bounce expected in coming sessions. Resistance at {:.0f} will be first target.".format(resistance)
            medium_term = "Value buying opportunity. Gradual accumulation recommended with stop loss below {:.0f}.".format(support - 20)
        elif total_return > 0:
            short_term = "Positive momentum continuing. Look for breakout above {:.0f} for further upside.".format(resistance)
            medium_term = "Uptrend intact. Hold existing positions. Add on dips near {:.0f}.".format(support)
        else:
            short_term = "Market consolidating. Range-bound trading expected between {:.0f} and {:.0f}.".format(support, resistance)
            medium_term = "Wait for directional clarity. Support at {:.0f} needs to hold for stability.".format(support)
        
        outlook = f"""
📅 **Short-term (Next Week)**:
{short_term}

📆 **Medium-term (2-4 Weeks)**:
{medium_term}

🎯 **Key Levels to Watch**:
- Breakout above {resistance:.0f} → Target {resistance + 50:.0f}
- Breakdown below {support:.0f} → Target {support - 40:.0f}

⚡ **Critical Events to Monitor**:
1. SEBON announcements on new regulations
2. NRB monetary policy review
3. Quarterly earnings results
4. Global market cues
5. Liquidity conditions in banking system
"""
        return outlook
    
    def generate_recommendation(self, sentiment, rsi, support, resistance, total_return):
        """Generate detailed investment recommendation"""
        
        if rsi > 70:
            rec = f"""
**Strategy**: BOOK PROFITS / REDUCE EXPOSURE

**Rationale**: Market has reached overbought territory (RSI: {rsi:.1f}) with {total_return:.1f}% gain in 30 days. Historical patterns suggest consolidation or pullback.

**Actionable Steps**:
1. Book partial profits (30-40%) at current levels
2. Place stop loss at {support - 15:.0f} for remaining holdings
3. Wait for correction to {support:.0f} before fresh buying
4. Avoid aggressive positions at current levels
5. Focus on fundamentally strong stocks for dips

**Risk Management**: Keep position size small (max 40% of portfolio)
"""
        elif rsi < 30:
            rec = f"""
**Strategy**: ACCUMULATE / BUY ON DIPS

**Rationale**: Market is oversold (RSI: {rsi:.1f}) with {abs(total_return):.1f}% decline. Value buying opportunity emerging.

**Actionable Steps**:
1. Start accumulating quality stocks in 2-3 tranches
2. First buy at current levels (40% of planned allocation)
3. Second buy if market falls to {support - 20:.0f} (30% allocation)
4. Third buy at {support - 40:.0f} (30% allocation)
5. Keep overall exposure below 60% until trend reverses

**Focus Sectors**: Banking, Hydropower, and fundamentally strong stocks
"""
        elif total_return > 0:
            rec = f"""
**Strategy**: HOLD / ADD ON MODERATE DIPS

**Rationale**: Positive momentum with {total_return:.1f}% gain. Uptrend intact.

**Actionable Steps**:
1. Hold existing quality positions
2. Add 20-30% allocation on dips near {support:.0f}
3. Book profits partially if market reaches {resistance + 30:.0f}
4. Keep stop loss at {support - 25:.0f} for protection
5. Maintain 60-70% portfolio exposure

**Watchlist**: Sector leaders with strong fundamentals
"""
        else:
            rec = f"""
**Strategy**: CAUTIOUS / WAIT-AND-WATCH

**Rationale**: Market in consolidation with {abs(total_return):.1f}% decline. Direction unclear.

**Actionable Steps**:
1. Maintain 30-40% portfolio exposure only
2. Avoid aggressive buying until trend clarity
3. Place tight stop losses at {support - 20:.0f}
4. Wait for breakout above {resistance:.0f} for entry
5. Focus on capital preservation

**Entry Triggers**: 
- Breakout above {resistance:.0f} with volume
- OR bounce from {support:.0f} with reversal pattern
"""
        
        return rec
    
    def get_basic_analysis(self, latest_data):
        """Fallback basic analysis"""
        return {
            'sentiment': 'NEUTRAL',
            'sentiment_detail': 'Insufficient data for detailed analysis',
            'technical_analysis': 'Need more historical data for technical analysis',
            'market_drivers': ['Market data is limited. Collecting more data points for better analysis.'],
            'weekly_outlook': 'Awaiting more market data for accurate outlook',
            'investment_recommendation': 'Wait for clearer market direction',
            'key_levels': {'support': 0, 'resistance': 0, 'ma5': 0, 'ma20': 0, 'rsi': 50}
        }

# Create instance
enhanced_analyzer = EnhancedMarketAnalyzer()