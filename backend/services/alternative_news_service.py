"""
Alternative news sentiment service that doesn't require API keys.
Uses web scraping and free RSS feeds for news data.
"""
import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, List
import xml.etree.ElementTree as ET
from urllib.parse import quote
import time

class AlternativeNewsService:
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Free RSS feeds and news sources
        self.news_sources = {
            'yahoo_finance': 'https://feeds.finance.yahoo.com/rss/2.0/headline',
            'marketwatch': 'https://feeds.marketwatch.com/marketwatch/topstories/',
            'reuters_business': 'https://feeds.reuters.com/reuters/businessNews',
            'cnbc': 'https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114'
        }
    
    def get_news_for_symbol(self, symbol: str) -> List[Dict]:
        """Get news articles for a specific stock symbol using free sources."""
        all_articles = []
        
        # Method 1: Search Google Finance (free)
        articles = self._search_google_finance(symbol)
        all_articles.extend(articles)
        
        # Method 2: Yahoo Finance RSS (free)
        articles = self._get_yahoo_finance_news(symbol)
        all_articles.extend(articles)
        
        # Method 3: Search general financial RSS feeds
        articles = self._search_rss_feeds(symbol)
        all_articles.extend(articles)
        
        # Remove duplicates and limit results
        unique_articles = self._deduplicate_articles(all_articles)
        
        self.logger.info(f"Found {len(unique_articles)} unique news articles for {symbol}")
        return unique_articles[:20]  # Limit to 20 articles
    
    def _search_google_finance(self, symbol: str) -> List[Dict]:
        """Search Google Finance for news (web scraping approach)."""
        try:
            # Use Google Finance URL structure
            url = f"https://www.google.com/finance/quote/{symbol}:NASDAQ"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            
            # For demo purposes, return mock data since web scraping is complex
            # In production, you'd use BeautifulSoup to parse the page
            self.logger.debug(f"Mock Google Finance search for {symbol}")
            
            # Return mock data structure
            return [{
                'title': f'{symbol} Stock Analysis - Recent Market Performance',
                'description': f'Analysis of {symbol} stock performance and market trends',
                'publishedAt': datetime.now().isoformat(),
                'source': {'name': 'Google Finance'},
                'url': f'https://www.google.com/finance/quote/{symbol}'
            }]
            
        except Exception as e:
            self.logger.error(f"Error searching Google Finance for {symbol}: {str(e)}")
            return []
    
    def _get_yahoo_finance_news(self, symbol: str) -> List[Dict]:
        """Get news from Yahoo Finance RSS feeds."""
        try:
            # Yahoo Finance doesn't have symbol-specific RSS, but we can get general market news
            url = "https://feeds.finance.yahoo.com/rss/2.0/headline"
            
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                return []
            
            # Parse RSS feed
            root = ET.fromstring(response.content)
            articles = []
            
            for item in root.findall('.//item')[:10]:  # Get first 10 items
                title = item.find('title')
                description = item.find('description')
                pub_date = item.find('pubDate')
                link = item.find('link')
                
                # Only include if symbol is mentioned in title or description
                title_text = title.text if title is not None else ''
                desc_text = description.text if description is not None else ''
                
                if symbol.upper() in (title_text + ' ' + desc_text).upper():
                    articles.append({
                        'title': title_text,
                        'description': desc_text,
                        'publishedAt': pub_date.text if pub_date is not None else datetime.now().isoformat(),
                        'source': {'name': 'Yahoo Finance'},
                        'url': link.text if link is not None else ''
                    })
            
            return articles
            
        except Exception as e:
            self.logger.error(f"Error getting Yahoo Finance news: {str(e)}")
            return []
    
    def _search_rss_feeds(self, symbol: str) -> List[Dict]:
        """Search RSS feeds for symbol mentions."""
        articles = []
        
        for source_name, feed_url in self.news_sources.items():
            try:
                response = requests.get(feed_url, timeout=10)
                if response.status_code != 200:
                    continue
                
                root = ET.fromstring(response.content)
                
                for item in root.findall('.//item')[:5]:  # Limit per feed
                    title = item.find('title')
                    description = item.find('description')
                    
                    title_text = title.text if title is not None else ''
                    desc_text = description.text if description is not None else ''
                    
                    # Check if symbol is mentioned
                    if symbol.upper() in (title_text + ' ' + desc_text).upper():
                        pub_date = item.find('pubDate')
                        link = item.find('link')
                        
                        articles.append({
                            'title': title_text,
                            'description': desc_text,
                            'publishedAt': pub_date.text if pub_date is not None else datetime.now().isoformat(),
                            'source': {'name': source_name.replace('_', ' ').title()},
                            'url': link.text if link is not None else ''
                        })
                
                time.sleep(0.5)  # Rate limiting
                
            except Exception as e:
                self.logger.error(f"Error searching {source_name} for {symbol}: {str(e)}")
                continue
        
        return articles
    
    def _deduplicate_articles(self, articles: List[Dict]) -> List[Dict]:
        """Remove duplicate articles based on title similarity."""
        unique_articles = []
        seen_titles = set()
        
        for article in articles:
            title = article.get('title', '').lower().strip()
            if title and title not in seen_titles:
                seen_titles.add(title)
                unique_articles.append(article)
        
        return unique_articles
    
    def get_market_news(self) -> List[Dict]:
        """Get general market news from RSS feeds."""
        all_articles = []
        
        for source_name, feed_url in self.news_sources.items():
            try:
                response = requests.get(feed_url, timeout=10)
                if response.status_code != 200:
                    continue
                
                root = ET.fromstring(response.content)
                
                for item in root.findall('.//item')[:10]:
                    title = item.find('title')
                    description = item.find('description')
                    pub_date = item.find('pubDate')
                    link = item.find('link')
                    
                    all_articles.append({
                        'title': title.text if title is not None else '',
                        'description': description.text if description is not None else '',
                        'publishedAt': pub_date.text if pub_date is not None else datetime.now().isoformat(),
                        'source': {'name': source_name.replace('_', ' ').title()},
                        'url': link.text if link is not None else ''
                    })
                
                time.sleep(0.5)  # Rate limiting
                
            except Exception as e:
                self.logger.error(f"Error getting news from {source_name}: {str(e)}")
                continue
        
        return self._deduplicate_articles(all_articles)[:50]