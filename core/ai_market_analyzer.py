# core/ai_market_analyzer.py
import google.generativeai as genai
from django.conf import settings
from django.core.cache import cache
import json
import re
from datetime import datetime

class AIMarketAnalyzer:
    def __init__(self):
        try:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            # Use gemini-2.0-flash which supports grounding/web search
            self.model = genai.GenerativeModel('gemini-2.0-flash')
            self.available = True
        except Exception as e:
            print(f"Gemini init error: {e}")
            self.available = False
    
    def analyze_market(self, thirty_day_data, latest_data):
        """Complete AI-powered market analysis with web search"""
        
        # Check cache (6 hours)
        cache_key = "ai_complete_analysis"
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        # Prepare data for AI
        closes = thirty_day_data.get('close', [])
        dates = thirty_day_data.get('labels', [])
        
        if closes and len(closes) >= 5:
            start_price = closes[0]
            end_price = closes[-1]
            monthly_return = ((end_price - start_price) / start_price * 100) if start_price != 0 else 0
            ma5 = sum(closes[-5:]) / 5
            ma10 = sum(closes[-10:]) / 10 if len(closes) >= 10 else ma5
            ma20 = sum(closes[-20:]) / 20 if len(closes) >= 20 else ma5
            high = max(closes)
            low = min(closes)
            
            # Calculate up/down days
            up_days = sum(1 for i in range(1, len(closes)) if closes[i] > closes[i-1])
            down_days = sum(1 for i in range(1, len(closes)) if closes[i] < closes[i-1])
            
            # Prepare daily data string
            daily_data = ""
            for i in range(len(closes)):
                if i < len(dates):
                    daily_data += f"{dates[i]}: {closes[i]}\n"
        else:
            monthly_return = 0
            ma5 = latest_data.get('close', 0)
            ma10 = latest_data.get('close', 0)
            ma20 = latest_data.get('close', 0)
            high = latest_data.get('high', 0)
            low = latest_data.get('low', 0)
            up_days = 0
            down_days = 0
            daily_data = "Insufficient daily data"
        
        current = latest_data.get('close', 0)
        daily_change = latest_data.get('percent_change', 0)
        daily_points = latest_data.get('point_change', 0)
        
        # Create comprehensive prompt for Gemini with web search instructions
        prompt = f"""You are a senior NEPSE (Nepal Stock Exchange) market analyst with 20+ years of experience. You have access to the internet via Google Search.

## YOUR TASK:
Provide a COMPLETE, DETAILED market analysis based on the data below AND real-time internet search for news.

## MARKET DATA (Last 30 days):
- Period: {dates[0] if dates else 'N/A'} to {dates[-1] if dates else 'N/A'}
- Current NEPSE Level: {current}
- Today's Change: {daily_change}% ({daily_points} points)
- 30-Day Return: {monthly_return:.2f}%
- 30-Day High: {high}
- 30-Day Low: {low}
- Up Days: {up_days}
- Down Days: {down_days}
- 5-Day Moving Average: {ma5:.2f}
- 10-Day Moving Average: {ma10:.2f}
- 20-Day Moving Average: {ma20:.2f}
- Current Position: {'Above' if current > ma20 else 'Below'} 20-day MA

## DAILY CLOSING DATA:
{daily_data}

## INSTRUCTIONS - YOU MUST USE GOOGLE SEARCH:

1. **SEARCH THE WEB** for real NEPSE news from the last 30 days from:
   - Sharesansar (www.sharesansar.com)
   - Nepalipaisa (www.nepalipaisa.com)
   - NEPSE Alpha (nepsealpha.com)
   - Other Nepali financial news sites

2. **FIND SPECIFIC NEWS** about:
   - SEBON announcements and regulatory changes
   - NRB monetary policy updates
   - Company-specific news (dividends, bonus shares, AGMs, financial results)
   - Banking sector developments
   - Hydropower project updates
   - IPO/FPO announcements
   - Major institutional activities

3. **ANALYZE** how these news events affected the market movement

## OUTPUT FORMAT - Provide analysis in this exact JSON structure:

{{
  "executive_summary": "2-3 sentence overview of market situation",
  
  "market_sentiment": {{
    "overall": "bullish/bearish/neutral/cautiously bullish",
    "score": "number from -10 to +10",
    "detailed": "detailed explanation of sentiment with reasons"
  }},
  
  "technical_analysis": {{
    "trend_analysis": "detailed analysis of the 30-day trend",
    "moving_averages": "what the MA positions indicate",
    "support_resistance": "key levels with explanation",
    "volume_analysis": "if volume data is available",
    "key_patterns": "any chart patterns observed"
  }},
  
  "key_market_drivers": [
    "driver 1 with specific data points and news references",
    "driver 2 with specific data points and news references",
    "driver 3 with specific data points and news references",
    "driver 4 with specific data points and news references",
    "driver 5 with specific data points and news references"
  ],
  
  "news_analysis": {{
    "top_news_found": [
      {{"headline": "actual news headline", "source": "website name", "date": "date", "impact": "positive/negative/neutral", "summary": "what this news means for market"}}
    ],
    "sector_news": {{
      "banking": "banking sector news and impact",
      "hydropower": "hydropower sector news and impact",
      "finance": "finance sector news and impact",
      "manufacturing": "manufacturing sector news and impact",
      "regulatory": "SEBON/NRB regulatory news"
    }},
    "overall_impact": "how news collectively affected the market"
  }},
  
  "technical_outlook": {{
    "short_term": "next 1-2 weeks outlook with specific levels",
    "medium_term": "next 1-2 months outlook",
    "key_levels": {{
      "support_1": "nearest support",
      "support_2": "second support",
      "resistance_1": "nearest resistance",
      "resistance_2": "second resistance"
    }}
  }},
  
  "investment_recommendation": {{
    "strategy": "specific strategy for current market",
    "actionable_steps": ["step 1", "step 2", "step 3", "step 4", "step 5"],
    "risk_management": "specific risk management advice",
    "sectors_to_watch": ["sector1", "sector2", "sector3"],
    "sectors_to_avoid": ["sector1", "sector2"]
  }},
  
  "risk_factors": [
    "risk 1 with explanation",
    "risk 2 with explanation",
    "risk 3 with explanation"
  ],
  
  "weekly_forecast": "Detailed prediction for next week with price targets"
}}

## CRITICAL REQUIREMENTS:
- You MUST use Google Search to find REAL news - do NOT make up news
- Provide SPECIFIC numbers and percentages from the data
- Cite your news sources with actual URLs
- If you cannot find news on a topic, say "No recent news found on this topic"
- Be detailed - each section should have substantial content
- Write for retail investors - explain technical terms

BEGIN ANALYSIS NOW:"""

        try:
            # Call Gemini with the prompt
            response = self.model.generate_content(prompt)
            response_text = response.text
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group())
            else:
                # Try to parse the whole response as JSON
                analysis = json.loads(response_text)
            
            # Add metadata
            analysis['analysis_date'] = datetime.now().strftime('%Y-%m-%d %H:%M')
            analysis['data_period'] = f"{dates[0] if dates else 'N/A'} to {dates[-1] if dates else 'N/A'}"
            
            # Cache for 6 hours
            cache.set(cache_key, analysis, 21600)
            return analysis
            
        except json.JSONDecodeError as e:
            print(f"JSON parse error: {e}")
            print(f"Raw response: {response_text[:500]}")
            return self._get_fallback_analysis(current, monthly_return, ma5, ma20, high, low)
        except Exception as e:
            print(f"Gemini API error: {e}")
            return self._get_fallback_analysis(current, monthly_return, ma5, ma20, high, low)
    
    def _get_fallback_analysis(self, current, monthly_return, ma5, ma20, high, low):
        """Fallback if AI fails"""
        return {
            "executive_summary": f"NEPSE currently at {current:.2f} with {monthly_return:.1f}% return over 30 days.",
            "market_sentiment": {
                "overall": "bullish" if monthly_return > 2 else "neutral" if monthly_return > -2 else "bearish",
                "score": min(10, max(-10, int(monthly_return * 2))) if monthly_return > 0 else max(-10, min(10, int(monthly_return * 2))),
                "detailed": f"Based on 30-day performance of {monthly_return:.1f}% and price position relative to moving averages."
            },
            "technical_analysis": {
                "trend_analysis": f"Market has {'gained' if monthly_return > 0 else 'lost'} {abs(monthly_return):.1f}% over 30 days.",
                "moving_averages": f"Price is {'above' if current > ma20 else 'below'} 20-day MA of {ma20:.2f}.",
                "support_resistance": f"Support at {low:.0f}, Resistance at {high:.0f}.",
                "key_patterns": "Analysis based on available data."
            },
            "key_market_drivers": [
                f"30-day return of {monthly_return:.1f}%",
                f"Price {'above' if current > ma20 else 'below'} key moving average",
                f"Trading range of {low:.0f} - {high:.0f}"
            ],
            "news_analysis": {
                "top_news_found": [],
                "sector_news": {},
                "overall_impact": "News analysis unavailable. Market movement based on technical factors."
            },
            "technical_outlook": {
                "short_term": f"Expected range between {low:.0f} and {high:.0f}.",
                "medium_term": "Direction depends on breakout from current range.",
                "key_levels": {
                    "support_1": low,
                    "support_2": low - 30,
                    "resistance_1": high,
                    "resistance_2": high + 30
                }
            },
            "investment_recommendation": {
                "strategy": "Wait for clearer direction",
                "actionable_steps": ["Monitor support and resistance levels", "Wait for breakout confirmation"],
                "risk_management": f"Use stop loss below {low - 20:.0f}",
                "sectors_to_watch": ["Banking", "Hydropower"],
                "sectors_to_avoid": []
            },
            "risk_factors": ["Market volatility", "Global cues", "Regulatory changes"],
            "weekly_forecast": f"Range-bound trading between {low:.0f}-{high:.0f} expected."
        }

# Create instance
ai_analyzer = AIMarketAnalyzer()