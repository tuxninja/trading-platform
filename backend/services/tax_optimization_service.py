"""
Tax Optimization Service for trading strategies.
Handles short-term vs long-term capital gains, wash sale rules, and tax loss harvesting.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from models import Trade
from services.data_service import DataService
from config import config

class TaxOptimizationService:
    """Service for tax-aware trading optimization."""
    
    def __init__(self):
        self.data_service = DataService()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Tax rates (can be configured per user)
        self.short_term_capital_gains_rate = 0.37  # 37% for high earners
        self.long_term_capital_gains_rate = 0.20   # 20% for high earners
        self.wash_sale_days = 30  # 30 days before and after
        
    def calculate_tax_impact(self, db: Session, trade: Trade, close_price: float) -> Dict:
        """Calculate tax impact of closing a trade."""
        try:
            # Calculate holding period
            holding_days = (datetime.now() - trade.timestamp).days
            is_long_term = holding_days >= 365
            
            # Calculate P&L
            if trade.trade_type == "BUY":
                profit_loss = (close_price - trade.price) * trade.quantity
            else:
                profit_loss = (trade.price - close_price) * trade.quantity
            
            # Determine tax rate
            tax_rate = self.long_term_capital_gains_rate if is_long_term else self.short_term_capital_gains_rate
            
            # Calculate tax liability
            tax_liability = profit_loss * tax_rate if profit_loss > 0 else 0
            after_tax_profit = profit_loss - tax_liability
            
            # Check for wash sale risk
            wash_sale_risk = self._check_wash_sale_risk(db, trade, profit_loss < 0)
            
            return {
                "profit_loss": profit_loss,
                "holding_days": holding_days,
                "is_long_term": is_long_term,
                "tax_rate": tax_rate,
                "tax_liability": tax_liability,
                "after_tax_profit": after_tax_profit,
                "wash_sale_risk": wash_sale_risk,
                "recommendation": self._get_tax_recommendation(
                    profit_loss, is_long_term, wash_sale_risk, holding_days
                )
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating tax impact: {str(e)}")
            return {"error": str(e)}
    
    def _check_wash_sale_risk(self, db: Session, trade: Trade, is_loss: bool) -> Dict:
        """Check if closing this trade would trigger wash sale rules."""
        if not is_loss:
            return {"risk": False, "reason": "Not a loss trade"}
        
        # Look for same symbol trades within wash sale window
        start_date = trade.timestamp - timedelta(days=self.wash_sale_days)
        end_date = datetime.now() + timedelta(days=self.wash_sale_days)
        
        similar_trades = db.query(Trade).filter(
            and_(
                Trade.symbol == trade.symbol,
                Trade.timestamp.between(start_date, end_date),
                Trade.id != trade.id,
                Trade.trade_type == "BUY"  # Look for purchases that could trigger wash sale
            )
        ).all()
        
        if similar_trades:
            return {
                "risk": True,
                "reason": f"Found {len(similar_trades)} similar trades within wash sale window",
                "affected_trades": [t.id for t in similar_trades]
            }
        
        return {"risk": False, "reason": "No wash sale risk detected"}
    
    def _get_tax_recommendation(self, profit_loss: float, is_long_term: bool, 
                               wash_sale_risk: Dict, holding_days: int) -> str:
        """Get tax-optimized trading recommendation."""
        if profit_loss > 0:  # Profitable trade
            if is_long_term:
                return "CLOSE - Long-term gains (20% tax rate)"
            elif holding_days >= 330:  # Close to long-term
                return "HOLD - Consider waiting for long-term status (35 days)"
            else:
                return f"CLOSE - Short-term gains (37% tax rate), {365 - holding_days} days to long-term"
        else:  # Loss trade
            if wash_sale_risk["risk"]:
                return f"CAUTION - Wash sale risk: {wash_sale_risk['reason']}"
            else:
                return "CLOSE - Harvest tax loss (deductible)"
    
    def optimize_trade_timing(self, db: Session) -> Dict:
        """Analyze all open positions for tax-optimized timing."""
        try:
            open_trades = db.query(Trade).filter(Trade.status == "OPEN").all()
            
            recommendations = []
            for trade in open_trades:
                # Get current market price
                market_data = self.data_service.get_market_data(trade.symbol, days=1)
                current_price = market_data.get('current_price', trade.price)
                
                # Calculate tax impact
                tax_analysis = self.calculate_tax_impact(db, trade, current_price)
                
                if 'error' not in tax_analysis:
                    recommendations.append({
                        "trade_id": trade.id,
                        "symbol": trade.symbol,
                        "current_price": current_price,
                        "entry_price": trade.price,
                        "holding_days": tax_analysis["holding_days"],
                        "is_long_term": tax_analysis["is_long_term"],
                        "profit_loss": tax_analysis["profit_loss"],
                        "after_tax_profit": tax_analysis["after_tax_profit"],
                        "tax_savings_potential": self._calculate_tax_savings(tax_analysis),
                        "recommendation": tax_analysis["recommendation"],
                        "wash_sale_risk": tax_analysis["wash_sale_risk"]["risk"]
                    })
            
            # Sort by tax efficiency
            recommendations.sort(key=lambda x: x["after_tax_profit"], reverse=True)
            
            return {
                "total_positions": len(open_trades),
                "long_term_positions": len([r for r in recommendations if r["is_long_term"]]),
                "short_term_positions": len([r for r in recommendations if not r["is_long_term"]]),
                "positions_near_long_term": len([r for r in recommendations if 330 <= r["holding_days"] < 365]),
                "wash_sale_risks": len([r for r in recommendations if r["wash_sale_risk"]]),
                "recommendations": recommendations[:10]  # Top 10 recommendations
            }
            
        except Exception as e:
            self.logger.error(f"Error optimizing trade timing: {str(e)}")
            return {"error": str(e)}
    
    def _calculate_tax_savings(self, tax_analysis: Dict) -> float:
        """Calculate potential tax savings by waiting for long-term status."""
        if tax_analysis["is_long_term"] or tax_analysis["profit_loss"] <= 0:
            return 0
        
        short_term_tax = tax_analysis["profit_loss"] * self.short_term_capital_gains_rate
        long_term_tax = tax_analysis["profit_loss"] * self.long_term_capital_gains_rate
        
        return short_term_tax - long_term_tax
    
    def suggest_tax_loss_harvesting(self, db: Session) -> Dict:
        """Suggest trades to close for tax loss harvesting."""
        try:
            open_trades = db.query(Trade).filter(Trade.status == "OPEN").all()
            
            loss_opportunities = []
            for trade in open_trades:
                # Get current market price
                market_data = self.data_service.get_market_data(trade.symbol, days=1)
                current_price = market_data.get('current_price', trade.price)
                
                # Calculate P&L
                if trade.trade_type == "BUY":
                    profit_loss = (current_price - trade.price) * trade.quantity
                else:
                    profit_loss = (trade.price - current_price) * trade.quantity
                
                # Only consider loss positions
                if profit_loss < -50:  # Minimum $50 loss threshold
                    tax_analysis = self.calculate_tax_impact(db, trade, current_price)
                    
                    if 'error' not in tax_analysis and not tax_analysis["wash_sale_risk"]["risk"]:
                        tax_benefit = abs(profit_loss) * self.short_term_capital_gains_rate
                        
                        loss_opportunities.append({
                            "trade_id": trade.id,
                            "symbol": trade.symbol,
                            "current_loss": profit_loss,
                            "tax_benefit": tax_benefit,
                            "holding_days": tax_analysis["holding_days"],
                            "wash_sale_safe": True,
                            "recommendation": f"Harvest ${abs(profit_loss):.2f} loss for ${tax_benefit:.2f} tax benefit"
                        })
            
            # Sort by tax benefit
            loss_opportunities.sort(key=lambda x: x["tax_benefit"], reverse=True)
            
            total_tax_benefit = sum(op["tax_benefit"] for op in loss_opportunities)
            
            return {
                "total_loss_opportunities": len(loss_opportunities),
                "total_harvestable_losses": sum(abs(op["current_loss"]) for op in loss_opportunities),
                "total_tax_benefit": total_tax_benefit,
                "opportunities": loss_opportunities[:5]  # Top 5 opportunities
            }
            
        except Exception as e:
            self.logger.error(f"Error suggesting tax loss harvesting: {str(e)}")
            return {"error": str(e)}
    
    def calculate_annual_tax_report(self, db: Session, year: int = None) -> Dict:
        """Generate annual tax report for closed trades."""
        try:
            if year is None:
                year = datetime.now().year
            
            start_date = datetime(year, 1, 1)
            end_date = datetime(year + 1, 1, 1)
            
            closed_trades = db.query(Trade).filter(
                and_(
                    Trade.status == "CLOSED",
                    Trade.close_timestamp.between(start_date, end_date)
                )
            ).all()
            
            short_term_gains = 0
            long_term_gains = 0
            wash_sales = 0
            
            trade_details = []
            
            for trade in closed_trades:
                holding_days = (trade.close_timestamp - trade.timestamp).days
                is_long_term = holding_days >= 365
                
                if is_long_term:
                    long_term_gains += trade.profit_loss or 0
                else:
                    short_term_gains += trade.profit_loss or 0
                
                # Check for wash sales (simplified)
                wash_sale_flag = self._check_wash_sale_risk(db, trade, (trade.profit_loss or 0) < 0)
                if wash_sale_flag["risk"]:
                    wash_sales += abs(trade.profit_loss or 0)
                
                trade_details.append({
                    "symbol": trade.symbol,
                    "buy_date": trade.timestamp.strftime("%Y-%m-%d"),
                    "sell_date": trade.close_timestamp.strftime("%Y-%m-%d"),
                    "holding_days": holding_days,
                    "is_long_term": is_long_term,
                    "proceeds": trade.close_price * trade.quantity if trade.close_price else 0,
                    "cost_basis": trade.price * trade.quantity,
                    "gain_loss": trade.profit_loss or 0,
                    "wash_sale": wash_sale_flag["risk"]
                })
            
            # Calculate tax liability
            short_term_tax = max(0, short_term_gains) * self.short_term_capital_gains_rate
            long_term_tax = max(0, long_term_gains) * self.long_term_capital_gains_rate
            total_tax = short_term_tax + long_term_tax
            
            return {
                "year": year,
                "total_trades": len(closed_trades),
                "short_term_gains": short_term_gains,
                "long_term_gains": long_term_gains,
                "total_gains": short_term_gains + long_term_gains,
                "short_term_tax": short_term_tax,
                "long_term_tax": long_term_tax,
                "total_tax_liability": total_tax,
                "after_tax_profit": (short_term_gains + long_term_gains) - total_tax,
                "wash_sales_amount": wash_sales,
                "effective_tax_rate": total_tax / max(1, short_term_gains + long_term_gains) * 100,
                "trade_details": trade_details
            }
            
        except Exception as e:
            self.logger.error(f"Error generating tax report: {str(e)}")
            return {"error": str(e)}

# Global tax optimization service instance
tax_optimization_service = TaxOptimizationService()