# stock_analysis/views.py

from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib import messages
from datetime import datetime, date
import json
import logging

from .services.stock_explainer import explain_stock_movement, get_all_symbols
from .models import StockDailyData

# Set up logging
logger = logging.getLogger(__name__)


def stock_search(request):
    """Main search page for stock movement analysis"""
    symbols = get_all_symbols()
    
    context = {
        'symbols': json.dumps(symbols),
        'default_symbol': request.GET.get('symbol', ''),
        'default_date': request.GET.get('date', ''),
    }
    return render(request, 'stock_analysis/search.html', context)



def analysis_result(request, symbol, year, month, day):
    """Display analysis results for a specific stock and date"""
    from .services.stock_explainer import explain_stock_movement
    from datetime import date
    
    target_date = date(year, month, day)
    
    analysis = explain_stock_movement(symbol, target_date)
    
    context = {
        'analysis': analysis,
        'target_date': target_date,
        'symbol': symbol.upper(),
    }
    
    return render(request, 'stock_analysis/result.html', context)

def analysis_result_by_form(request):
    """Handle form submission redirect to SEO-friendly URL"""
    if request.method == 'GET':
        symbol = request.GET.get('symbol', '').upper().strip()
        date_str = request.GET.get('date', '').strip()
        
        print(f"===== DEBUG =====")
        print(f"Symbol received: {symbol}")
        print(f"Date received: {date_str}")
        print(f"Full GET data: {request.GET}")
        
        if not symbol:
            messages.error(request, "Please enter a stock symbol")
            return redirect('/why-moved/')
        
        if not date_str:
            messages.error(request, "Please select a date")
            return redirect('/why-moved/')
        
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            # Check if data exists
            data_exists = StockDailyData.objects.filter(
                symbol=symbol, 
                date=target_date
            ).exists()
            
            print(f"Data exists for {symbol} on {target_date}: {data_exists}")
            
            if not data_exists:
                messages.error(request, f"No data found for {symbol} on {target_date}. Please check your data import.")
                return redirect('/why-moved/')
            
            # Build the redirect URL
            redirect_url = f'/why-moved/{symbol}/{target_date.year}/{target_date.month}/{target_date.day}/'
            print(f"Redirecting to: {redirect_url}")
            
            return redirect(redirect_url)
            
        except ValueError as e:
            print(f"Date parsing error: {e}")
            messages.error(request, f"Invalid date format: {date_str}. Please use YYYY-MM-DD format.")
            return redirect('/why-moved/')
    
    # If not GET request
    return redirect('/why-moved/')


def autocomplete_symbols(request):
    """API endpoint for symbol autocomplete"""
    query = request.GET.get('q', '').upper()
    symbols = get_all_symbols()
    
    if query:
        symbols = [s for s in symbols if query in s]
    
    return JsonResponse({'symbols': symbols[:10]})


def get_available_dates(request, symbol):
    """API endpoint to get available dates for a symbol"""
    symbol = symbol.upper()
    dates = StockDailyData.objects.filter(
        symbol=symbol
    ).values_list('date', flat=True).order_by('-date')[:365]
    
    date_list = [d.strftime('%Y-%m-%d') for d in dates]
    return JsonResponse({'dates': date_list})