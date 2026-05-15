import os
import pandas as pd
import sqlite3
import glob

DB_NAME = 'stock_market.db'

def migrate_data():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Create tables
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS companies (
        symbol TEXT PRIMARY KEY,
        name TEXT,
        sector TEXT,
        email TEXT,
        website TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS stock_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT,
        date TEXT,
        change REAL,
        change_pct REAL,
        close REAL,
        turnover REAL,
        volume INTEGER,
        trade INTEGER,
        open REAL,
        high REAL,
        low REAL,
        FOREIGN KEY (symbol) REFERENCES companies (symbol)
    )
    ''')

    # Load companies
    print("Loading companies.csv...")
    try:
        companies_df = pd.read_csv('companies.csv')
        # data2: name, data: symbol, data3: sector, email, website
        for _, row in companies_df.iterrows():
            cursor.execute('''
            INSERT OR REPLACE INTO companies (symbol, name, sector, email, website)
            VALUES (?, ?, ?, ?, ?)
            ''', (row['data'], row['data2'], row['data3'], row['email'], row['website']))
        conn.commit()
        print(f"Successfully loaded {len(companies_df)} companies.")
    except Exception as e:
        print(f"Error loading companies: {e}")

    # Load history files
    print("Loading history files from data/ directory...")
    history_files = glob.glob('data/*_full_history.csv')
    
    total_records = 0
    for file_path in history_files:
        symbol = os.path.basename(file_path).split('_')[0]
        print(f"Processing {symbol}...")
        
        try:
            df = pd.read_csv(file_path)
            # DATE,CHANGE,CHANGE %,CLOSE,TURNOVER,VOLUME,TRADE,OPEN,HIGH,LOW
            for _, row in df.iterrows():
                cursor.execute('''
                INSERT INTO stock_history (symbol, date, change, change_pct, close, turnover, volume, trade, open, high, low)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    symbol, 
                    row['DATE'], 
                    row.get('CHANGE'), 
                    row.get('CHANGE %'), 
                    row.get('CLOSE'), 
                    row.get('TURNOVER'), 
                    row.get('VOLUME'), 
                    row.get('TRADE'), 
                    row.get('OPEN'), 
                    row.get('HIGH'), 
                    row.get('LOW')
                ))
            total_records += len(df)
        except Exception as e:
            print(f"Error processing {symbol}: {e}")
            
    conn.commit()
    print(f"Successfully loaded {total_records} history records.")
    conn.close()

if __name__ == '__main__':
    migrate_data()
