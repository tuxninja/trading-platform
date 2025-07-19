"""
Trade recommendation service for sentiment-based trading strategies.
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_

from models import TradeRecommendation, SentimentData, StockData
from schemas import (
    TradeRecommendationResponse, 
    MarketScanResult, 
    StrategySignal,
    TradeCreate
)
from services.sentiment_service import SentimentService
from services.data_service import DataService
from services.trading_service import TradingService
from config import config
from exceptions import TradingAppException

class RecommendationService:
    def __init__(self):
        self.sentiment_service = SentimentService()
        self.data_service = DataService()
        self.trading_service = TradingService()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def generate_recommendations(self, db: Session, symbols: Optional[List[str]] = None) -> List[TradeRecommendationResponse]:
        """Generate trade recommendations based on sentiment analysis."""
        try:
            self.logger.info("Generating trade recommendations...")
            
            if symbols is None:
                # Use all tracked stocks
                symbols = self.data_service.tracked_stocks
            
            recommendations = []
            
            for symbol in symbols:
                try:
                    recommendation = self._analyze_symbol_for_recommendation(db, symbol)
                    if recommendation:
                        recommendations.append(recommendation)
                except Exception as e:
                    self.logger.error(f"Error analyzing {symbol} for recommendation: {str(e)}")
                    continue
            
            self.logger.info(f"Generated {len(recommendations)} trade recommendations")
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Error generating recommendations: {str(e)}")
            raise TradingAppException(f"Failed to generate recommendations: {str(e)}")
    
    def _analyze_symbol_for_recommendation(self, db: Session, symbol: str) -> Optional[TradeRecommendationResponse]:
        """Analyze a single symbol and create recommendation if warranted."""
        try:
            # Get latest sentiment data
            sentiment_data = self.sentiment_service.get_stock_sentiment(db, symbol)
            if not sentiment_data:
                # Generate fresh sentiment analysis
                sentiment_data = self.sentiment_service.analyze_stock_sentiment(db, symbol)
            
            # Get market data
            market_data = self.data_service.get_market_data(symbol, days=5)
            if "error" in market_data:
                self.logger.warning(f"Could not get market data for {symbol}")
                return None
            
            current_price = market_data["current_price"]
            sentiment_score = sentiment_data.overall_sentiment
            
            # Determine action based on sentiment thresholds
            action = self._determine_action(sentiment_score, symbol)
            if action == "HOLD":
                return None  # Don't create recommendations for HOLD actions
            
            # Calculate confidence and risk level
            confidence = self._calculate_confidence(sentiment_score, sentiment_data)
            risk_level = self._assess_risk_level(confidence, sentiment_score, market_data)
            
            # Calculate recommended quantity and value
            recommended_quantity, recommended_value = self._calculate_position_size(
                action, current_price, confidence, symbol
            )
            
            if recommended_quantity <= 0:
                return None
            
            # Create reasoning and news summary
            reasoning = self._create_reasoning(sentiment_score, sentiment_data, market_data, action)
            news_summary = self._create_news_summary(symbol, sentiment_data)
            
            # Create recommendation record
            recommendation = TradeRecommendation(
                symbol=symbol,
                action=action,
                confidence=confidence,
                sentiment_score=sentiment_score,
                current_price=current_price,
                recommended_quantity=recommended_quantity,
                recommended_value=recommended_value,
                reasoning=reasoning,
                risk_level=risk_level,
                news_summary=news_summary,
                expires_at=datetime.now() + timedelta(hours=4)  # Recommendations expire in 4 hours
            )
            
            db.add(recommendation)
            db.commit()
            db.refresh(recommendation)
            
            self.logger.info(f"Created {action} recommendation for {symbol}: {recommended_quantity} shares at ${current_price:.2f}")
            return TradeRecommendationResponse.from_orm(recommendation)
            
        except Exception as e:
            self.logger.error(f"Error analyzing {symbol}: {str(e)}")
            db.rollback()
            return None
    
    def _determine_action(self, sentiment_score: float, symbol: str) -> str:
        """Determine trading action based on sentiment score."""
        # Check current position
        current_position = self.trading_service.positions.get(symbol, 0)
        
        if sentiment_score > config.BUY_SENTIMENT_THRESHOLD and current_position == 0:
            return "BUY"
        elif sentiment_score < config.SELL_SENTIMENT_THRESHOLD and current_position > 0:
            return "SELL"
        else:
            return "HOLD"
    
    def _calculate_confidence(self, sentiment_score: float, sentiment_data) -> float:
        """Calculate confidence level for the recommendation."""
        # Base confidence on sentiment strength
        base_confidence = min(abs(sentiment_score) * 2, 1.0)
        
        # Adjust based on data quality
        total_sources = sentiment_data.news_count + sentiment_data.social_count
        if total_sources > 20:
            data_quality_multiplier = 1.0
        elif total_sources > 10:
            data_quality_multiplier = 0.9
        elif total_sources > 5:
            data_quality_multiplier = 0.8
        else:
            data_quality_multiplier = 0.6
        
        return min(base_confidence * data_quality_multiplier, 1.0)
    
    def _assess_risk_level(self, confidence: float, sentiment_score: float, market_data: Dict) -> str:
        """Assess risk level for the recommendation."""
        if confidence > 0.8 and abs(sentiment_score) > 0.5:
            return "LOW"
        elif confidence > 0.6 and abs(sentiment_score) > 0.3:
            return "MEDIUM"
        else:
            return "HIGH"
    
    def _calculate_position_size(self, action: str, current_price: float, confidence: float, symbol: str = "") -> tuple:
        """Calculate recommended position size based on confidence and risk management."""
        if action == "BUY":
            # Base position size on configuration and confidence
            base_position_value = self.trading_service.current_balance * config.MAX_POSITION_SIZE
            confidence_adjusted_value = base_position_value * confidence
            
            quantity = int(confidence_adjusted_value / current_price)
            actual_value = quantity * current_price
            
            return quantity, actual_value
        
        elif action == "SELL":
            # Sell entire position for now (could be made more sophisticated)
            current_position = self.trading_service.positions.get(symbol, 0)
            actual_value = current_position * current_price
            return current_position, actual_value
        
        return 0, 0.0
    
    def _create_reasoning(self, sentiment_score: float, sentiment_data, market_data: Dict, action: str) -> str:
        """Create human-readable reasoning for the recommendation."""
        price_change = market_data.get("price_change_pct", 0)
        
        reasoning_parts = []
        
        # Sentiment reasoning
        if sentiment_score > 0.3:
            reasoning_parts.append(f"Strong positive sentiment ({sentiment_score:.3f})")
        elif sentiment_score > 0.1:
            reasoning_parts.append(f"Moderate positive sentiment ({sentiment_score:.3f})")
        elif sentiment_score < -0.3:
            reasoning_parts.append(f"Strong negative sentiment ({sentiment_score:.3f})")
        elif sentiment_score < -0.1:
            reasoning_parts.append(f"Moderate negative sentiment ({sentiment_score:.3f})")
        
        # Data sources
        total_sources = sentiment_data.news_count + sentiment_data.social_count
        reasoning_parts.append(f"based on {total_sources} sources ({sentiment_data.news_count} news, {sentiment_data.social_count} social)")
        
        # Recent price movement
        if abs(price_change) > 5:
            direction = "up" if price_change > 0 else "down"
            reasoning_parts.append(f"Recent price movement: {price_change:.1f}% {direction}")
        
        # Action justification
        if action == "BUY":
            reasoning_parts.append("Recommend buying to capitalize on positive sentiment")
        elif action == "SELL":
            reasoning_parts.append("Recommend selling to avoid potential losses from negative sentiment")
        
        return ". ".join(reasoning_parts) + "."
    
    def _create_news_summary(self, symbol: str, sentiment_data) -> str:
        """Create a summary of news affecting the sentiment."""
        try:
            # Get recent news for summary
            news_data = self.sentiment_service.get_news_sentiment(symbol)
            articles = news_data.get("articles", [])
            
            if not articles:
                return f"Limited news coverage for {symbol}. Sentiment based on available social signals."
            
            # Create summary from top articles
            summary_parts = []
            for i, article in enumerate(articles[:3]):  # Top 3 articles
                title = article.get("title", "")
                if title:
                    summary_parts.append(f"{i+1}. {title}")
            
            if summary_parts:
                return "Recent news highlights:\n" + "\n".join(summary_parts)
            else:
                return f"Multiple news articles analyzed for {symbol} sentiment."
                
        except Exception as e:
            self.logger.error(f"Error creating news summary for {symbol}: {str(e)}")
            return f"News analysis completed for {symbol}."
    
    def get_pending_recommendations(self, db: Session) -> List[TradeRecommendationResponse]:
        """Get all pending (unexpired) recommendations."""
        try:
            recommendations = db.query(TradeRecommendation).filter(
                and_(
                    TradeRecommendation.status == "PENDING",
                    TradeRecommendation.expires_at > datetime.now()
                )
            ).order_by(desc(TradeRecommendation.created_at)).all()
            
            return [TradeRecommendationResponse.from_orm(rec) for rec in recommendations]
            
        except Exception as e:
            self.logger.error(f"Error getting pending recommendations: {str(e)}")
            return []
    
    def approve_recommendation(self, db: Session, recommendation_id: int) -> Dict:
        """Approve and execute a trade recommendation."""
        try:
            recommendation = db.query(TradeRecommendation).filter(
                TradeRecommendation.id == recommendation_id
            ).first()
            
            if not recommendation:
                raise TradingAppException(f"Recommendation {recommendation_id} not found")
            
            if recommendation.status != "PENDING":
                raise TradingAppException(f"Recommendation {recommendation_id} is not pending")
            
            if recommendation.expires_at and recommendation.expires_at < datetime.now():
                recommendation.status = "EXPIRED"
                db.commit()
                raise TradingAppException(f"Recommendation {recommendation_id} has expired")
            
            # Create and execute the trade
            trade_data = TradeCreate(
                symbol=recommendation.symbol,
                trade_type=recommendation.action,
                quantity=recommendation.recommended_quantity,
                price=recommendation.current_price,
                strategy="SENTIMENT_RECOMMENDATION"
            )
            
            executed_trade = self.trading_service.create_trade(db, trade_data)
            
            # Update recommendation status
            recommendation.status = "APPROVED"
            recommendation.processed_at = datetime.now()
            recommendation.trade_id = executed_trade.id
            
            db.commit()
            
            self.logger.info(f"Approved and executed recommendation {recommendation_id}: {recommendation.action} {recommendation.symbol}")
            
            return {
                "message": "Recommendation approved and trade executed",
                "recommendation_id": recommendation_id,
                "trade_id": executed_trade.id,
                "trade": executed_trade
            }
            
        except TradingAppException:
            raise
        except Exception as e:
            db.rollback()
            self.logger.error(f"Error approving recommendation {recommendation_id}: {str(e)}")
            raise TradingAppException(f"Failed to approve recommendation: {str(e)}")
    
    def reject_recommendation(self, db: Session, recommendation_id: int, reason: str = "") -> Dict:
        """Reject a trade recommendation."""
        try:
            recommendation = db.query(TradeRecommendation).filter(
                TradeRecommendation.id == recommendation_id
            ).first()
            
            if not recommendation:
                raise TradingAppException(f"Recommendation {recommendation_id} not found")
            
            if recommendation.status != "PENDING":
                raise TradingAppException(f"Recommendation {recommendation_id} is not pending")
            
            recommendation.status = "REJECTED"
            recommendation.processed_at = datetime.now()
            if reason:
                recommendation.reasoning += f"\n\nRejection reason: {reason}"
            
            db.commit()
            
            self.logger.info(f"Rejected recommendation {recommendation_id}: {recommendation.action} {recommendation.symbol}")
            
            return {
                "message": "Recommendation rejected",
                "recommendation_id": recommendation_id
            }
            
        except TradingAppException:
            raise
        except Exception as e:
            db.rollback()
            self.logger.error(f"Error rejecting recommendation {recommendation_id}: {str(e)}")
            raise TradingAppException(f"Failed to reject recommendation: {str(e)}")