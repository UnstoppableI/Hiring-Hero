"""
Embeddings and Vector Search Module
Uses OpenAI embeddings with FAISS for efficient semantic search
"""

import os
import json
import numpy as np
import faiss
from openai import OpenAI
from typing import List, Tuple, Dict, Any
import pickle


class EmbeddingsManager:
    """Manages embeddings and vector search operations"""
    
    def __init__(self, model: str = "text-embedding-3-small", cache_dir: str = ".cache"):
        """Initialize embeddings manager with OpenAI client"""
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = model
        self.cache_dir = cache_dir
        self.index = None
        self.documents = []
        self.embeddings_cache = {}
        
        os.makedirs(cache_dir, exist_ok=True)
    
    def get_embedding(self, text: str) -> List[float]:
        """Get embedding for a single text, with caching"""
        # Check cache first
        cache_key = hash(text) % ((2**31) - 1)
        
        if cache_key in self.embeddings_cache:
            return self.embeddings_cache[cache_key]
        
        # Call OpenAI API
        response = self.client.embeddings.create(
            input=text,
            model=self.model
        )
        
        embedding = response.data[0].embedding
        self.embeddings_cache[cache_key] = embedding
        
        return embedding
    
    def batch_embed(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for multiple texts efficiently"""
        embeddings = []
        
        for text in texts:
            embedding = self.get_embedding(text)
            embeddings.append(embedding)
        
        return embeddings
    
    def build_index(self, documents: List[Dict[str, Any]]):
        """Build FAISS index from documents"""
        self.documents = documents
        
        # Extract text content from documents
        texts = [self._extract_text(doc) for doc in documents]
        
        # Get embeddings
        print(f"[embeddings] Generating embeddings for {len(texts)} documents...")
        embeddings = self.batch_embed(texts)
        
        # Convert to numpy array
        embeddings_array = np.array(embeddings).astype('float32')
        
        # Create FAISS index
        dimension = embeddings_array.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(embeddings_array)
        
        print(f"[embeddings] Index built with {len(embeddings)} documents")
    
    def search(self, query: str, k: int = 5) -> List[Tuple[Dict[str, Any], float]]:
        """Search for similar documents"""
        if self.index is None:
            raise ValueError("Index not built. Call build_index first.")
        
        # Get query embedding
        query_embedding = np.array([self.get_embedding(query)]).astype('float32')
        
        # Search
        distances, indices = self.index.search(query_embedding, k)
        
        # Return results with scores
        results = []
        for idx, distance in zip(indices[0], distances[0]):
            if idx < len(self.documents):
                # Convert L2 distance to similarity score (0-100)
                similarity = max(0, 100 - distance)
                results.append((self.documents[idx], similarity))
        
        return results
    
    def _extract_text(self, document: Dict[str, Any]) -> str:
        """Extract searchable text from document"""
        if isinstance(document, dict):
            # For job descriptions
            if 'description' in document:
                return f"{document.get('title', '')} {document.get('description', '')}"
            # For candidate profiles
            elif 'resume' in document or 'experience' in document:
                parts = [
                    document.get('name', ''),
                    document.get('summary', ''),
                    document.get('experience', ''),
                    document.get('resume', '')
                ]
                return ' '.join(str(p) for p in parts if p)
        
        return str(document)
    
    def save_index(self, path: str):
        """Save FAISS index to disk"""
        if self.index is None:
            raise ValueError("No index to save")
        
        faiss.write_index(self.index, path)
        # Also save documents metadata
        with open(path + ".meta", "w") as f:
            json.dump(self.documents, f)
        print(f"[embeddings] Index saved to {path}")
    
    def load_index(self, path: str):
        """Load FAISS index from disk"""
        self.index = faiss.read_index(path)
        with open(path + ".meta", "r") as f:
            self.documents = json.load(f)
        print(f"[embeddings] Index loaded from {path}")
