# core/news_fetcher.py
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta
import re

class NewsFetcher:
    """Fetch real NEPSE news from multiple sources"""
    
    def __init__(self):
        self.news_data = []
    
    def fetch_from_sharesansar(self):
        """Fetch news from Sharesansar"""
        news_items = []
        try:
            # Sharesansar latest news page
            url = "https://www.sharesansar.com/latest"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find news articles
            articles = soup.find_all('div', class_='news-block')[:15]
            
            for article in articles:
                title_elem = article.find('h3')
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    link = title_elem.find('a')['href'] if title_elem.find('a') else ''
                    date_elem = article.find('span', class_='date')
                    date = date_elem.get_text(strip=True) if date_elem else datetime.now().strftime('%Y-%m-%d')
                    
                    news_items.append({
                        'title': title,
                        'link': f"https://www.sharesansar.com{link}" if link else '',
                        'date': date,
                        'source': 'Sharesansar',
                        'summary': title[:200]
                    })
        except Exception as e:
            print(f"Sharesansar error: {e}")
        
        return news_items
    
    def fetch_from_nepalipaisa(self):
        """Fetch news from Nepalipaisa"""
        news_items = []
        try:
            url = "https://www.nepalipaisa.com/News"
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            articles = soup.find_all('div', class_='news-item')[:15]
            
            for article in articles:
                title_elem = article.find('a')
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    link = title_elem['href'] if title_elem.get('href') else ''
                    date_elem = article.find('span', class_='news-date')
                    date = date_elem.get_text(strip=True) if date_elem else datetime.now().strftime('%Y-%m-%d')
                    
                    news_items.append({
                        'title': title,
                        'link': f"https://www.nepalipaisa.com{link}" if link else '',
                        'date': date,
                        'source': 'Nepalipaisa',
                        'summary': title[:200]
                    })
        except Exception as e:
            print(f"Nepalipaisa error: {e}")
        
        return news_items
    
    def fetch_from_nepse_alpha(self):
        """Fetch from NEPSE Alpha"""
        news_items = []
        try:
            url = "https://nepsealpha.com/category/news/"
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            articles = soup.find_all('article')[:15]
            
            for article in articles:
                title_elem = article.find('h2')
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    link = title_elem.find('a')['href'] if title_elem.find('a') else ''
                    date_elem = article.find('time')
                    date = date_elem.get_text(strip=True) if date_elem else datetime.now().strftime('%Y-%m-%d')
                    
                    news_items.append({
                        'title': title,
                        'link': link,
                        'date': date,
                        'source': 'NEPSE Alpha',
                        'summary': title[:200]
                    })
        except Exception as e:
            print(f"NEPSE Alpha error: {e}")
        
        return news_items
    
    def fetch_all_news(self):
        """Fetch news from all sources"""
        all_news = []
        
        print("Fetching from Sharesansar...")
        all_news.extend(self.fetch_from_sharesansar())
        
        print("Fetching from Nepalipaisa...")
        all_news.extend(self.fetch_from_nepalipaisa())
        
        print("Fetching from NEPSE Alpha...")
        all_news.extend(self.fetch_from_nepse_alpha())
        
        # Remove duplicates by title
        seen = set()
        unique_news = []
        for news in all_news:
            if news['title'] not in seen:
                seen.add(news['title'])
                unique_news.append(news)
        
        return unique_news[:25]  # Return top 25 news

# Create instance
news_fetcher = NewsFetcher()