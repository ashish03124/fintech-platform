# tests/unit/test_rag_pipeline.py
import pytest
from unittest.mock import Mock, patch, AsyncMock
from ai-services.rag.pipeline import FinancialRAGPipeline

@pytest.fixture
def rag_pipeline():
    with patch('qdrant_client.QdrantClient'):
        with patch('langchain.embeddings.HuggingFaceEmbeddings'):
            pipeline = FinancialRAGPipeline()
            return pipeline

@pytest.mark.asyncio
async def test_document_loading(rag_pipeline):
    """Test document loading"""
    with patch.object(rag_pipeline, 'load_financial_documents') as mock_load:
        mock_load.return_value = [Mock(page_content="Test doc", metadata={})]
        
        docs = await rag_pipeline.load_financial_documents()
        
        assert len(docs) > 0
        assert "Test doc" in docs[0].page_content

@pytest.mark.asyncio
async def test_vector_store_creation(rag_pipeline):
    """Test vector store creation"""
    with patch('langchain.vectorstores.Qdrant.from_documents') as mock_from_docs:
        mock_from_docs.return_value = Mock()
        
        await rag_pipeline.create_vector_store()
        
        mock_from_docs.assert_called_once()

@pytest.mark.asyncio
async def test_get_advice(rag_pipeline):
    """Test getting financial advice"""
    with patch.object(rag_pipeline, 'qa_chain') as mock_chain:
        mock_chain.acall = AsyncMock(return_value={
            "result": "Test advice",
            "source_documents": [Mock(page_content="Source", metadata={"source": "test"})]
        })
        
        user_context = {
            "risk_tolerance": "MODERATE",
            "investment_horizon": "5-10 years",
            "financial_goals": "Wealth accumulation"
        }
        
        result = await rag_pipeline.get_financial_advice(
            query="Should I invest in stocks?",
            user_context=user_context
        )
        
        assert "advice" in result
        assert result["advice"] == "Test advice"
        assert len(result["sources"]) > 0