"""
ERPNext AI Agent - Phase 1: Vector Search Setup
ChromaDB integration for semantic document search
"""

import chromadb
from chromadb.config import Settings
import requests
from typing import List, Dict, Any, Optional
import json
from pathlib import Path
import time

class ERPNextVectorSearch:
    """Setup and manage vector search for ERPNext documents"""
    
    def __init__(self, chroma_host: str = "localhost", chroma_port: int = 8001):
        self.chroma_host = chroma_host
        self.chroma_port = chroma_port
        self.chroma_url = f"http://{chroma_host}:{chroma_port}"
        self.client = None
        self.collection = None
        
    def connect_to_chroma(self) -> bool:
        """Connect to ChromaDB instance"""
        try:
            self.client = chromadb.HttpClient(
                host=self.chroma_host,
                port=self.chroma_port,
                settings=Settings(allow_reset=True)
            )
            
            # Test connection
            heartbeat = self.client.heartbeat()
            print(f"✅ Connected to ChromaDB: {heartbeat}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to connect to ChromaDB: {e}")
            return False
    
    def create_erpnext_collection(self, collection_name: str = "erpnext_documents") -> bool:
        """Create collection for ERPNext documents"""
        try:
            # Create or get collection
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={
                    "description": "ERPNext documents for semantic search",
                    "created_at": str(time.time())
                }
            )
            
            print(f"✅ Collection '{collection_name}' ready")
            return True
            
        except Exception as e:
            print(f"❌ Failed to create collection: {e}")
            return False
    
    def index_sample_documents(self) -> bool:
        """Index sample ERPNext documents for testing"""
        sample_docs = [
            {
                "id": "customer-001",
                "text": "Customer ABC Corp with credit limit 100000 and payment terms Net 30",
                "metadata": {"doctype": "Customer", "name": "ABC Corp"}
            },
            {
                "id": "sales-order-001", 
                "text": "Sales Order SO-2024-001 for customer ABC Corp worth $50000",
                "metadata": {"doctype": "Sales Order", "name": "SO-2024-001"}
            },
            {
                "id": "item-001",
                "text": "Item laptop computer with standard rate $1500 in stock",
                "metadata": {"doctype": "Item", "name": "Laptop Computer"}
            }
        ]
        
        try:
            # Add documents to collection
            self.collection.add(
                documents=[doc["text"] for doc in sample_docs],
                metadatas=[doc["metadata"] for doc in sample_docs],
                ids=[doc["id"] for doc in sample_docs]
            )
            
            print(f"✅ Indexed {len(sample_docs)} sample documents")
            return True
            
        except Exception as e:
            print(f"❌ Failed to index documents: {e}")
            return False    
    def test_search(self, query: str = "customer with credit limit") -> bool:
        """Test semantic search functionality"""
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=2
            )
            
            print(f"\n🔍 Search results for: '{query}'")
            for i, doc in enumerate(results['documents'][0]):
                metadata = results['metadatas'][0][i]
                distance = results['distances'][0][i]
                print(f"  {i+1}. {metadata['doctype']}: {metadata['name']}")
                print(f"     Text: {doc}")
                print(f"     Distance: {distance:.3f}\n")
            
            return True
            
        except Exception as e:
            print(f"❌ Search test failed: {e}")
            return False
    
    def setup_vector_search(self) -> bool:
        """Complete vector search setup"""
        print("🚀 Setting up ERPNext Vector Search...")
        
        # Step 1: Connect to ChromaDB
        if not self.connect_to_chroma():
            return False
        
        # Step 2: Create collection
        if not self.create_erpnext_collection():
            return False
        
        # Step 3: Index sample documents
        if not self.index_sample_documents():
            return False
        
        # Step 4: Test search
        if not self.test_search():
            return False
        
        print("✅ Vector search setup complete!")
        return True

class ERPNextDocumentIndexer:
    """Index real ERPNext documents into vector database"""
    
    def __init__(self, erpnext_url: str = "http://localhost:8000"):
        self.erpnext_url = erpnext_url
        self.vector_search = ERPNextVectorSearch()
    
    def fetch_documents(self, doctype: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Fetch documents from ERPNext API"""
        try:
            # This would use actual ERPNext API with credentials
            # For now, return mock data
            mock_docs = [
                {
                    "name": f"TEST-{i:03d}",
                    "doctype": doctype,
                    "content": f"Sample {doctype} document {i} with business data"
                }
                for i in range(1, min(limit + 1, 6))  # Limit to 5 for demo
            ]
            
            return mock_docs
            
        except Exception as e:
            print(f"❌ Failed to fetch {doctype} documents: {e}")
            return []
    
    def index_doctype(self, doctype: str, limit: int = 100) -> bool:
        """Index all documents of a specific doctype"""
        print(f"📄 Indexing {doctype} documents...")
        
        documents = self.fetch_documents(doctype, limit)
        if not documents:
            return False
        
        try:
            # Prepare data for ChromaDB
            ids = [f"{doc['doctype']}-{doc['name']}" for doc in documents]
            texts = [doc['content'] for doc in documents]
            metadata = [{"doctype": doc['doctype'], "name": doc['name']} for doc in documents]
            
            # Add to collection
            self.vector_search.collection.add(
                documents=texts,
                metadatas=metadata,
                ids=ids
            )
            
            print(f"✅ Indexed {len(documents)} {doctype} documents")
            return True
            
        except Exception as e:
            print(f"❌ Failed to index {doctype}: {e}")
            return False
    
    def index_all_doctypes(self) -> bool:
        """Index common ERPNext doctypes"""
        doctypes = [
            "Customer",
            "Supplier", 
            "Item",
            "Sales Order",
            "Purchase Order",
            "Sales Invoice",
            "Purchase Invoice"
        ]
        
        # Connect to vector database
        if not self.vector_search.connect_to_chroma():
            return False
        
        if not self.vector_search.create_erpnext_collection():
            return False
        
        # Index each doctype
        success_count = 0
        for doctype in doctypes:
            if self.index_doctype(doctype):
                success_count += 1
        
        print(f"\n📊 Indexing complete: {success_count}/{len(doctypes)} doctypes")
        return success_count > 0

def main():
    """Main setup function"""
    # Setup basic vector search
    vector_search = ERPNextVectorSearch()
    if not vector_search.setup_vector_search():
        print("❌ Vector search setup failed!")
        return
    
    # Setup document indexing
    print("\n" + "="*50)
    indexer = ERPNextDocumentIndexer()
    indexer.index_all_doctypes()
    
    print("\n🎉 Vector search setup complete!")
    print("\nNext steps:")
    print("1. Integrate with real ERPNext API")
    print("2. Add more sophisticated embedding models")
    print("3. Implement batch indexing for large datasets")

if __name__ == "__main__":
    main()
