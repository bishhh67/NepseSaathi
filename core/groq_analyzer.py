# # core/groq_analyzer.py
# from groq import Groq
# from django.conf import settings
# from django.core.cache import cache
# import json
# import re
# from datetime import datetime

# class GroqAnalyzer:
#     def __init__(self):
#         try:
#             self.client = Groq(api_key=settings.GROQ_API_KEY)
#             self.available = True
#             print("✅ Groq AI initialized successfully")
#         except Exception as e:
#             print(f"❌ Groq init error: {e}")
#             self.available = False
    
#     def analyze_market(self, thirty_day_data, latest_data):
#         """Complete AI-powered market analysis with Groq (free, fast)"""
        
#         # Check cache (6 hours)
#         cache_key = "groq_complete_analysis"
#         cached = cache.get(cache_key)
#         if cached:
#             print("Returning cached Groq analysis")
#             return cached
        
#         # Prepare data for AI
#         closes = thirty_day_data.get('close', [])
#         dates = thirty_day_data.get('labels', [])
        
#         if closes and len(closes) >= 5:
#             start_price = closes[0]
#             end_price = closes[-1]
#             monthly_return = ((end_price - start_price) / start_price * 100) if start_price != 0 else 0
#             ma5 = sum(closes[-5:]) / 5
#             ma10 = sum(closes[-10:]) / 10 if len(closes) >= 10 else ma5
#             ma20 = sum(closes[-20:]) / 20 if len(closes) >= 20 else ma5
#             high = max(closes)
#             low = min(closes)
            
#             # Calculate up/down days
#             up_days = sum(1 for i in range(1, len(closes)) if closes[i] > closes[i-1])
#             down_days = sum(1 for i in range(1, len(closes)) if closes[i] < closes[i-1])
            
#             # Calculate RSI
#             gains, losses = [], []
#             for i in range(1, len(closes)):
#                 diff = closes[i] - closes[i-1]
#                 if diff > 0:
#                     gains.append(diff)
#                 else:
#                     losses.append(abs(diff))
#             avg_gain = sum(gains[-14:]) / 14 if len(gains) >= 14 else (sum(gains) / len(gains) if gains else 0)
#             avg_loss = sum(losses[-14:]) / 14 if len(losses) >= 14 else (sum(losses) / len(losses) if losses else 1)
#             rs = avg_gain / avg_loss if avg_loss > 0 else 1
#             rsi = 100 - (100 / (1 + rs))
            
#             # Prepare daily data string
#             daily_data = ""
#             for i in range(min(len(closes), 30)):
#                 if i < len(dates):
#                     daily_data += f"{dates[i]}: {closes[i]}\n"
#         else:
#             monthly_return = 0
#             ma5 = latest_data.get('close', 0)
#             ma10 = latest_data.get('close', 0)
#             ma20 = latest_data.get('close', 0)
#             high = latest_data.get('high', 0)
#             low = latest_data.get('low', 0)
#             up_days = 0
#             down_days = 0
#             rsi = 50
#             daily_data = "Insufficient daily data"
        
#         current = latest_data.get('close', 0)
#         daily_change = latest_data.get('percent_change', 0)
#         daily_points = latest_data.get('point_change', 0)
#         period_start = dates[0] if dates else 'N/A'
#         period_end = dates[-1] if dates else 'N/A'
#         ma5_val = f"{ma5:.2f}"
#         ma10_val = f"{ma10:.2f}"
#         ma20_val = f"{ma20:.2f}"
#         rsi_val = f"{rsi:.1f}"
        
#         # Create comprehensive prompt for Groq
#         prompt = f"""You are a senior NEPSE (Nepal Stock Exchange) market analyst with 20+ years of experience. Provide a COMPLETE, DETAILED market analysis based on the data below.

# ## MARKET DATA (Last 30 days):
# - Period: {period_start} to {period_end}
# - Current NEPSE Level: {current}
# - Today's Change: {daily_change}% ({daily_points} points)
# - 30-Day Return: {monthly_return:.2f}%
# - 30-Day High: {high}
# - 30-Day Low: {low}
# - Up Days: {up_days}
# - Down Days: {down_days}
# - RSI (14-day): {rsi_val}
# - 5-Day Moving Average: {ma5_val}
# - 10-Day Moving Average: {ma10_val}
# - 20-Day Moving Average: {ma20_val}
# - Current Position: {'Above' if current > ma20 else 'Below'} 20-day MA

# ## YOUR ANALYSIS MUST BE DETAILED AND EDUCATIONAL. INCLUDE:

# ### EXECUTIVE SUMMARY
# Write 3-4 sentences explaining the overall market situation and key takeaways.

# ### MARKET SENTIMENT ANALYSIS
# - Overall sentiment (Bullish/Bearish/Neutral/Cautiously Bullish)
# - Sentiment score (-10 to +10)
# - Detailed explanation of WHY this sentiment exists

# ### DETAILED TECHNICAL ANALYSIS
# - Trend Analysis: What does the 30-day price movement tell us?
# - Moving Averages: What do MA5, MA10, MA20 positions indicate?
# - Support & Resistance: Why are these levels important?
# - RSI Analysis: What does RSI tell us about buying/selling pressure?

# ### KEY MARKET DRIVERS (5 detailed reasons)
# List 5 specific reasons for this market movement with explanations.

