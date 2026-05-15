import pandas as pd
import numpy as np

def calculate_rsi(data, window=14):
    """Calculates the Relative Strength Index (RSI)."""
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def get_analysis(df):
    """
    Calculates technical indicators and returns a dictionary with values and a conclusion.
    """
    if df.empty:
        return {
            'rsi': 'N/A', 'sma20': 'N/A', 'sma50': 'N/A', 'high_52': 'N/A', 'low_52': 'N/A',
            'volatility': 'N/A', 'data_span_years': 0, 'signals': [], 'conclusion': 'No data available.'
        }

    # Ensure data is sorted and date is datetime
    df = df.sort_values('date')
    df['date'] = pd.to_datetime(df['date'])
    
    # Calculate data span immediately
    date_min = df['date'].min()
    date_max = df['date'].max()
    data_span_years = round((date_max - date_min).days / 365.25, 2)
    
    if len(df) < 50:
        return {
            'rsi': 'N/A', 'sma20': 'N/A', 'sma50': 'N/A', 
            'high_52': df['high'].max() if 'high' in df.columns else 'N/A', 
            'low_52': df['low'].min() if 'low' in df.columns else 'N/A',
            'volatility': 'N/A', 'data_span_years': data_span_years, 'signals': [], 
            'conclusion': 'Insufficient data for reliable technical analysis (min 50 days required).'
        }

    current_price = df['close'].iloc[-1]
    
    # Calculate Indicators
    df['rsi'] = calculate_rsi(df['close'])
    df['sma20'] = df['close'].rolling(window=20).mean()
    df['sma50'] = df['close'].rolling(window=50).mean()
    
    rsi = df['rsi'].iloc[-1]
    sma20 = df['sma20'].iloc[-1]
    sma50 = df['sma50'].iloc[-1]
    
    # Conclusion Logic
    conclusion = ""
    signals = []
    
    if not np.isnan(rsi):
        if rsi > 70:
            signals.append("RSI indicates the stock is Overbought (>70).")
            bias = -1
        elif rsi < 30:
            signals.append("RSI indicates the stock is Oversold (<30).")
            bias = 1
        else:
            signals.append(f"RSI is neutral at {rsi:.2f}.")
            bias = 0
    else:
        bias = 0
        
    if not (np.isnan(sma20) or np.isnan(sma50)):
        if current_price > sma20 and sma20 > sma50:
            signals.append("Price is in an uptrend (Price > SMA20 > SMA50).")
            bias += 1
        elif current_price < sma20 and sma20 < sma50:
            signals.append("Price is in a downtrend (Price < SMA20 < SMA50).")
            bias -= 1
        else:
            signals.append("Trend is mixed or consolidating.")
        
    if bias >= 1:
        conclusion = "The overall sentiment is BULLISH. Consider buying or holding if you have a long-term perspective."
    elif bias <= -1:
        conclusion = "The overall sentiment is BEARISH. Caution is advised; the stock might be due for a correction."
    else:
        conclusion = "The market is currently NEUTRAL. It might be best to wait for a clearer trend to emerge."
        
    # Additional Stats
    high_52 = df['high'].max()
    low_52 = df['low'].min()
    volatility = df['close'].pct_change().std() * np.sqrt(252) * 100 # Annualized volatility
    
    return {
        'rsi': round(rsi, 2) if not np.isnan(rsi) else 'N/A',
        'sma20': round(sma20, 2) if not np.isnan(sma20) else 'N/A',
        'sma50': round(sma50, 2) if not np.isnan(sma50) else 'N/A',
        'high_52': round(high_52, 2) if not np.isnan(high_52) else 'N/A',
        'low_52': round(low_52, 2) if not np.isnan(low_52) else 'N/A',
        'volatility': round(volatility, 2) if not np.isnan(volatility) else 'N/A',
        'data_span_years': data_span_years,
        'signals': signals,
        'conclusion': conclusion
    }

