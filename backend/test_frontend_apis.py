#!/usr/bin/env python3
"""
Test script to verify APIs are working correctly for the frontend.
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_api_endpoint(method, url, data=None, description=""):
    """Test an API endpoint and return the result."""
    print(f"\n🧪 Testing: {description}")
    print(f"   {method} {url}")
    
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        else:
            response = requests.request(method, url, json=data)
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                if isinstance(result, list):
                    print(f"   Result: Array with {len(result)} items")
                    if result:
                        print(f"   Sample: {json.dumps(result[0], indent=2, default=str)[:200]}...")
                elif isinstance(result, dict):
                    print(f"   Result: Object with keys: {list(result.keys())}")
                else:
                    print(f"   Result: {type(result).__name__}")
                
                return True, result
            except:
                print(f"   Result: {response.text}")
                return True, response.text
        else:
            print(f"   Error: {response.text}")
            return False, response.text
            
    except Exception as e:
        print(f"   Exception: {str(e)}")
        return False, str(e)

def main():
    print("🚀 Testing Trading App APIs for Frontend Compatibility")
    
    # Test basic connectivity
    success, _ = test_api_endpoint("GET", f"{BASE_URL}/", description="Basic connectivity")
    if not success:
        print("❌ Cannot connect to backend! Make sure it's running on localhost:8000")
        return
    
    print("\n" + "="*60)
    print(" TESTING CORE APIs USED BY FRONTEND")
    print("="*60)
    
    # Test sentiment API (main issue)
    test_api_endpoint("GET", f"{BASE_URL}/api/sentiment", description="Get all sentiment data")
    
    # Test other core APIs
    test_api_endpoint("GET", f"{BASE_URL}/api/stocks", description="Get all stocks")
    test_api_endpoint("GET", f"{BASE_URL}/api/trades", description="Get all trades")
    test_api_endpoint("GET", f"{BASE_URL}/api/performance", description="Get performance metrics")
    
    # Test if we have any stocks/sentiment data
    print("\n" + "="*60)
    print(" CHECKING DATA AVAILABILITY")
    print("="*60)
    
    success, stocks = test_api_endpoint("GET", f"{BASE_URL}/api/stocks", description="Check available stocks")
    if success and isinstance(stocks, list) and len(stocks) > 0:
        print(f"✅ Found {len(stocks)} stocks in watchlist")
        
        # Test sentiment for existing stocks
        success, sentiment = test_api_endpoint("GET", f"{BASE_URL}/api/sentiment", description="Check existing sentiment data")
        if success and isinstance(sentiment, list) and len(sentiment) > 0:
            print(f"✅ Found sentiment data for {len(sentiment)} stocks")
        else:
            print("⚠️  No sentiment data found. Let's generate some...")
            
            # Try to analyze sentiment for first few stocks
            stock_symbols = [stock.get('symbol', '') for stock in stocks[:3] if stock.get('symbol')]
            if stock_symbols:
                test_api_endpoint("POST", f"{BASE_URL}/api/analyze-bulk-sentiment", 
                               {"symbols": stock_symbols, "force_refresh": True},
                               f"Bulk analyze sentiment for {stock_symbols}")
    else:
        print("⚠️  No stocks in watchlist. Let's add some...")
        
        # Add some default stocks
        default_stocks = ["AAPL", "TSLA", "MSFT"]
        for symbol in default_stocks:
            test_api_endpoint("POST", f"{BASE_URL}/api/stocks", symbol, f"Add {symbol}")
        
        # Analyze sentiment for them
        test_api_endpoint("POST", f"{BASE_URL}/api/analyze-bulk-sentiment", 
                       {"symbols": default_stocks, "force_refresh": True},
                       f"Analyze sentiment for {default_stocks}")
    
    print("\n" + "="*60)
    print(" TESTING NEW FEATURES")
    print("="*60)
    
    # Test recommendation features
    test_api_endpoint("GET", f"{BASE_URL}/api/recommendations", description="Get pending recommendations")
    test_api_endpoint("POST", f"{BASE_URL}/api/generate-recommendations", 
                     ["AAPL", "TSLA"], description="Generate recommendations")
    
    # Test market discovery
    test_api_endpoint("POST", f"{BASE_URL}/api/market-scan?limit=5", description="Market scan")
    
    print("\n🎉 API testing completed!")
    print("\nIf all tests passed, the frontend should work correctly.")
    print("If you're still seeing errors, try:")
    print("1. Refresh the frontend browser page")
    print("2. Clear browser cache")
    print("3. Check browser console for more details")

if __name__ == "__main__":
    main()