import pandas as pd
import numpy as np
from prophet import Prophet
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
from scipy.signal import savgol_filter
import warnings
warnings.filterwarnings('ignore')

print("="*70)
print("🇳🇵 NEPSE STOCK PRICE FORECAST - SMOOTH PATTERN (NO EDGE FALL)")
print("="*70)

# ============================================
# 1. LOAD DATA
# ============================================

data_filename = 'nepse_data.csv'

try:
    df = pd.read_csv(data_filename)
    print(f"✅ Loaded data from {data_filename}")
except FileNotFoundError:
    print(f"\n❌ ERROR: Data file '{data_filename}' not found!")
    exit()

if 'Date' not in df.columns or 'Close' not in df.columns:
    print(f"\n❌ ERROR: Missing columns! Need 'Date' and 'Close'")
    exit()

# Prepare data
df_all = df[['Date', 'Close']].copy()
df_all.columns = ['ds', 'y']
df_all['ds'] = pd.to_datetime(df_all['ds'], format='%m/%d/%Y', errors='coerce')
df_all = df_all.dropna()
df_all = df_all.sort_values('ds').reset_index(drop=True)

first_date = df_all['ds'].min()
last_date = df_all['ds'].max()
current_price = df_all['y'].iloc[-1]

price_min = df_all['y'].min()
price_max = df_all['y'].max()

print(f"\n📊 YOUR DATA:")
print(f"   Period: {first_date.strftime('%Y-%m-%d')} to {last_date.strftime('%Y-%m-%d')}")
print(f"   Current price: Rs. {current_price:.0f}")
print(f"   Price range: Rs. {price_min:.0f} - Rs. {price_max:.0f}")

# ============================================
# 2. TRAIN MODEL
# ============================================

df_with_freq = df_all.set_index('ds').asfreq('D')
df_with_freq['y'] = df_with_freq['y'].fillna(method='ffill')
df_complete = df_with_freq.reset_index().dropna()

three_years_ago = last_date - timedelta(days=3*365)
df_train = df_complete[df_complete['ds'] >= three_years_ago].copy()

print(f"\n📊 Training: Last 3 years ({len(df_train)} days)")

model = Prophet(
    changepoint_prior_scale=0.05,
    weekly_seasonality=True,
    yearly_seasonality=True,
    interval_width=0.80
)

model.fit(df_train)

# ============================================
# 3. FORECAST
# ============================================

future = model.make_future_dataframe(periods=365)
forecast = model.predict(future)

future_pred = forecast[forecast['ds'] > last_date].copy()

# Force prediction to start at current price
adjustment = current_price - future_pred['yhat'].iloc[0]
future_pred['yhat'] = future_pred['yhat'] + adjustment
future_pred['yhat_lower'] = future_pred['yhat_lower'] + adjustment
future_pred['yhat_upper'] = future_pred['yhat_upper'] + adjustment

forecast_end = future_pred['yhat'].iloc[-1]
change_pct = ((forecast_end - current_price) / current_price) * 100

# ============================================
# 4. CREATE SMOOTH PATTERN (NO EDGE FALL)
# ============================================

historical_dates = df_train['ds'].values
historical_prices = df_train['y'].values

# Convert numpy datetime64 to Python datetime objects
historical_dates_list = [pd.Timestamp(d).to_pydatetime() for d in historical_dates]
historical_prices_list = list(historical_prices)

