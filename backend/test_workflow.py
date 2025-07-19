#!/usr/bin/env python3
"""
Simple testing script for the Trading Sentiment Application.
Run this script to test the complete workflow easily.
"""
import requests
import json
import time
from typing import List, Dict, Any

BASE_URL = "http://localhost:8000"

def print_section(title: str):
    """Print a section header."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def print_response(response: requests.Response, title: str = "Response"):
    """Print a formatted response."""
    print(f"\n--- {title} ---")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        try:
            data = response.json()
            print(json.dumps(data, indent=2, default=str))
        except:
            print(response.text)
    else:
        print(f"Error: {response.text}")

def test_add_stocks():
    """Add stocks to the watchlist."""
    print_section("STEP 1: Adding Stocks to Watchlist")
    
    stocks = ["AAPL", "TSLA", "MSFT", "GOOGL"]
    
    for stock in stocks:
        print(f"\nAdding {stock}...")
        response = requests.post(f"{BASE_URL}/api/stocks", json=stock)
        if response.status_code == 200:
            print(f"✅ {stock} added successfully")
        else:
            print(f"❌ Failed to add {stock}: {response.text}")
    
    # Show current watchlist
    print("\\nCurrent watchlist:")
    response = requests.get(f"{BASE_URL}/api/stocks")
    if response.status_code == 200:
        stocks_data = response.json()
        for stock in stocks_data:
            print(f"  - {stock.get('symbol', 'Unknown')}: ${stock.get('current_price', 0):.2f}")

def test_sentiment_analysis():
    """Test sentiment analysis."""
    print_section("STEP 2: Analyzing Sentiment")
    
    # Run bulk sentiment analysis
    symbols = ["AAPL", "TSLA", "MSFT"]
    
    request_data = {
        "symbols": symbols,
        "force_refresh": True
    }
    
    print(f"Analyzing sentiment for: {', '.join(symbols)}")
    response = requests.post(f"{BASE_URL}/api/analyze-bulk-sentiment", json=request_data)
    print_response(response, "Sentiment Analysis Results")
    
    return response.status_code == 200

def test_generate_recommendations():
    """Test recommendation generation."""
    print_section("STEP 3: Generating Trade Recommendations")
    
    symbols = ["AAPL", "TSLA", "MSFT"]
    
    print(f"Generating recommendations for: {', '.join(symbols)}")
    response = requests.post(f"{BASE_URL}/api/generate-recommendations", json=symbols)
    print_response(response, "Recommendation Generation Results")
    
    return response.json() if response.status_code == 200 else None

def test_view_recommendations():
    """View pending recommendations."""
    print_section("STEP 4: Viewing Pending Recommendations")
    
    response = requests.get(f"{BASE_URL}/api/recommendations")
    print_response(response, "Pending Recommendations")
    
    if response.status_code == 200:
        data = response.json()
        recommendations = data.get("recommendations", [])
        
        if recommendations:
            print(f"\\n📋 Found {len(recommendations)} pending recommendations:")
            for i, rec in enumerate(recommendations, 1):
                print(f"\\n{i}. Recommendation ID: {rec['id']}")
                print(f"   Symbol: {rec['symbol']}")
                print(f"   Action: {rec['action']}")
                print(f"   Confidence: {rec['confidence']:.2%}")
                print(f"   Risk Level: {rec['risk_level']}")
                print(f"   Recommended Quantity: {rec['recommended_quantity']}")
                print(f"   Value: ${rec['recommended_value']:.2f}")
                print(f"   Reasoning: {rec['reasoning'][:100]}...")
        
        return recommendations
    
    return []

def test_approve_recommendation(recommendations: List[Dict]):
    """Test approving a recommendation."""
    if not recommendations:
        print("\\n❌ No recommendations to approve")
        return
    
    print_section("STEP 5: Approving a Recommendation")
    
    # Find the first BUY recommendation with reasonable confidence
    best_rec = None
    for rec in recommendations:
        if rec['action'] == 'BUY' and rec['confidence'] > 0.5:
            best_rec = rec
            break
    
    if not best_rec:
        # Just take the first one
        best_rec = recommendations[0]
    
    rec_id = best_rec['id']
    print(f"Approving recommendation {rec_id} for {best_rec['symbol']} ({best_rec['action']})...")
    
    # Ask for confirmation
    confirm = input(f"\\nApprove {best_rec['action']} {best_rec['recommended_quantity']} shares of {best_rec['symbol']} for ${best_rec['recommended_value']:.2f}? (y/N): ")
    
    if confirm.lower() == 'y':
        response = requests.post(f"{BASE_URL}/api/recommendations/{rec_id}/approve")
        print_response(response, "Approval Result")
        
        if response.status_code == 200:
            print("✅ Trade executed successfully!")
        else:
            print("❌ Failed to execute trade")
    else:
        print("Trade approval cancelled.")

def test_check_performance():
    """Check trading performance."""
    print_section("STEP 6: Checking Performance")
    
    response = requests.get(f"{BASE_URL}/api/performance")
    print_response(response, "Trading Performance")
    
    if response.status_code == 200:
        perf = response.json()
        print(f"\\n📊 Performance Summary:")
        print(f"   Total Trades: {perf.get('total_trades', 0)}")
        print(f"   Current Balance: ${perf.get('current_balance', 0):,.2f}")
        print(f"   Total P&L: ${perf.get('total_profit_loss', 0):,.2f}")
        print(f"   Win Rate: {perf.get('win_rate', 0):.1f}%")

def test_full_cycle():
    """Test the complete full analysis cycle."""
    print_section("ALTERNATIVE: Full Analysis Cycle")
    
    symbols = ["AAPL", "TSLA", "MSFT"]
    
    print(f"Running complete analysis cycle for: {', '.join(symbols)}")
    print("This will analyze sentiment AND generate recommendations in one step...")
    
    response = requests.post(f"{BASE_URL}/api/full-analysis-cycle", json=symbols)
    print_response(response, "Full Analysis Cycle Results")
    
    return response.status_code == 200

def main():
    """Main testing workflow."""
    print("🚀 Trading Sentiment Application - Manual Testing")
    print("This script will test the complete workflow of the application.")
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code != 200:
            print("❌ Server is not responding correctly!")
            return
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server! Make sure the backend is running on localhost:8000")
        return
    
    print("✅ Server is running!")
    
    # Ask user which test to run
    print("\\nChoose testing approach:")
    print("1. Step-by-step workflow (recommended for learning)")
    print("2. Quick full-cycle test")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "2":
        # Quick test
        test_full_cycle()
        print("\\nNow check recommendations:")
        recommendations = test_view_recommendations()
        if recommendations:
            test_approve_recommendation(recommendations)
        test_check_performance()
    else:
        # Step by step
        test_add_stocks()
        
        print("\\nPress Enter to continue to sentiment analysis...")
        input()
        
        if test_sentiment_analysis():
            print("\\nPress Enter to continue to recommendation generation...")
            input()
            
            test_generate_recommendations()
            
            print("\\nPress Enter to view recommendations...")
            input()
            
            recommendations = test_view_recommendations()
            
            if recommendations:
                print("\\nPress Enter to approve a recommendation...")
                input()
                test_approve_recommendation(recommendations)
            
            print("\\nPress Enter to check final performance...")
            input()
            test_check_performance()
    
    print("\\n🎉 Testing completed!")
    print("\\nNext steps:")
    print("- Check the trading_app.log file for detailed logs")
    print("- Try different stocks with recent news")
    print("- Adjust configuration in .env file")
    print("- Explore the frontend UI")

if __name__ == "__main__":
    main()