import asyncio
import httpx
import json
import os
import re
import sys

# --- CONFIGURATION ---
DATA_FILE = "market_data.js"
# ---------------------

def clean_val(val):
    if val is None: return ""
    # Strip HTML tags
    text = re.sub('<[^<]+?>', '', str(val)).strip()
    # Decode basic entities
    text = text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    # Remove commas from numbers
    return text.replace(',', '')

async def fetch_endpoint(client, key, name, url, columns):
    """Fetches the latest data for a specific category."""
    print(f"Fetching {name}...")
    
    params = {
        "draw": "1",
        "start": "0",
        "length": "50",
        "search[value]": "",
        "search[regex]": "false"
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": url
    }
    
    try:
        response = await client.get(url, params=params, headers=headers, timeout=15.0)
        if response.status_code != 200:
            print(f"FAILED {name}: {response.status_code}")
            return None
            
        raw_data = response.json().get("data", [])
        formatted_data = []
        
        for item in raw_data:
            row = {}
            for col in columns:
                row[col] = clean_val(item.get(col, ""))
            formatted_data.append(row)
            
        # Numerical sorting for Broker Total Amount (High to Low)
        if key == 'brokers':
            try:
                formatted_data.sort(key=lambda x: float(x.get('totalAmount', 0)) if x.get('totalAmount') else 0, reverse=True)
            except Exception as sort_err:
                print(f"Sort Error for {name}: {sort_err}")
        
        # Add S.N. AFTER sorting
        for i, row in enumerate(formatted_data):
            row["S.N."] = i + 1
            
        return {"key": key, "name": name, "data": formatted_data}
    except Exception as e:
        print(f"ERROR {name}: {e}")
        return None

async def main():
    endpoints = [
        {"key": "gainers", "name": "Top Gainers", "url": "https://www.sharesansar.com/top-gainers", "cols": ["symbol", "close", "change_pts", "diff_per"]},
        {"key": "losers", "name": "Top Losers", "url": "https://www.sharesansar.com/top-losers", "cols": ["symbol", "close", "change_pts", "diff_per"]},
        {"key": "turnovers", "name": "Top Turnovers", "url": "https://www.sharesansar.com/top-turnovers", "cols": ["symbol", "close", "traded_amount"]},
        {"key": "traded", "name": "Top Traded Shares", "url": "https://www.sharesansar.com/top-tradedshares", "cols": ["symbol", "close", "traded_quantity"]},
        {"key": "transactions", "name": "Top Transactions", "url": "https://www.sharesansar.com/top-transactions", "cols": ["symbol", "close", "no_trade"]},
        {"key": "brokers", "name": "Top Brokers", "url": "https://www.sharesansar.com/top-brokers", "cols": ["number", "name", "buyerAmount", "sellerAmount", "totalAmount"]}
    ]
    
    async with httpx.AsyncClient() as client:
        tasks = [fetch_endpoint(client, e["key"], e["name"], e["url"], e["cols"]) for e in endpoints]
        results = await asyncio.gather(*tasks)
    
    # Filter out None results
    final_data = {r["key"]: {"name": r["name"], "data": r["data"]} for r in results if r}
    
    if final_data:
        with open(DATA_FILE, "w", encoding='utf-8') as f:
            f.write(f"window.LATEST_MARKET_DATA = {json.dumps(final_data, indent=2)};")
        print(f"Successfully updated {DATA_FILE} with latest data.")

if __name__ == "__main__":
    asyncio.run(main())
