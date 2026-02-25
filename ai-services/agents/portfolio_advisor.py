# ai-services/agents/portfolio_advisor.py
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import asyncio
from dataclasses import dataclass
import json

@dataclass
class PortfolioPosition:
    symbol: str
    asset_type: str
    quantity: float
    average_price: float
    current_price: float
    market_value: float
    unrealized_pnl: float
    allocation: float

class PortfolioAdvisorAgent:
    def __init__(self, user_id: str, user_context: Dict[str, Any]):
        self.user_id = user_id
        self.user_context = user_context
        self.portfolio = []
        self.benchmarks = {
            "SPY": {"return": 0.12, "risk": 0.15},  # S&P 500
            "AGG": {"return": 0.04, "risk": 0.04},  # Aggregate Bond
            "GLD": {"return": 0.06, "risk": 0.12},  # Gold
        }
        
    async def analyze_portfolio(self) -> Dict[str, Any]:
        """Comprehensive portfolio analysis"""
        
        # Load portfolio data
        await self._load_portfolio_data()
        
        # Run all analyses
        analyses = await asyncio.gather(
            self._calculate_diversification(),
            self._calculate_risk_metrics(),
            self._calculate_performance(),
            self._detect_concentration(),
            self._check_rebalancing_needs()
        )
        
        # Combine results
        result = {
            "portfolio_summary": self._get_portfolio_summary(),
            "diversification_analysis": analyses[0],
            "risk_analysis": analyses[1],
            "performance_analysis": analyses[2],
            "concentration_analysis": analyses[3],
            "rebalancing_recommendations": analyses[4],
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": self.user_id
        }
        
        return result
    
    async def _load_portfolio_data(self):
        """Load portfolio data from database"""
        # Mock data - in production, query from database
        self.portfolio = [
            PortfolioPosition(
                symbol="AAPL",
                asset_type="STOCK",
                quantity=100,
                average_price=150.0,
                current_price=180.0,
                market_value=18000.0,
                unrealized_pnl=3000.0,
                allocation=0.30
            ),
            PortfolioPosition(
                symbol="MSFT",
                asset_type="STOCK",
                quantity=50,
                average_price=250.0,
                current_price=350.0,
                market_value=17500.0,
                unrealized_pnl=5000.0,
                allocation=0.29
            ),
            PortfolioPosition(
                symbol="BND",
                asset_type="BOND",
                quantity=200,
                average_price=80.0,
                current_price=82.0,
                market_value=16400.0,
                unrealized_pnl=400.0,
                allocation=0.27
            ),
            PortfolioPosition(
                symbol="GLD",
                asset_type="COMMODITY",
                quantity=50,
                average_price=170.0,
                current_price=185.0,
                market_value=9250.0,
                unrealized_pnl=750.0,
                allocation=0.14
            )
        ]
    
    async def _calculate_diversification(self) -> Dict[str, Any]:
        """Calculate portfolio diversification metrics"""
        
        # Calculate by asset class
        asset_classes = {}
        for position in self.portfolio:
            asset_class = position.asset_type
            asset_classes[asset_class] = asset_classes.get(asset_class, 0) + position.allocation
        
        # Calculate Herfindahl-Hirschman Index (HHI) for concentration
        hhi = sum(allocation ** 2 for allocation in asset_classes.values())
        
        # Calculate effective number of holdings
        effective_holdings = 1 / hhi if hhi > 0 else 0
        
        return {
            "asset_allocation": asset_classes,
            "hhi_index": round(hhi, 4),
            "effective_holdings": round(effective_holdings, 2),
            "diversification_score": round((1 - hhi) * 100, 1),
            "recommendation": self._get_diversification_recommendation(hhi)
        }
    
    async def _calculate_risk_metrics(self) -> Dict[str, Any]:
        """Calculate portfolio risk metrics"""
        
        total_value = sum(pos.market_value for pos in self.portfolio)
        
        # Calculate weighted metrics
        portfolio_beta = 0.0
        portfolio_volatility = 0.0
        
        for position in self.portfolio:
            weight = position.market_value / total_value
            # Simplified - in production, use actual beta and volatility
            if position.asset_type == "STOCK":
                beta = 1.2  # Assume tech stocks have higher beta
                volatility = 0.25
            elif position.asset_type == "BOND":
                beta = 0.2
                volatility = 0.05
            else:
                beta = 0.5
                volatility = 0.15
            
            portfolio_beta += weight * beta
            portfolio_volatility += weight * volatility
        
        # Calculate Value at Risk (VaR) - simplified
        var_95 = total_value * portfolio_volatility * 1.645  # 95% confidence
        
        # Calculate Sharpe ratio (assuming risk-free rate of 2%)
        expected_return = portfolio_beta * 0.08  # Market return assumption
        sharpe_ratio = (expected_return - 0.02) / portfolio_volatility
        
        return {
            "portfolio_beta": round(portfolio_beta, 3),
            "portfolio_volatility": round(portfolio_volatility, 3),
            "value_at_risk_95": round(var_95, 2),
            "sharpe_ratio": round(sharpe_ratio, 3),
            "risk_level": self._get_risk_level(portfolio_volatility),
            "stress_test_results": await self._run_stress_tests()
        }
    
    async def _calculate_performance(self) -> Dict[str, Any]:
        """Calculate portfolio performance metrics"""
        
        total_cost = sum(pos.quantity * pos.average_price for pos in self.portfolio)
        total_value = sum(pos.market_value for pos in self.portfolio)
        total_pnl = sum(pos.unrealized_pnl for pos in self.portfolio)
        
        # Calculate returns
        total_return = (total_value - total_cost) / total_cost if total_cost > 0 else 0
        annualized_return = ((1 + total_return) ** (1/5)) - 1  # Assume 5-year holding
        
        # Compare to benchmarks
        benchmark_comparison = []
        for benchmark, metrics in self.benchmarks.items():
            excess_return = annualized_return - metrics["return"]
            benchmark_comparison.append({
                "benchmark": benchmark,
                "benchmark_return": metrics["return"],
                "portfolio_return": annualized_return,
                "excess_return": excess_return,
                "outperformance": excess_return > 0
            })
        
        return {
            "total_value": round(total_value, 2),
            "total_pnl": round(total_pnl, 2),
            "total_return_pct": round(total_return * 100, 2),
            "annualized_return_pct": round(annualized_return * 100, 2),
            "benchmark_comparison": benchmark_comparison,
            "performance_rating": self._get_performance_rating(annualized_return)
        }
    
    async def _detect_concentration(self) -> Dict[str, Any]:
        """Detect concentration risks"""
        
        concentration_risks = []
        
        # Check individual position concentration
        for position in self.portfolio:
            if position.allocation > 0.20:  # >20% in single position
                concentration_risks.append({
                    "type": "single_position",
                    "symbol": position.symbol,
                    "allocation": round(position.allocation * 100, 1),
                    "threshold": 20,
                    "risk_level": "high" if position.allocation > 0.30 else "medium",
                    "recommendation": "Consider reducing position size"
                })
        
        # Check sector concentration (simplified)
        tech_allocation = sum(pos.allocation for pos in self.portfolio 
                            if pos.symbol in ["AAPL", "MSFT", "GOOGL"])
        
        if tech_allocation > 0.50:  # >50% in tech
            concentration_risks.append({
                "type": "sector_concentration",
                "sector": "Technology",
                "allocation": round(tech_allocation * 100, 1),
                "threshold": 50,
                "risk_level": "high",
                "recommendation": "Diversify into other sectors"
            })
        
        return {
            "concentration_risks": concentration_risks,
            "has_concentration_risk": len(concentration_risks) > 0,
            "overall_concentration_score": len(concentration_risks) * 10
        }
    
    async def _check_rebalancing_needs(self) -> Dict[str, Any]:
        """Check if portfolio needs rebalancing"""
        
        target_allocation = self._get_target_allocation()
        current_allocation = await self._calculate_diversification()
        
        deviations = []
        rebalancing_trades = []
        
        for asset_class, target_pct in target_allocation.items():
            current_pct = current_allocation["asset_allocation"].get(asset_class, 0)
            deviation = current_pct - target_pct
            
            if abs(deviation) > 0.05:  # 5% deviation threshold
                deviations.append({
                    "asset_class": asset_class,
                    "current": round(current_pct * 100, 1),
                    "target": round(target_pct * 100, 1),
                    "deviation": round(deviation * 100, 1)
                })
                
                # Calculate rebalancing trade
                total_value = sum(pos.market_value for pos in self.portfolio)
                trade_amount = total_value * deviation
                
                if deviation > 0:
                    action = "SELL"
                else:
                    action = "BUY"
                
                rebalancing_trades.append({
                    "action": action,
                    "asset_class": asset_class,
                    "amount": abs(round(trade_amount, 2)),
                    "priority": "high" if abs(deviation) > 0.10 else "medium"
                })
        
        return {
            "needs_rebalancing": len(deviations) > 0,
            "deviations": deviations,
            "rebalancing_trades": rebalancing_trades,
            "target_allocation": target_allocation,
            "recommended_rebalance_frequency": "Quarterly"
        }
    
    def _get_target_allocation(self) -> Dict[str, float]:
        """Get target allocation based on risk profile"""
        risk_profile = self.user_context.get("risk_tolerance", "MODERATE").upper()
        
        if risk_profile == "CONSERVATIVE":
            return {"STOCK": 0.40, "BOND": 0.50, "CASH": 0.10}
        elif risk_profile == "AGGRESSIVE":
            return {"STOCK": 0.80, "BOND": 0.15, "ALTERNATIVE": 0.05}
        else:  # MODERATE
            return {"STOCK": 0.60, "BOND": 0.35, "CASH": 0.05}
    
    def _get_portfolio_summary(self) -> Dict[str, Any]:
        """Get portfolio summary"""
        total_value = sum(pos.market_value for pos in self.portfolio)
        total_cost = sum(pos.quantity * pos.average_price for pos in self.portfolio)
        total_pnl = total_value - total_cost
        
        return {
            "total_positions": len(self.portfolio),
            "total_value": round(total_value, 2),
            "total_cost": round(total_cost, 2),
            "total_pnl": round(total_pnl, 2),
            "pnl_percentage": round((total_pnl / total_cost) * 100, 2) if total_cost > 0 else 0,
            "largest_position": max(self.portfolio, key=lambda x: x.market_value).symbol,
            "best_performer": max(self.portfolio, key=lambda x: x.unrealized_pnl / (x.quantity * x.average_price)).symbol
        }
    
    def _get_diversification_recommendation(self, hhi: float) -> str:
        """Get diversification recommendation based on HHI"""
        if hhi > 0.25:
            return "Highly concentrated portfolio. Consider diversifying across more asset classes."
        elif hhi > 0.15:
            return "Moderate concentration. Monitor position sizes."
        else:
            return "Well-diversified portfolio."
    
    def _get_risk_level(self, volatility: float) -> str:
        """Get risk level based on volatility"""
        if volatility > 0.20:
            return "HIGH"
        elif volatility > 0.10:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _get_performance_rating(self, annualized_return: float) -> str:
        """Get performance rating"""
        if annualized_return > 0.10:
            return "EXCELLENT"
        elif annualized_return > 0.05:
            return "GOOD"
        elif annualized_return > 0:
            return "FAIR"
        else:
            return "POOR"
    
    async def _run_stress_tests(self) -> Dict[str, Any]:
        """Run portfolio stress tests"""
        
        total_value = sum(pos.market_value for pos in self.portfolio)
        
        # Market crash scenario (-20% for stocks, -5% for bonds)
        crash_loss = 0
        for position in self.portfolio:
            if position.asset_type == "STOCK":
                crash_loss += position.market_value * 0.20
            elif position.asset_type == "BOND":
                crash_loss += position.market_value * 0.05
        
        # Interest rate rise scenario
        rate_rise_loss = 0
        for position in self.portfolio:
            if position.asset_type == "BOND":
                rate_rise_loss += position.market_value * 0.10
        
        # Liquidity crisis scenario
        liquidity_loss = 0
        liquid_assets = sum(pos.market_value for pos in self.portfolio 
                          if pos.asset_type in ["CASH", "STOCK"])
        liquidity_ratio = liquid_assets / total_value if total_value > 0 else 0
        
        return {
            "market_crash_impact": round(crash_loss, 2),
            "market_crash_pct": round((crash_loss / total_value) * 100, 2),
            "interest_rate_rise_impact": round(rate_rise_loss, 2),
            "liquidity_ratio": round(liquidity_ratio * 100, 2),
            "liquidity_rating": "GOOD" if liquidity_ratio > 0.20 else "POOR"
        }