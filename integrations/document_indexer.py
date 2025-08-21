#!/usr/bin/env python3
"""
ERPNext Document Indexer
Indexes real ERPNext documents into ChromaDB for semantic search
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import hashlib

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import pandas as pd

from erpnext_connector import ERPNextConnector

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ERPNextDocumentIndexer:
    """Index ERPNext documents for semantic search"""
    
    def __init__(self, 
                 chroma_path: str = "../volumes/chroma",
                 model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        
        self.chroma_path = Path(chroma_path).absolute()
        self.chroma_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB
        self.chroma_client = chromadb.PersistentClient(
            path=str(self.chroma_path),
            settings=Settings(allow_reset=True, anonymized_telemetry=False)
        )
        
        # Initialize sentence transformer
        self.model = SentenceTransformer(model_name)
        
        # Initialize ERPNext connector
        self.erpnext = ERPNextConnector()
        
        logger.info(f"Indexer initialized with ChromaDB at: {self.chroma_path}")
    
    def get_or_create_collection(self, name: str) -> chromadb.Collection:
        """Get or create a ChromaDB collection"""
        try:
            collection = self.chroma_client.get_collection(name)
            logger.info(f"Using existing collection: {name}")
        except:
            collection = self.chroma_client.create_collection(
                name=name,
                metadata={"description": f"ERPNext {name} documents"}
            )
            logger.info(f"Created new collection: {name}")
        
        return collection
    
    def create_document_id(self, doctype: str, name: str) -> str:
        """Create unique document ID"""
        return f"{doctype}::{name}"
    
    def extract_text_content(self, document: Dict[str, Any]) -> str:
        """Extract searchable text from ERPNext document"""
        text_parts = []
        
        # Include name/title
        if document.get('name'):
            text_parts.append(f"Name: {document['name']}")
            
        # Include subject/title fields
        for field in ['subject', 'title', 'item_name', 'customer_name', 'supplier_name']:
            if document.get(field):
                text_parts.append(f"{field}: {document[field]}")
        
        # Include description fields
        for field in ['description', 'remarks', 'notes']:
            if document.get(field):
                text_parts.append(f"{field}: {document[field]}")
        
        # Include status and key metadata
        if document.get('status'):
            text_parts.append(f"Status: {document['status']}")
            
        if document.get('docstatus'):
            status_map = {0: 'Draft', 1: 'Submitted', 2: 'Cancelled'}
            text_parts.append(f"Document Status: {status_map.get(document['docstatus'], 'Unknown')}")
        
        return " | ".join(text_parts)
    
    def create_document_metadata(self, doctype: str, document: Dict[str, Any]) -> Dict[str, Any]:
        """Create metadata for the document"""
        metadata = {
            'doctype': doctype,
            'name': document.get('name', ''),
            'creation': document.get('creation', ''),
            'modified': document.get('modified', ''),
            'owner': document.get('owner', ''),
            'docstatus': document.get('docstatus', 0)
        }
        
        # Add common business fields
        for field in ['customer', 'supplier', 'company', 'status', 'item_code']:
            if document.get(field):
                metadata[field] = str(document[field])
        
        return {k: v for k, v in metadata.items() if v}  # Remove empty values
    
    def index_doctype(self, doctype: str, limit: int = 100) -> Dict[str, Any]:
        """Index documents from a specific DocType"""
        results = {
            'doctype': doctype,
            'total_processed': 0,
            'successfully_indexed': 0,
            'errors': []
        }
        
        try:
            # Get collection for this doctype
            collection_name = f"erpnext_{doctype.lower().replace(' ', '_')}"
            collection = self.get_or_create_collection(collection_name)
            
            # Get documents from ERPNext
            documents = self.erpnext.get_sample_documents(doctype, limit)
            
            if not documents:
                logger.warning(f"No documents found for DocType: {doctype}")
                return results
            
            # Process documents in batches
            batch_size = 10
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i + batch_size]
                self._index_document_batch(collection, doctype, batch, results)
            
            results['total_processed'] = len(documents)
            logger.info(f"Indexed {results['successfully_indexed']}/{len(documents)} documents from {doctype}")
            
        except Exception as e:
            error_msg = f"Error indexing DocType {doctype}: {str(e)}"
            logger.error(error_msg)
            results['errors'].append(error_msg)
        
        return results
    
    def _index_document_batch(self, collection: chromadb.Collection, doctype: str, 
                             batch: List[Dict[str, Any]], results: Dict[str, Any]):
        """Index a batch of documents"""
        try:
            ids = []
            documents = []
            metadatas = []
            
            for doc in batch:
                try:
                    # Create document ID
                    doc_id = self.create_document_id(doctype, doc.get('name', ''))
                    
                    # Extract text content
                    text_content = self.extract_text_content(doc)
                    if not text_content.strip():
                        continue
                    
                    # Create metadata
                    metadata = self.create_document_metadata(doctype, doc)
                    
                    ids.append(doc_id)
                    documents.append(text_content)
                    metadatas.append(metadata)
                    
                except Exception as e:
                    results['errors'].append(f"Error processing document {doc.get('name', '')}: {str(e)}")
            
            if ids:
                # Add to collection
                collection.add(
                    ids=ids,
                    documents=documents,
                    metadatas=metadatas
                )
                results['successfully_indexed'] += len(ids)
                
        except Exception as e:
            results['errors'].append(f"Error adding batch to collection: {str(e)}")
    
    def index_common_doctypes(self) -> Dict[str, Any]:
        """Index common ERPNext DocTypes"""
        
        # Connect to ERPNext first
        connection_status = self.erpnext.test_connection()
        if not connection_status['connected']:
            return {
                'error': 'Could not connect to ERPNext',
                'connection_status': connection_status
            }
        
        # Common DocTypes to index
        common_doctypes = [
            'Customer', 'Supplier', 'Item', 'Sales Order', 'Purchase Order',
            'Sales Invoice', 'Purchase Invoice', 'Quotation', 'Lead',
            'Opportunity', 'Project', 'Task', 'Issue', 'Employee'
        ]
        
        results = {
            'connection_status': connection_status,
            'indexing_results': {},
            'summary': {'total_doctypes': 0, 'successful_doctypes': 0, 'total_documents': 0}
        }
        
        for doctype in common_doctypes:
            logger.info(f"Indexing DocType: {doctype}")
            doctype_results = self.index_doctype(doctype, limit=50)  # Limit for testing
            results['indexing_results'][doctype] = doctype_results
            
            results['summary']['total_doctypes'] += 1
            if doctype_results['successfully_indexed'] > 0:
                results['summary']['successful_doctypes'] += 1
                results['summary']['total_documents'] += doctype_results['successfully_indexed']
        
        return results
    
    def search_documents(self, query: str, n_results: int = 10) -> List[Dict[str, Any]]:
        """Search indexed documents"""
        try:
            # Get all collections
            collections = self.chroma_client.list_collections()
            all_results = []
            
            for collection in collections:
                try:
                    results = collection.query(
                        query_texts=[query],
                        n_results=min(n_results, collection.count())
                    )
                    
                    # Format results
                    for i, doc_id in enumerate(results['ids'][0]):
                        all_results.append({
                            'id': doc_id,
                            'document': results['documents'][0][i],
                            'metadata': results['metadatas'][0][i],
                            'distance': results['distances'][0][i],
                            'collection': collection.name
                        })
                        
                except Exception as e:
                    logger.error(f"Error searching collection {collection.name}: {e}")
            
            # Sort by distance (lower is better)
            all_results.sort(key=lambda x: x['distance'])
            return all_results[:n_results]
            
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return []
    
    def get_indexing_status(self) -> Dict[str, Any]:
        """Get current indexing status"""
        try:
            collections = self.chroma_client.list_collections()
            status = {
                'total_collections': len(collections),
                'collections': {},
                'total_documents': 0
            }
            
            for collection in collections:
                count = collection.count()
                status['collections'][collection.name] = {
                    'document_count': count,
                    'metadata': collection.metadata
                }
                status['total_documents'] += count
            
            return status
            
        except Exception as e:
            return {'error': str(e)}

def main():
    """Test the indexer"""
    indexer = ERPNextDocumentIndexer()
    
    print("🔍 Testing Document Indexer...")
    
    # Check current status
    status = indexer.get_indexing_status()
    print(f"Current Status: {status}")
    
    # Try to index common DocTypes
    print("\n📋 Starting ERPNext Document Indexing...")
    results = indexer.index_common_doctypes()
    
    print(f"Connection Status: {results.get('connection_status', {}).get('connected', False)}")
    print(f"Summary: {results.get('summary', {})}")
    
    # Test search if we have documents
    if results.get('summary', {}).get('total_documents', 0) > 0:
        print("\n🔍 Testing Search...")
        search_results = indexer.search_documents("customer order")
        print(f"Found {len(search_results)} results for 'customer order'")

if __name__ == "__main__":
    main()