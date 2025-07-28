"""
Adaptive Learning Service - Makes the trading platform smarter over time.

This service analyzes trade performance to:
1. Extract patterns from successful and unsuccessful trades
2. Adjust strategy parameters based on performance feedback
3. Discover insights about market conditions and timing
4. Continuously optimize trading decisions

The system learns from every trade to improve future performance.
"""

import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc
from collections import defaultdict
import json

from models import (
    Trade, SentimentData, StockData, Strategy, StrategyPerformance,
    TradePattern, StrategyLearning, LearningInsight, PerformanceBaseline
)
from services.data_service import DataService
from config import config


class AdaptiveLearningService:
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.data_service = DataService()
        
        # Learning parameters
        self.min_trades_for_pattern = 5  # Minimum trades to establish a pattern
        self.min_sample_size_for_adjustment = 10  # Minimum trades before adjusting parameters
        self.confidence_threshold_for_changes = 0.7  # Confidence required to make changes
        self.max_parameter_adjustment = 0.2  # Maximum % change per adjustment
        
    def analyze_and_learn(self, db: Session) -> Dict[str, Any]:
        """Main learning function - analyzes all trade data and updates strategy"""
        try:
            self.logger.info("Starting adaptive learning analysis...")
            
            results = {
                "patterns_discovered": 0,
                "parameters_adjusted": 0,
                "insights_generated": 0,
                "baselines_updated": 0,
                "recommendations": []
            }
            
            # Step 1: Extract patterns from recent trades
            patterns = self._extract_trade_patterns(db)
            results["patterns_discovered"] = len(patterns)
            
            # Step 2: Analyze strategy performance and adjust parameters
            adjustments = self._analyze_and_adjust_strategy_parameters(db)
            results["parameters_adjusted"] = len(adjustments)
            
            # Step 3: Generate high-level insights
            insights = self._generate_market_insights(db)
            results["insights_generated"] = len(insights)
            
            # Step 4: Update performance baselines
            baselines = self._update_performance_baselines(db)
            results["baselines_updated"] = len(baselines)
            
            # Step 5: Generate recommendations
            recommendations = self._generate_learning_recommendations(db)
            results["recommendations"] = recommendations
            
            self.logger.info(f"Learning analysis complete: {results}")
            return results
            
        except Exception as e:
            self.logger.error(f"Error in adaptive learning analysis: {str(e)}")
            raise
    
    def _extract_trade_patterns(self, db: Session) -> List[Dict]:
        """Extract patterns from successful and unsuccessful trades"""
        try:
            # Get recent closed trades with sufficient data
            recent_trades = db.query(Trade).filter(
                Trade.status == "CLOSED",
                Trade.profit_loss.isnot(None),
                Trade.timestamp >= datetime.now() - timedelta(days=90)
            ).all()
            
            if len(recent_trades) < self.min_trades_for_pattern:
                self.logger.info(f"Not enough trades ({len(recent_trades)}) to extract patterns")
                return []
            
            patterns_created = []
            
            for trade in recent_trades:
                try:
                    # Get market context at trade time
                    market_context = self._get_market_context_for_trade(db, trade)
                    
                    # Determine if this was a successful trade
                    is_successful = trade.profit_loss > 0
                    pattern_type = "SUCCESSFUL_ENTRY" if is_successful else "FAILED_ENTRY"
                    
                    # Create or update pattern
                    pattern = self._create_or_update_pattern(db, trade, market_context, pattern_type)
                    if pattern:
                        patterns_created.append(pattern)
                        
                except Exception as e:
                    self.logger.warning(f"Error processing trade {trade.id} for patterns: {str(e)}")
                    continue
            
            self.logger.info(f"Extracted {len(patterns_created)} trade patterns")
            return patterns_created
            
        except Exception as e:
            self.logger.error(f"Error extracting trade patterns: {str(e)}")
            return []
    
    def _get_market_context_for_trade(self, db: Session, trade: Trade) -> Dict:
        """Get market context (sentiment, price trends, etc.) for a trade"""
        try:
            # Get sentiment data near trade time
            sentiment = db.query(SentimentData).filter(
                SentimentData.symbol == trade.symbol,
                SentimentData.timestamp <= trade.timestamp,
                SentimentData.timestamp >= trade.timestamp - timedelta(hours=24)
            ).order_by(desc(SentimentData.timestamp)).first()
            
            # Get price trend data
            market_data = self.data_service.get_market_data(trade.symbol, days=30)
            
            # Calculate price trends
            price_change_1d = 0
            price_change_5d = 0
            price_change_30d = 0
            
            if "historical_data" in market_data and market_data["historical_data"]:
                hist_data = market_data["historical_data"]
                if len(hist_data) >= 1:
                    price_change_1d = ((trade.price - hist_data[-1]["close"]) / hist_data[-1]["close"]) * 100
                if len(hist_data) >= 5:
                    price_change_5d = ((trade.price - hist_data[-5]["close"]) / hist_data[-5]["close"]) * 100
                if len(hist_data) >= 30:
                    price_change_30d = ((trade.price - hist_data[0]["close"]) / hist_data[0]["close"]) * 100
            
            # Determine trends
            price_trend = "SIDEWAYS"
            if abs(price_change_5d) > 5:
                price_trend = "UP" if price_change_5d > 0 else "DOWN"
            
            # Volume analysis (simplified)
            volume_trend = "NORMAL"  # Would implement based on historical volume data
            
            # Volatility analysis
            volatility_level = "MEDIUM"
            if abs(price_change_1d) > 5:
                volatility_level = "HIGH"
            elif abs(price_change_1d) < 1:
                volatility_level = "LOW"
            
            return {
                "sentiment_score": sentiment.overall_sentiment if sentiment else 0.0,
                "sentiment_strength": abs(sentiment.overall_sentiment) if sentiment else 0.0,
                "news_count": sentiment.news_count if sentiment else 0,
                "social_count": sentiment.social_count if sentiment else 0,
                "price_trend": price_trend,
                "volume_trend": volume_trend,
                "volatility_level": volatility_level,
                "price_change_1d": price_change_1d,
                "price_change_5d": price_change_5d,
                "price_change_30d": price_change_30d,
                "sector": self._get_symbol_sector(trade.symbol),
                "market_cap_range": self._get_market_cap_range(trade.symbol)
            }
            
        except Exception as e:
            self.logger.warning(f"Error getting market context for trade {trade.id}: {str(e)}")
            return {}
    
    def _create_or_update_pattern(self, db: Session, trade: Trade, market_context: Dict, pattern_type: str) -> Optional[Dict]:
        """Create or update a trade pattern in the database"""
        try:
            # Calculate hold duration
            hold_duration = 0
            if trade.close_timestamp and trade.timestamp:
                hold_duration = (trade.close_timestamp - trade.timestamp).days
            
            # Look for existing similar pattern
            existing_pattern = db.query(TradePattern).filter(
                TradePattern.symbol == trade.symbol,
                TradePattern.pattern_type == pattern_type,
                TradePattern.sentiment_score.between(
                    market_context.get("sentiment_score", 0) - 0.1,
                    market_context.get("sentiment_score", 0) + 0.1
                ),
                TradePattern.price_trend == market_context.get("price_trend", "SIDEWAYS"),
                TradePattern.volatility_level == market_context.get("volatility_level", "MEDIUM")
            ).first()
            
            if existing_pattern:
                # Update existing pattern
                existing_pattern.occurrence_count += 1
                
                # Update success rate
                if pattern_type.startswith("SUCCESSFUL"):
                    existing_pattern.success_rate = (
                        existing_pattern.success_rate * (existing_pattern.occurrence_count - 1) + 1
                    ) / existing_pattern.occurrence_count
                else:
                    existing_pattern.success_rate = (
                        existing_pattern.success_rate * (existing_pattern.occurrence_count - 1)
                    ) / existing_pattern.occurrence_count
                
                # Update average profit/loss
                existing_pattern.profit_loss = (
                    existing_pattern.profit_loss * (existing_pattern.occurrence_count - 1) + trade.profit_loss
                ) / existing_pattern.occurrence_count
                
                existing_pattern.updated_at = datetime.now()
                
                db.commit()
                return {"action": "updated", "pattern_id": existing_pattern.id}
                
            else:
                # Create new pattern
                new_pattern = TradePattern(
                    pattern_type=pattern_type,
                    symbol=trade.symbol,
                    sector=market_context.get("sector", "Unknown"),
                    market_cap_range=market_context.get("market_cap_range", "UNKNOWN"),
                    volatility_level=market_context.get("volatility_level", "MEDIUM"),
                    
                    sentiment_score=market_context.get("sentiment_score", 0.0),
                    sentiment_strength=market_context.get("sentiment_strength", 0.0),
                    news_count=market_context.get("news_count", 0),
                    social_count=market_context.get("social_count", 0),
                    
                    price_trend=market_context.get("price_trend", "SIDEWAYS"),
                    volume_trend=market_context.get("volume_trend", "NORMAL"),
                    price_change_1d=market_context.get("price_change_1d", 0.0),
                    price_change_5d=market_context.get("price_change_5d", 0.0),
                    price_change_30d=market_context.get("price_change_30d", 0.0),
                    
                    profit_loss=trade.profit_loss,
                    profit_loss_percent=(trade.profit_loss / trade.total_value) * 100 if trade.total_value > 0 else 0,
                    hold_duration_days=hold_duration,
                    
                    confidence_threshold=config.CONFIDENCE_THRESHOLD,
                    position_size_percent=config.MAX_POSITION_SIZE * 100,
                    buy_sentiment_threshold=config.BUY_SENTIMENT_THRESHOLD,
                    sell_sentiment_threshold=config.SELL_SENTIMENT_THRESHOLD,
                    
                    success_rate=1.0 if pattern_type.startswith("SUCCESSFUL") else 0.0
                )
                
                db.add(new_pattern)
                db.commit()
                db.refresh(new_pattern)
                
                return {"action": "created", "pattern_id": new_pattern.id}
                
        except Exception as e:
            self.logger.error(f"Error creating/updating pattern: {str(e)}")
            db.rollback()
            return None
    
    def _analyze_and_adjust_strategy_parameters(self, db: Session) -> List[Dict]:
        """Analyze performance and adjust strategy parameters for better results"""
        try:
            adjustments_made = []
            
            # Get recent performance data
            recent_trades = db.query(Trade).filter(
                Trade.status == "CLOSED",
                Trade.profit_loss.isnot(None),
                Trade.timestamp >= datetime.now() - timedelta(days=30)
            ).all()
            
            if len(recent_trades) < self.min_sample_size_for_adjustment:
                self.logger.info(f"Not enough recent trades ({len(recent_trades)}) for parameter adjustment")
                return adjustments_made
            
            # Calculate current performance metrics
            current_metrics = self._calculate_performance_metrics(recent_trades)
            
            # Get baseline performance for comparison
            baseline = self._get_or_create_baseline(db, "OVERALL")
            
            # Analyze specific areas for improvement
            potential_adjustments = []
            
            # 1. Confidence threshold adjustment
            if current_metrics["win_rate"] < baseline.win_rate * 0.9:  # Win rate dropped significantly
                confidence_adjustment = self._analyze_confidence_threshold(db, recent_trades)
                if confidence_adjustment:
                    potential_adjustments.append(confidence_adjustment)
            
            # 2. Sentiment threshold adjustment
            sentiment_adjustment = self._analyze_sentiment_thresholds(db, recent_trades)
            if sentiment_adjustment:
                potential_adjustments.append(sentiment_adjustment)
            
            # 3. Position sizing adjustment
            position_adjustment = self._analyze_position_sizing(db, recent_trades, current_metrics)
            if position_adjustment:
                potential_adjustments.append(position_adjustment)
            
            # Apply adjustments that meet confidence criteria
            for adjustment in potential_adjustments:
                if adjustment["confidence"] >= self.confidence_threshold_for_changes:
                    applied_adjustment = self._apply_parameter_adjustment(db, adjustment)
                    if applied_adjustment:
                        adjustments_made.append(applied_adjustment)
            
            return adjustments_made
            
        except Exception as e:
            self.logger.error(f"Error analyzing strategy parameters: {str(e)}")
            return []
    
    def _analyze_confidence_threshold(self, db: Session, recent_trades: List[Trade]) -> Optional[Dict]:
        """Analyze if confidence threshold should be adjusted"""
        try:
            # Group trades by confidence level (approximate from sentiment strength)
            high_confidence_trades = []
            low_confidence_trades = []
            
            for trade in recent_trades:
                # Get sentiment for this trade
                sentiment = db.query(SentimentData).filter(
                    SentimentData.symbol == trade.symbol,
                    SentimentData.timestamp <= trade.timestamp,
                    SentimentData.timestamp >= trade.timestamp - timedelta(hours=24)
                ).order_by(desc(SentimentData.timestamp)).first()
                
                if sentiment:
                    sentiment_strength = abs(sentiment.overall_sentiment)
                    if sentiment_strength > 0.6:  # High confidence proxy
                        high_confidence_trades.append(trade)
                    else:
                        low_confidence_trades.append(trade)
            
            if len(high_confidence_trades) < 3 or len(low_confidence_trades) < 3:
                return None
            
            # Calculate performance for each group
            high_conf_win_rate = sum(1 for t in high_confidence_trades if t.profit_loss > 0) / len(high_confidence_trades)
            low_conf_win_rate = sum(1 for t in low_confidence_trades if t.profit_loss > 0) / len(low_confidence_trades)
            
            high_conf_avg_profit = sum(t.profit_loss for t in high_confidence_trades) / len(high_confidence_trades)
            low_conf_avg_profit = sum(t.profit_loss for t in low_confidence_trades) / len(low_confidence_trades)
            
            # Determine if adjustment is needed
            if high_conf_win_rate > low_conf_win_rate + 0.1 and high_conf_avg_profit > low_conf_avg_profit:
                # High confidence trades are performing better - increase threshold
                new_threshold = min(config.CONFIDENCE_THRESHOLD * 1.1, 0.9)
                return {
                    "parameter": "confidence_threshold",
                    "current_value": config.CONFIDENCE_THRESHOLD,
                    "new_value": new_threshold,
                    "reason": f"High confidence trades show {high_conf_win_rate:.1%} win rate vs {low_conf_win_rate:.1%} for low confidence",
                    "confidence": 0.8,
                    "expected_improvement": (high_conf_win_rate - low_conf_win_rate) * 0.5
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error analyzing confidence threshold: {str(e)}")
            return None
    
    def _analyze_sentiment_thresholds(self, db: Session, recent_trades: List[Trade]) -> Optional[Dict]:
        """Analyze if sentiment thresholds should be adjusted"""
        try:
            buy_trades = [t for t in recent_trades if t.trade_type == "BUY"]
            
            if len(buy_trades) < 5:
                return None
            
            # Analyze performance by sentiment ranges
            sentiment_performance = defaultdict(list)
            
            for trade in buy_trades:
                sentiment = db.query(SentimentData).filter(
                    SentimentData.symbol == trade.symbol,
                    SentimentData.timestamp <= trade.timestamp,
                    SentimentData.timestamp >= trade.timestamp - timedelta(hours=24)
                ).order_by(desc(SentimentData.timestamp)).first()
                
                if sentiment:
                    score = sentiment.overall_sentiment
                    if score > 0.4:
                        sentiment_performance["very_positive"].append(trade.profit_loss)
                    elif score > 0.2:
                        sentiment_performance["positive"].append(trade.profit_loss)
                    elif score > 0:
                        sentiment_performance["slightly_positive"].append(trade.profit_loss)
            
            # Find the optimal sentiment threshold
            best_threshold = config.BUY_SENTIMENT_THRESHOLD
            best_performance = 0
            
            for threshold_name, profits in sentiment_performance.items():
                if len(profits) >= 3:
                    avg_profit = sum(profits) / len(profits)
                    win_rate = sum(1 for p in profits if p > 0) / len(profits)
                    performance_score = avg_profit * win_rate
                    
                    if performance_score > best_performance:
                        best_performance = performance_score
                        if threshold_name == "very_positive":
                            best_threshold = 0.4
                        elif threshold_name == "positive":
                            best_threshold = 0.2
            
            # If we found a better threshold, suggest adjustment
            if abs(best_threshold - config.BUY_SENTIMENT_THRESHOLD) > 0.05:
                return {
                    "parameter": "buy_sentiment_threshold",
                    "current_value": config.BUY_SENTIMENT_THRESHOLD,
                    "new_value": best_threshold,
                    "reason": f"Sentiment threshold {best_threshold} shows better performance",
                    "confidence": 0.7,
                    "expected_improvement": 0.1
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error analyzing sentiment thresholds: {str(e)}")
            return None
    
    def _analyze_position_sizing(self, db: Session, recent_trades: List[Trade], current_metrics: Dict) -> Optional[Dict]:
        """Analyze if position sizing should be adjusted"""
        try:
            # Analyze position sizes and their outcomes
            large_positions = [t for t in recent_trades if t.total_value > 4000]  # > 4% of 100k
            small_positions = [t for t in recent_trades if t.total_value < 2000]  # < 2% of 100k
            
            if len(large_positions) < 3 or len(small_positions) < 3:
                return None
            
            large_pos_win_rate = sum(1 for t in large_positions if t.profit_loss > 0) / len(large_positions)
            small_pos_win_rate = sum(1 for t in small_positions if t.profit_loss > 0) / len(small_positions)
            
            large_pos_avg_profit = sum(t.profit_loss for t in large_positions) / len(large_positions)
            small_pos_avg_profit = sum(t.profit_loss for t in small_positions) / len(small_positions)
            
            # Risk-adjusted performance
            large_pos_risk_adj = large_pos_avg_profit / (sum(t.total_value for t in large_positions) / len(large_positions))
            small_pos_risk_adj = small_pos_avg_profit / (sum(t.total_value for t in small_positions) / len(small_positions))
            
            # Determine optimal position size
            if small_pos_risk_adj > large_pos_risk_adj * 1.2 and small_pos_win_rate > large_pos_win_rate:
                # Smaller positions are more efficient
                new_position_size = max(config.MAX_POSITION_SIZE * 0.8, 0.02)  # Reduce but not below 2%
                return {
                    "parameter": "max_position_size",
                    "current_value": config.MAX_POSITION_SIZE,
                    "new_value": new_position_size,
                    "reason": f"Smaller positions show better risk-adjusted returns ({small_pos_risk_adj:.3f} vs {large_pos_risk_adj:.3f})",
                    "confidence": 0.75,
                    "expected_improvement": 0.05
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error analyzing position sizing: {str(e)}")
            return None
    
    def _apply_parameter_adjustment(self, db: Session, adjustment: Dict) -> Optional[Dict]:
        """Apply a parameter adjustment and record it"""
        try:
            # Record the adjustment
            learning_record = StrategyLearning(
                strategy_id=1,  # Default strategy
                parameter_name=adjustment["parameter"],
                old_value=adjustment["current_value"],
                new_value=adjustment["new_value"],
                adjustment_reason=adjustment["reason"],
                confidence_level=adjustment["confidence"]
            )
            
            db.add(learning_record)
            db.commit()
            
            # Apply the adjustment to config (in production, this would update persistent config)
            if adjustment["parameter"] == "confidence_threshold":
                config.CONFIDENCE_THRESHOLD = adjustment["new_value"]
            elif adjustment["parameter"] == "buy_sentiment_threshold":
                config.BUY_SENTIMENT_THRESHOLD = adjustment["new_value"]
            elif adjustment["parameter"] == "max_position_size":
                config.MAX_POSITION_SIZE = adjustment["new_value"]
            
            self.logger.info(f"Applied parameter adjustment: {adjustment['parameter']} = {adjustment['new_value']}")
            
            return {
                "parameter": adjustment["parameter"],
                "old_value": adjustment["current_value"],
                "new_value": adjustment["new_value"],
                "reason": adjustment["reason"],
                "learning_record_id": learning_record.id
            }
            
        except Exception as e:
            self.logger.error(f"Error applying parameter adjustment: {str(e)}")
            db.rollback()
            return None
    
    def _generate_market_insights(self, db: Session) -> List[Dict]:
        """Generate high-level market insights from patterns"""
        try:
            insights_created = []
            
            # Get successful patterns to analyze
            successful_patterns = db.query(TradePattern).filter(
                TradePattern.pattern_type.like("SUCCESSFUL%"),
                TradePattern.occurrence_count >= 3,
                TradePattern.success_rate >= 0.6
            ).all()
            
            # Group patterns by various dimensions
            sector_insights = self._analyze_sector_patterns(successful_patterns)
            timing_insights = self._analyze_timing_patterns(successful_patterns)
            sentiment_insights = self._analyze_sentiment_patterns(successful_patterns)
            
            # Create insight records
            for insight_data in sector_insights + timing_insights + sentiment_insights:
                insight = LearningInsight(
                    insight_type=insight_data["type"],
                    title=insight_data["title"],
                    description=insight_data["description"],
                    symbols_affected=insight_data.get("symbols", []),
                    sectors_affected=insight_data.get("sectors", []),
                    confidence_score=insight_data["confidence"],
                    impact_magnitude=insight_data["impact"],
                    supporting_trades_count=insight_data["supporting_trades"]
                )
                
                db.add(insight)
                insights_created.append(insight_data)
            
            db.commit()
            
            self.logger.info(f"Generated {len(insights_created)} market insights")
            return insights_created
            
        except Exception as e:
            self.logger.error(f"Error generating market insights: {str(e)}")
            return []
    
    def _analyze_sector_patterns(self, patterns: List[TradePattern]) -> List[Dict]:
        """Analyze patterns by sector"""
        sector_performance = defaultdict(list)
        
        for pattern in patterns:
            if pattern.sector and pattern.sector != "Unknown":
                sector_performance[pattern.sector].append({
                    "success_rate": pattern.success_rate,
                    "avg_profit": pattern.profit_loss,
                    "count": pattern.occurrence_count
                })
        
        insights = []
        for sector, data in sector_performance.items():
            if len(data) >= 2:  # At least 2 patterns in this sector
                avg_success_rate = sum(d["success_rate"] for d in data) / len(data)
                avg_profit = sum(d["avg_profit"] for d in data) / len(data)
                total_trades = sum(d["count"] for d in data)
                
                if avg_success_rate > 0.7 and avg_profit > 0:
                    insights.append({
                        "type": "SECTOR_TREND",
                        "title": f"{sector} Sector Shows Strong Performance",
                        "description": f"{sector} sector demonstrates {avg_success_rate:.1%} success rate with average profit of ${avg_profit:.2f}",
                        "sectors": [sector],
                        "confidence": min(avg_success_rate, 0.9),
                        "impact": avg_profit / 100.0,  # Normalize impact
                        "supporting_trades": total_trades
                    })
        
        return insights
    
    def _analyze_timing_patterns(self, patterns: List[TradePattern]) -> List[Dict]:
        """Analyze patterns by timing"""
        # This is a simplified version - in practice, you'd analyze day of week, time of day, etc.
        insights = []
        
        # Analyze hold duration patterns
        short_term = [p for p in patterns if p.hold_duration_days <= 3]
        long_term = [p for p in patterns if p.hold_duration_days >= 10]
        
        if len(short_term) >= 3 and len(long_term) >= 3:
            short_success = sum(p.success_rate for p in short_term) / len(short_term)
            long_success = sum(p.success_rate for p in long_term) / len(long_term)
            
            if short_success > long_success + 0.1:
                insights.append({
                    "type": "TIMING_PATTERN",
                    "title": "Short-term Holds Outperform Long-term",
                    "description": f"Positions held 3 days or less show {short_success:.1%} success vs {long_success:.1%} for longer holds",
                    "confidence": 0.7,
                    "impact": short_success - long_success,
                    "supporting_trades": len(short_term) + len(long_term)
                })
        
        return insights
    
    def _analyze_sentiment_patterns(self, patterns: List[TradePattern]) -> List[Dict]:
        """Analyze patterns by sentiment levels"""
        insights = []
        
        high_sentiment = [p for p in patterns if p.sentiment_strength > 0.6]
        medium_sentiment = [p for p in patterns if 0.3 < p.sentiment_strength <= 0.6]
        
        if len(high_sentiment) >= 3 and len(medium_sentiment) >= 3:
            high_success = sum(p.success_rate for p in high_sentiment) / len(high_sentiment)
            medium_success = sum(p.success_rate for p in medium_sentiment) / len(medium_sentiment)
            
            if high_success > medium_success + 0.15:
                insights.append({
                    "type": "MARKET_CONDITION",
                    "title": "Strong Sentiment Signals More Reliable",
                    "description": f"High sentiment strength (>0.6) shows {high_success:.1%} success vs {medium_success:.1%} for medium sentiment",
                    "confidence": 0.8,
                    "impact": high_success - medium_success,
                    "supporting_trades": len(high_sentiment) + len(medium_sentiment)
                })
        
        return insights
    
    def _update_performance_baselines(self, db: Session) -> List[Dict]:
        """Update performance baselines for comparison"""
        try:
            baselines_updated = []
            
            # Update overall baseline
            overall_baseline = self._get_or_create_baseline(db, "OVERALL")
            
            # Get recent performance
            recent_trades = db.query(Trade).filter(
                Trade.status == "CLOSED",
                Trade.profit_loss.isnot(None),
                Trade.timestamp >= datetime.now() - timedelta(days=30)
            ).all()
            
            if len(recent_trades) >= 10:
                metrics = self._calculate_performance_metrics(recent_trades)
                
                # Update baseline with recent performance
                overall_baseline.win_rate = metrics["win_rate"]
                overall_baseline.avg_profit = metrics["avg_profit"]
                overall_baseline.avg_loss = metrics["avg_loss"]
                overall_baseline.profit_factor = metrics["profit_factor"]
                overall_baseline.total_trades = len(recent_trades)
                overall_baseline.period_start = recent_trades[0].timestamp
                overall_baseline.period_end = recent_trades[-1].timestamp
                
                db.commit()
                baselines_updated.append({"type": "OVERALL", "baseline_id": overall_baseline.id})
            
            return baselines_updated
            
        except Exception as e:
            self.logger.error(f"Error updating performance baselines: {str(e)}")
            return []
    
    def _get_or_create_baseline(self, db: Session, baseline_type: str) -> PerformanceBaseline:
        """Get existing baseline or create a new one"""
        baseline = db.query(PerformanceBaseline).filter(
            PerformanceBaseline.baseline_type == baseline_type,
            PerformanceBaseline.is_current == True
        ).first()
        
        if not baseline:
            baseline = PerformanceBaseline(
                baseline_type=baseline_type,
                win_rate=0.5,
                avg_profit=0.0,
                avg_loss=0.0,
                profit_factor=1.0,
                total_trades=0,
                period_start=datetime.now() - timedelta(days=30),
                period_end=datetime.now()
            )
            db.add(baseline)
            db.commit()
            db.refresh(baseline)
        
        return baseline
    
    def _calculate_performance_metrics(self, trades: List[Trade]) -> Dict:
        """Calculate performance metrics for a list of trades"""
        if not trades:
            return {"win_rate": 0, "avg_profit": 0, "avg_loss": 0, "profit_factor": 1}
        
        winning_trades = [t for t in trades if t.profit_loss > 0]
        losing_trades = [t for t in trades if t.profit_loss < 0]
        
        win_rate = len(winning_trades) / len(trades)
        avg_profit = sum(t.profit_loss for t in winning_trades) / len(winning_trades) if winning_trades else 0
        avg_loss = sum(t.profit_loss for t in losing_trades) / len(losing_trades) if losing_trades else 0
        
        total_profit = sum(t.profit_loss for t in winning_trades)
        total_loss = abs(sum(t.profit_loss for t in losing_trades))
        profit_factor = total_profit / total_loss if total_loss > 0 else float('inf')
        
        return {
            "win_rate": win_rate,
            "avg_profit": avg_profit,
            "avg_loss": avg_loss,
            "profit_factor": profit_factor
        }
    
    def _generate_learning_recommendations(self, db: Session) -> List[str]:
        """Generate actionable recommendations based on learning analysis"""
        recommendations = []
        
        # Get recent insights
        recent_insights = db.query(LearningInsight).filter(
            LearningInsight.discovered_at >= datetime.now() - timedelta(days=7),
            LearningInsight.confidence_score >= 0.7
        ).all()
        
        for insight in recent_insights:
            if insight.insight_type == "SECTOR_TREND":
                recommendations.append(f"Consider increasing allocation to {insight.sectors_affected[0]} sector based on strong performance patterns")
            elif insight.insight_type == "TIMING_PATTERN":
                recommendations.append(f"Optimize holding periods: {insight.description}")
            elif insight.insight_type == "MARKET_CONDITION":
                recommendations.append(f"Sentiment strategy: {insight.description}")
        
        # Add parameter adjustment recommendations
        recent_adjustments = db.query(StrategyLearning).filter(
            StrategyLearning.adjustment_date >= datetime.now() - timedelta(days=7)
        ).all()
        
        for adj in recent_adjustments:
            recommendations.append(f"Monitor impact of {adj.parameter_name} adjustment from {adj.old_value} to {adj.new_value}")
        
        return recommendations[:5]  # Limit to top 5 recommendations
    
    def _get_symbol_sector(self, symbol: str) -> str:
        """Get sector for a symbol (simplified mapping)"""
        tech_symbols = ["AAPL", "GOOGL", "MSFT", "META", "NVDA", "AMD", "INTC", "CRM", "ORCL", "ADBE"]
        if symbol in tech_symbols:
            return "Technology"
        return "Other"
    
    def _get_market_cap_range(self, symbol: str) -> str:
        """Get market cap range for a symbol (simplified)"""
        large_cap = ["AAPL", "GOOGL", "MSFT", "META", "NVDA", "AMZN"]
        if symbol in large_cap:
            return "LARGE"
        return "MID"

    def get_learning_dashboard_data(self, db: Session) -> Dict[str, Any]:
        """Get comprehensive learning data for dashboard display"""
        try:
            # Recent patterns - ensure we're getting accurate count
            recent_patterns_count = db.query(TradePattern).filter(
                TradePattern.created_at >= datetime.now() - timedelta(days=30)
            ).count()
            
            # Total patterns ever discovered for verification
            total_patterns_count = db.query(TradePattern).count()
            
            # Parameter adjustments
            recent_adjustments = db.query(StrategyLearning).filter(
                StrategyLearning.adjustment_date >= datetime.now() - timedelta(days=30)
            ).all()
            
            # Active insights
            active_insights = db.query(LearningInsight).filter(
                LearningInsight.is_active == True,
                LearningInsight.confidence_score >= 0.7
            ).all()
            
            # Performance improvement
            current_baseline = self._get_or_create_baseline(db, "OVERALL")
            
            # Log for debugging data consistency
            self.logger.info(f"Dashboard data: {recent_patterns_count} recent patterns, {total_patterns_count} total patterns")
            
            return {
                "patterns_discovered_30d": recent_patterns_count,
                "total_patterns_ever": total_patterns_count,
                "parameter_adjustments_30d": len(recent_adjustments),
                "active_insights": len(active_insights),
                "current_win_rate": current_baseline.win_rate,
                "current_profit_factor": current_baseline.profit_factor,
                "learning_system_active": total_patterns_count > 0 or len(recent_adjustments) > 0,
                "data_source": "database",
                "recent_adjustments": [
                    {
                        "parameter": adj.parameter_name,
                        "old_value": adj.old_value,
                        "new_value": adj.new_value,
                        "reason": adj.adjustment_reason,
                        "date": adj.adjustment_date.strftime("%Y-%m-%d")
                    } for adj in recent_adjustments[-5:]
                ],
                "top_insights": [
                    {
                        "title": insight.title,
                        "description": insight.description,
                        "confidence": insight.confidence_score,
                        "impact": insight.impact_magnitude
                    } for insight in active_insights[:3]
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Error getting learning dashboard data: {str(e)}")
            return {
                "patterns_discovered_30d": 0,
                "total_patterns_ever": 0,
                "parameter_adjustments_30d": 0,
                "active_insights": 0,
                "current_win_rate": 0.0,
                "current_profit_factor": 0.0,
                "learning_system_active": False,
                "data_source": "error_fallback",
                "recent_adjustments": [],
                "top_insights": []
            }