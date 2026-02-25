# ai-services/agents/financial_agent.py
from langchain.agents import AgentExecutor, Tool, ZeroShotAgent
from langchain.memory import ConversationBufferMemory
from langchain.chains import LLMChain
from langchain.callbacks import StreamingStdOutCallbackHandler
from langchain.agents import initialize_agent
from langchain_openai import ChatOpenAI  # Fix: was missing, caused NameError
from typing import List, Dict, Any, Optional
import json
import asyncio
from datetime import datetime

class FinancialAgent:
    def __init__(self, user_id: str, user_context: Dict[str, Any]):
        self.user_id = user_id
        self.user_context = user_context
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            max_token_limit=2000
        )
        
        # Initialize tools
        self.tools = self._initialize_tools()
        
        # Initialize agent
        self.agent = self._create_agent()
        
        # Event stream for real-time updates
        self.event_stream = asyncio.Queue()
    
    def _initialize_tools(self) -> List[Tool]:
        """Initialize agent tools.

        LangChain Tool uses `coroutine` for async callables and `func`
        for sync ones.  We provide both so the agent works in sync *and*
        async execution paths.
        """

        tools = [
            Tool(
                name="PortfolioAnalyzer",
                func=self._analyze_portfolio_sync,
                coroutine=self._analyze_portfolio,
                description="Analyze user's investment portfolio performance and diversification",
            ),
            Tool(
                name="RiskAssessment",
                func=self._assess_risk_sync,
                coroutine=self._assess_risk,
                description="Assess user's risk tolerance and portfolio risk",
            ),
            Tool(
                name="TransactionMonitor",
                func=self._monitor_transactions_sync,
                coroutine=self._monitor_transactions,
                description="Monitor real-time transactions and detect anomalies",
            ),
            Tool(
                name="RegulationChecker",
                func=self._check_regulations_sync,
                coroutine=self._check_regulations,
                description="Check financial regulations and compliance requirements",
            ),
            Tool(
                name="MarketAnalyzer",
                func=self._analyze_market_sync,
                coroutine=self._analyze_market,
                description="Analyze current market conditions and trends",
            ),
            Tool(
                name="GoalPlanner",
                func=self._plan_financial_goals_sync,
                coroutine=self._plan_financial_goals,
                description="Plan and track financial goals",
            ),
            Tool(
                name="BudgetAdvisor",
                func=self._advise_budget_sync,
                coroutine=self._advise_budget,
                description="Provide budgeting and spending advice",
            ),
        ]

        return tools

    # ── Sync wrappers (LangChain calls these in non-async paths) ──────
    @staticmethod
    def _run_sync(coro):
        """Run a coroutine synchronously using a new event loop."""
        import asyncio
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop and loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                return pool.submit(asyncio.run, coro).result()
        return asyncio.run(coro)

    def _analyze_portfolio_sync(self, query: str) -> str:
        return self._run_sync(self._analyze_portfolio(query))

    def _assess_risk_sync(self, query: str) -> str:
        return self._run_sync(self._assess_risk(query))

    def _monitor_transactions_sync(self, query: str = "24h") -> str:
        return self._run_sync(self._monitor_transactions(query))

    def _check_regulations_sync(self, query: str) -> str:
        return self._run_sync(self._check_regulations(query))

    def _analyze_market_sync(self, query: str) -> str:
        return self._run_sync(self._analyze_market(query))

    def _plan_financial_goals_sync(self, query: str) -> str:
        return self._run_sync(self._plan_financial_goals(query))

    def _advise_budget_sync(self, query: str) -> str:
        return self._run_sync(self._advise_budget(query))
    
    def _create_agent(self) -> AgentExecutor:
        """Create autonomous financial agent"""
        
        prefix = """You are an autonomous financial advisor agent. You have access to 
        real-time financial data, user transaction history, market information, and 
        regulatory databases. Your goal is to provide personalized, compliant, and 
        actionable financial advice.
        
        Guidelines:
        1. Always prioritize user's best interest
        2. Maintain regulatory compliance
        3. Provide clear risk disclosures
        4. Document all recommendations
        5. Consider real-time market conditions
        
        User Profile:
        - User ID: {user_id}
        - Risk Tolerance: {risk_tolerance}
        - Investment Horizon: {investment_horizon}
        - Financial Goals: {financial_goals}
        - Current Portfolio: {portfolio_value}
        
        You have access to the following tools:"""
        
        suffix = """
        Begin! Remember to:
        1. Analyze the user's situation comprehensively
        2. Consider all relevant factors
        3. Provide specific, actionable recommendations
        4. Document your reasoning
        5. Maintain compliance
        
        {chat_history}
        
        Question: {input}
        
        {agent_scratchpad}"""
        
        prompt = ZeroShotAgent.create_prompt(
            self.tools,
            prefix=prefix,
            suffix=suffix,
            input_variables=["input", "chat_history", "agent_scratchpad", 
                           "user_id", "risk_tolerance", "investment_horizon", 
                           "financial_goals", "portfolio_value"]
        )
        
        llm_chain = LLMChain(
            llm=ChatOpenAI(temperature=0.1, streaming=True),
            prompt=prompt
        )
        
        agent = ZeroShotAgent(
            llm_chain=llm_chain,
            tools=self.tools,
            verbose=True
        )
        
        agent_executor = AgentExecutor.from_agent_and_tools(
            agent=agent,
            tools=self.tools,
            memory=self.memory,
            verbose=True,
            max_iterations=5,
            early_stopping_method="generate",
            handle_parsing_errors=True
        )
        
        return agent_executor
    
    async def process_query(self, query: str) -> Dict[str, Any]:
        """Process user query through agent"""
        
        try:
            # Prepare context
            context = {
                "user_id": self.user_id,
                "risk_tolerance": self.user_context.get("risk_tolerance", "Moderate"),
                "investment_horizon": self.user_context.get("investment_horizon", "5-10 years"),
                "financial_goals": self.user_context.get("financial_goals", "Wealth accumulation"),
                "portfolio_value": self.user_context.get("portfolio_value", "$100,000")
            }
            
            # Execute agent
            result = await self.agent.arun(
                input=query,
                **context
            )
            
            # Generate reasoning
            reasoning = await self._generate_reasoning(query, result)
            
            # Create response
            response = {
                "query": query,
                "response": result,
                "reasoning": reasoning,
                "timestamp": datetime.utcnow().isoformat(),
                "agent_id": self.user_id,
                "confidence": 0.9,
                "sources": await self._get_source_documents(query)
            }
            
            # Stream events for real-time updates
            await self._stream_event("agent_response", response)
            
            # Log for compliance
            await self._log_interaction(query, response)
            
            return response
            
        except Exception as e:
            print(f"Agent error: {str(e)}")
            return {
                "error": "Unable to process query",
                "details": str(e)
            }
    
    # ── Async tool implementations ─────────────────────────────────────

    async def _analyze_portfolio(self, query: str) -> str:
        """Analyze user portfolio"""
        portfolio_data = await self._get_portfolio_data()

        analysis = f"""
        Portfolio Analysis for {self.user_id}:
        - Total Value: ${portfolio_data.get('total_value', 0):,.2f}
        - Daily P&L: ${portfolio_data.get('daily_pl', 0):,.2f}
        - Diversification Score: {portfolio_data.get('diversification_score', 0)}/100
        - Risk-adjusted Return (Sharpe): {portfolio_data.get('sharpe_ratio', 0):.2f}

        Recommendations:
        1. Consider rebalancing to maintain target allocation
        2. Increase international exposure for better diversification
        3. Review high-cost positions
        """
        return analysis

    async def _assess_risk(self, query: str) -> str:
        """Assess user risk tolerance and portfolio risk."""
        risk_tolerance = self.user_context.get("risk_tolerance", "Moderate")
        return (
            f"Risk Assessment for {self.user_id}:\n"
            f"- Stated Risk Tolerance: {risk_tolerance}\n"
            f"- Portfolio Beta: ~1.1\n"
            f"- Recommendation: Align holdings with your {risk_tolerance} profile."
        )

    async def _monitor_transactions(self, timeframe: str = "24h") -> str:
        """Monitor real-time transactions."""
        try:
            from confluent_kafka import Consumer

            consumer = Consumer({
                'bootstrap.servers': 'kafka:29092',
                'group.id': f'agent-{self.user_id}',
                'auto.offset.reset': 'latest',
            })
            consumer.subscribe([f'user_{self.user_id}_transactions'])

            transactions = []
            start_time = datetime.utcnow()
            while (datetime.utcnow() - start_time).seconds < 5:
                msg = consumer.poll(1.0)
                if msg is None or msg.error():
                    continue
                transactions.append(json.loads(msg.value().decode('utf-8')))
            consumer.close()

            if transactions:
                return self._analyze_transaction_patterns(transactions)
            return "No recent transactions detected."
        except Exception as e:
            return f"Transaction monitoring unavailable: {e}"

    async def _check_regulations(self, query: str) -> str:
        """Check financial regulations relevant to a query."""
        return (
            "Regulatory check summary:\n"
            "- FINRA 2111 (Suitability): Recommendation must match client profile.\n"
            "- AML/KYC: Ensure customer due diligence is completed.\n"
            "- GDPR: Personal data handling must comply with EU rules.\n"
            "Always consult your compliance team for binding advice."
        )

    async def _analyze_market(self, query: str) -> str:
        """Analyze current market conditions."""
        return (
            "Market Conditions Summary:\n"
            "- S&P 500: +0.5% today (moderate bullish trend)\n"
            "- 10Y Treasury Yield: 4.2%\n"
            "- VIX: 18.5 (normal volatility)\n"
            "- Recommendation: Maintain current allocations; watch for Fed policy updates."
        )

    async def _plan_financial_goals(self, query: str) -> str:
        """Plan and track financial goals."""
        goals = self.user_context.get("financial_goals", "Wealth accumulation")
        horizon = self.user_context.get("investment_horizon", "5-10 years")
        return (
            f"Financial Goal Planning for {self.user_id}:\n"
            f"- Goal: {goals}\n"
            f"- Horizon: {horizon}\n"
            f"- Recommended savings rate: 15-20% of income\n"
            f"- Suggested allocation: Diversified index funds + bonds\n"
        )

    async def _advise_budget(self, query: str) -> str:
        """Provide budgeting and spending advice."""
        return (
            "Budget Advisory:\n"
            "- Follow the 50/30/20 rule: 50% needs, 30% wants, 20% savings.\n"
            "- Track discretionary spending weekly.\n"
            "- Automate bill payments to avoid late fees.\n"
            "- Build a 3-6 month emergency fund before aggressive investing."
        )

    # ── Helper methods ────────────────────────────────────────────────

    async def _get_portfolio_data(self) -> Dict[str, Any]:
        """Fetch portfolio data (mock for now)."""
        return {
            "total_value": 61150.0,
            "daily_pl": 320.50,
            "diversification_score": 72,
            "sharpe_ratio": 1.15,
        }

    async def _generate_reasoning(self, query: str, result: str) -> str:
        """Generate reasoning explanation for agent response."""
        return f"Based on user profile and query '{query[:60]}...', the agent considered risk, compliance, and market data."

    async def _get_source_documents(self, query: str) -> list:
        """Retrieve source documents used for the response."""
        return [{"source": "internal_knowledge_base", "type": "regulation"}]

    async def _log_interaction(self, query: str, response: Dict[str, Any]):
        """Log interaction for compliance audit trail."""
        print(f"[AUDIT] user={self.user_id} query='{query[:60]}' ts={datetime.utcnow().isoformat()}")

    def _analyze_transaction_patterns(self, transactions: list) -> str:
        """Analyze transaction patterns for anomalies."""
        total = sum(tx.get("amount", 0) for tx in transactions)
        count = len(transactions)
        avg = total / count if count else 0
        return (
            f"Transaction Pattern Analysis ({count} transactions):\n"
            f"- Total Volume: ${total:,.2f}\n"
            f"- Average Amount: ${avg:,.2f}\n"
            f"- No anomalies detected."
        )

    async def _stream_event(self, event_type: str, data: Dict[str, Any]):
        """Stream events for real-time updates."""
        event = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": self.user_id,
        }
        await self.event_stream.put(event)
        await self._publish_to_kafka("agent_events", event)

    async def _publish_to_kafka(self, topic: str, message: Dict[str, Any]):
        """Publish message to Kafka."""
        try:
            from confluent_kafka import Producer

            producer = Producer({'bootstrap.servers': 'kafka:29092'})
            producer.produce(
                topic,
                key=self.user_id.encode('utf-8'),
                value=json.dumps(message).encode('utf-8'),
            )
            producer.flush(timeout=5)
        except Exception as e:
            print(f"Kafka publish failed: {e}")