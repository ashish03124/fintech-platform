# ai-services/llm/prompt_templates.py
from typing import Dict, Any, List
from string import Template

class PromptTemplates:
    """Collection of prompt templates for financial advisory"""
    
    @staticmethod
    def get_financial_advice_template() -> Template:
        """Template for general financial advice"""
        return Template("""
        You are a certified financial advisor with expertise in:
        - Investment management
        - Financial planning
        - Risk management
        - Regulatory compliance
        
        **User Query:** $query
        
        **User Context:**
        - Risk Tolerance: $risk_tolerance
        - Investment Horizon: $investment_horizon
        - Financial Goals: $financial_goals
        - Portfolio Value: $portfolio_value
        
        **Relevant Information from Knowledge Base:**
        $context
        
        **Guidelines:**
        1. Provide accurate, personalized advice based on user context
        2. Reference specific regulations when applicable
        3. Include clear risk disclosures
        4. Consider current market conditions if relevant
        5. Provide actionable recommendations
        6. Be transparent about limitations
        
        **Response Structure:**
        1. Summary of the query
        2. Key considerations (regulatory, risk, market)
        3. Personalized recommendations
        4. Action steps
        5. Risk factors and disclosures
        
        **Financial Advisor Response:**
        """)
    
    @staticmethod
    def get_portfolio_analysis_template() -> Template:
        """Template for portfolio analysis"""
        return Template("""
        You are a portfolio management expert analyzing the following portfolio:
        
        **Portfolio Data:** $portfolio_data
        
        **User Context:**
        - Risk Profile: $risk_profile
        - Investment Objectives: $investment_objectives
        - Time Horizon: $time_horizon
        
        **Market Context:** $market_context
        
        **Analysis Guidelines:**
        1. Calculate diversification score (0-100)
        2. Analyze asset allocation
        3. Assess risk-adjusted returns
        4. Identify concentration risks
        5. Compare to benchmark
        6. Provide rebalancing recommendations
        
        **Required Output Format (JSON):**
        {
            "diversification_score": number,
            "asset_allocation": {
                "stocks": percentage,
                "bonds": percentage,
                "cash": percentage,
                "alternatives": percentage
            },
            "risk_metrics": {
                "sharpe_ratio": number,
                "max_drawdown": percentage,
                "volatility": percentage
            },
            "recommendations": [
                {
                    "action": "buy/sell/hold",
                    "asset": "symbol",
                    "reason": "string",
                    "priority": "high/medium/low"
                }
            ],
            "rebalancing_suggestions": "string"
        }
        
        **Analysis:**
        """)
    
    @staticmethod
    def get_risk_assessment_template() -> Template:
        """Template for risk assessment"""
        return Template("""
        Assess the risk profile for the following user:
        
        **User Information:**
        - Age: $age
        - Income: $income
        - Net Worth: $net_worth
        - Investment Experience: $experience
        - Financial Goals: $goals
        - Time Horizon: $horizon
        
        **Transaction History (Last 30 days):**
        $transaction_history
        
        **Risk Assessment Guidelines:**
        1. Calculate risk tolerance score (1-10)
        2. Identify risk capacity vs risk tolerance
        3. Assess behavioral biases
        4. Consider life stage factors
        5. Evaluate financial stability
        
        **Risk Categories to Assess:**
        - Market Risk
        - Credit Risk
        - Liquidity Risk
        - Inflation Risk
        - Longevity Risk
        
        **Required Output:**
        {
            "risk_tolerance_score": number,
            "risk_profile": "conservative/moderate/aggressive",
            "risk_capacity": "low/medium/high",
            "key_risks": [
                {
                    "risk_type": "string",
                    "exposure_level": "low/medium/high",
                    "mitigation_suggestions": "string"
                }
            ],
            "recommended_asset_allocation": {
                "conservative": percentages,
                "moderate": percentages,
                "aggressive": percentages
            }
        }
        
        **Risk Assessment:**
        """)
    
    @staticmethod
    def get_compliance_check_template() -> Template:
        """Template for compliance checking"""
        return Template("""
        Check the following financial recommendation for regulatory compliance:
        
        **Recommendation:** $recommendation
        
        **User Information:**
        - Jurisdiction: $jurisdiction
        - Investor Type: $investor_type (retail/accredited/institutional)
        - Account Type: $account_type
        
        **Relevant Regulations:**
        $regulations
        
        **Compliance Checklist:**
        1. Suitability (FINRA 2111, MiFID II)
        2. Best Execution (MiFID II, Reg NMS)
        3. Conflicts of Interest
        4. Disclosure Requirements
        5. Anti-Money Laundering (AML)
        6. Data Protection (GDPR, CCPA)
        7. Market Abuse Regulations
        
        **Required Output:**
        {
            "is_compliant": boolean,
            "compliance_score": percentage,
            "violations": [
                {
                    "regulation": "string",
                    "article": "string",
                    "description": "string",
                    "severity": "low/medium/high"
                }
            ],
            "required_disclosures": [
                "string"
            ],
            "suggested_amendments": "string"
        }
        
        **Compliance Analysis:**
        """)
    
    @staticmethod
    def get_transaction_analysis_template() -> Template:
        """Template for transaction pattern analysis"""
        return Template("""
        Analyze the following transaction patterns for anomalies:
        
        **Recent Transactions (Last 24 hours):**
        $transactions
        
        **User Baseline (Normal Behavior):**
        $baseline
        
        **Analysis Parameters:**
        - Time Window: $time_window
        - Amount Threshold: $amount_threshold
        - Frequency Threshold: $frequency_threshold
        
        **Anomaly Detection Criteria:**
        1. Unusual transaction amounts (> 3 standard deviations)
        2. High frequency in short period
        3. Transactions at unusual times
        4. Geographic anomalies
        5. Device/ip anomalies
        6. Merchant category anomalies
        
        **Required Output:**
        {
            "anomaly_score": number,
            "anomalies_detected": [
                {
                    "transaction_id": "string",
                    "anomaly_type": "amount/frequency/time/location/device",
                    "confidence": number,
                    "description": "string"
                }
            ],
            "risk_level": "low/medium/high/critical",
            "recommended_actions": [
                "string"
            ],
            "false_positive_probability": percentage
        }
        
        **Anomaly Analysis:**
        """)
    
    @staticmethod
    def get_explanation_template() -> Template:
        """Template for explaining AI decisions"""
        return Template("""
        Explain the following AI-generated financial recommendation:
        
        **Recommendation:** $recommendation
        
        **Input Data Used:**
        $input_data
        
        **Model Factors Considered:**
        $model_factors
        
        **Explanation Requirements:**
        1. Explain in simple, non-technical language
        2. Show the key factors that influenced the decision
        3. Quantify the impact of each factor
        4. Provide alternative scenarios considered
        5. Include confidence level and uncertainty
        6. Reference regulatory considerations
        
        **Audience:** $audience (client/regulator/internal)
        
        **Required Output Format:**
        {
            "summary": "Brief summary of recommendation",
            "key_factors": [
                {
                    "factor": "string",
                    "impact": "positive/negative/neutral",
                    "weight": percentage,
                    "explanation": "string"
                }
            ],
            "alternative_scenarios": [
                {
                    "scenario": "string",
                    "outcome": "string",
                    "probability": percentage,
                    "why_not_chosen": "string"
                }
            ],
            "confidence_metrics": {
                "overall_confidence": percentage,
                "data_quality_score": percentage,
                "model_confidence": percentage
            },
            "regulatory_basis": [
                "string"
            ]
        }
        
        **Explanation:**
        """)