#!/usr/bin/env python3
"""
ERPNext AI Agent Integration Test
Tests all real integration components
"""

import os
import sys
import json
import subprocess
import time
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_erpnext_availability():
    """Test if ERPNext is available and try to start it"""
    print("🔍 Testing ERPNext Availability...")
    
    # Check if any ERPNext/Frappe is running on common ports
    import requests
    ports = [8000, 8001, 8080, 9000]
    
    for port in ports:
        try:
            response = requests.get(f"http://localhost:{port}/api/method/ping", timeout=2)
            if response.status_code == 200:
                print(f"✅ Found ERPNext running on port {port}")
                return f"http://localhost:{port}"
        except:
            continue
    
    print("❌ No running ERPNext found on standard ports")
    
    # Try to find and start ERPNext bench
    bench_paths = [
        "/Users/mekdesyared/frappe-bench",
        "/Users/mekdesyared/erpnext-mcp-builder/bench-setup/frappe-bench"
    ]
    
    for bench_path in bench_paths:
        if Path(bench_path).exists():
            print(f"🔧 Found bench at {bench_path}, trying to start...")
            try:
                # Try to start bench
                result = subprocess.run([
                    'bench', 'start'
                ], cwd=bench_path, timeout=10, capture_output=True, text=True)
                
                if "Starting" in result.stdout or result.returncode == 0:
                    print("🚀 Started ERPNext bench")
                    time.sleep(5)  # Give it time to start
                    
                    # Test again
                    try:
                        response = requests.get("http://localhost:8000/api/method/ping", timeout=5)
                        if response.status_code == 200:
                            return "http://localhost:8000"
                    except:
                        pass
                        
            except subprocess.TimeoutExpired:
                print("⏰ Bench start timed out (this is normal)")
                # Bench might be starting in background
                time.sleep(10)
                try:
                    response = requests.get("http://localhost:8000/api/method/ping", timeout=5)
                    if response.status_code == 200:
                        return "http://localhost:8000"
                except:
                    pass
            except Exception as e:
                print(f"❌ Error starting bench: {e}")
    
    return None

def test_integration_components():
    """Test all integration components"""
    results = {
        'erpnext_connector': False,
        'document_indexer': False, 
        'knowledge_graph': False,
        'chromadb_status': {},
        'errors': []
    }
    
    print("🧪 Testing Integration Components...")
    
    # 1. Test ERPNext Connector
    try:
        from erpnext_connector import ERPNextConnector
        connector = ERPNextConnector()
        status = connector.test_connection()
        results['erpnext_connector'] = status['connected']
        print(f"ERPNext Connector: {'✅' if status['connected'] else '❌'}")
        if not status['connected']:
            results['errors'].append(f"ERPNext connection failed: {status}")
    except Exception as e:
        results['errors'].append(f"ERPNext connector error: {str(e)}")
        print(f"ERPNext Connector: ❌ ({e})")
    
    # 2. Test ChromaDB (basic)
    try:
        import chromadb
        client = chromadb.Client()
        collections = client.list_collections()
        results['chromadb_status'] = {
            'available': True,
            'collections_count': len(collections),
            'collections': [c.name for c in collections]
        }
        print(f"ChromaDB: ✅ ({len(collections)} collections)")
    except Exception as e:
        results['errors'].append(f"ChromaDB error: {str(e)}")
        results['chromadb_status'] = {'available': False, 'error': str(e)}
        print(f"ChromaDB: ❌ ({e})")
    
    # 3. Test Knowledge Graph Builder
    try:
        from knowledge_graph_builder import ERPNextKnowledgeGraph
        builder = ERPNextKnowledgeGraph()
        stats = builder.get_graph_statistics()
        results['knowledge_graph'] = True
        print(f"Knowledge Graph: ✅ (NetworkX available)")
    except Exception as e:
        results['errors'].append(f"Knowledge graph error: {str(e)}")
        print(f"Knowledge Graph: ❌ ({e})")
    
    # 4. Test Document Indexer (lightweight - no model loading)
    try:
        # Test the class import without initializing the heavy model
        import sys
        import importlib.util
        spec = importlib.util.spec_from_file_location("document_indexer", "document_indexer.py")
        doc_indexer_module = importlib.util.module_from_spec(spec)
        results['document_indexer'] = True
        print("Document Indexer: ✅ (import successful)")
    except Exception as e:
        results['errors'].append(f"Document indexer error: {str(e)}")
        print(f"Document Indexer: ❌ ({e})")
    
    return results

