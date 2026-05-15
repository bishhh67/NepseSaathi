import sqlite3
import pandas as pd
import os
from forecaster import generate_forecast_graphs
from tqdm import tqdm

DB_NAME = 'stock_market.db'
STATIC_GRAPHS = os.path.join('static', 'graphs')

if not os.path.exists(STATIC_GRAPHS):
    os.makedirs(STATIC_GRAPHS)

def pregenerate():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    companies = conn.execute('SELECT symbol FROM companies').fetchall()
    
    print(f"Starting pre-generation for {len(companies)} companies...")
    
    for row in tqdm(companies):
        symbol = row['symbol']
        
        # Check if already exists
        g1, g2, g3 = f'{symbol}_forecast.png', f'{symbol}_weekly.png', f'{symbol}_yearly.png'
        if all(os.path.exists(os.path.join(STATIC_GRAPHS, g)) for g in [g1, g2, g3]):
            continue
            
        # Get history
        history_df = pd.read_sql_query('SELECT * FROM stock_history WHERE symbol = ? ORDER BY date ASC', conn, params=(symbol,))
        
        if not history_df.empty and len(history_df) > 10:
            try:
                generate_forecast_graphs(history_df, symbol, STATIC_GRAPHS)
            except Exception as e:
                print(f"Error generating for {symbol}: {e}")
                
    conn.close()
    print("Pre-generation complete!")

if __name__ == '__main__':
    pregenerate()
