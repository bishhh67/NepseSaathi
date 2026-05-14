# core/gemini_analyzer.py
import requests
import json
from django.conf import settings
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)

class GeminiAnalyzer:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        # Use gemini-2.5-flash which is available
        self.url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={self.api_key}"
    
    def analyze_market(self, market_data):
        """Get market analysis using Gemini"""
        
        # Check cache (6 hours)
        cache_key = "nepse_gemini_analysis"
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        # Prepare prompt with your data
        prompt = f"""You are a NEPSE (Nepal Stock Exchange) market expert. Analyze this market data:

**30-Day Market Data:**
- Current NEPSE: {market_data.get('close', 'N/A')}
- Today's change: {market_data.get('percent_change', 0)}%
- 30-day high: {market_data.get('high', 'N/A')}
- 30-day low: {market_data.get('low', 'N/A')}
- Trend direction: {market_data.get('trend', 'N/A')}

**Your tasks:**
1. Analyze what this market movement means
2. List 3-5 possible reasons for this movement (based on typical NEPSE patterns)
3. What should investors watch for next?

**Respond in this JSON format ONLY (no other text):**
{{
  "summary": "2-3 sentence market summary",
  "market_sentiment": "bullish or bearish or neutral",
  "reasons": ["reason 1", "reason 2", "reason 3", "reason 4"],
  "technical_view": "technical analysis based on price action",
  "investor_advice": "what investors should do now",
  "next_week_outlook": "prediction for next week"
}}

Make your analysis specific, data-driven, and useful for Nepali investors."""
        
        # Make API call
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.7,
                "topP": 0.95,
                "topK": 40,
                "maxOutputTokens": 1024
            }
        }
        
        try:
            response = requests.post(self.url, json=payload)
            result = response.json()
            
            # Extract the text response
            if 'candidates' in result and len(result['candidates']) > 0:
                text_response = result['candidates'][0]['content']['parts'][0]['text']
                
                # Parse JSON from response
                import re
                json_match = re.search(r'\{.*\}', text_response, re.DOTALL)
                if json_match:
                    analysis = json.loads(json_match.group())
                else:
                    analysis = self._fallback_analysis(market_data)
            else:
                analysis = self._fallback_analysis(market_data)
            
            # Cache for 6 hours
            cache.set(cache_key, analysis, 21600)
            return analysis
            
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return self._fallback_analysis(market_data)
    
    def _fallback_analysis(self, market_data):
        """Fallback if API fails"""
        return {
            "summary": f"Market closed at {market_data.get('close', 'N/A')} with {market_data.get('percent_change', 0)}% change.",
            "market_sentiment": "neutral",
            "reasons": [
                "Based on technical indicators",
                "Volume analysis suggests consolidation",
                "Support and resistance levels at play"
            ],
            "technical_view": f"Support at {market_data.get('low', 'N/A')}, Resistance at {market_data.get('high', 'N/A')}",
            "investor_advice": "Wait for clearer direction before making large positions",
            "next_week_outlook": "Range-bound trading expected"
        }

# Create instance
gemini = GeminiAnalyzer()