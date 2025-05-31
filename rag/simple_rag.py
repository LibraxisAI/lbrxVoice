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

try:
    from sentence_transformers import SentenceTransformer
    HAS_EMBEDDINGS = True
except ImportError:
    HAS_EMBEDDINGS = False
    print("⚠️  sentence-transformers not installed. Run: uv add sentence-transformers")


class SimpleRAG:
    """Simple RAG implementation for lbrxWhisper"""
    
    def __init__(self, 
                 persist_directory: str = "rag_db",
                 collection_name: str = "lbrx_knowledge",
                 embedding_model: str = "all-MiniLM-L6-v2"):
        
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
        
        # Initialize embedding model
        print(f"📊 Loading embedding model: {embedding_model}")
        self.embedder = SentenceTransformer(embedding_model)
        print("✅ Embedding model ready!")
    
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
        embeddings = self.embedder.encode(texts).tolist()
        
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
        query_embedding = self.embedder.encode([query])[0].tolist()
        
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