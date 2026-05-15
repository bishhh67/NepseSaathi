# forecast/views.py - Complete Django version
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import pandas as pd
import sqlite3
import os
from pathlib import Path

# Import your existing analyzers (keep these as they are)
from .analyzer import get_analysis
from .forecaster import generate_forecast_graphs

# Configuration
DB_PATH = Path(__file__).parent / 'stock_market.db'
STATIC_GRAPHS = os.path.join(settings.BASE_DIR, 'static', 'forecast_graphs')

# Ensure directories exist
os.makedirs(STATIC_GRAPHS, exist_ok=True)

def get_db_connection():
    """Get SQLite connection to your existing database"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def index(request):
    """Main forecast dashboard - equivalent to Flask @app.route('/')"""
    query = request.GET.get('query', '')
    conn = get_db_connection()
    
    if query:
        companies = conn.execute(
            'SELECT * FROM companies WHERE name LIKE ? OR symbol LIKE ?', 
            ('%' + query + '%', '%' + query + '%')
        ).fetchall()
    else:
        companies = conn.execute('SELECT * FROM companies').fetchall()
    
    conn.close()
    return render(request, 'forecast/index.html', {
        'companies': companies, 
        'query': query
    })

def stock_detail(request, symbol):
    conn = get_db_connection()
    company = conn.execute('SELECT * FROM companies WHERE symbol = ?', (symbol,)).fetchone()
    
    if not company:
        conn.close()
        # Return page with no data message instead of 404
        return render(request, 'forecast/details.html', {
            'company': {
                'symbol': symbol,
                'name': 'Company Not Found',
                'sector': 'N/A',
                'website': '#',
            },
            'analysis': {
                'rsi': 'N/A',
                'sma20': 'N/A',
                'sma50': 'N/A',
                'high_52': 'N/A',
                'low_52': 'N/A',
                'volatility': 'N/A',
                'signals': [],
                'conclusion': f'No data available for {symbol}. This stock symbol does not exist in our database.',
                'data_span_years': 0,
            },
            'graphs': None,
            'symbol': symbol,
            'last_price': 'N/A',
            'no_data': True,  # Flag to show no data message
        })
    
    # Get history for analysis
    history_df = pd.read_sql_query(
        'SELECT * FROM stock_history WHERE symbol = ? ORDER BY date ASC', 
        conn, params=(symbol,)
    )
    conn.close()
    
    if history_df.empty:
        return render(request, 'forecast/details.html', {
            'company': company,
            'analysis': {
                'rsi': 'N/A',
                'sma20': 'N/A',
                'sma50': 'N/A',
                'high_52': 'N/A',
                'low_52': 'N/A',
                'volatility': 'N/A',
                'signals': [],
                'conclusion': f'No historical price data available for {symbol}. The stock may be newly listed or data not yet imported.',
                'data_span_years': 0,
            },
            'graphs': None,
            'symbol': symbol,
            'last_price': 'N/A',
            'no_data': True,
        })
    
    # Generate Analysis using your existing analyzer
    analysis = get_analysis(history_df)
    
    # Check if graphs already exist
    g1, g2, g3 = f'{symbol}_forecast.png', f'{symbol}_weekly.png', f'{symbol}_yearly.png'
    graph_paths = [os.path.join(STATIC_GRAPHS, g) for g in [g1, g2, g3]]
    graphs_exist = all(os.path.exists(p) for p in graph_paths)
    
    # Cache validation
    if graphs_exist:
        try:
            latest_db_date = pd.to_datetime(history_df['date'].max())
            cache_mtime = os.path.getmtime(graph_paths[0])
            cache_dt = pd.to_datetime(cache_mtime, unit='s')
            if latest_db_date > cache_dt:
                graphs_exist = False
        except Exception as e:
            print(f"Cache validation error for {symbol}: {e}")
            graphs_exist = False
    
    return render(request, 'forecast/details.html', {
        'company': company,
        'analysis': analysis,
        'graphs': [g1, g2, g3] if graphs_exist else None,
        'symbol': symbol,
        'last_price': history_df['close'].iloc[-1],
        'no_data': False,
    })






@csrf_exempt
def generate_graphs_api(request, symbol):
    """API endpoint to generate graphs - equivalent to Flask @app.route('/generate_graphs/<symbol>')"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    conn = get_db_connection()
    history_df = pd.read_sql_query(
        'SELECT * FROM stock_history WHERE symbol = ? ORDER BY date ASC', 
        conn, params=(symbol,)
    )
    conn.close()
    
    if history_df.empty:
        return JsonResponse({'error': 'No data available'}, status=404)
    
    # Check cache validation
    g1, g2, g3 = f'{symbol}_forecast.png', f'{symbol}_weekly.png', f'{symbol}_yearly.png'
    graph_paths = [os.path.join(STATIC_GRAPHS, g) for g in [g1, g2, g3]]
    already_valid = all(os.path.exists(p) for p in graph_paths)
    
    if already_valid:
        try:
            latest_db_dt = pd.to_datetime(history_df['date'].max())
            cache_dt = pd.to_datetime(os.path.getmtime(graph_paths[0]), unit='s')
            if latest_db_dt > cache_dt:
                already_valid = False
        except Exception:
            already_valid = False
    
    if already_valid:
        return JsonResponse({'success': True, 'graphs': [g1, g2, g3], 'cached': True})
    
    # Generate Graphs using your existing forecaster
    try:
        generate_forecast_graphs(history_df, symbol, STATIC_GRAPHS)
        return JsonResponse({
            'success': True,
            'graphs': [g1, g2, g3],
            'cached': False
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)