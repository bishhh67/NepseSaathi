"""
ULTRA-FAST Full History Scraper - WITH REAL-TIME PROGRESS
"""
import pandas as pd
import time
import random
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import traceback
import shutil
import sys

class OptimizedFullHistoryScraper:
    def __init__(self, company_csv='companies.csv', data_folder='data', max_workers=7):
        self.data_folder = data_folder
        self.max_workers = max_workers
        self.create_data_folder()
        
        # Load companies
        self.companies_df = pd.read_csv(company_csv)
        self.companies = self.companies_df['data'].astype(str).tolist()
        self.company_names = dict(zip(self.companies_df['data'].astype(str), self.companies_df['data2']))
        
        print(f"📊 Loaded {len(self.companies)} companies")
        print(f"💾 Data folder: {os.path.abspath(self.data_folder)}/")
        print(f"⚡ Using {self.max_workers} parallel workers")
        
        # Chrome options for maximum speed
        self.chrome_options = webdriver.ChromeOptions()
        self.chrome_options.add_argument('--headless=new')
        self.chrome_options.add_argument('--disable-gpu')
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--disable-dev-shm-usage')
        self.chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        self.chrome_options.add_argument('--disable-extensions')
        self.chrome_options.add_argument('--disable-logging')
        self.chrome_options.add_argument('--log-level=3')
        self.chrome_options.add_argument('--silent')
        self.chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
        
        # Progress tracking
        self.progress_file = 'full_scrape_progress.json'
        self.completed_companies = self.load_progress()
        
    def create_data_folder(self):
        if not os.path.exists(self.data_folder):
            os.makedirs(self.data_folder)
            print(f"📁 Created folder: {self.data_folder}/")
    
    def load_progress(self):
        if os.path.exists(self.progress_file):
            with open(self.progress_file, 'r') as f:
                return set(json.load(f))
        return set()
    
    def save_progress(self):
        with open(self.progress_file, 'w') as f:
            json.dump(list(self.completed_companies), f)
    
    def get_driver(self):
        """Fast driver creation"""
        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=self.chrome_options)
            driver.set_page_load_timeout(30)
            return driver
        except Exception as e:
            if "version" in str(e).lower():
                shutil.rmtree(os.path.expanduser("~/.wdm"), ignore_errors=True)
                service = Service(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=self.chrome_options)
                return driver
            raise e
    
    def scrape_single_company(self, symbol):
        """Scrape single company with real-time output"""
        driver = None
        all_data = []
        
        try:
            driver = self.get_driver()
            url = f"https://sharehubnepal.com/company/{symbol}/price-history"
            driver.get(url)
            time.sleep(2)
            
            # Quick popup handling
            try:
                driver.execute_script("document.querySelector('[role=\"dialog\"]')?.remove()")
            except:
                pass
            
            # Get table
            table = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "table"))
            )
            rows = table.find_elements(By.TAG_NAME, "tr")
            headers = [th.text.strip() for th in rows[0].find_elements(By.TAG_NAME, "th")]
            
            page_num = 1
            while True:
                rows = driver.find_element(By.TAG_NAME, "table").find_elements(By.TAG_NAME, "tr")
                
                page_data = []
                for row in rows[1:]:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if cells and len(cells) >= 10 and cells[0].text.strip():
                        page_data.append([cell.text.strip() for cell in cells])
                
                all_data.extend(page_data)
                
                # Check for next page
                try:
                    next_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Next')]")
                    if next_btn.get_attribute('disabled'):
                        break
                    driver.execute_script("arguments[0].click();", next_btn)
                    page_num += 1
                    time.sleep(1)
                except:
                    break
            
            if all_data:
                df = pd.DataFrame(all_data, columns=headers[:len(all_data[0])])
                df = self.clean_dataframe(df)
                
                filename = os.path.join(self.data_folder, f"{symbol}_full_history.csv")
                df.to_csv(filename, index=False)
                
                # Real-time output
                print(f"✅ {symbol} ({self.company_names.get(symbol, 'Unknown')[:20]}): {len(df)} records")
                return df
            else:
                print(f"⚠️ {symbol}: No data found")
                return None
                
        except Exception as e:
            print(f"❌ {symbol}: Error - {str(e)[:60]}")
            return None
        finally:
            if driver:
                driver.quit()
    
    def clean_dataframe(self, df):
        """Clean dataframe (fixed regex warning)"""
        df.columns = [col.upper().strip() for col in df.columns]
        
        numeric_cols = ['CHANGE', 'CHANGE %', 'CLOSE', 'TURNOVER', 'VOLUME', 'TRADE', 'OPEN', 'HIGH', 'LOW']
        for col in numeric_cols:
            if col in df.columns:
                # Fixed: proper regex escaping
                df[col] = df[col].astype(str).str.replace(r'Rs\.|,|%|L', '', regex=True).str.strip()
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        if 'DATE' in df.columns:
            df['DATE'] = pd.to_datetime(df['DATE'])
            df = df.sort_values('DATE', ascending=False)
        
        return df
    
    def scrape_all_companies(self, max_companies=None):
        """Parallel scraping with live progress bar"""
        companies_to_scrape = self.companies[:max_companies] if max_companies else self.companies
        pending = [c for c in companies_to_scrape if c not in self.completed_companies]
        
        if not pending:
            print("✅ All companies already scraped!")
            return [], []
        
        print(f"\n🚀 Starting parallel scrape with {self.max_workers} workers")
        print(f"📊 Companies to process: {len(pending)}")
        print(f"⏱️  Estimated time: {len(pending) * 12 / 60 / self.max_workers:.1f} minutes")
        print("📈 Live progress will appear below as companies complete:\n")
        print("-" * 70)
        
        start_time = time.time()
        successful = []
        failed = []
        completed_count = 0
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_company = {
                executor.submit(self.scrape_single_company, symbol): symbol 
                for symbol in pending
            }
            
            for future in as_completed(future_to_company):
                symbol = future_to_company[future]
                completed_count += 1
                
                try:
                    result = future.result(timeout=300)
                    if result is not None:
                        successful.append(symbol)
                        self.completed_companies.add(symbol)
                    else:
                        failed.append(symbol)
                except Exception as e:
                    print(f"❌ {symbol}: Timeout/Error - {str(e)[:50]}")
                    failed.append(symbol)
                
                self.save_progress()
                
                # Progress update every 5 companies
                if completed_count % 5 == 0 or completed_count == len(pending):
                    elapsed = time.time() - start_time
                    rate = completed_count / elapsed if elapsed > 0 else 0
                    remaining = len(pending) - completed_count
                    eta = remaining / rate if rate > 0 else 0
                    
                    print(f"\n📊 Progress: {completed_count}/{len(pending)} ({completed_count/len(pending)*100:.1f}%)")
                    print(f"   ✅ Success: {len(successful)} | ❌ Failed: {len(failed)}")
                    print(f"   ⚡ Speed: {rate*60:.1f} companies/minute | ETA: {eta/60:.1f} min")
                    print("-" * 70)
        
        elapsed = time.time() - start_time
        print("\n" + "="*70)
        print(f"✅ SCRAPING COMPLETE!")
        print(f"   ✅ Successful: {len(successful)} companies")
        print(f"   ❌ Failed: {len(failed)} companies")
        print(f"   ⏱️  Time: {elapsed/60:.1f} minutes")
        print(f"   ⚡ Speed: {len(successful)/(elapsed/60):.1f} companies/minute")
        print(f"   💾 Data saved in: {os.path.abspath(self.data_folder)}/")
        print("="*70)
        
        return successful, failed

if __name__ == "__main__":
    scraper = OptimizedFullHistoryScraper(max_workers=7)
    successful, failed = scraper.scrape_all_companies()