# ai-services/rag/vector_store.py
from typing import List, Dict, Any, Optional
from langchain.vectorstores import Qdrant
from langchain.embeddings.base import Embeddings
from qdrant_client import QdrantClient
from qdrant_client.http import models
import json
import logging

logger = logging.getLogger(__name__)

class FinancialVectorStore:
    def __init__(self, embeddings: Embeddings, qdrant_url: str = "http://qdrant:6333"):
        self.embeddings = embeddings
        self.qdrant_url = qdrant_url
        self.client = None
        self.collection_name = "financial_knowledge"
        self.vector_size = 384  # all-MiniLM-L6-v2 embedding size
        
    async def initialize(self):
        """Initialize Qdrant client and collection"""
        try:
            self.client = QdrantClient(
                url=self.qdrant_url,
                timeout=60,
                prefer_grpc=False
            )
            
            # Check if collection exists
            collections = self.client.get_collections().collections
            collection_exists = any(c.name == self.collection_name for c in collections)
            
            if not collection_exists:
                await self._create_collection()
            
            logger.info(f"Vector store initialized with collection: {self.collection_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}")
            raise
    
    async def _create_collection(self):
        """Create Qdrant collection with optimized configuration"""
        try:
            self.client.recreate_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=self.vector_size,
                    distance=models.Distance.COSINE
                ),
                # Add payload schema for filtering
                payload_schema={
                    "source": models.PayloadSchemaType.KEYWORD,
                    "type": models.PayloadSchemaType.KEYWORD,
                    "category": models.PayloadSchemaType.KEYWORD,
                    "jurisdiction": models.PayloadSchemaType.KEYWORD,
                    "effective_date": models.PayloadSchemaType.DATETIME,
                }
            )
            
            # Create indexes for faster filtering
            self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="category",
                field_schema=models.PayloadSchemaType.KEYWORD
            )
            
            self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="type",
                field_schema=models.PayloadSchemaType.KEYWORD
            )
            
            logger.info(f"Collection {self.collection_name} created with indexes")
            
        except Exception as e:
            logger.error(f"Failed to create collection: {e}")
            raise
    
    async def add_documents(self, documents: List[Dict[str, Any]]):
        """Add documents to vector store"""
        try:
            # Prepare points for Qdrant
            points = []
            
            for i, doc in enumerate(documents):
                # Generate embedding
                embedding = await self.embeddings.aembed_query(doc["content"])
                
                # Create point
                point = models.PointStruct(
                    id=i,
                    vector=embedding,
                    payload={
                        "content": doc["content"],
                        **doc["metadata"]
                    }
                )
                points.append(point)
            
            # Upload to Qdrant
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            
            logger.info(f"Added {len(documents)} documents to vector store")
            
        except Exception as e:
            logger.error(f"Failed to add documents: {e}")
            raise
    
    async def search(self, query: str, 
                    filter_criteria: Optional[Dict[str, Any]] = None,
                    limit: int = 5,
                    score_threshold: float = 0.7) -> List[Dict[str, Any]]:
        """Search for similar documents"""
        try:
            # Generate query embedding
            query_embedding = await self.embeddings.aembed_query(query)
            
            # Build filter
            filter_condition = None
            if filter_criteria:
                must_conditions = []
                for key, value in filter_criteria.items():
                    if isinstance(value, list):
                        must_conditions.append(
                            models.FieldCondition(
                                key=key,
                                match=models.MatchAny(any=value)
                            )
                        )
                    else:
                        must_conditions.append(
                            models.FieldCondition(
                                key=key,
                                match=models.MatchValue(value=value)
                            )
                        )
                
                filter_condition = models.Filter(must=must_conditions)
            
            # Search in Qdrant
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                query_filter=filter_condition,
                limit=limit,
                score_threshold=score_threshold
            )
            
            # Format results
            results = []
            for hit in search_result:
                results.append({
                    "score": hit.score,
                    "content": hit.payload.get("content", ""),
                    "metadata": {k: v for k, v in hit.payload.items() if k != "content"}
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    async def similarity_search_with_score(
        self, 
        query: str, 
        k: int = 4,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[tuple]:
        """Search with similarity scores"""
        results = await self.search(query, filter, limit=k)
        return [(r["content"], r["score"]) for r in results]
    
    async def get_collection_info(self) -> Dict[str, Any]:
        """Get collection information"""
        try:
            info = self.client.get_collection(self.collection_name)
            
            return {
                "points_count": info.points_count,
                "vectors_count": info.vectors_count,
                "segments_count": len(info.segments),
                "status": info.status,
                "config": {
                    "vector_size": info.config.params.vectors.size,
                    "distance": str(info.config.params.vectors.distance)
                }
            }
        except Exception as e:
            logger.error(f"Failed to get collection info: {e}")
            return {}
    
    async def delete_points(self, point_ids: List[int]):
        """Delete points from collection"""
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=models.PointIdsList(points=point_ids)
            )
            logger.info(f"Deleted {len(point_ids)} points")
        except Exception as e:
            logger.error(f"Failed to delete points: {e}")
    
    async def clear_collection(self):
        """Clear entire collection"""
        try:
            self.client.delete_collection(self.collection_name)
            await self._create_collection()
            logger.info("Collection cleared and recreated")
        except Exception as e:
            logger.error(f"Failed to clear collection: {e}")