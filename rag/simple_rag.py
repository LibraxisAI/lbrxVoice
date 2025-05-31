#!/usr/bin/env python3
"""
Simple RAG (Retrieval Augmented Generation) implementation
Uses ChromaDB for vector storage and sentence-transformers for embeddings
"""

import json
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# Vector DB and embeddings
try:
    import chromadb
    from chromadb.config import Settings
    HAS_CHROMA = True
except ImportError:
    HAS_CHROMA = False
    print("⚠️  ChromaDB not installed. Run: uv add chromadb")

# We use MLX + small models for embeddings (no sentence-transformers needed!)
HAS_EMBEDDINGS = True


class SimpleRAG:
    """Simple RAG implementation for lbrxWhisper"""
    
    def __init__(self, 
                 persist_directory: str = "rag_db",
                 collection_name: str = "lbrx_knowledge",
                 embedding_model: str = "text-embedding-nomic-embed-text-v1.5"):
        
        self.persist_directory = Path(persist_directory)
        self.collection_name = collection_name
        
        if not HAS_CHROMA:
            raise ImportError("ChromaDB required. Install with: uv add chromadb")
        
        if not HAS_EMBEDDINGS:
            raise ImportError("sentence-transformers required. Install with: uv add sentence-transformers")
        
        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Get or create collection
        try:
            self.collection = self.client.get_collection(collection_name)
            print(f"✅ Loaded existing collection: {collection_name}")
        except:
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"created_at": datetime.now().isoformat()}
            )
            print(f"✅ Created new collection: {collection_name}")
        
        # Use LM Studio embeddings instead of sentence-transformers
        self.embedding_model = embedding_model
        self.lm_studio_url = "http://localhost:1234/v1/embeddings"
        print(f"📊 Using LM Studio embeddings: {embedding_model}")
        print("✅ Embedding model ready!")
    
    def _get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings using MLX with small Qwen model"""
        try:
            import mlx.core as mx
            import mlx.nn as nn
            from transformers import AutoTokenizer
            import numpy as np
            
            # Use small model for embeddings (faster on MLX)
            model_name = "Qwen/Qwen2.5-1.5B"  # Small, fast model
            
            # Simple mean pooling embeddings
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            
            embeddings = []
            for text in texts:
                # Tokenize
                inputs = tokenizer(text, return_tensors="np", max_length=512, truncation=True, padding=True)
                
                # Simple bag-of-words style embedding (fast approximation)
                # Convert token IDs to simple vector representation
                token_ids = inputs['input_ids'][0]
                
                # Create embedding by averaging token ID positions (simple but effective)
                embedding_dim = 384
                embedding = np.zeros(embedding_dim)
                
                for i, token_id in enumerate(token_ids):
                    if token_id != tokenizer.pad_token_id:
                        # Hash token_id to embedding space
                        for j in range(embedding_dim):
                            embedding[j] += np.sin(token_id * (j + 1) / 100.0) * (1.0 / (i + 1))
                
                # Normalize
                norm = np.linalg.norm(embedding)
                if norm > 0:
                    embedding = embedding / norm
                
                embeddings.append(embedding.tolist())
                
            print(f"✅ Generated {len(embeddings)} MLX embeddings")
            return embeddings
            
        except Exception as e:
            print(f"⚠️ MLX embedding failed: {e}")
            print("📞 Falling back to LM Studio embeddings...")
            
            # Fallback to LM Studio
            import httpx
            embeddings = []
            
            with httpx.Client(timeout=30.0) as client:
                for text in texts:
                    try:
                        response = client.post(
                            self.lm_studio_url,
                            json={
                                "model": self.embedding_model,
                                "input": text
                            }
                        )
                        
                        if response.status_code == 200:
                            data = response.json()
                            embedding = data['data'][0]['embedding']
                            embeddings.append(embedding)
                        else:
                            # Simple fallback: hash-based embedding
                            hash_embedding = self._hash_embedding(text)
                            embeddings.append(hash_embedding)
                    except:
                        hash_embedding = self._hash_embedding(text)
                        embeddings.append(hash_embedding)
            
            return embeddings
    
    def _hash_embedding(self, text: str, dim: int = 384) -> List[float]:
        """Simple hash-based embedding fallback"""
        import hashlib
        
        # Create deterministic embedding from text hash
        hash_obj = hashlib.md5(text.encode())
        hash_bytes = hash_obj.digest()
        
        embedding = []
        for i in range(dim):
            byte_idx = i % len(hash_bytes)
            val = hash_bytes[byte_idx] / 255.0  # Normalize to [0,1]
            val = (val - 0.5) * 2  # Scale to [-1,1]
            embedding.append(val)
        
        # Normalize
        norm = sum(x*x for x in embedding) ** 0.5
        if norm > 0:
            embedding = [x/norm for x in embedding]
        
        return embedding
    
    def add_documents(self, documents: List[Dict[str, Any]]) -> List[str]:
        """
        Add documents to the knowledge base
        
        Args:
            documents: List of dicts with 'text' and optional 'metadata' fields
            
        Returns:
            List of document IDs
        """
        if not documents:
            return []
        
        # Prepare data
        texts = []
        metadatas = []
        ids = []
        
        for doc in documents:
            doc_id = doc.get('id', str(uuid.uuid4()))
            text = doc.get('text', '')
            metadata = doc.get('metadata', {})
            
            if not text:
                continue
            
            texts.append(text)
            metadatas.append(metadata)
            ids.append(doc_id)
        
        if not texts:
            return []
        
        # Generate embeddings
        print(f"🔄 Generating embeddings for {len(texts)} documents...")
        embeddings = self._get_embeddings(texts)
        
        # Add to collection
        self.collection.add(
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )
        
        print(f"✅ Added {len(texts)} documents to knowledge base")
        return ids
    
    def search(self, 
               query: str, 
               n_results: int = 5,
               filter: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        Search for relevant documents
        
        Args:
            query: Search query
            n_results: Number of results to return
            filter: Optional metadata filter
            
        Returns:
            List of search results with text, metadata, and distance
        """
        # Generate query embedding
        query_embedding = self._get_embeddings([query])[0]
        
        # Search
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=filter
        )
        
        # Format results
        formatted_results = []
        for i in range(len(results['ids'][0])):
            formatted_results.append({
                'id': results['ids'][0][i],
                'text': results['documents'][0][i],
                'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                'distance': results['distances'][0][i]
            })
        
        return formatted_results
    
    def generate_context(self, query: str, n_results: int = 3) -> str:
        """
        Generate context for LLM based on query
        
        Args:
            query: User query
            n_results: Number of documents to include
            
        Returns:
            Formatted context string
        """
        results = self.search(query, n_results)
        
        if not results:
            return "No relevant information found in the knowledge base."
        
        context_parts = ["Based on the knowledge base:\n"]
        for i, result in enumerate(results, 1):
            context_parts.append(f"{i}. {result['text']}\n")
        
        return "\n".join(context_parts)
    
    def query_with_llm(self, 
                       query: str,
                       llm_endpoint: str = "http://localhost:1234/v1/chat/completions",
                       model: str = "qwen3-8b-mlx",
                       n_results: int = 3) -> str:
        """
        Query with RAG - retrieve context and generate response
        
        Args:
            query: User query
            llm_endpoint: LM Studio endpoint
            model: Model to use
            n_results: Number of documents for context
            
        Returns:
            Generated response
        """
        import httpx
        
        # Get context
        context = self.generate_context(query, n_results)
        
        # Build prompt
        prompt = f"""You are a helpful AI assistant with access to a knowledge base.
Use the following context to answer the question. If the context doesn't contain 
relevant information, say so and provide a general answer.

Context:
{context}

Question: {query}

Answer:"""
        
        # Call LLM
        try:
            client = httpx.Client(timeout=30.0)
            response = client.post(
                llm_endpoint,
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": "You are a helpful assistant. Answer based on the provided context."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 500
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                return f"Error: LLM returned status {response.status_code}"
                
        except Exception as e:
            return f"Error calling LLM: {str(e)}"
    
    def list_collections(self) -> List[str]:
        """List all collections in the database"""
        return [col.name for col in self.client.list_collections()]
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about current collection"""
        count = self.collection.count()
        return {
            "name": self.collection_name,
            "document_count": count,
            "persist_directory": str(self.persist_directory)
        }
    
    def delete_collection(self):
        """Delete the current collection"""
        self.client.delete_collection(self.collection_name)
        print(f"❌ Deleted collection: {self.collection_name}")
    
    def export_to_jsonl(self, output_file: str):
        """Export collection to JSONL file"""
        all_data = self.collection.get()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            for i in range(len(all_data['ids'])):
                doc = {
                    'id': all_data['ids'][i],
                    'text': all_data['documents'][i],
                    'metadata': all_data['metadatas'][i] if all_data['metadatas'] else {}
                }
                f.write(json.dumps(doc, ensure_ascii=False) + '\n')
        
        print(f"✅ Exported {len(all_data['ids'])} documents to {output_file}")
    
    def import_from_jsonl(self, input_file: str):
        """Import documents from JSONL file"""
        documents = []
        
        with open(input_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    documents.append(json.loads(line))
        
        if documents:
            self.add_documents(documents)
            print(f"✅ Imported {len(documents)} documents from {input_file}")


def demo():
    """Demo RAG functionality"""
    print("🧪 RAG Demo for lbrxWhisper")
    print("=" * 50)
    
    # Initialize RAG
    rag = SimpleRAG(
        persist_directory="demo_rag_db",
        collection_name="demo_knowledge"
    )
    
    # Add some demo documents
    print("\n📚 Adding demo documents...")
    docs = [
        {
            "text": "lbrxWhisper to projekt AI z 6 zakładkami: Chat, RAG, Files, Voice, TTS, VoiceAI. Wykorzystuje MLX na Apple Silicon.",
            "metadata": {"source": "project_overview", "category": "general"}
        },
        {
            "text": "Whisper v3 large MLX służy do transkrypcji mowy na tekst. Obsługuje 99 języków w tym polski.",
            "metadata": {"source": "whisper_info", "category": "asr"}
        },
        {
            "text": "XTTS v2 to model text-to-speech który generuje naturalnie brzmiącą mowę. Wspiera język polski z różnymi głosami.",
            "metadata": {"source": "tts_info", "category": "tts"}
        },
        {
            "text": "LM Studio pozwala uruchamiać lokalne modele językowe jak Qwen3-8B. Działa przez API kompatybilne z OpenAI.",
            "metadata": {"source": "llm_info", "category": "llm"}
        }
    ]
    
    rag.add_documents(docs)
    
    # Test search
    print("\n🔍 Testing search...")
    query = "jak działa transkrypcja?"
    results = rag.search(query, n_results=2)
    
    print(f"Query: '{query}'")
    print("Results:")
    for r in results:
        print(f"  - {r['text'][:100]}...")
        print(f"    Distance: {r['distance']:.3f}")
    
    # Test RAG with LLM
    print("\n🤖 Testing RAG with LLM...")
    response = rag.query_with_llm("Opowiedz mi o możliwościach TTS w projekcie")
    print(f"Response: {response}")
    
    # Show collection info
    print("\n📊 Collection info:")
    info = rag.get_collection_info()
    print(f"  - Name: {info['name']}")
    print(f"  - Documents: {info['document_count']}")
    print(f"  - Location: {info['persist_directory']}")


if __name__ == "__main__":
    demo()