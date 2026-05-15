import pandas as pd
import numpy as np
from prophet import Prophet
import matplotlib
matplotlib.use('Agg') # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
from scipy.signal import savgol_filter
import os
import warnings

warnings.filterwarnings('ignore')

def generate_forecast_graphs(df, symbol, static_dir):
    """
    Generates 3 forecast graphs for a given stock symbol.
    Saves them to static_dir and returns the relative paths.
    """
    if df.empty:
        return None, None, None

    # Prepare data
    df_all = df[['date', 'close']].copy()
    df_all.columns = ['ds', 'y']
    df_all['ds'] = pd.to_datetime(df_all['ds'])
    df_all = df_all.dropna()
    df_all = df_all.sort_values('ds').reset_index(drop=True)

    if len(df_all) < 10:
        return None, None, None

    last_date = df_all['ds'].max()
    current_price = df_all['y'].iloc[-1]

    # Train model (using last 3 years or all if less)
    three_years_ago = last_date - timedelta(days=3*365)
    df_train = df_all[df_all['ds'] >= three_years_ago].copy()
    
    # Prophet needs freq for better results, but daily is fine
    model = Prophet(
        changepoint_prior_scale=0.05,
        weekly_seasonality=True,
        yearly_seasonality=True,
        interval_width=0.80
    )
    model.fit(df_train)

    # Forecast
    future = model.make_future_dataframe(periods=365)
    forecast = model.predict(future)
    future_pred = forecast[forecast['ds'] > last_date].copy()

    # Adjustment to start at current price
    if not future_pred.empty:
        adjustment = current_price - future_pred['yhat'].iloc[0]
        for col in ['yhat', 'yhat_lower', 'yhat_upper']:
            future_pred[col] = future_pred[col] + adjustment

    # 1. Main Forecast Graph
    fig1, ax1 = plt.subplots(figsize=(12, 6))
    ax1.plot(df_train['ds'], df_train['y'], color='#2c3e50', label='Historical', alpha=0.6)
    if not future_pred.empty:
        ax1.plot(future_pred['ds'], future_pred['yhat'], color='#3498db', linewidth=2, label='Forecast')
        ax1.fill_between(future_pred['ds'], future_pred['yhat_lower'], future_pred['yhat_upper'], color='#3498db', alpha=0.1)
    
    ax1.set_title(f'{symbol} - 1 Year Price Forecast', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Price (NPR)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    main_graph_path = os.path.join(static_dir, f'{symbol}_forecast.png')
    plt.tight_layout()
    plt.savefig(main_graph_path)
    plt.close()

    # 2. Weekly Effect Graph
    fig2, ax2 = plt.subplots(figsize=(10, 5))
    weekly_data = forecast[['ds', 'weekly']].dropna().copy()
    weekly_data['DayName'] = weekly_data['ds'].dt.day_name()
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    weekly_effect = weekly_data.groupby('DayName')['weekly'].mean().reindex(day_order)
    
    ax2.bar(day_order, weekly_effect.values, color='#e67e22', alpha=0.7)
    ax2.set_title('Weekly Seasonality Effect', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Effect (NPR)')
    plt.xticks(rotation=45)
    
    weekly_graph_path = os.path.join(static_dir, f'{symbol}_weekly.png')
    plt.tight_layout()
    plt.savefig(weekly_graph_path)
    plt.close()

    # 3. Yearly Pattern Graph
    fig3, ax3 = plt.subplots(figsize=(10, 5))
    if 'yearly' in forecast.columns:
        dates_range = pd.date_range('2024-01-01', '2024-12-31', freq='D')
        yearly_values = []
        for date in dates_range:
            temp_df = pd.DataFrame({'ds': [date]})
            yearly_val = model.predict_seasonal_components(temp_df)['yearly'].iloc[0]
            yearly_values.append(yearly_val)
        
        ax3.plot(dates_range, yearly_values, color='#27ae60', linewidth=2)
        ax3.fill_between(dates_range, yearly_values, 0, color='#27ae60', alpha=0.1)
        ax3.set_title('Yearly Seasonality Pattern', fontsize=12, fontweight='bold')
        ax3.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
        ax3.set_ylabel('Effect (NPR)')
    
    yearly_graph_path = os.path.join(static_dir, f'{symbol}_yearly.png')
    plt.tight_layout()
    plt.savefig(yearly_graph_path)
    plt.close()

    return f'{symbol}_forecast.png', f'{symbol}_weekly.png', f'{symbol}_yearly.png'
