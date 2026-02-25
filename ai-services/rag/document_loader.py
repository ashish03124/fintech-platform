# ai-services/rag/document_loader.py
import os
import json
from typing import List, Dict, Any
from langchain.schema import Document
from langchain.document_loaders import (
    PyPDFLoader,
    TextLoader,
    CSVLoader,
    UnstructuredHTMLLoader,
    UnstructuredMarkdownLoader
)
import aiofiles
import asyncio

class FinancialDocumentLoader:
    def __init__(self, docs_directory: str = "data/financial_docs"):
        self.docs_directory = docs_directory
        os.makedirs(docs_directory, exist_ok=True)
        
    async def load_all_documents(self) -> List[Document]:
        """Load all financial documents"""
        documents = []
        
        # Load from different sources
        documents.extend(await self._load_pdf_documents())
        documents.extend(await self._load_text_documents())
        documents.extend(await self._load_regulatory_documents())
        documents.extend(await self._load_investment_guides())
        documents.extend(await self._load_compliance_documents())
        
        return documents
    
    async def _load_pdf_documents(self) -> List[Document]:
        """Load PDF documents"""
        pdf_docs = []
        pdf_dir = os.path.join(self.docs_directory, "pdfs")
        
        if os.path.exists(pdf_dir):
            for filename in os.listdir(pdf_dir):
                if filename.endswith(".pdf"):
                    filepath = os.path.join(pdf_dir, filename)
                    try:
                        loader = PyPDFLoader(filepath)
                        docs = loader.load()
                        
                        # Add metadata
                        for doc in docs:
                            doc.metadata.update({
                                "source": filename,
                                "type": "pdf",
                                "category": self._categorize_document(filename)
                            })
                        
                        pdf_docs.extend(docs)
                    except Exception as e:
                        print(f"Error loading PDF {filename}: {e}")
        
        return pdf_docs
    
    async def _load_text_documents(self) -> List[Document]:
        """Load text documents"""
        text_docs = []
        text_dir = os.path.join(self.docs_directory, "text")
        
        if os.path.exists(text_dir):
            for filename in os.listdir(text_dir):
                filepath = os.path.join(text_dir, filename)
                try:
                    if filename.endswith(".txt"):
                        loader = TextLoader(filepath, encoding="utf-8")
                        docs = loader.load()
                    elif filename.endswith(".md"):
                        loader = UnstructuredMarkdownLoader(filepath)
                        docs = loader.load()
                    elif filename.endswith(".html"):
                        loader = UnstructuredHTMLLoader(filepath)
                        docs = loader.load()
                    elif filename.endswith(".csv"):
                        loader = CSVLoader(filepath)
                        docs = loader.load()
                    else:
                        continue
                    
                    # Add metadata
                    for doc in docs:
                        doc.metadata.update({
                            "source": filename,
                            "type": filename.split('.')[-1],
                            "category": self._categorize_document(filename)
                        })
                    
                    text_docs.extend(docs)
                except Exception as e:
                    print(f"Error loading text document {filename}: {e}")
        
        return text_docs
    
    async def _load_regulatory_documents(self) -> List[Document]:
        """Load regulatory documents"""
        regulations = [
            {
                "content": """
                **General Data Protection Regulation (GDPR) - Key Requirements:**
                1. Lawful Basis for Processing: Must have valid reason for processing personal data
                2. Data Minimization: Collect only necessary data
                3. Purpose Limitation: Use data only for specified purposes
                4. Storage Limitation: Don't keep data longer than needed
                5. Data Accuracy: Keep data accurate and up-to-date
                6. Integrity & Confidentiality: Implement appropriate security measures
                7. Accountability: Demonstrate compliance with principles
                
                **Financial Services Specifics:**
                - Customer consent must be explicit and informed
                - Right to access, rectify, and erase personal data
                - Data portability for account information
                - 72-hour breach notification requirement
                - Data Protection Impact Assessments (DPIAs) for high-risk processing
                """,
                "metadata": {
                    "source": "gdpr_regulations",
                    "type": "regulation",
                    "category": "compliance",
                    "jurisdiction": "EU",
                    "effective_date": "2018-05-25"
                }
            },
            {
                "content": """
                **Anti-Money Laundering (AML) Directive 5 (5AMLD):**
                1. Customer Due Diligence (CDD): Verify customer identity
                2. Enhanced Due Diligence (EDD): For high-risk customers
                3. Ongoing Monitoring: Continuous transaction monitoring
                4. Suspicious Activity Reports (SARs): File for suspicious transactions
                5. Record Keeping: Maintain records for 5-7 years
                
                **Thresholds:**
                - Currency Transaction Report (CTR): $10,000
                - Suspicious Activity Report (SAR): $5,000 or suspicious pattern
                - Wire Transfers: $3,000 for information recording
                
                **High-Risk Indicators:**
                - Rapid movement of funds
                - Transactions inconsistent with customer profile
                - Use of multiple accounts
                - Transactions with high-risk jurisdictions
                """,
                "metadata": {
                    "source": "aml_directive_5",
                    "type": "regulation",
                    "category": "compliance",
                    "jurisdiction": "Global",
                    "effective_date": "2020-01-10"
                }
            }
        ]
        
        return [Document(page_content=doc["content"], metadata=doc["metadata"]) 
                for doc in regulations]
    
    async def _load_investment_guides(self) -> List[Document]:
        """Load investment guides"""
        guides = [
            {
                "content": """
                **Modern Portfolio Theory (MPT) Principles:**
                1. Diversification: Spread investments across uncorrelated assets
                2. Efficient Frontier: Optimal portfolios for given risk level
                3. Risk-Return Tradeoff: Higher returns require higher risk
                4. Asset Allocation: Primary determinant of portfolio performance
                
                **Recommended Asset Allocation by Risk Profile:**
                - Conservative (Low Risk): 20% Stocks, 50% Bonds, 30% Cash
                - Moderate (Medium Risk): 50% Stocks, 40% Bonds, 10% Cash
                - Aggressive (High Risk): 80% Stocks, 15% Bonds, 5% Cash
                
                **Rebalancing Strategy:**
                - Rebalance when allocation drifts 5% from target
                - Quarterly or semi-annually recommended
                - Consider tax implications of rebalancing
                """,
                "metadata": {
                    "source": "investment_guide_mpt",
                    "type": "guide",
                    "category": "investment",
                    "author": "Financial Advisory Board",
                    "version": "2.1"
                }
            },
            {
                "content": """
                **Risk Management Framework:**
                1. Risk Identification: Identify potential risks in portfolio
                2. Risk Measurement: Quantify risks using metrics
                3. Risk Mitigation: Implement strategies to reduce risk
                4. Risk Monitoring: Continuously monitor risk exposure
                
                **Risk Metrics:**
                - Value at Risk (VaR): Maximum loss with 95% confidence over X days
                - Expected Shortfall (ES): Average loss beyond VaR
                - Sharpe Ratio: Risk-adjusted return (≥1.0 is good)
                - Sortino Ratio: Downside risk-adjusted return
                - Maximum Drawdown: Largest peak-to-trough decline
                
                **Hedging Strategies:**
                - Options: Protective puts, covered calls
                - Futures: Interest rate, currency futures
                - Diversification: Across asset classes, geographies
                """,
                "metadata": {
                    "source": "risk_management_guide",
                    "type": "guide",
                    "category": "risk",
                    "author": "Risk Management Institute",
                    "version": "1.5"
                }
            }
        ]
        
        return [Document(page_content=doc["content"], metadata=doc["metadata"]) 
                for doc in guides]
    
    async def _load_compliance_documents(self) -> List[Document]:
        """Load compliance documents"""
        compliance_docs = [
            {
                "content": """
                **FINRA Rule 2111: Suitability**
                Broker-dealers must have reasonable basis to believe recommended transactions are suitable.
                
                **Requirements:**
                1. Reasonable Basis Suitability: Understand investment product
                2. Customer Specific Suitability: Match recommendation to customer profile
                3. Quantitative Suitability: Series of transactions must be suitable
                
                **Customer Investment Profile Factors:**
                - Age
                - Other investments
                - Financial situation and needs
                - Tax status
                - Investment objectives
                - Investment experience
                - Investment time horizon
                - Liquidity needs
                - Risk tolerance
                
                **Documentation Requirements:**
                - Maintain records of recommendations
                - Document customer profile updates
                - Keep suitability determinations for 6 years
                """,
                "metadata": {
                    "source": "finra_rule_2111",
                    "type": "regulation",
                    "category": "compliance",
                    "jurisdiction": "US",
                    "regulator": "FINRA"
                }
            }
        ]
        
        return [Document(page_content=doc["content"], metadata=doc["metadata"]) 
                for doc in compliance_docs]
    
    def _categorize_document(self, filename: str) -> str:
        """Categorize document based on filename"""
        filename_lower = filename.lower()
        
        if any(word in filename_lower for word in ['regulation', 'compliance', 'law', 'rule']):
            return "compliance"
        elif any(word in filename_lower for word in ['investment', 'portfolio', 'stock', 'bond']):
            return "investment"
        elif any(word in filename_lower for word in ['risk', 'security', 'fraud']):
            return "risk"
        elif any(word in filename_lower for word in ['tax', 'irs', 'vat']):
            return "tax"
        else:
            return "general"
    
    async def save_document(self, content: str, metadata: Dict[str, Any]) -> str:
        """Save a new document"""
        doc_id = f"doc_{hash(content) % 1000000:06d}"
        filename = f"{doc_id}.txt"
        filepath = os.path.join(self.docs_directory, "custom", filename)
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
            await f.write(content)
        
        # Save metadata
        metadata_file = filepath.replace('.txt', '.meta.json')
        async with aiofiles.open(metadata_file, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(metadata, indent=2))
        
        return doc_id