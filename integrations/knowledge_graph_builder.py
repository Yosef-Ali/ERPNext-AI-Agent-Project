#!/usr/bin/env python3
"""
ERPNext Knowledge Graph Builder
Creates knowledge graphs from real ERPNext DocTypes and relationships
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import networkx as nx
import pandas as pd
from collections import defaultdict

from erpnext_connector import ERPNextConnector

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ERPNextKnowledgeGraph:
    """Build knowledge graphs from ERPNext data"""
    
    def __init__(self, output_dir: str = "../volumes/knowledge_graphs"):
        self.output_dir = Path(output_dir).absolute()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize NetworkX graph
        self.graph = nx.MultiDiGraph()
        
        # Initialize ERPNext connector
        self.erpnext = ERPNextConnector()
        
        # DocType relationships mapping
        self.known_relationships = {
            'Customer': ['Sales Order', 'Sales Invoice', 'Quotation', 'Opportunity'],
            'Supplier': ['Purchase Order', 'Purchase Invoice', 'Request for Quotation'],
            'Item': ['Sales Order Item', 'Purchase Order Item', 'Stock Entry'],
            'Project': ['Task', 'Timesheet', 'Project Update'],
            'Employee': ['Task', 'Timesheet', 'Leave Application', 'Expense Claim'],
            'Sales Order': ['Sales Invoice', 'Delivery Note', 'Sales Order Item'],
            'Purchase Order': ['Purchase Invoice', 'Purchase Receipt', 'Purchase Order Item'],
        }
        
        logger.info(f"Knowledge Graph Builder initialized, output: {self.output_dir}")
    
    def discover_doctype_relationships(self, doctype: str) -> Dict[str, List[str]]:
        """Discover relationships for a DocType by analyzing its schema"""
        relationships = {
            'links_to': [],      # Link fields pointing to other DocTypes
            'linked_from': [],   # DocTypes that link to this one
            'child_tables': []   # Child table DocTypes
        }
        
        try:
            schema = self.erpnext.get_doctype_schema(doctype)
            if not schema:
                return relationships
            
            # Analyze fields for relationships
            fields = schema.get('fields', [])
            for field in fields:
                field_type = field.get('fieldtype')
                
                if field_type == 'Link' and field.get('options'):
                    # This DocType links to another
                    linked_doctype = field['options']
                    relationships['links_to'].append(linked_doctype)
                    
                elif field_type == 'Table' and field.get('options'):
                    # This DocType has a child table
                    child_doctype = field['options']
                    relationships['child_tables'].append(child_doctype)
            
            # Use known relationships as fallback
            if doctype in self.known_relationships:
                relationships['links_to'].extend(self.known_relationships[doctype])
                
        except Exception as e:
            logger.error(f"Error discovering relationships for {doctype}: {e}")
            
        return relationships
    
    def add_doctype_node(self, doctype: str, metadata: Dict[str, Any] = None):
        """Add a DocType as a node in the knowledge graph"""
        if metadata is None:
            metadata = {}
            
        # Get DocType schema for metadata
        schema = self.erpnext.get_doctype_schema(doctype)
        if schema:
            metadata.update({
                'node_type': 'doctype',
                'module': schema.get('module', 'Unknown'),
                'is_custom': schema.get('custom', 0),
                'is_virtual': schema.get('is_virtual', 0),
                'field_count': len(schema.get('fields', [])),
                'has_web_view': bool(schema.get('has_web_view', 0)),
                'is_submittable': bool(schema.get('is_submittable', 0)),
            })
        
        self.graph.add_node(doctype, **metadata)
        logger.debug(f"Added DocType node: {doctype}")
    
    def add_document_node(self, doctype: str, doc_name: str, doc_data: Dict[str, Any]):
        """Add a specific document as a node"""
        node_id = f"{doctype}::{doc_name}"
        
        metadata = {
            'node_type': 'document',
            'doctype': doctype,
            'name': doc_name,
            'status': doc_data.get('status', 'Unknown'),
            'docstatus': doc_data.get('docstatus', 0),
            'creation': doc_data.get('creation', ''),
            'modified': doc_data.get('modified', ''),
        }
        
        # Add business-specific metadata
        for field in ['customer', 'supplier', 'company', 'item_code', 'project']:
            if doc_data.get(field):
                metadata[field] = str(doc_data[field])
        
        self.graph.add_node(node_id, **metadata)
        
        # Connect to DocType
        self.graph.add_edge(node_id, doctype, relationship='instance_of')
        
        return node_id
    
    def add_relationship_edge(self, from_node: str, to_node: str, 
                            relationship_type: str, metadata: Dict[str, Any] = None):
        """Add a relationship edge between nodes"""
        if metadata is None:
            metadata = {}
            
        metadata['relationship_type'] = relationship_type
        metadata['created_at'] = datetime.now().isoformat()
        
        self.graph.add_edge(from_node, to_node, **metadata)
        logger.debug(f"Added relationship: {from_node} -[{relationship_type}]-> {to_node}")
    
    def build_doctype_schema_graph(self) -> Dict[str, Any]:
        """Build a graph of DocType schemas and their relationships"""
        results = {
            'doctypes_processed': 0,
            'relationships_found': 0,
            'errors': []
        }
        
        # Connect to ERPNext
        connection_status = self.erpnext.test_connection()
        if not connection_status['connected']:
            results['error'] = 'Could not connect to ERPNext'
            return results
        
        # Get all DocTypes
        doctypes = self.erpnext.get_doctypes()
        if not doctypes:
            results['error'] = 'No DocTypes found'
            return results
        
        # Add DocType nodes
        for doctype_info in doctypes:
            doctype = doctype_info.get('name') if isinstance(doctype_info, dict) else doctype_info
            try:
                self.add_doctype_node(doctype)
                results['doctypes_processed'] += 1
            except Exception as e:
                results['errors'].append(f"Error adding DocType {doctype}: {str(e)}")
        
        # Add relationships between DocTypes
        for doctype_info in doctypes:
            doctype = doctype_info.get('name') if isinstance(doctype_info, dict) else doctype_info
            try:
                relationships = self.discover_doctype_relationships(doctype)
                
                # Add link relationships
                for linked_doctype in relationships.get('links_to', []):
                    if self.graph.has_node(linked_doctype):
                        self.add_relationship_edge(doctype, linked_doctype, 'links_to')
                        results['relationships_found'] += 1
                
                # Add child table relationships
                for child_doctype in relationships.get('child_tables', []):
                    if self.graph.has_node(child_doctype):
                        self.add_relationship_edge(doctype, child_doctype, 'has_child_table')
                        results['relationships_found'] += 1
                        
            except Exception as e:
                results['errors'].append(f"Error adding relationships for {doctype}: {str(e)}")
        
        return results
    
    def build_document_relationship_graph(self, doctype: str, limit: int = 20) -> Dict[str, Any]:
        """Build a graph of actual document relationships"""
        results = {
            'doctype': doctype,
            'documents_processed': 0,
            'relationships_found': 0,
            'errors': []
        }
        
        try:
            # Get sample documents
            documents = self.erpnext.get_sample_documents(doctype, limit)
            if not documents:
                results['error'] = f'No documents found for {doctype}'
                return results
            
            # Add document nodes
            document_nodes = []
            for doc in documents:
                try:
                    doc_name = doc.get('name')
                    if doc_name:
                        node_id = self.add_document_node(doctype, doc_name, doc)
                        document_nodes.append((node_id, doc))
                        results['documents_processed'] += 1
                except Exception as e:
                    results['errors'].append(f"Error adding document {doc.get('name', '')}: {str(e)}")
            
            # Find relationships between documents
            for node_id, doc in document_nodes:
                try:
                    # Look for link fields that reference other documents
                    for field_name, field_value in doc.items():
                        if field_value and isinstance(field_value, str):
                            # Check if this looks like a reference to another document
                            for other_node_id, other_doc in document_nodes:
                                if other_node_id != node_id and other_doc.get('name') == field_value:
                                    self.add_relationship_edge(node_id, other_node_id, f'references_{field_name}')
                                    results['relationships_found'] += 1
                                    
                except Exception as e:
                    results['errors'].append(f"Error finding relationships for {node_id}: {str(e)}")
            
        except Exception as e:
            results['error'] = str(e)
        
        return results
    
    def export_graph(self, format: str = 'graphml') -> str:
        """Export the knowledge graph to a file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"erpnext_knowledge_graph_{timestamp}.{format}"
        filepath = self.output_dir / filename
        
        try:
            if format == 'graphml':
                nx.write_graphml(self.graph, filepath)
            elif format == 'json':
                graph_data = nx.node_link_data(self.graph)
                with open(filepath, 'w') as f:
                    json.dump(graph_data, f, indent=2, default=str)
            elif format == 'gexf':
                nx.write_gexf(self.graph, filepath)
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            logger.info(f"Exported knowledge graph to: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error exporting graph: {e}")
            raise
    
    def get_graph_statistics(self) -> Dict[str, Any]:
        """Get statistics about the current graph"""
        stats = {
            'nodes': self.graph.number_of_nodes(),
            'edges': self.graph.number_of_edges(),
            'node_types': {},
            'relationship_types': {},
            'most_connected_nodes': []
        }
        
        # Count node types
        for node, data in self.graph.nodes(data=True):
            node_type = data.get('node_type', 'unknown')
            stats['node_types'][node_type] = stats['node_types'].get(node_type, 0) + 1
        
        # Count relationship types
        for u, v, data in self.graph.edges(data=True):
            rel_type = data.get('relationship_type', 'unknown')
            stats['relationship_types'][rel_type] = stats['relationship_types'].get(rel_type, 0) + 1
        
        # Find most connected nodes
        degree_centrality = nx.degree_centrality(self.graph)
        most_connected = sorted(degree_centrality.items(), key=lambda x: x[1], reverse=True)[:10]
        stats['most_connected_nodes'] = most_connected
        
        return stats
    
    def build_complete_knowledge_graph(self) -> Dict[str, Any]:
        """Build a complete knowledge graph from ERPNext data"""
        logger.info("Starting complete knowledge graph build...")
        
        results = {
            'schema_graph': {},
            'document_graphs': {},
            'export_paths': [],
            'statistics': {}
        }
        
        # 1. Build DocType schema graph
        logger.info("Building DocType schema graph...")
        results['schema_graph'] = self.build_doctype_schema_graph()
        
        # 2. Build document graphs for key DocTypes
        key_doctypes = ['Customer', 'Item', 'Sales Order', 'Purchase Order', 'Project']
        for doctype in key_doctypes:
            logger.info(f"Building document graph for {doctype}...")
            results['document_graphs'][doctype] = self.build_document_relationship_graph(doctype, limit=10)
        
        # 3. Export graphs
        try:
            for fmt in ['json', 'graphml']:
                export_path = self.export_graph(fmt)
                results['export_paths'].append(export_path)
        except Exception as e:
            logger.error(f"Error exporting graphs: {e}")
        
        # 4. Generate statistics
        results['statistics'] = self.get_graph_statistics()
        
        logger.info("Knowledge graph build complete!")
        return results

def main():
    """Test the knowledge graph builder"""
    builder = ERPNextKnowledgeGraph()
    
    print("🔍 Testing Knowledge Graph Builder...")
    
    # Build complete knowledge graph
    results = builder.build_complete_knowledge_graph()
    
    print(f"Schema Graph: {results.get('schema_graph', {})}")
    print(f"Statistics: {results.get('statistics', {})}")
    print(f"Export Paths: {results.get('export_paths', [])}")

if __name__ == "__main__":
    main()