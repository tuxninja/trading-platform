"""
Market scanning service for automatic stock discovery based on news trends.
This service scans news for trending stocks and adds them to analysis pipeline.
"""
import logging
import requests
import re
from datetime import datetime, timedelta
from typing import List, Dict, Set, Optional
from sqlalchemy.orm import Session
import yfinance as yf

from config import config
from exceptions import StockDataError
from services.sentiment_service import SentimentService
from services.data_service import DataService
from schemas import MarketScanResult

class MarketScannerService:
    def __init__(self):
        self.sentiment_service = SentimentService()
        self.data_service = DataService()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Common stock patterns and known symbols
        self.known_symbols = set([
            "AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "META", "NVDA", "NFLX",
            "AMD", "INTC", "CRM", "ORCL", "ADBE", "PYPL", "UBER", "LYFT",
            "SPOT", "ZOOM", "SHOP", "SQ", "ROKU", "PLTR", "SNOW", "COIN",
            "RBLX", "HOOD", "RIVN", "LCID", "NIO", "XPEV", "LI", "BABA"
        ])
        
        # Keywords that often indicate stock discussions
        self.stock_keywords = [
            "stock", "shares", "trading", "earnings", "revenue", "profit",
            "IPO", "acquisition", "merger", "buyback", "dividend"
        ]
    
    def scan_trending_stocks(self, db: Session, limit: int = 10) -> List[MarketScanResult]:
        """Scan news for trending stocks and return discovery results."""
        try:
            self.logger.info("Starting market scan for trending stocks...")
            
            # Get general market news
            market_news = self._get_market_news()
            
            # Extract stock symbols from news
            discovered_symbols = self._extract_stock_symbols(market_news)
            
            # Score and rank discoveries
            scored_discoveries = self._score_discoveries(db, discovered_symbols, market_news)
            
            # Return top discoveries
            top_discoveries = sorted(scored_discoveries, key=lambda x: x.trending_score, reverse=True)[:limit]
            
            self.logger.info(f"Market scan completed. Found {len(top_discoveries)} trending stocks")
            return top_discoveries
            
        except Exception as e:
            self.logger.error(f"Error during market scan: {str(e)}")
            return []
    
    def _get_market_news(self) -> List[Dict]:
        """Fetch general market and business news."""
        try:
            # Use multiple news queries to get broader coverage
            news_queries = [
                "stock market",
                "earnings report", 
                "business news",
                "tech stocks",
                "financial markets"
            ]
            
            all_articles = []
            
            for query in news_queries:
                try:
                    url = "https://newsapi.org/v2/everything"
                    params = {
                        'q': query,
                        'language': 'en',
                        'sortBy': 'publishedAt',
                        'pageSize': 20,  # Smaller batches per query
                        'apiKey': config.NEWS_API_KEY,
                        'from': (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')  # Last 24 hours
                    }
                    
                    response = requests.get(url, params=params, timeout=30)
                    if response.status_code == 200:
                        data = response.json()
                        articles = data.get('articles', [])
                        all_articles.extend(articles)
                        self.logger.debug(f"Retrieved {len(articles)} articles for query: {query}")
                    else:
                        self.logger.warning(f"News API returned status {response.status_code} for query: {query}")
                
                except Exception as e:
                    self.logger.error(f"Error fetching news for query '{query}': {str(e)}")
                    continue
            
            # Remove duplicates based on URL
            unique_articles = []
            seen_urls = set()
            for article in all_articles:
                url = article.get('url', '')
                if url and url not in seen_urls:
                    unique_articles.append(article)
                    seen_urls.add(url)
            
            self.logger.info(f"Retrieved {len(unique_articles)} unique articles from {len(news_queries)} queries")
            return unique_articles
            
        except Exception as e:
            self.logger.error(f"Error getting market news: {str(e)}")
            return []
    
    def _extract_stock_symbols(self, articles: List[Dict]) -> Dict[str, Dict]:
        """Extract stock symbols from news articles with context."""
        symbol_mentions = {}
        
        # Regex patterns for finding stock symbols
        ticker_patterns = [
            r'\\b([A-Z]{1,5})\\s+(?:stock|shares|ticker)',  # "AAPL stock"
            r'\\(([A-Z]{1,5})\\)',  # "(AAPL)"
            r'\\$([A-Z]{1,5})\\b',  # "$AAPL"
            r'ticker:\\s*([A-Z]{1,5})',  # "ticker: AAPL"
        ]
        
        for article in articles:
            title = article.get('title', '')
            description = article.get('description', '')
            content = f"{title} {description}".upper()
            
            # Look for patterns
            for pattern in ticker_patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    symbol = match.strip()
                    
                    # Filter out common false positives
                    if self._is_valid_symbol(symbol):
                        if symbol not in symbol_mentions:
                            symbol_mentions[symbol] = {
                                'mentions': 0,
                                'articles': [],
                                'contexts': []
                            }
                        
                        symbol_mentions[symbol]['mentions'] += 1
                        symbol_mentions[symbol]['articles'].append(article)
                        
                        # Extract context around the mention
                        context = self._extract_context(content, symbol)
                        symbol_mentions[symbol]['contexts'].append(context)
            
            # Also check against known symbols
            for symbol in self.known_symbols:
                if symbol in content:
                    if symbol not in symbol_mentions:
                        symbol_mentions[symbol] = {
                            'mentions': 0,
                            'articles': [],
                            'contexts': []
                        }
                    
                    symbol_mentions[symbol]['mentions'] += 1
                    symbol_mentions[symbol]['articles'].append(article)
                    
                    context = self._extract_context(content, symbol)
                    symbol_mentions[symbol]['contexts'].append(context)
        
        self.logger.info(f"Extracted {len(symbol_mentions)} unique symbols from articles")
        return symbol_mentions
    
    def _is_valid_symbol(self, symbol: str) -> bool:
        """Check if a symbol is likely to be a valid stock ticker."""
        # Basic validation rules
        if len(symbol) < 1 or len(symbol) > 5:
            return False
        
        # Skip common false positives
        false_positives = {
            'THE', 'AND', 'FOR', 'ARE', 'BUT', 'NOT', 'YOU', 'ALL', 'CAN', 'HAD', 'HER', 'WAS', 'ONE', 'OUR', 'OUT', 'DAY', 'GET', 'HAS', 'HIM', 'HIS', 'HOW', 'ITS', 'NEW', 'NOW', 'OLD', 'SEE', 'TWO', 'WHO', 'BOY', 'DID', 'ITS', 'LET', 'PUT', 'SAY', 'SHE', 'TOO', 'USE'
        }
        
        if symbol in false_positives:
            return False
        
        # Must be all letters
        if not symbol.isalpha():
            return False
        
        return True
    
    def _extract_context(self, content: str, symbol: str) -> str:
        """Extract context around a symbol mention."""
        try:
            index = content.find(symbol)
            if index == -1:
                return ""
            
            # Get 50 characters before and after
            start = max(0, index - 50)
            end = min(len(content), index + len(symbol) + 50)
            
            return content[start:end].strip()
        except:
            return ""
    
    def _score_discoveries(self, db: Session, symbol_mentions: Dict, articles: List[Dict]) -> List[MarketScanResult]:
        """Score discovered symbols based on various factors."""
        scored_discoveries = []
        
        for symbol, data in symbol_mentions.items():
            try:
                # Skip if already being tracked
                if symbol in self.data_service.tracked_stocks:
                    self.logger.debug(f"Skipping {symbol} - already tracked")
                    continue
                
                # Verify it's a real stock
                stock_info = self._verify_stock_symbol(symbol)
                if not stock_info:
                    continue
                
                # Calculate trending score
                trending_score = self._calculate_trending_score(data, articles)
                
                # Get quick sentiment
                sentiment_score = self._get_quick_sentiment(symbol, data['contexts'])
                
                # Create discovery result
                discovery = MarketScanResult(
                    symbol=symbol,
                    company_name=stock_info['company_name'],
                    current_price=stock_info['current_price'],
                    sentiment_score=sentiment_score,
                    news_count=data['mentions'],
                    trending_score=trending_score,
                    reason_found=self._create_discovery_reason(data),
                    discovered_at=datetime.now()
                )
                
                scored_discoveries.append(discovery)
                
            except Exception as e:
                self.logger.error(f"Error scoring discovery for {symbol}: {str(e)}")
                continue
        
        return scored_discoveries
    
    def _verify_stock_symbol(self, symbol: str) -> Optional[Dict]:
        """Verify that a symbol represents a real, tradeable stock."""
        try:
            stock = yf.Ticker(symbol)
            info = stock.info
            
            # Check if it has basic stock information
            if 'longName' in info or 'shortName' in info:
                hist = stock.history(period="1d")
                if not hist.empty:
                    return {
                        'company_name': info.get('longName', info.get('shortName', symbol)),
                        'current_price': float(hist['Close'].iloc[-1])
                    }
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Symbol {symbol} verification failed: {str(e)}")
            return None
    
    def _calculate_trending_score(self, data: Dict, all_articles: List[Dict]) -> float:
        """Calculate how trending a stock is based on mentions and recency."""
        mentions = data['mentions']
        articles = data['articles']
        
        # Base score from mention frequency
        mention_score = min(mentions / 10.0, 1.0)  # Normalize to 0-1
        
        # Recency boost - recent articles get higher scores
        recency_score = 0.0
        now = datetime.now()
        
        for article in articles:
            try:
                pub_date_str = article.get('publishedAt', '')
                if pub_date_str:
                    pub_date = datetime.fromisoformat(pub_date_str.replace('Z', '+00:00'))
                    hours_ago = (now - pub_date.replace(tzinfo=None)).total_seconds() / 3600
                    
                    # More recent = higher score
                    if hours_ago < 1:
                        recency_score += 1.0
                    elif hours_ago < 6:
                        recency_score += 0.7
                    elif hours_ago < 24:
                        recency_score += 0.3
            except:
                continue
        
        recency_score = min(recency_score / len(articles), 1.0) if articles else 0.0
        
        # Combine scores
        trending_score = (mention_score * 0.6) + (recency_score * 0.4)
        
        return trending_score
    
    def _get_quick_sentiment(self, symbol: str, contexts: List[str]) -> float:
        """Get a quick sentiment analysis from the contexts."""
        try:
            # Combine all contexts
            combined_text = " ".join(contexts)
            
            if not combined_text.strip():
                return 0.0
            
            # Use sentiment service to analyze
            return self.sentiment_service.analyze_text_sentiment(combined_text)
            
        except Exception as e:
            self.logger.error(f"Error getting quick sentiment for {symbol}: {str(e)}")
            return 0.0
    
    def _create_discovery_reason(self, data: Dict) -> str:
        """Create a human-readable reason for why this stock was discovered."""
        mentions = data['mentions']
        
        if mentions == 1:
            return "Mentioned in recent market news"
        elif mentions < 5:
            return f"Mentioned {mentions} times in recent articles"
        else:
            return f"Trending with {mentions} mentions in recent news"
    
    def auto_discover_and_analyze(self, db: Session, min_trending_score: float = 0.5) -> Dict:
        """Automatically discover trending stocks and add them for analysis."""
        try:
            self.logger.info("Starting auto-discovery and analysis...")
            
            # Scan for trending stocks
            discoveries = self.scan_trending_stocks(db, limit=20)
            
            # Filter by trending score
            high_potential = [d for d in discoveries if d.trending_score >= min_trending_score]
            
            added_stocks = []
            analysis_results = []
            
            for discovery in high_potential:
                try:
                    # Add to tracking
                    add_result = self.data_service.add_stock(db, discovery.symbol)
                    if "error" not in add_result:
                        added_stocks.append(discovery.symbol)
                        
                        # Perform sentiment analysis
                        sentiment_result = self.sentiment_service.analyze_stock_sentiment(db, discovery.symbol)
                        analysis_results.append(sentiment_result)
                        
                        self.logger.info(f"Auto-discovered and analyzed {discovery.symbol}: sentiment {sentiment_result.overall_sentiment:.3f}")
                    
                except Exception as e:
                    self.logger.error(f"Error adding/analyzing {discovery.symbol}: {str(e)}")
                    continue
            
            result = {
                "discoveries": discoveries,
                "added_stocks": added_stocks,
                "analysis_results": analysis_results,
                "summary": f"Discovered {len(discoveries)} trending stocks, added {len(added_stocks)} for analysis"
            }
            
            self.logger.info(f"Auto-discovery completed: {len(added_stocks)} stocks added for analysis")
            return result
            
        except Exception as e:
            self.logger.error(f"Error in auto-discovery: {str(e)}")
            return {"error": str(e)}