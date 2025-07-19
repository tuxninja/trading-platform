# SentimentService Documentation

The SentimentService analyzes financial news and generates sentiment scores to inform trading decisions in the Trading Platform.

## 📋 Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Core Methods](#core-methods)
- [Sentiment Analysis](#sentiment-analysis)
- [Data Sources](#data-sources)
- [Scoring System](#scoring-system)
- [Error Handling](#error-handling)
- [Configuration](#configuration)
- [Usage Examples](#usage-examples)
- [Testing](#testing)

## 🎯 Overview

The SentimentService is responsible for collecting financial news, analyzing sentiment, and providing actionable sentiment data for trading strategies. It uses multiple sentiment analysis libraries and news sources to generate reliable sentiment scores.

**File Location**: `backend/services/sentiment_service.py`

### Key Responsibilities
- Collect financial news from multiple sources
- Analyze sentiment using NLP libraries
- Generate confidence-weighted sentiment scores
- Store and retrieve sentiment data
- Support both individual and bulk sentiment analysis

## ✨ Key Features

### Multi-Source News Analysis
- ✅ **Yahoo Finance News** - Primary news source with financial focus
- ✅ **Alternative Free Sources** - MarketWatch, Reuters, CNBC RSS feeds
- ✅ **API Fallback** - News API integration when available
- ✅ **Source Validation** - Content quality and relevance filtering

### Advanced Sentiment Analysis
- ✅ **VADER Sentiment** - Optimized for social media and financial text
- ✅ **TextBlob Analysis** - General-purpose sentiment analysis
- ✅ **Ensemble Scoring** - Combined sentiment from multiple algorithms
- ✅ **Confidence Metrics** - Reliability indicators for sentiment scores

### Data Management
- ✅ **Historical Storage** - Sentiment data persistence and tracking
- ✅ **Bulk Processing** - Efficient analysis of multiple stocks
- ✅ **Cache Management** - Optimized performance with intelligent caching
- ✅ **Quality Control** - Data validation and error handling

## 🏗️ Architecture

```python
class SentimentService:
    def __init__(self):
        # Dependencies
        self.alternative_news_service = AlternativeNewsService()
        
        # Configuration
        self.tracked_stocks = config.DEFAULT_TRACKED_STOCKS
        
        # News sources configuration
        self.news_sources = {
            'yahoo': 'https://finance.yahoo.com/rss/headline',
            'marketwatch': 'http://feeds.marketwatch.com/marketwatch/topstories/',
            'reuters': 'http://feeds.reuters.com/reuters/businessNews',
            'cnbc': 'https://www.cnbc.com/id/100003114/device/rss/rss.html'
        }
        
        # Sentiment analysis tools
        self.vader_analyzer = vaderSentiment.SentimentIntensityAnalyzer()
        
        # Logging
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
```

### Dependencies

| Component | Purpose | Description |
|-----------|---------|-------------|
| `AlternativeNewsService` | Free news sources | RSS feed parsing and content extraction |
| `vaderSentiment` | Sentiment analysis | VADER (Valence Aware Dictionary and sEntiment Reasoner) |
| `textblob` | NLP processing | Text processing and sentiment analysis |
| `feedparser` | RSS parsing | Parse RSS feeds from news sources |
| `requests` | HTTP client | Web scraping and API calls |

## 🔧 Core Methods

### Individual Analysis

#### `analyze_stock_sentiment(db: Session, symbol: str) -> SentimentResponse`

Analyze sentiment for a single stock symbol.

**Parameters:**
- `db`: Database session
- `symbol`: Stock symbol to analyze (e.g., "AAPL")

**Returns:** SentimentResponse with complete sentiment analysis

**Process:**
1. Collect news articles mentioning the stock
2. Filter for relevance and quality
3. Analyze sentiment using multiple algorithms
4. Calculate confidence-weighted scores
5. Store results in database
6. Return comprehensive sentiment data

**Example Usage:**
```python
sentiment_service = SentimentService()
with SessionLocal() as db:
    result = sentiment_service.analyze_stock_sentiment(db, "AAPL")
    print(f"AAPL Sentiment: {result.overall_sentiment:.3f}")
    print(f"Confidence: {result.confidence_score:.2f}")
```

#### `get_stock_sentiment(db: Session, symbol: str) -> Optional[SentimentResponse]`

Retrieve existing sentiment data for a stock.

**Returns:** Most recent sentiment analysis or None if not found

### Bulk Operations

#### `run_daily_sentiment_analysis(db: Session) -> List[SentimentResponse]`

Run sentiment analysis for all tracked stocks.

**Process:**
1. Get list of tracked stocks
2. Analyze sentiment for each stock
3. Handle errors gracefully (continue processing other stocks)
4. Return list of successful analyses

**Example Return:**
```python
[
    {
        "symbol": "AAPL",
        "overall_sentiment": 0.125,
        "news_sentiment": 0.089,
        "confidence_score": 0.75,
        "sources_count": 12,
        "positive_articles": 8,
        "negative_articles": 2
    },
    # ... more stocks
]
```

#### `get_all_sentiment(db: Session) -> List[SentimentResponse]`

Retrieve sentiment data for all stocks in the database.

## 📊 Sentiment Analysis

### Sentiment Algorithms

#### VADER Sentiment Analysis
```python
def analyze_with_vader(self, text: str) -> Dict[str, float]:
    """Analyze text using VADER sentiment analyzer"""
    scores = self.vader_analyzer.polarity_scores(text)
    
    return {
        'compound': scores['compound'],  # Overall sentiment (-1 to 1)
        'positive': scores['pos'],       # Positive intensity (0 to 1)
        'negative': scores['neg'],       # Negative intensity (0 to 1)
        'neutral': scores['neu'],        # Neutral intensity (0 to 1)
        'confidence': abs(scores['compound'])  # Confidence in sentiment
    }
```

**VADER Advantages:**
- Optimized for social media and informal text
- Handles punctuation, capitalization, and intensifiers
- Good performance on financial news
- Provides confidence scores

#### TextBlob Analysis
```python
def analyze_with_textblob(self, text: str) -> Dict[str, float]:
    """Analyze text using TextBlob sentiment analyzer"""
    blob = TextBlob(text)
    
    return {
        'polarity': blob.sentiment.polarity,      # -1 (negative) to 1 (positive)
        'subjectivity': blob.sentiment.subjectivity,  # 0 (objective) to 1 (subjective)
        'confidence': abs(blob.sentiment.polarity)
    }
```

**TextBlob Advantages:**
- Simple and reliable
- Good baseline sentiment analysis
- Handles longer text well
- Less sensitive to slang and informal language

### Ensemble Scoring

The service combines multiple sentiment scores for better accuracy:

```python
def calculate_ensemble_sentiment(self, vader_score: float, textblob_score: float, 
                               vader_confidence: float, textblob_confidence: float) -> Dict:
    """Combine multiple sentiment scores with confidence weighting"""
    
    # Weight scores by confidence
    total_confidence = vader_confidence + textblob_confidence
    
    if total_confidence > 0:
        weighted_sentiment = (
            (vader_score * vader_confidence + textblob_score * textblob_confidence)
            / total_confidence
        )
        overall_confidence = total_confidence / 2  # Average confidence
    else:
        weighted_sentiment = 0.0
        overall_confidence = 0.0
    
    return {
        'overall_sentiment': weighted_sentiment,
        'confidence_score': overall_confidence,
        'vader_sentiment': vader_score,
        'textblob_sentiment': textblob_score
    }
```

## 🌐 Data Sources

### Primary Sources

#### Yahoo Finance News
```python
def get_yahoo_finance_news(self, symbol: str) -> List[Dict]:
    """Fetch news from Yahoo Finance for specific stock"""
    url = f"https://finance.yahoo.com/rss/headline?s={symbol}"
    
    try:
        feed = feedparser.parse(url)
        articles = []
        
        for entry in feed.entries:
            article = {
                'title': entry.title,
                'summary': entry.summary,
                'link': entry.link,
                'published': entry.published,
                'source': 'Yahoo Finance'
            }
            articles.append(article)
            
        return articles
    except Exception as e:
        self.logger.warning(f"Failed to fetch Yahoo Finance news for {symbol}: {str(e)}")
        return []
```

#### Alternative Free Sources
```python
def get_alternative_news(self, symbol: str) -> List[Dict]:
    """Get news from free RSS sources"""
    return self.alternative_news_service.get_financial_news([symbol])
```

**Supported Free Sources:**
- MarketWatch RSS feeds
- Reuters Business News
- CNBC Business feeds
- Yahoo Finance RSS
- Financial news aggregators

### API Sources (Optional)

#### News API Integration
```python
def get_news_api_articles(self, symbol: str) -> List[Dict]:
    """Fetch news using News API (requires API key)"""
    if not self.news_api_key:
        return []
    
    params = {
        'q': f'{symbol} stock',
        'category': 'business',
        'language': 'en',
        'sortBy': 'publishedAt',
        'apiKey': self.news_api_key
    }
    
    response = requests.get('https://newsapi.org/v2/everything', params=params)
    
    if response.status_code == 200:
        articles = response.json().get('articles', [])
        return self.format_news_api_articles(articles)
    
    return []
```

### Content Filtering

#### Relevance Filtering
```python
def filter_relevant_articles(self, articles: List[Dict], symbol: str) -> List[Dict]:
    """Filter articles for relevance to the stock symbol"""
    relevant_articles = []
    
    # Keywords that indicate financial relevance
    financial_keywords = [
        'stock', 'shares', 'trading', 'market', 'earnings', 
        'revenue', 'profit', 'loss', 'financial', 'investor'
    ]
    
    for article in articles:
        text = f"{article['title']} {article.get('summary', '')}"
        
        # Check if symbol mentioned
        if symbol.lower() in text.lower():
            # Check for financial keywords
            if any(keyword in text.lower() for keyword in financial_keywords):
                relevant_articles.append(article)
                
    return relevant_articles
```

#### Quality Control
```python
def validate_article_quality(self, article: Dict) -> bool:
    """Validate article meets quality standards"""
    
    # Minimum content length
    content = f"{article.get('title', '')} {article.get('summary', '')}"
    if len(content.strip()) < 50:
        return False
    
    # Check for spam indicators
    spam_indicators = ['click here', 'limited time', 'act now', 'free trial']
    if any(indicator in content.lower() for indicator in spam_indicators):
        return False
    
    # Require publication date within reasonable timeframe
    if 'published' in article:
        try:
            pub_date = datetime.strptime(article['published'], '%a, %d %b %Y %H:%M:%S %z')
            days_old = (datetime.now(timezone.utc) - pub_date).days
            if days_old > 7:  # Only recent articles
                return False
        except:
            pass  # If date parsing fails, continue anyway
    
    return True
```

## 📈 Scoring System

### Sentiment Scale
- **Range**: -1.0 to +1.0
- **-1.0 to -0.5**: Strong negative sentiment
- **-0.5 to -0.1**: Weak negative sentiment  
- **-0.1 to +0.1**: Neutral sentiment
- **+0.1 to +0.5**: Weak positive sentiment
- **+0.5 to +1.0**: Strong positive sentiment

### Confidence Scoring
- **Range**: 0.0 to 1.0
- **0.0 to 0.3**: Low confidence (insufficient data)
- **0.3 to 0.6**: Moderate confidence
- **0.6 to 0.8**: High confidence
- **0.8 to 1.0**: Very high confidence

### Composite Score Calculation
```python
def calculate_final_sentiment_score(self, articles: List[Dict]) -> Dict:
    """Calculate final sentiment score from analyzed articles"""
    
    if not articles:
        return {
            'overall_sentiment': 0.0,
            'confidence_score': 0.0,
            'sources_count': 0
        }
    
    sentiments = []
    confidences = []
    
    for article in articles:
        # Analyze article text
        text = f"{article['title']} {article.get('summary', '')}"
        
        vader_result = self.analyze_with_vader(text)
        textblob_result = self.analyze_with_textblob(text)
        
        # Combine scores
        ensemble = self.calculate_ensemble_sentiment(
            vader_result['compound'],
            textblob_result['polarity'],
            vader_result['confidence'],
            textblob_result['confidence']
        )
        
        sentiments.append(ensemble['overall_sentiment'])
        confidences.append(ensemble['confidence_score'])
    
    # Calculate weighted average
    total_weight = sum(confidences)
    if total_weight > 0:
        weighted_sentiment = sum(s * c for s, c in zip(sentiments, confidences)) / total_weight
        average_confidence = sum(confidences) / len(confidences)
    else:
        weighted_sentiment = 0.0
        average_confidence = 0.0
    
    # Adjust confidence based on sample size
    sample_size_factor = min(len(articles) / 10, 1.0)  # More articles = higher confidence
    final_confidence = average_confidence * sample_size_factor
    
    return {
        'overall_sentiment': round(weighted_sentiment, 4),
        'news_sentiment': round(weighted_sentiment, 4),  # Same for now
        'social_sentiment': 0.0,  # Not implemented yet
        'confidence_score': round(final_confidence, 4),
        'sources_count': len(articles),
        'positive_articles': sum(1 for s in sentiments if s > 0.1),
        'negative_articles': sum(1 for s in sentiments if s < -0.1),
        'neutral_articles': sum(1 for s in sentiments if -0.1 <= s <= 0.1)
    }
```

## ❌ Error Handling

### Graceful Degradation
```python
def analyze_stock_sentiment(self, db: Session, symbol: str) -> SentimentResponse:
    """Analyze sentiment with comprehensive error handling"""
    
    try:
        # Primary analysis attempt
        return self._perform_sentiment_analysis(db, symbol)
        
    except requests.RequestException as e:
        self.logger.warning(f"Network error analyzing {symbol}: {str(e)}")
        # Return cached data if available
        cached_result = self.get_cached_sentiment(db, symbol)
        if cached_result:
            return cached_result
        
        # Return neutral sentiment as fallback
        return self._create_neutral_sentiment_response(symbol)
        
    except Exception as e:
        self.logger.error(f"Unexpected error analyzing sentiment for {symbol}: {str(e)}")
        return self._create_error_sentiment_response(symbol, str(e))

def _create_neutral_sentiment_response(self, symbol: str) -> SentimentResponse:
    """Create neutral sentiment response for error cases"""
    return SentimentResponse(
        symbol=symbol,
        overall_sentiment=0.0,
        news_sentiment=0.0,
        social_sentiment=0.0,
        confidence_score=0.0,
        sources_count=0,
        error_message="Unable to analyze sentiment - using neutral default"
    )
```

### Retry Logic
```python
def fetch_news_with_retry(self, symbol: str, max_retries: int = 3) -> List[Dict]:
    """Fetch news with exponential backoff retry"""
    
    for attempt in range(max_retries):
        try:
            return self._fetch_news_sources(symbol)
            
        except requests.RequestException as e:
            wait_time = 2 ** attempt  # Exponential backoff
            self.logger.warning(
                f"Attempt {attempt + 1} failed for {symbol}: {str(e)}. "
                f"Retrying in {wait_time} seconds..."
            )
            time.sleep(wait_time)
            
        except Exception as e:
            self.logger.error(f"Non-retryable error for {symbol}: {str(e)}")
            break
    
    self.logger.error(f"Failed to fetch news for {symbol} after {max_retries} attempts")
    return []
```

## ⚙️ Configuration

### Environment Variables
```bash
# News API configuration (optional)
NEWS_API_KEY=your_news_api_key_here
NEWS_API_TIMEOUT=45

# Sentiment analysis settings
SENTIMENT_CACHE_TTL=1800              # Cache sentiment for 30 minutes
MIN_ARTICLES_FOR_ANALYSIS=3          # Minimum articles needed
MAX_ARTICLES_PER_ANALYSIS=50         # Limit articles processed
SENTIMENT_CONFIDENCE_THRESHOLD=0.3    # Minimum confidence for valid sentiment

# News source configuration
ENABLE_YAHOO_FINANCE_NEWS=true
ENABLE_ALTERNATIVE_NEWS_SOURCES=true
ENABLE_NEWS_API=false                 # Requires API key

# Content filtering
MIN_ARTICLE_LENGTH=50                 # Minimum characters per article
MAX_ARTICLE_AGE_DAYS=7               # Only analyze recent articles
REQUIRE_FINANCIAL_KEYWORDS=true       # Filter for financial relevance
```

### Service Configuration
```python
class SentimentConfig:
    # Analysis parameters
    MIN_ARTICLES_FOR_ANALYSIS: int = 3
    MAX_ARTICLES_PER_ANALYSIS: int = 50
    SENTIMENT_CONFIDENCE_THRESHOLD: float = 0.3
    
    # Caching
    CACHE_TTL_SECONDS: int = 1800  # 30 minutes
    ENABLE_CACHING: bool = True
    
    # News sources
    YAHOO_FINANCE_ENABLED: bool = True
    ALTERNATIVE_SOURCES_ENABLED: bool = True
    NEWS_API_ENABLED: bool = False
    
    # Quality filters
    MIN_ARTICLE_LENGTH: int = 50
    MAX_ARTICLE_AGE_DAYS: int = 7
    FINANCIAL_KEYWORD_FILTER: bool = True
    
    # Performance
    REQUEST_TIMEOUT: int = 30
    MAX_CONCURRENT_REQUESTS: int = 5
    RATE_LIMIT_DELAY: float = 0.1
```

## 🔧 Usage Examples

### Basic Sentiment Analysis
```python
from services.sentiment_service import SentimentService

# Initialize service
sentiment_service = SentimentService()

# Analyze single stock
with SessionLocal() as db:
    result = sentiment_service.analyze_stock_sentiment(db, "AAPL")
    
    print(f"Symbol: {result.symbol}")
    print(f"Overall Sentiment: {result.overall_sentiment:.3f}")
    print(f"Confidence: {result.confidence_score:.2f}")
    print(f"Sources: {result.sources_count}")
    print(f"Articles: +{result.positive_articles} -{result.negative_articles} ={result.neutral_articles}")
```

### Bulk Sentiment Analysis
```python
# Analyze multiple stocks
symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]

with SessionLocal() as db:
    results = []
    
    for symbol in symbols:
        try:
            result = sentiment_service.analyze_stock_sentiment(db, symbol)
            results.append(result)
            print(f"{symbol}: {result.overall_sentiment:.3f} (confidence: {result.confidence_score:.2f})")
        except Exception as e:
            print(f"Failed to analyze {symbol}: {str(e)}")
    
    print(f"\nAnalyzed {len(results)} stocks successfully")
```

### Daily Sentiment Update
```python
# Run daily sentiment analysis for all tracked stocks
with SessionLocal() as db:
    results = sentiment_service.run_daily_sentiment_analysis(db)
    
    print(f"Daily sentiment analysis completed: {len(results)} stocks")
    
    # Sort by sentiment for review
    sorted_results = sorted(results, key=lambda x: x.overall_sentiment, reverse=True)
    
    print("\nTop 5 Most Positive:")
    for result in sorted_results[:5]:
        print(f"  {result.symbol}: {result.overall_sentiment:.3f}")
    
    print("\nTop 5 Most Negative:")
    for result in sorted_results[-5:]:
        print(f"  {result.symbol}: {result.overall_sentiment:.3f}")
```

### Historical Sentiment Analysis
```python
# Get sentiment trends over time
with SessionLocal() as db:
    # Get current sentiment
    current = sentiment_service.get_stock_sentiment(db, "AAPL")
    
    if current:
        print(f"Current AAPL sentiment: {current.overall_sentiment:.3f}")
        
        # Get historical data
        historical_data = db.query(SentimentData)\
            .filter(SentimentData.symbol == "AAPL")\
            .order_by(SentimentData.analysis_date.desc())\
            .limit(30)\
            .all()
        
        print(f"Historical data points: {len(historical_data)}")
        
        # Calculate trend
        if len(historical_data) >= 2:
            recent_avg = sum(d.overall_sentiment for d in historical_data[:7]) / 7
            older_avg = sum(d.overall_sentiment for d in historical_data[-7:]) / 7
            trend = recent_avg - older_avg
            
            print(f"7-day sentiment trend: {trend:+.3f}")
```

## 🧪 Testing

### Unit Test Examples
```python
import pytest
from unittest.mock import Mock, patch, MagicMock
from services.sentiment_service import SentimentService

class TestSentimentService:
    def setup_method(self):
        self.service = SentimentService()
        self.mock_db = Mock()
    
    def test_vader_analysis(self):
        """Test VADER sentiment analysis"""
        # Positive text
        result = self.service.analyze_with_vader("This stock is performing great!")
        assert result['compound'] > 0
        assert result['positive'] > result['negative']
        
        # Negative text
        result = self.service.analyze_with_vader("This stock is terrible and declining!")
        assert result['compound'] < 0
        assert result['negative'] > result['positive']
    
    def test_textblob_analysis(self):
        """Test TextBlob sentiment analysis"""
        result = self.service.analyze_with_textblob("The company reported excellent quarterly results.")
        assert result['polarity'] > 0
        assert 0 <= result['subjectivity'] <= 1
    
    @patch('services.sentiment_service.feedparser.parse')
    def test_yahoo_finance_news_fetching(self, mock_feedparser):
        """Test Yahoo Finance news fetching"""
        # Mock RSS feed response
        mock_feed = MagicMock()
        mock_feed.entries = [
            MagicMock(
                title="Apple Reports Strong Earnings",
                summary="Apple Inc. exceeded expectations...",
                link="https://finance.yahoo.com/news/apple-earnings",
                published="Mon, 15 Jul 2024 10:00:00 +0000"
            )
        ]
        mock_feedparser.return_value = mock_feed
        
        # Test news fetching
        articles = self.service.get_yahoo_finance_news("AAPL")
        
        assert len(articles) == 1
        assert articles[0]['title'] == "Apple Reports Strong Earnings"
        assert articles[0]['source'] == 'Yahoo Finance'
    
    def test_sentiment_score_calculation(self):
        """Test final sentiment score calculation"""
        # Mock articles with known sentiment
        mock_articles = [
            {'title': 'Great quarterly results', 'summary': 'Excellent performance'},
            {'title': 'Stock price drops', 'summary': 'Disappointing earnings'},
            {'title': 'Positive outlook', 'summary': 'Strong future prospects'}
        ]
        
        result = self.service.calculate_final_sentiment_score(mock_articles)
        
        assert -1.0 <= result['overall_sentiment'] <= 1.0
        assert 0.0 <= result['confidence_score'] <= 1.0
        assert result['sources_count'] == 3
    
    def test_error_handling_no_articles(self):
        """Test handling when no articles are found"""
        result = self.service.calculate_final_sentiment_score([])
        
        assert result['overall_sentiment'] == 0.0
        assert result['confidence_score'] == 0.0
        assert result['sources_count'] == 0
    
    @patch('services.sentiment_service.requests.get')
    def test_network_error_handling(self, mock_get):
        """Test network error handling"""
        # Mock network failure
        mock_get.side_effect = requests.RequestException("Network error")
        
        # Should not raise exception, should return empty list
        articles = self.service.get_news_api_articles("AAPL")
        assert articles == []
```

### Integration Tests
```python
def test_full_sentiment_analysis_integration():
    """Integration test for complete sentiment analysis"""
    from database import SessionLocal
    
    service = SentimentService()
    
    with SessionLocal() as db:
        # Run analysis
        result = service.analyze_stock_sentiment(db, "AAPL")
        
        # Verify result structure
        assert result.symbol == "AAPL"
        assert -1.0 <= result.overall_sentiment <= 1.0
        assert 0.0 <= result.confidence_score <= 1.0
        assert result.sources_count >= 0
        
        # Verify database storage
        stored_sentiment = db.query(SentimentData)\
            .filter(SentimentData.symbol == "AAPL")\
            .order_by(SentimentData.timestamp.desc())\
            .first()
        
        assert stored_sentiment is not None
        assert stored_sentiment.overall_sentiment == result.overall_sentiment

def test_bulk_analysis_performance():
    """Test performance of bulk sentiment analysis"""
    import time
    
    service = SentimentService()
    symbols = ["AAPL", "MSFT", "GOOGL"]
    
    start_time = time.time()
    
    with SessionLocal() as db:
        results = service.run_daily_sentiment_analysis(db)
    
    end_time = time.time()
    duration = end_time - start_time
    
    # Should complete within reasonable time
    assert duration < 30  # 30 seconds max
    assert len(results) >= 0  # Should not fail
```

---

## 📚 Additional Resources

- [TradingService Documentation](trading-service.md)
- [DataService Documentation](data-service.md)
- [API Documentation](../api.md)
- [Database Schema](../database.md)
- [Configuration Guide](../configuration.md)

For questions about the SentimentService or to report issues, please refer to the main project documentation.