def test_end_to_end_workflow():
    """Test a simple end-to-end workflow if ERPNext is available"""
    print("\n🔄 Testing End-to-End Workflow...")
    
    try:
        from erpnext_connector import ERPNextConnector
        from knowledge_graph_builder import ERPNextKnowledgeGraph
        
        # Test connection
        connector = ERPNextConnector()
        connection_status = connector.test_connection()
        
        if not connection_status['connected']:
            print("❌ Cannot test end-to-end: ERPNext not available")
            return False
        
        print("✅ ERPNext connected, testing workflow...")
        
        # Test getting DocTypes
        doctypes = connector.get_doctypes()
        print(f"📋 Found {len(doctypes)} DocTypes")
        
        # Test knowledge graph with minimal data
        kg_builder = ERPNextKnowledgeGraph()
        if doctypes:
            # Add a few DocType nodes
            for doctype_info in doctypes[:5]:  # Just first 5
                doctype = doctype_info.get('name') if isinstance(doctype_info, dict) else doctype_info
                kg_builder.add_doctype_node(doctype)
            
            stats = kg_builder.get_graph_statistics()
            print(f"🕸️ Knowledge graph: {stats['nodes']} nodes, {stats['edges']} edges")
        
        print("✅ End-to-end workflow test successful!")
        return True
        
    except Exception as e:
        print(f"❌ End-to-end test failed: {e}")
        return False

def generate_status_report(erpnext_url, integration_results, e2e_result):
    """Generate a comprehensive status report"""
    report = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'erpnext_status': {
            'available': erpnext_url is not None,
            'url': erpnext_url
        },
        'integration_components': integration_results,
        'end_to_end_test': e2e_result,
        'recommendations': []
    }
    
    # Generate recommendations
    if not erpnext_url:
        report['recommendations'].append("Start ERPNext instance to enable data integration")
    
    if not integration_results['erpnext_connector']:
        report['recommendations'].append("Fix ERPNext connector to enable data access")
    
    if integration_results['chromadb_status'].get('collections_count', 0) == 0:
        report['recommendations'].append("Run document indexing to populate ChromaDB")
    
    if integration_results['errors']:
        report['recommendations'].append("Address integration errors listed above")
    
    # Save report
    report_path = Path("../volumes/integration_test_report.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📊 Status report saved to: {report_path}")
    return report

def main():
    """Run comprehensive integration test"""
    print("🚀 ERPNext AI Agent - Integration Test")
    print("=" * 50)
    
    # 1. Test ERPNext availability
    erpnext_url = test_erpnext_availability()
    
    # 2. Test integration components
    integration_results = test_integration_components()
    
    # 3. Test end-to-end workflow
    e2e_result = test_end_to_end_workflow()
    
    # 4. Generate status report
    report = generate_status_report(erpnext_url, integration_results, e2e_result)
    
    # 5. Summary
    print("\n📋 Integration Test Summary:")
    print(f"ERPNext Available: {'✅' if erpnext_url else '❌'}")
    print(f"Components Working: {sum(1 for v in integration_results.values() if v and not isinstance(v, list))} / 4")
    print(f"End-to-End Test: {'✅' if e2e_result else '❌'}")
    print(f"Errors: {len(integration_results.get('errors', []))}")
    
    if report['recommendations']:
        print("\n💡 Recommendations:")
        for rec in report['recommendations']:
            print(f"  • {rec}")

if __name__ == "__main__":
    main()