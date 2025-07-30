#!/usr/bin/env python3
"""
Test script for watchlist functionality
"""

import requests
import json
import sqlite3

BASE_URL = "http://localhost:8000"

def test_watchlist_functionality():
    print("=== Testing Watchlist Functionality ===")
    
    # Test 1: Get empty watchlist (should return empty list)
    print("\n1. Testing GET watchlist (empty)...")
    try:
        response = requests.get(f"{BASE_URL}/api/watchlist")
        print(f"Status: {response.status_code}")
        if response.status_code == 401:
            print("Expected: Authentication required")
        else:
            print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 2: Add stock to watchlist
    print("\n2. Testing POST watchlist (add AAPL)...")
    try:
        payload = {
            "symbol": "AAPL",
            "preferences": {
                "sentiment_monitoring": True,
                "auto_trading": True,
                "max_position_size": 1000,
                "risk_tolerance": "medium"
            }
        }
        response = requests.post(f"{BASE_URL}/api/watchlist", json=payload)
        print(f"Status: {response.status_code}")
        if response.status_code == 401:
            print("Expected: Authentication required")
        else:
            print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 3: Check database directly
    print("\n3. Checking database directly...")
    try:
        conn = sqlite3.connect('trading_app.db')
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM watchlist_stocks')
        count = cursor.fetchone()[0]
        print(f"Watchlist stocks count: {count}")
        
        if count > 0:
            cursor.execute('SELECT symbol, company_name, is_active FROM watchlist_stocks LIMIT 3')
            rows = cursor.fetchall()
            print("Sample stocks:", rows)
        
        conn.close()
    except Exception as e:
        print(f"Database error: {e}")
    
    # Test 4: Test backend logs for any errors
    print("\n4. Checking recent backend logs...")
    try:
        with open('backend_startup.log', 'r') as f:
            lines = f.readlines()
            recent_logs = lines[-10:] if len(lines) > 10 else lines
            for line in recent_logs:
                if 'ERROR' in line or 'watchlist' in line.lower():
                    print(f"Log: {line.strip()}")
    except Exception as e:
        print(f"Log read error: {e}")

if __name__ == "__main__":
    test_watchlist_functionality()