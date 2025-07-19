# Manual Testing Guide for Trading Sentiment Application

This guide shows you how to manually test the sentiment analysis and recommendation features.

## Quick Start - Test the Complete Workflow

### 1. Start the Application
```bash
cd backend
python main.py
```

### 2. Add Stocks to Watchlist (if not already done)
```bash
curl -X POST "http://localhost:8000/api/stocks" \
  -H "Content-Type: application/json" \
  -d '"AAPL"'

curl -X POST "http://localhost:8000/api/stocks" \
  -H "Content-Type: application/json" \
  -d '"TSLA"'
```

### 3. Option A: Run Complete Analysis Cycle (RECOMMENDED for known stocks)
This will analyze sentiment and generate recommendations in one step:
```bash
curl -X POST "http://localhost:8000/api/full-analysis-cycle" \
  -H "Content-Type: application/json" \
  -d '["AAPL", "TSLA", "MSFT"]'
```

### 3. Option B: Auto-Discover Trending Stocks (NEW FEATURE)
This will automatically find trending stocks from news and analyze them:
```bash
curl -X POST "http://localhost:8000/api/discovery-to-recommendations?min_trending_score=0.3" \
  -H "Content-Type: application/json"
```

### 4. View Generated Recommendations
```bash
curl -X GET "http://localhost:8000/api/recommendations"
```

### 5. Approve a Recommendation
Replace `{recommendation_id}` with an actual ID from step 4:
```bash
curl -X POST "http://localhost:8000/api/recommendations/1/approve" \
  -H "Content-Type: application/json"
```

## Market Discovery Features (NEW!)

### Scan for Trending Stocks
Find stocks mentioned in recent market news:
```bash
curl -X POST "http://localhost:8000/api/market-scan?limit=15" \
  -H "Content-Type: application/json"
```

### Auto-Discover and Analyze
Automatically discover trending stocks and add them to your watchlist:
```bash
curl -X POST "http://localhost:8000/api/auto-discover?min_trending_score=0.4" \
  -H "Content-Type: application/json"
```

### Complete Discovery Pipeline
Discover stocks, analyze sentiment, and generate recommendations all in one:
```bash
curl -X POST "http://localhost:8000/api/discovery-to-recommendations?min_trending_score=0.5" \
  -H "Content-Type: application/json"
```

## Detailed Testing Options

### Manual Sentiment Analysis

#### Analyze sentiment for multiple stocks:
```bash
curl -X POST "http://localhost:8000/api/analyze-bulk-sentiment" \
  -H "Content-Type: application/json" \
  -d '{
    "symbols": ["AAPL", "TSLA", "GOOGL"],
    "force_refresh": true
  }'
```

#### Analyze sentiment for a single stock:
```bash
curl -X POST "http://localhost:8000/api/analyze-sentiment" \
  -H "Content-Type: application/json" \
  -d '"AAPL"'
```

### Trade Recommendations

#### Generate recommendations for specific stocks:
```bash
curl -X POST "http://localhost:8000/api/generate-recommendations" \
  -H "Content-Type: application/json" \
  -d '["AAPL", "TSLA"]'
```

#### Generate recommendations for all tracked stocks:
```bash
curl -X POST "http://localhost:8000/api/generate-recommendations" \
  -H "Content-Type: application/json"
```

#### Reject a recommendation:
```bash
curl -X POST "http://localhost:8000/api/recommendations/1/reject" \
  -H "Content-Type: application/json" \
  -d '"Not confident in this analysis"'
```

### View Current State

#### Get all sentiment data:
```bash
curl -X GET "http://localhost:8000/api/sentiment"
```

#### Get trading performance:
```bash
curl -X GET "http://localhost:8000/api/performance"
```

#### Get all trades:
```bash
curl -X GET "http://localhost:8000/api/trades"
```

#### Get tracked stocks:
```bash
curl -X GET "http://localhost:8000/api/stocks"
```

## Testing Workflow Recommendations

### For First-Time Testing:
1. Run the **full analysis cycle** (step 3 above) - this is the easiest way to see everything working
2. Check the **recommendations** endpoint to see what the system suggests
3. **Approve one recommendation** to see a trade get executed
4. Check the **performance** endpoint to see the results

### For Regular Testing:
1. Add new stocks to the watchlist
2. Run sentiment analysis on them
3. Generate recommendations
4. Approve/reject recommendations based on your judgment

## Understanding the Output

### Sentiment Analysis Results:
- `overall_sentiment`: Combined sentiment score (-1 to +1)
- `news_sentiment`: Sentiment from news articles
- `social_sentiment`: Simulated social media sentiment
- `news_count`: Number of news articles analyzed

### Trade Recommendations:
- `action`: "BUY" or "SELL"
- `confidence`: Confidence level (0-1)
- `risk_level`: "LOW", "MEDIUM", or "HIGH"
- `reasoning`: Human-readable explanation
- `expires_at`: When the recommendation expires

### Risk Levels:
- **LOW**: High confidence (>0.8) with strong sentiment (>0.5)
- **MEDIUM**: Moderate confidence (>0.6) with moderate sentiment (>0.3)
- **HIGH**: Lower confidence or weaker sentiment signals

## Troubleshooting

### If sentiment analysis returns 0.0 sentiment:
- Check if NEWS_API_KEY is set correctly in your environment
- The demo key has limited functionality
- Stock symbols must be valid (publicly traded)

### If no recommendations are generated:
- Sentiment scores might be too neutral (between -0.2 and +0.2)
- Try stocks with recent news events
- Check if you have sufficient balance for BUY recommendations

### If trades fail:
- Check trading balance vs. recommended trade value
- Ensure you have shares to sell for SELL recommendations
- Check logs for detailed error messages

## Configuration

You can adjust the sensitivity by modifying `.env`:
```bash
# Make the system more sensitive to sentiment
BUY_SENTIMENT_THRESHOLD=0.1
SELL_SENTIMENT_THRESHOLD=-0.1

# Require higher confidence for trades
CONFIDENCE_THRESHOLD=0.8

# Adjust position sizing
MAX_POSITION_SIZE=0.10  # 10% instead of 5%
```

## Logs

Check `trading_app.log` for detailed information about what the system is doing during analysis and recommendation generation.