# ### TECHNICAL OUTLOOK
# - Short-term (1-2 weeks): Specific price targets
# - Medium-term (1-2 months): Broader outlook
# - Key support and resistance levels with explanations

# ### INVESTMENT RECOMMENDATION

# **Conservative Investors:**
# - Portfolio allocation
# - Entry levels and stop losses

# **Moderate Investors:**
# - Strategy and position sizing
# - Accumulation zones

# **Aggressive Investors:**
# - Trading strategy with specific levels

# **Actionable Steps (5 specific bullet points):**
# 1. Specific action with price level
# 2. Specific action with price level
# 3. Specific action with price level
# 4. Specific action with price level
# 5. Specific action with price level

# ### RISK FACTORS (3-5 specific risks)
# List specific risks with explanations.

# ### WEEKLY FORECAST
# Detailed prediction for next week with specific price targets.

# Be EXTREMELY DETAILED. Use specific numbers. Write for retail investors.

# BEGIN ANALYSIS:"""

#         try:
#             print("Calling Groq API for detailed market analysis...")
            
#             response = self.client.chat.completions.create(
#                 model="llama-3.3-70b-versatile",
#                 messages=[{"role": "user", "content": prompt}],
#                 temperature=0.7,
#                 max_tokens=4096,
#                 top_p=0.95
#             )
            
#             analysis_text = response.choices[0].message.content
#             print(f"Groq analysis received ({len(analysis_text)} characters)")
            
#             result = {
#                 'analysis': analysis_text,
#                 'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
#                 'data_period': f"{period_start} to {period_end}",
#                 'monthly_return': monthly_return,
#                 'rsi': rsi,
#                 'support': low,
#                 'resistance': high,
#                 'current': current,
#                 'ma20': ma20,
#                 'model': 'Llama 3.3 70B (Groq)'
#             }
            
#             cache.set(cache_key, result, 21600)
#             return result
            
#         except Exception as e:
#             print(f"Groq API error: {e}")
#             return self._get_fallback_analysis(current, monthly_return, rsi, low, high, ma20, ma5, up_days, down_days)
    
#     def _get_fallback_analysis(self, current, monthly_return, rsi, low, high, ma20, ma5, up_days, down_days):
#         """Detailed fallback if API fails"""
#         return {
#             'analysis': f"""
# ## EXECUTIVE SUMMARY

# The NEPSE index is currently trading at {current:.2f}, showing a {monthly_return:+.1f}% return over the past 30 days. The market has experienced {up_days} up days vs {down_days} down days. The index is trading {'above' if current > ma20 else 'below'} its 20-day moving average of {ma20:.2f}.

# ## MARKET SENTIMENT

# **Overall Sentiment:** {'BULLISH' if monthly_return > 2 else 'NEUTRAL' if monthly_return > -2 else 'BEARISH'}
# **Sentiment Score:** {min(10, max(-10, int(monthly_return * 3))) if monthly_return > 0 else max(-10, min(10, int(monthly_return * 3)))}/10

# ## TECHNICAL ANALYSIS

# - **30-Day Performance:** {monthly_return:+.1f}%
# - **RSI Level:** {rsi:.0f} - {'Overbought' if rsi > 70 else 'Oversold' if rsi < 30 else 'Neutral'}
# - **Moving Averages:** Price is {'above' if current > ma5 else 'below'} 5-day MA ({ma5:.0f})
# - **Support:** {low:.0f} | **Resistance:** {high:.0f}

# ## KEY MARKET DRIVERS

# 1. {monthly_return:.1f}% {'gain' if monthly_return >= 0 else 'loss'} over 30 days
# 2. Price {'above' if current > ma20 else 'below'} 20-day moving average
# 3. RSI at {rsi:.0f} indicates {'overbought conditions' if rsi > 70 else 'oversold conditions' if rsi < 30 else 'neutral momentum'}
# 4. Trading range of {low:.0f} - {high:.0f}
# 5. {up_days} up days vs {down_days} down days

# ## INVESTMENT RECOMMENDATION

# **Conservative Investors:** Maintain 40-50% exposure. Entry near {low:.0f}.
# **Moderate Investors:** Accumulate on dips to {low:.0f}. Target {high:.0f}.
# **Aggressive Investors:** {'Book profits near {high:.0f}' if monthly_return > 2 else 'Start accumulating gradually'}

# **Actionable Steps:**
# 1. Set alerts at {low:.0f} and {high:.0f}
# 2. Use stop loss below {low - 20:.0f}
# 3. Book partial profits at {high:.0f}
# 4. Add positions on pullbacks to {low:.0f}
# 5. Maintain 30-40% cash for opportunities

# ## RISK FACTORS
# - Technical correction risk
# - Global market volatility
# - Regulatory changes
# - Liquidity conditions

# ## WEEKLY FORECAST
# Expected range: {low:.0f} - {high:.0f}. {'Breakout above {high:.0f} targets {high + 50:.0f}.' if current > ma20 else f'Support at {low:.0f} may hold.'}
# """,
#             'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
#             'monthly_return': monthly_return,
#             'rsi': rsi,
#             'support': low,
#             'resistance': high,
#             'current': current,
#             'ma20': ma20,
#             'model': 'Fallback Analysis'
#         }

# # Create instance
# groq_analyzer = GroqAnalyzer()