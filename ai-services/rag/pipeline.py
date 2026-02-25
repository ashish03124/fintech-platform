# ai-services/rag/pipeline.py
from datetime import datetime

from langchain.document_loaders import DirectoryLoader, PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor
from langchain.schema import Document
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Qdrant
from langchain_openai import ChatOpenAI
import qdrant_client
from typing import List, Dict, Any
import json
import os

class FinancialRAGPipeline:
    def __init__(self):
        # Initialize embedding model
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        # Initialize Qdrant client
        self.qdrant_client = qdrant_client.QdrantClient(
            host="qdrant",
            port=6333,
            timeout=60
        )
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model="gpt-4-1106-preview",
            temperature=0.1,
            max_tokens=1000,
            streaming=True
        )
        
        # Load financial documents
        self.documents = self.load_financial_documents()
        
        # Create vector store
        self.vector_store = self.create_vector_store()
        
        # Create QA chain
        self.qa_chain = self.create_qa_chain()
    
    def load_financial_documents(self) -> List:
        """Load financial regulations and knowledge base"""
        
        documents = []
        
        # Load PDF documents
        pdf_loader = DirectoryLoader(
            "data/financial_docs/",
            glob="**/*.pdf",
            loader_cls=PyPDFLoader,
            recursive=True
        )
        pdf_docs = pdf_loader.load()
        documents.extend(pdf_docs)
        
        # Load compliance rules
        compliance_rules = self.load_compliance_rules()
        documents.extend(compliance_rules)
        
        # Load investment knowledge
        investment_knowledge = self.load_investment_knowledge()
        documents.extend(investment_knowledge)
        
        return documents
    
    def load_compliance_rules(self) -> List:
        """Load compliance rules as documents"""
        compliance_data = [
            {
                "content": """
                **GDPR Compliance for Financial Services**:
                - Customer data must be encrypted at rest and in transit
                - Right to be forgotten: Delete customer data upon request
                - Data minimization: Collect only necessary data
                - Consent management: Explicit consent for data processing
                - Data breach notification within 72 hours
                """,
                "metadata": {"source": "gdpr_compliance", "type": "regulation"}
            },
            {
                "content": """
                **Anti-Money Laundering (AML) Requirements**:
                - Customer Due Diligence (CDD) for all new accounts
                - Enhanced Due Diligence (EDD) for high-risk customers
                - Transaction monitoring for suspicious activity
                - Reporting threshold: $10,000 for CTR, $5,000 for SAR
                - Record keeping: 5 years minimum
                """,
                "metadata": {"source": "aml_compliance", "type": "regulation"}
            },
            {
                "content": """
                **FINRA Rule 2111: Suitability**:
                - Recommendations must be suitable for customer's investment profile
                - Consider customer's age, financial situation, risk tolerance
                - Document all recommendations and rationale
                - Provide clear risk disclosures
                - Ongoing monitoring of customer accounts
                """,
                "metadata": {"source": "finra_2111", "type": "regulation"}
            }
        ]
        
        return [Document(page_content=doc["content"], metadata=doc["metadata"]) 
                for doc in compliance_data]
    
    def load_investment_knowledge(self) -> List:
        """Load investment knowledge base"""
        investment_data = [
            {
                "content": """
                **Portfolio Diversification Strategies**:
                - Asset allocation: 60% stocks, 30% bonds, 10% alternatives
                - Geographic diversification: Domestic 70%, International 30%
                - Sector diversification across 11 GICS sectors
                - Rebalance portfolio quarterly or when allocation drifts 5%
                - Consider risk-adjusted returns (Sharpe ratio > 1.0)
                """,
                "metadata": {"source": "portfolio_management", "type": "investment"}
            },
            {
                "content": """
                **Risk Management Framework**:
                - Value at Risk (VaR): Maximum loss with 95% confidence over 1 day
                - Stop-loss orders: 10-20% below purchase price
                - Position sizing: No more than 5% in any single security
                - Correlation analysis: Avoid highly correlated assets (>0.7)
                - Stress testing for market crashes
                """,
                "metadata": {"source": "risk_management", "type": "investment"}
            }
        ]
        
        return [Document(page_content=doc["content"], metadata=doc["metadata"]) 
                for doc in investment_data]
    
    def create_vector_store(self):
        """Create and populate vector store"""
        
        # Split documents
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        chunks = text_splitter.split_documents(self.documents)
        print(f"Created {len(chunks)} document chunks")
        
        # Create Qdrant collection
        vector_store = Qdrant.from_documents(
            chunks,
            self.embeddings,
            url="http://qdrant:6333",
            collection_name="financial_knowledge",
            force_recreate=True
        )
        
        return vector_store
    
    def create_qa_chain(self):
        """Create RAG-based QA chain with financial context"""
        
        # Custom prompt template for financial advice
        prompt_template = """
        You are a certified financial advisor with expertise in investment management, 
        compliance regulations, and financial planning. Always provide accurate, 
        compliant, and personalized advice.
        
        **Context Information:**
        {context}
        
        **User Query:** {question}
        
        **User Context:**
        - Risk Tolerance: {risk_tolerance}
        - Investment Horizon: {investment_horizon}
        - Financial Goals: {financial_goals}
        
        **Guidelines:**
        1. Always reference relevant regulations when applicable
        2. Provide clear risk disclosures
        3. Cite specific compliance requirements when relevant
        4. Offer personalized recommendations based on user context
        5. Include specific action items when appropriate
        
        **Response Structure:**
        1. Summary of the query
        2. Relevant regulations/considerations
        3. Personalized recommendations
        4. Risk factors to consider
        5. Next steps
        
        **Financial Advisor Response:**
        """
        
        PROMPT = PromptTemplate(
            template=prompt_template,
            input_variables=["context", "question", "risk_tolerance", 
                           "investment_horizon", "financial_goals"]
        )
        
        # Create retriever
        retriever = self.vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={
                "k": 5,
                "score_threshold": 0.7,
                "filter": {"type": {"$in": ["regulation", "investment"]}}
            }
        )
        
        # Create compression retriever for more precise results
        compressor = LLMChainExtractor.from_llm(self.llm)
        compression_retriever = ContextualCompressionRetriever(
            base_compressor=compressor,
            base_retriever=retriever
        )
        
        # Create QA chain
        qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=compression_retriever,
            chain_type_kwargs={
                "prompt": PROMPT,
                "verbose": True
            },
            return_source_documents=True,
            verbose=True
        )
        
        return qa_chain
    
    async def get_financial_advice(self, query: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Get personalized financial advice"""
        
        try:
            # Prepare context variables
            context_vars = {
                "risk_tolerance": user_context.get("risk_tolerance", "Moderate"),
                "investment_horizon": user_context.get("investment_horizon", "5-10 years"),
                "financial_goals": user_context.get("financial_goals", "Wealth accumulation")
            }
            
            # Get response from QA chain
            result = await self.qa_chain.acall(
                {"query": query, **context_vars}
            )
            
            # Extract source documents for citations
            source_docs = []
            for doc in result["source_documents"]:
                source_docs.append({
                    "content": doc.page_content[:500] + "...",
                    "source": doc.metadata.get("source", "Unknown"),
                    "type": doc.metadata.get("type", "general")
                })
            
            # Create audit trail
            audit_record = {
                "query": query,
                "user_context": user_context,
                "response": result["result"],
                "sources": source_docs,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Log for compliance
            await self.log_advice_session(audit_record)
            
            return {
                "advice": result["result"],
                "sources": source_docs,
                "confidence": 0.95,  # Could be calculated from similarity scores
                "audit_id": audit_record["timestamp"],
                "disclaimer": "This is for informational purposes only. Consult a financial advisor."
            }
            
        except Exception as e:
            print(f"Error in financial advice: {str(e)}")
            return {
                "error": "Unable to provide advice at this time",
                "details": str(e)
            }
    
    async def log_advice_session(self, audit_record: Dict[str, Any]):
        """Log advice session for compliance"""
        
        # Write to database
        # Write to Kafka for audit stream
        # Store in vector database for future reference
        
        pass