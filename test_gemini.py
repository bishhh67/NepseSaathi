# test_gemini.py
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nepse_sathi.settings')
import django
django.setup()

from django.conf import settings
import google.generativeai as genai

print(f"API Key exists: {bool(settings.GEMINI_API_KEY)}")
print(f"API Key: {settings.GEMINI_API_KEY[:10]}...")

try:
    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.0-flash')
    response = model.generate_content("Say 'Hello, NEPSE Sathi is working!'")
    print(f"Gemini Response: {response.text}")
    print("✅ Gemini API is WORKING!")
except Exception as e:
    print(f"❌ Gemini API Error: {e}")