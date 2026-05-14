# core/ai_analyzer.py
import google.generativeai as genai
from django.conf import settings
from django.core.cache import cache
import json
import logging
from datetime import datetime
import re

# At the top of ai_analyzer.py, add:
import google.generativeai as genai

logger = logging.getLogger(__name__)

class NEPSEAIAnalyzer:
    """AI-powered NEPSE market analyzer using Google Gemini with Web Search"""
    
    def __init__(self):
        try:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            # Use v1beta API for grounding/Google Search support [citation:10]
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            self.is_available = True
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}")
            self.is_available = False
            self.model = None
    
    def prepare_market_data_for_ai(self, thirty_day_data, latest_data):
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
        
        # Calculate 30-day performance
        monthly_return = ((closes[-1] - closes[0]) / closes[0] * 100) if closes[0] != 0 else 0
        
        return {
            "period": f"{dates[0]} to {dates[-1]}" if dates else "Last 30 days",
            "days": len(closes),
            "latest_close": latest_data.get('close'),
            "latest_change_percent": latest_data.get('percent_change'),
            "thirty_day_return": round(monthly_return, 2),
            "highest_close": max(closes),
            "lowest_close": min(closes),
            "ma5": round(ma5, 2),
            "ma20": round(ma20, 2),
            "current_position_vs_ma5": "above" if latest_data.get('close', 0) > ma5 else "below",
        }
    
    def analyze_market(self, market_data):
        """Get AI-powered market analysis with Google Search grounding"""
        if not self.is_available or not self.model:
            return self.get_fallback_analysis()
        
        if not market_data:
            return self.get_fallback_analysis()
        
        # Check cache first
        cache_key = f"ai_analysis_{market_data['period'].replace(' ', '_')}"
        cached_analysis = cache.get(cache_key)
        if cached_analysis:
            logger.info("Returning cached AI analysis")
            return cached_analysis
        
        # PROMPT with instructions to SEARCH THE WEB
        prompt = f"""
You are a senior NEPSE (Nepal Stock Exchange) market analyst.

## USE GOOGLE SEARCH TO FIND REAL INFORMATION
For the following tasks, you MUST search the web using Google Search. Do not make up information.

## DATA FROM USER (Use this for technical analysis):
- Period: {market_data['period']} ({market_data['days']} trading days)
- Current NEPSE Level: {market_data['latest_close']}
- Today's Change: {market_data['latest_change_percent']}%
- 30-Day Return: {market_data['thirty_day_return']}%
- Highest in 30 days: {market_data['highest_close']}
- Lowest in 30 days: {market_data['lowest_close']}
- 5-Day Moving Average: {market_data['ma5']}
- 20-Day Moving Average: {market_data['ma20']}
- Price vs 5-Day MA: {market_data['current_position_vs_ma5']}

## TASKS (USE GOOGLE SEARCH FOR EACH):

1. **FIND REAL NEWS**: Search for actual NEPSE news from the last 30 days. Find:
   - SEBON announcements
   - NRB policy changes
   - Company-specific news (bonus, rights shares, AGM)
   - Hydropower project updates
   - Banking sector news
   
2. **ANALYZE MARKET MOVEMENT**: Based on the data AND the news you found, explain:
   - Why the market moved this way
   - Which sectors performed well/poorly
   - What specific events caused price changes

3. **IDENTIFY KEY DRIVERS**: List 5 specific reasons for the current market trend, citing your sources

4. **PROVIDE OUTLOOK**: Technical and fundamental outlook for next week

## CRITICAL REQUIREMENTS:
- You MUST cite your sources (website names and URLs)
- If you cannot find information through search, say "No recent news found on this topic"
- DO NOT make up fake news or events
- Provide specific dates for news events when possible

Respond in JSON format:
{{
  "market_sentiment": "bullish/bearish/neutral",
  "sentiment_score": -10 to +10,
  "detailed_analysis": "2-3 paragraph analysis based on data AND real news",
  "real_news_found": [
    {{"headline": "Actual news headline", "date": "date", "source": "website name", "url": "source URL", "impact": "positive/negative/neutral"}}
  ],
  "key_drivers": ["driver 1 with source", "driver 2 with source", ...],
  "sector_analysis": {{
    "banking": "performance and news",
    "hydropower": "performance and news",
    "finance": "performance and news"
  }},
  "technical_outlook": "technical analysis",
  "next_week_prediction": "prediction with levels",
  "investment_insight": "actionable insight"
}}
"""
        
        try:
            # Use the generate_content method - Gemini will automatically use Google Search
            # when the prompt asks for current information
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.7,
                    "top_p": 0.95,
                    "top_k": 40,
                }
            )
            
            analysis_text = response.text
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', analysis_text, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group())
            else:
                analysis = self._parse_text_response(analysis_text, market_data)
            
            # Cache the analysis
            cache.set(cache_key, analysis, 21600)  # 6 hours
            
            return analysis
            
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            return self.get_fallback_analysis()
    
    def _parse_text_response(self, text, market_data):
        """Parse text response if JSON extraction fails"""
        return {
            "market_sentiment": "neutral",
            "sentiment_score": 0,
            "detailed_analysis": text[:500] if len(text) > 500 else text,
            "real_news_found": [],
            "key_drivers": ["Analysis completed - check detailed analysis above"],
            "sector_analysis": {
                "banking": "See detailed analysis",
                "hydropower": "See detailed analysis",
                "finance": "See detailed analysis"
            },
            "technical_outlook": f"Support at {market_data.get('lowest_close', 'N/A')}, Resistance at {market_data.get('highest_close', 'N/A')}",
            "next_week_prediction": "Based on 30-day data, expect range-bound trading",
            "investment_insight": "Wait for clearer direction"
        }
    
    def get_fallback_analysis(self):
        """Fallback analysis when AI fails"""
        return {
            "market_sentiment": "neutral",
            "sentiment_score": 0,
            "detailed_analysis": "Unable to fetch real-time market analysis. Please check your internet connection and API key configuration.",
            "real_news_found": [],
            "key_drivers": ["Connectivity issue - analysis unavailable"],
            "sector_analysis": {
                "banking": "Data unavailable",
                "hydropower": "Data unavailable",
                "finance": "Data unavailable"
            },
            "technical_outlook": "Analysis unavailable due to connection issues",
            "next_week_prediction": "Please refresh and try again",
            "investment_insight": "Check back soon for AI-powered insights"
        }

# Initialize the analyzer
ai_analyzer = NEPSEAIAnalyzer()