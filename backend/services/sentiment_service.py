import requests
import yfinance as yf
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from sqlalchemy.orm import Session
from sqlalchemy import desc
import pandas as pd
from datetime import datetime, timedelta
import os
from typing import Dict, List, Optional
import time
import logging

from models import SentimentData
from schemas import SentimentResponse
from config import config
from exceptions import SentimentAnalysisError, APIRateLimitError
from services.alternative_news_service import AlternativeNewsService

class SentimentService:
    def __init__(self):
        self.analyzer = SentimentIntensityAnalyzer()
        self.news_api_key = config.NEWS_API_KEY
        self.tracked_stocks = [
            "AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "META", "NVDA", "NFLX",
            "AMD", "INTC", "CRM", "ORCL", "ADBE", "PYPL", "UBER", "LYFT"
        ]
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.last_api_call = 0  # For rate limiting
        
        # Initialize alternative news service for fallback
        self.alternative_news = AlternativeNewsService()
        self.use_alternative_news = (self.news_api_key == "demo" or 
                                   self.news_api_key == "your_news_api_key_here" or 
                                   not self.news_api_key)
    
    def _rate_limit(self, api_type: str = "default") -> None:
        """Implement rate limiting for API calls."""
        rate_limit = config.API_RATE_LIMIT if api_type == "default" else config.NEWS_API_RATE_LIMIT
        elapsed = time.time() - self.last_api_call
        if elapsed < rate_limit:
            sleep_time = rate_limit - elapsed
            self.logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        self.last_api_call = time.time()
    
    def analyze_text_sentiment(self, text: str) -> float:
        """Analyze sentiment of text using VADER and TextBlob."""
        if not text or len(text.strip()) == 0:
            return 0.0
        
        try:
            # VADER sentiment analysis
            vader_scores = self.analyzer.polarity_scores(text)
            
            # TextBlob sentiment analysis
            blob = TextBlob(text)
            textblob_sentiment = blob.sentiment.polarity
            
            # Combine both scores (VADER is more reliable for social media)
            combined_score = (vader_scores['compound'] + textblob_sentiment) / 2
            
            self.logger.debug(f"Sentiment analysis: VADER={vader_scores['compound']:.3f}, TextBlob={textblob_sentiment:.3f}, Combined={combined_score:.3f}")
            return combined_score
            
        except Exception as e:
            self.logger.error(f"Error analyzing text sentiment: {str(e)}")
            return 0.0
    
    def get_news_sentiment(self, symbol: str) -> Dict:
        """Get news sentiment for a stock symbol with error handling and rate limiting."""
        try:
            # Validate input
            if not symbol or not symbol.strip():
                raise SentimentAnalysisError("Symbol cannot be empty")
            
            symbol = symbol.upper().strip()
            self.logger.info(f"Fetching news sentiment for {symbol}")
            
            # Use alternative news service if no valid API key
            if self.use_alternative_news:
                self.logger.info(f"Using alternative news sources for {symbol}")
                return self._get_alternative_news_sentiment(symbol)
            
            # Rate limiting
            self._rate_limit("news")
            
            # News API endpoint
            url = "https://newsapi.org/v2/everything"
            params = {
                'q': f'"{symbol}" stock',
                'language': 'en',
                'sortBy': 'publishedAt',
                'pageSize': 50,
                'apiKey': self.news_api_key
            }
            
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 429:
                raise APIRateLimitError("News API rate limit exceeded")
            elif response.status_code == 401:
                self.logger.warning(f"News API authentication failed for {symbol}, switching to alternative sources")
                self.use_alternative_news = True  # Switch to alternative for future calls
                return self._get_alternative_news_sentiment(symbol)
            elif response.status_code != 200:
                self.logger.warning(f"News API returned status {response.status_code} for {symbol}")
                return {"sentiment": 0.0, "count": 0, "articles": []}
            
            data = response.json()
            articles = data.get('articles', [])
            
            if not articles:
                self.logger.info(f"No news articles found for {symbol}")
                return {"sentiment": 0.0, "count": 0, "articles": []}
            
            # Analyze sentiment for each article
            sentiments = []
            for article in articles:
                title = article.get('title', '')
                description = article.get('description', '')
                if title and description:  # Skip articles with missing content
                    content = f"{title} {description}"
                    sentiment = self.analyze_text_sentiment(content)
                    sentiments.append(sentiment)
            
            # Calculate average sentiment
            avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0.0
            
            self.logger.info(f"News sentiment for {symbol}: {avg_sentiment:.3f} from {len(articles)} articles")
            
            return {
                "sentiment": avg_sentiment,
                "count": len(articles),
                "articles": articles[:10]  # Return first 10 articles
            }
            
        except APIRateLimitError:
            raise
        except requests.RequestException as e:
            self.logger.error(f"Network error getting news sentiment for {symbol}: {str(e)}")
            return {"sentiment": 0.0, "count": 0, "articles": []}
        except Exception as e:
            self.logger.error(f"Error getting news sentiment for {symbol}: {str(e)}")
            return {"sentiment": 0.0, "count": 0, "articles": []}
    
    def get_social_sentiment(self, symbol: str) -> Dict:
        """Get social media sentiment (simulated for demo)"""
        try:
            # For demo purposes, we'll simulate social sentiment
            # In production, you'd integrate with Twitter API, Reddit API, etc.
            
            # Simulate sentiment based on stock price movement
            stock = yf.Ticker(symbol)
            hist = stock.history(period="5d")
            
            if hist.empty:
                return {"sentiment": 0.0, "count": 0}
            
            # Calculate price change percentage
            price_change = ((hist['Close'].iloc[-1] - hist['Close'].iloc[0]) / hist['Close'].iloc[0]) * 100
            
            # Simulate sentiment based on price movement
            # This is a simplified approach - in reality you'd analyze actual social media posts
            if price_change > 5:
                sentiment = 0.3 + (price_change - 5) * 0.02  # Positive sentiment
            elif price_change < -5:
                sentiment = -0.3 + (price_change + 5) * 0.02  # Negative sentiment
            else:
                sentiment = price_change * 0.05  # Neutral to slight sentiment
            
            # Clamp sentiment between -1 and 1
            sentiment = max(-1.0, min(1.0, sentiment))
            
            # Simulate post count
            post_count = int(abs(price_change) * 10 + 50)  # More posts for bigger moves
            
            return {
                "sentiment": sentiment,
                "count": post_count
            }
            
        except Exception as e:
            self.logger.error(f"Error getting social sentiment for {symbol}: {str(e)}")
            return {"sentiment": 0.0, "count": 0}
    
    def analyze_stock_sentiment(self, db: Session, symbol: str) -> SentimentResponse:
        """Analyze sentiment for a specific stock with comprehensive error handling."""
        try:
            # Validate input
            if not symbol or not symbol.strip():
                raise SentimentAnalysisError("Symbol cannot be empty")
            
            symbol = symbol.upper().strip()
            self.logger.info(f"Starting sentiment analysis for {symbol}")
            
            # Get news sentiment
            news_data = self.get_news_sentiment(symbol)
            news_sentiment = news_data["sentiment"]
            news_count = news_data["count"]
            
            # Get social sentiment
            social_data = self.get_social_sentiment(symbol)
            social_sentiment = social_data["sentiment"]
            social_count = social_data["count"]
            
            # Calculate overall sentiment (weighted average)
            total_count = news_count + social_count
            if total_count > 0:
                overall_sentiment = (
                    (news_sentiment * news_count + social_sentiment * social_count) / total_count
                )
            else:
                overall_sentiment = 0.0
            
            self.logger.info(f"Sentiment analysis complete for {symbol}: news={news_sentiment:.3f}, social={social_sentiment:.3f}, overall={overall_sentiment:.3f}")
            
            # Save to database
            sentiment_data = SentimentData(
                symbol=symbol,
                news_sentiment=news_sentiment,
                social_sentiment=social_sentiment,
                overall_sentiment=overall_sentiment,
                news_count=news_count,
                social_count=social_count,
                source="COMBINED"
            )
            
            db.add(sentiment_data)
            db.commit()
            db.refresh(sentiment_data)
            
            return SentimentResponse.from_orm(sentiment_data)
            
        except APIRateLimitError:
            db.rollback()
            raise
        except SentimentAnalysisError:
            db.rollback()
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error analyzing sentiment for {symbol}: {str(e)}")
            db.rollback()
            raise SentimentAnalysisError(f"Failed to analyze sentiment for {symbol}: {str(e)}")
    
    def get_stock_sentiment(self, db: Session, symbol: str) -> Optional[SentimentResponse]:
        """Get the latest sentiment data for a stock"""
        sentiment_data = db.query(SentimentData).filter(
            SentimentData.symbol == symbol
        ).order_by(desc(SentimentData.timestamp)).first()
        
        if sentiment_data:
            return SentimentResponse.from_orm(sentiment_data)
        return None
    
    def get_all_sentiment(self, db: Session) -> List[SentimentResponse]:
        """Get sentiment for all tracked stocks"""
        # Get latest sentiment for each stock
        latest_sentiments = []
        for symbol in self.tracked_stocks:
            sentiment = self.get_stock_sentiment(db, symbol)
            if sentiment:
                latest_sentiments.append(sentiment)
        
        return latest_sentiments
    
    def run_daily_sentiment_analysis(self, db: Session):
        """Run sentiment analysis for all tracked stocks"""
        results = []
        for symbol in self.tracked_stocks:
            try:
                result = self.analyze_stock_sentiment(db, symbol)
                results.append(result)
                self._rate_limit()  # Rate limiting
            except Exception as e:
                self.logger.error(f"Error analyzing sentiment for {symbol}: {str(e)}")
        
        return results
    
    def _get_alternative_news_sentiment(self, symbol: str) -> Dict:
        """Get news sentiment using alternative free sources."""
        try:
            articles = self.alternative_news.get_news_for_symbol(symbol)
            
            if not articles:
                self.logger.info(f"No alternative news articles found for {symbol}")
                return {"sentiment": 0.0, "count": 0, "articles": []}
            
            # Analyze sentiment for each article
            sentiments = []
            for article in articles:
                title = article.get('title', '')
                description = article.get('description', '')
                if title and description:
                    content = f"{title} {description}"
                    sentiment = self.analyze_text_sentiment(content)
                    sentiments.append(sentiment)
            
            # Calculate average sentiment
            avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0.0
            
            self.logger.info(f"Alternative news sentiment for {symbol}: {avg_sentiment:.3f} from {len(articles)} articles")
            
            return {
                "sentiment": avg_sentiment,
                "count": len(articles),
                "articles": articles[:10]
            }
            
        except Exception as e:
            self.logger.error(f"Error getting alternative news sentiment for {symbol}: {str(e)}")
            return {"sentiment": 0.0, "count": 0, "articles": []} 