# Add padding at the end to prevent edge fall
padding_size = min(10, len(historical_prices_list) // 10)

# Create padded arrays as lists
padded_dates = list(historical_dates_list)
padded_prices = list(historical_prices_list)

# Add repeated last value to prevent edge fall
last_date_obj = historical_dates_list[-1]
last_price = historical_prices_list[-1]

for i in range(padding_size):
    padded_dates.append(last_date_obj + timedelta(days=i+1))
    padded_prices.append(last_price)

# Convert to numpy arrays
padded_dates = np.array(padded_dates)
padded_prices = np.array(padded_prices)

# Apply smoothing on padded data
window_size = max(5, len(padded_prices) // 15)
if window_size % 2 == 0:
    window_size += 1

# Use Savitzky-Golay filter
if len(padded_prices) > window_size and window_size >= 5:
    # Ensure window_length is odd and <= len(padded_prices)
    window_length = min(window_size, len(padded_prices) - 1 if len(padded_prices) % 2 == 0 else len(padded_prices))
    if window_length % 2 == 0:
        window_length -= 1
    if window_length >= 5:
        smooth_prices = savgol_filter(padded_prices, window_length=window_length, polyorder=2)
    else:
        smooth_prices = padded_prices
else:
    smooth_prices = padded_prices

# Remove padding from smoothed result (keep only original range)
smooth_prices = smooth_prices[:len(historical_prices_list)]
smooth_dates = historical_dates

# Force the last smoothed point to match actual current price
smooth_prices[-1] = current_price

# Also adjust the last few points to ensure smooth connection
for i in range(1, min(3, len(smooth_prices))):
    smooth_prices[-i] = (smooth_prices[-i] + current_price) / 2

print(f"\n📊 Smoothing: Applied edge prevention (no fall at end)")
print(f"   Padding size: {padding_size} days")
print(f"   Window size: {window_size}")

# ============================================
# 5. TIGHT ZOOM
# ============================================

all_prices = list(historical_prices) + list(future_pred['yhat'].values)
data_min = min(all_prices)
data_max = max(all_prices)

padding = max(5, (data_max - data_min) * 0.05)
y_min = max(0, data_min - padding)
y_max = data_max + padding

y_min_rounded = np.floor(y_min / 10) * 10
y_max_rounded = np.ceil(y_max / 10) * 10

# ============================================
# 6. GRAPH 1: MAIN FORECAST (SMOOTH PATTERN - NO EDGE FALL)
# ============================================

print(f"\n📈 Generating Graph 1: Main Forecast (Smooth Pattern - No Edge Fall)...")

fig1, ax1 = plt.subplots(figsize=(14, 7))

x_start = df_train['ds'].min() - timedelta(days=10)
x_end = future_pred['ds'].max() + timedelta(days=10)

# Plot SMOOTH PATTERN line
ax1.plot(smooth_dates, smooth_prices, color='#1f77b4', linewidth=2.5, 
         label='Historical Pattern (Smoothed Trend)', alpha=0.9)

# Plot ACTUAL data points as small dots
ax1.scatter(historical_dates, historical_prices, color='black', s=4, alpha=0.2, zorder=3)

# Plot forecast
ax1.plot(future_pred['ds'], future_pred['yhat'], color='#1f77b4', linewidth=2.5, label='1 Year Forecast', alpha=0.9)

# Confidence interval
ax1.fill_between(future_pred['ds'], future_pred['yhat_lower'], future_pred['yhat_upper'], 
                  color='#1f77b4', alpha=0.12, label='80% Confidence Interval')

# Connect last smoothed point to first prediction (seamless)
last_smooth_date = smooth_dates[-1]
last_smooth_price = smooth_prices[-1]
ax1.plot([last_smooth_date, future_pred['ds'].iloc[0]], 
         [last_smooth_price, future_pred['yhat'].iloc[0]], 
         color='#1f77b4', linewidth=2.5, alpha=0.9)

# Vertical line at present
ax1.axvline(x=last_date, color='gray', linestyle='--', linewidth=1.5, alpha=0.5)

# Set limits
ax1.set_ylim(y_min_rounded, y_max_rounded)
ax1.set_xlim(x_start, x_end)

# Format axes
ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')

y_step = 20 if (y_max_rounded - y_min_rounded) <= 100 else 50
y_ticks = np.arange(y_min_rounded, y_max_rounded + y_step, y_step)
ax1.set_yticks(y_ticks)
ax1.set_yticklabels([f'{int(x)}' for x in y_ticks])

ax1.set_xlabel('Date', fontsize=12)
ax1.set_ylabel('Price (NPR)', fontsize=12)
ax1.set_title(f'NEPSE Stock Price Forecast - SMOOTH PATTERN (No edge fall)', fontsize=13, fontweight='bold')
ax1.legend(loc='upper left')
ax1.grid(True, alpha=0.3)

# Explanation
ax1.text(0.02, 0.98, 'Blue line = Smooth pattern (overall trend)\nBlack dots = Actual daily prices (faint)\n✓ No fall at the end', 
         transform=ax1.transAxes, fontsize=8, verticalalignment='top',
         bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))

# Current price annotation
ax1.annotate(f'Current: Rs.{current_price:.0f}', xy=(last_date, current_price), xytext=(5, 10), 
             textcoords='offset points', fontsize=10, fontweight='bold', color='#1f77b4')

trend_icon = '📉' if change_pct < 0 else '📈'
ax1.annotate(f'{trend_icon} 1-Year: Rs.{forecast_end:.0f} ({change_pct:+.1f}%)', 
             xy=(future_pred['ds'].iloc[-1], forecast_end), 
             xytext=(-80, -30 if change_pct < 0 else 20), textcoords='offset points', 
             fontsize=10, fontweight='bold', color='#1f77b4')

plt.tight_layout()
plt.savefig('1_main_forecast_smooth_pattern.png', dpi=150)
plt.show()

# ============================================
# 7. GRAPH 2: WEEKLY EFFECT
# ============================================

print(f"\n📈 Generating Graph 2: Weekly Effect...")

weekly_data = forecast[['ds', 'weekly']].dropna().copy()
weekly_data['DayName'] = weekly_data['ds'].dt.day_name()

day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
weekly_effect = weekly_data.groupby('DayName')['weekly'].mean().reindex(day_order)

fig2, ax2 = plt.subplots(figsize=(10, 5))

ax2.plot(day_order, weekly_effect.values, color='#1f77b4', linewidth=2, marker='o', markersize=5)
ax2.axhline(y=0, color='gray', linestyle='--', linewidth=0.8, alpha=0.5)

ax2.set_xlabel('Day of Week', fontsize=12)
ax2.set_ylabel('Weekly Effect (NPR)', fontsize=12)
ax2.set_title('Weekly Seasonality Effect', fontsize=13, fontweight='bold')
ax2.grid(True, alpha=0.3)
ax2.set_xticklabels(day_order, rotation=45, ha='right')

plt.tight_layout()
plt.savefig('2_weekly_effect.png', dpi=150, bbox_inches='tight')
plt.show()

# ============================================
# 8. GRAPH 3: YEARLY PATTERN
# ============================================

print(f"\n📈 Generating Graph 3: Yearly Pattern...")

if 'yearly' in forecast.columns:
    dates_2024 = pd.date_range('2024-01-01', '2024-12-31', freq='D')
    yearly_values = []
    
    for date in dates_2024:
        temp_df = pd.DataFrame({'ds': [date]})
        yearly_val = model.predict_seasonal_components(temp_df)['yearly'].iloc[0]
        yearly_values.append(yearly_val)
    
    fig3, ax3 = plt.subplots(figsize=(14, 6))
    
    ax3.plot(dates_2024, yearly_values, color='#1f77b4', linewidth=2)
    ax3.fill_between(dates_2024, yearly_values, 0, color='#1f77b4', alpha=0.1)
    ax3.axhline(y=0, color='gray', linestyle='--', linewidth=0.8, alpha=0.5)
    
    ax3.set_xlabel('Month', fontsize=12)
    ax3.set_ylabel('Yearly Effect (NPR)', fontsize=12)
    ax3.set_title('Yearly Seasonality (January - December)', fontsize=13, fontweight='bold')
    ax3.grid(True, alpha=0.3)
    ax3.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
    ax3.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
    plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    plt.tight_layout()
    plt.savefig('3_yearly_pattern.png', dpi=150, bbox_inches='tight')
    plt.show()
else:
    print("   Yearly pattern not available")

# ============================================
# 9. FORECAST TABLE
# ============================================

future_pred['Month'] = future_pred['ds'].dt.to_period('M')
monthly = future_pred.groupby('Month').agg({
    'yhat': 'mean'
}).round(2)
monthly.columns = ['Forecast_NPR']
monthly = monthly.reset_index()
monthly['Month'] = monthly['Month'].astype(str)
monthly.to_csv('forecast_table.csv', index=False)

print("\n" + "="*70)
print("📊 MONTHLY FORECAST")
print("="*70)
print(f"\n{'Month':<12} {'Forecast (NPR)':<15}")
print("-"*30)
for _, row in monthly.head(12).iterrows():
    print(f"{row['Month']:<12} Rs. {row['Forecast_NPR']:<10.2f}")

# ============================================
# 10. SUMMARY
# ============================================

print("\n" + "="*70)
print("SUMMARY")
print("="*70)
print(f"""
Your Data Span:    {first_date.strftime('%Y-%m-%d')} to {last_date.strftime('%Y-%m-%d')}
Price Range:       Rs. {price_min:.0f} - Rs. {price_max:.0f}
Current Price:     Rs. {current_price:.0f}

1-Year Forecast:   Rs. {forecast_end:.0f}
Change:            {change_pct:+.1f}%

Key Fix Applied:
   ✓ Converted numpy datetime64 to Python datetime
   ✓ Added padding at the end with repeated last value
   ✓ Used Savitzky-Golay filter
   ✓ Forced last smoothed point to match current price
   ✓ NO MORE FALL TO ZERO at the end

Files Generated:
   1. 1_main_forecast_smooth_pattern.png - Main forecast (no edge fall)
   2. 2_weekly_effect.png - Weekly effect
   3. 3_yearly_pattern.png - Yearly pattern
   4. forecast_table.csv - Monthly forecast table
""")
print("="*70)
print("✅ COMPLETE!")