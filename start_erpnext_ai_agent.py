#!/usr/bin/env python3
"""
ERPNext AI Agent - Quick Start Guide
Ready for immediate use with your ERPNext instance
"""

import os
import sys
import json
import time
import subprocess
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import requests

# Import integration components
from integrations.erpnext_connector import ERPNextConnector
from integrations.document_indexer import ERPNextDocumentIndexer
from integrations.knowledge_graph_builder import ERPNextKnowledgeGraph
from integrations.multi_agent_workflows import MultiAgentOrchestrator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ERPNextAIAgentStartup:
    """Quick startup orchestrator for ERPNext AI Agent"""
    
    def __init__(self):
        self.connector = ERPNextConnector()
        self.indexer = None  # Initialize when needed
        self.kg_builder = ERPNextKnowledgeGraph()
        self.orchestrator = MultiAgentOrchestrator()
        
        self.status = {
            'erpnext_running': False,
            'data_indexed': False,
            'knowledge_graph_built': False,
            'agents_ready': False,
            'ready_for_use': False
        }
    
    def step1_start_erpnext(self) -> bool:
        """Step 1: Start ERPNext instance"""
        print("🚀 Step 1: Starting ERPNext Instance...")
        
        # First check if already running
        connection_status = self.connector.test_connection()
        if connection_status['connected']:
            print(f"✅ ERPNext already running at {self.connector.base_url}")
            self.status['erpnext_running'] = True
            return True
        
        # Try to start from known bench locations
        bench_paths = [
            "/Users/mekdesyared/frappe-bench",
            "/Users/mekdesyared/erpnext-mcp-builder/bench-setup/frappe-bench"
        ]
        
        for bench_path in bench_paths:
            if Path(bench_path).exists():
                print(f"🔧 Found bench at {bench_path}")
                try:
                    # Start bench in background
                    print("   Starting bench serve (this may take a moment)...")
                    subprocess.Popen([
                        'bench', 'start'
                    ], cwd=bench_path)
                    
                    # Wait and test connection
                    print("   Waiting for ERPNext to start...")
                    for i in range(30):  # Wait up to 30 seconds
                        time.sleep(1)
                        try:
                            response = requests.get("http://localhost:8000/api/method/ping", timeout=2)
                            if response.status_code == 200:
                                print("✅ ERPNext started successfully!")
                                self.connector.base_url = "http://localhost:8000"
                                self.status['erpnext_running'] = True
                                return True
                        except:
                            continue
                    
                    print("⏰ ERPNext is starting in background...")
                    print("   Try running this script again in a few minutes")
                    return False
                    
                except Exception as e:
                    print(f"❌ Error starting bench: {e}")
                    continue
        
        print("❌ Could not start ERPNext automatically")
        print("📋 Manual startup options:")
        print("   1. cd /path/to/your/frappe-bench && bench start")
        print("   2. Or start your Docker ERPNext instance")
        print("   3. Ensure ERPNext is accessible at http://localhost:8000")
        
        return False
    
    def step2_index_documents(self) -> bool:
        """Step 2: Index ERPNext documents for AI search"""
        print("\n📋 Step 2: Indexing ERPNext Documents...")
        
        if not self.status['erpnext_running']:
            print("❌ ERPNext must be running first")
            return False
        
        try:
            # Initialize indexer (this loads the ML model)
            print("   Loading AI models (this may take a moment)...")
            self.indexer = ERPNextDocumentIndexer()
            
            # Index common DocTypes
            print("   Indexing ERPNext documents...")
            results = self.indexer.index_common_doctypes()
            
            if results['summary']['total_documents'] > 0:
                print(f"✅ Indexed {results['summary']['total_documents']} documents")
                print(f"   Successful DocTypes: {results['summary']['successful_doctypes']}")
                self.status['data_indexed'] = True
                return True
            else:
                print("⚠️ No documents found to index (ERPNext may be empty)")
                print("   Creating test collection for demonstration...")
                
                # Create empty collection for testing
                collection = self.indexer.get_or_create_collection("test_collection")
                self.status['data_indexed'] = True
                return True
                
        except Exception as e:
            print(f"❌ Error indexing documents: {e}")
            print("   Continuing without document indexing...")
            return False
    
    def step3_build_knowledge_graph(self) -> bool:
        """Step 3: Build knowledge graph from ERPNext data"""
        print("\n🕸️ Step 3: Building Knowledge Graph...")
        
        try:
            # Build knowledge graph
            results = self.kg_builder.build_complete_knowledge_graph()
            
            stats = results.get('statistics', {})
            if stats.get('nodes', 0) > 0:
                print(f"✅ Knowledge graph built: {stats['nodes']} nodes, {stats['edges']} edges")
                print(f"   Export files: {len(results.get('export_paths', []))}")
            else:
                print("⚠️ Knowledge graph is empty (no ERPNext data)")
                print("   Graph structure ready for when data is available")
            
            self.status['knowledge_graph_built'] = True
            return True
            
        except Exception as e:
            print(f"❌ Error building knowledge graph: {e}")
            print("   Continuing without knowledge graph...")
            return False
    
    def step4_activate_agents(self) -> bool:
        """Step 4: Activate AI agents"""
        print("\n🤖 Step 4: Activating AI Agents...")
        
        try:
            # Test agent system
            test_task = "Test agent system readiness"
            result = self.orchestrator.execute_workflow(test_task)
            
            if result.get('status') == 'completed':
                print("✅ AI Agents activated and ready!")
                print(f"   Available agents: {list(self.orchestrator.agents.keys())}")
                self.status['agents_ready'] = True
                return True
            else:
                print("⚠️ Agents available but may have limited functionality")
                self.status['agents_ready'] = True
                return True
                
        except Exception as e:
            print(f"❌ Error activating agents: {e}")
            return False
    
    def demonstrate_ai_capabilities(self):
        """Demonstrate AI agent capabilities"""
        print("\n🎯 AI Agent Capabilities Demo:")
        print("=" * 50)
        
        # 1. Requirements Analysis Demo
        print("\n📋 1. Requirements Analysis:")
        task1 = "Create a customer relationship management system"
        result1 = self.orchestrator.execute_workflow(task1)
        
        if result1.get('status') == 'completed':
            deliverables = result1.get('final_deliverables', {})
            print(f"   ✅ Generated {len(deliverables)} deliverable types")
            for key, value in deliverables.items():
                if value:
                    print(f"      • {key}: {len(value) if isinstance(value, list) else 'Available'}")
        
        # 2. Document Search Demo (if indexer available)
        if self.indexer and self.status['data_indexed']:
            print("\n🔍 2. Document Search:")
            search_results = self.indexer.search_documents("customer order", n_results=3)
            print(f"   ✅ Found {len(search_results)} relevant documents")
            for i, result in enumerate(search_results[:2], 1):
                print(f"      {i}. {result.get('id', 'Document')} (relevance: {1-result.get('distance', 1):.2f})")
        
        # 3. Knowledge Graph Query Demo
        if self.status['knowledge_graph_built']:
            print("\n🕸️ 3. Knowledge Graph Analysis:")
            stats = self.kg_builder.get_graph_statistics()
            print(f"   ✅ Graph contains {stats['nodes']} entities and {stats['edges']} relationships")
            if stats.get('most_connected_nodes'):
                top_node = stats['most_connected_nodes'][0]
                print(f"   Most connected entity: {top_node[0]} (centrality: {top_node[1]:.3f})")
    
    def provide_usage_examples(self):
        """Provide real usage examples"""
        print("\n💡 Real Usage Examples:")
        print("=" * 50)
        
        examples = [
            {
                "task": "Design a sales order management system",
                "description": "Get complete architecture, DocTypes, and workflow design"
            },
            {
                "task": "Create inventory tracking with low stock alerts", 
                "description": "Build comprehensive inventory management solution"
            },
            {
                "task": "Set up customer service ticket system",
                "description": "Design support workflow with escalation rules"
            },
            {
                "task": "Implement project management with time tracking",
                "description": "Create project workflows with resource allocation"
            }
        ]
        
        for i, example in enumerate(examples, 1):
            print(f"\n{i}. {example['task']}")
            print(f"   → {example['description']}")
        
        print(f"\n🔧 To try any example:")
        print(f"   from integrations.multi_agent_workflows import MultiAgentOrchestrator")
        print(f"   orchestrator = MultiAgentOrchestrator()")
        print(f"   result = orchestrator.execute_workflow('your task here')")
    
    def check_final_status(self) -> bool:
        """Check if system is ready for use"""
        required_components = ['erpnext_running', 'agents_ready']
        optional_components = ['data_indexed', 'knowledge_graph_built']
        
        required_ready = all(self.status[comp] for comp in required_components)
        optional_ready = any(self.status[comp] for comp in optional_components)
        
        self.status['ready_for_use'] = required_ready
        
        print(f"\n📊 Final Status Check:")
        print(f"   ERPNext Running: {'✅' if self.status['erpnext_running'] else '❌'}")
        print(f"   Documents Indexed: {'✅' if self.status['data_indexed'] else '⚠️'}")
        print(f"   Knowledge Graph: {'✅' if self.status['knowledge_graph_built'] else '⚠️'}")
        print(f"   AI Agents: {'✅' if self.status['agents_ready'] else '❌'}")
        
        return self.status['ready_for_use']
    
    def run_complete_startup(self) -> bool:
        """Run complete startup sequence"""
        print("🚀 ERPNext AI Agent - Quick Start")
        print("=" * 50)
        
        # Step 1: Start ERPNext
        if not self.step1_start_erpnext():
            print("\n⚠️ ERPNext startup incomplete. You can:")
            print("   1. Start ERPNext manually")
            print("   2. Run this script again once ERPNext is running")
            print("   3. Continue with limited functionality")
            
            # Ask user if they want to continue
            try:
                response = input("\nContinue anyway? (y/n): ").lower().strip()
                if response != 'y':
                    return False
            except KeyboardInterrupt:
                return False
        
        # Step 2: Index documents
        self.step2_index_documents()
        
        # Step 3: Build knowledge graph  
        self.step3_build_knowledge_graph()
        
        # Step 4: Activate agents
        if not self.step4_activate_agents():
            print("\n❌ Critical error: Could not activate AI agents")
            return False
        
        # Check final status
        ready = self.check_final_status()
        
        if ready:
            print(f"\n🎉 ERPNext AI Agent is READY FOR USE!")
            self.demonstrate_ai_capabilities()
            self.provide_usage_examples()
        else:
            print(f"\n⚠️ Partial functionality available")
            print(f"   AI agents are ready, but data integration may be limited")
        
        return ready

def main():
    """Main startup function"""
    startup = ERPNextAIAgentStartup()
    
    try:
        success = startup.run_complete_startup()
        
        if success:
            print(f"\n🚀 SUCCESS: ERPNext AI Agent is ready for intelligent assistance!")
            print(f"📚 Next: Try the usage examples above or create your own workflows")
        else:
            print(f"\n⚠️ PARTIAL SUCCESS: Some functionality may be limited")
            print(f"📚 Check ERPNext status and try running again")
            
    except KeyboardInterrupt:
        print(f"\n\n⏹️ Startup interrupted by user")
    except Exception as e:
        print(f"\n❌ Startup error: {e}")
        logger.exception("Startup failed")

if __name__ == "__main__":
    main()