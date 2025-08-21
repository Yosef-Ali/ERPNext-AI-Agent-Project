#!/usr/bin/env python3
"""
ERPNext MCP Server Configuration
Configures the Frappe MCP server to work with real ERPNext instances
"""

import os
import json
import subprocess
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import yaml

from erpnext_connector import ERPNextConnector

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ERPNextMCPConfig:
    """Configure MCP server for ERPNext integration"""
    
    def __init__(self, config_dir: str = "../config"):
        self.config_dir = Path(config_dir).absolute()
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.erpnext = ERPNextConnector()
        
        # MCP server configuration paths
        self.mcp_config_path = self.config_dir / "mcp_server_config.json"
        self.claude_config_path = Path.home() / ".claude" / "claude_desktop_config.json"
        
        logger.info(f"MCP Config initialized, config dir: {self.config_dir}")
    
    def detect_erpnext_instances(self) -> List[Dict[str, Any]]:
        """Detect available ERPNext instances"""
        instances = []
        
        # Test connection
        connection_status = self.erpnext.test_connection()
        
        if connection_status['connected']:
            instance = {
                'name': 'primary',
                'method': connection_status['method'],
                'details': connection_status['details'],
                'status': 'active'
            }
            
            if connection_status['method'] == 'api':
                instance.update({
                    'type': 'api',
                    'url': self.erpnext.base_url,
                    'api_key': getattr(self.erpnext, 'api_key', ''),
                    'api_secret': getattr(self.erpnext, 'api_secret', '')
                })
            elif connection_status['method'] == 'bench':
                instance.update({
                    'type': 'bench',
                    'bench_path': connection_status['details'].get('bench_path'),
                    'site_name': connection_status['details'].get('site_name')
                })
            
            instances.append(instance)
        
        return instances
    
    def generate_mcp_server_config(self) -> Dict[str, Any]:
        """Generate MCP server configuration"""
        instances = self.detect_erpnext_instances()
        
        if not instances:
            logger.warning("No ERPNext instances detected for MCP configuration")
            return {}
        
        primary_instance = instances[0]
        
        config = {
            "server": {
                "name": "erpnext-ai-agent",
                "version": "1.0.0",
                "description": "AI-powered ERPNext assistant with multi-agent workflows"
            },
            "erpnext": {
                "instances": instances,
                "primary_instance": primary_instance['name']
            },
            "ai_capabilities": {
                "document_indexing": {
                    "enabled": True,
                    "chromadb_path": "../volumes/chroma",
                    "model": "sentence-transformers/all-MiniLM-L6-v2"
                },
                "knowledge_graph": {
                    "enabled": True,
                    "output_path": "../volumes/knowledge_graphs",
                    "export_formats": ["json", "graphml"]
                },
                "multi_agent": {
                    "enabled": True,
                    "agents": [
                        "requirements-analyzer",
                        "erpnext-architect", 
                        "db-architect",
                        "frontend-developer",
                        "integration-specialist",
                        "test-engineer"
                    ]
                }
            },
            "tools": [
                {
                    "name": "search_documents",
                    "description": "Semantic search across ERPNext documents",
                    "function": "document_indexer.search_documents"
                },
                {
                    "name": "analyze_requirements", 
                    "description": "Convert business requirements to technical specifications",
                    "function": "multi_agent_workflows.requirements_analyzer"
                },
                {
                    "name": "design_architecture",
                    "description": "Design ERPNext system architecture",
                    "function": "multi_agent_workflows.erpnext_architect"
                },
                {
                    "name": "design_database",
                    "description": "Design DocTypes and database schema",
                    "function": "multi_agent_workflows.db_architect"
                },
                {
                    "name": "query_knowledge_graph",
                    "description": "Query ERPNext knowledge graph for relationships",
                    "function": "knowledge_graph_builder.query_graph"
                }
            ]
        }
        
        return config
    
    def create_claude_desktop_config(self) -> Dict[str, Any]:
        """Create Claude Desktop configuration for MCP integration"""
        mcp_config = {
            "mcpServers": {
                "erpnext-ai-agent": {
                    "command": "npx",
                    "args": [
                        "frappe-mcp-server",
                        "--config",
                        str(self.mcp_config_path)
                    ],
                    "env": {
                        "ERPNEXT_CONFIG_PATH": str(self.mcp_config_path),
                        "PYTHONPATH": str(Path(__file__).parent.absolute())
                    }
                }
            }
        }
        
        # Merge with existing config if it exists
        if self.claude_config_path.exists():
            try:
                with open(self.claude_config_path, 'r') as f:
                    existing_config = json.load(f)
                
                if 'mcpServers' in existing_config:
                    existing_config['mcpServers'].update(mcp_config['mcpServers'])
                else:
                    existing_config.update(mcp_config)
                
                return existing_config
            except Exception as e:
                logger.warning(f"Could not read existing Claude config: {e}")
        
        return mcp_config
    
    def save_configurations(self) -> Dict[str, str]:
        """Save all configuration files"""
        saved_files = {}
        
        # 1. Save MCP server config
        mcp_config = self.generate_mcp_server_config()
        if mcp_config:
            with open(self.mcp_config_path, 'w') as f:
                json.dump(mcp_config, f, indent=2)
            saved_files['mcp_config'] = str(self.mcp_config_path)
            logger.info(f"Saved MCP config to: {self.mcp_config_path}")
        
        # 2. Save Claude Desktop config
        claude_config = self.create_claude_desktop_config()
        if claude_config:
            # Ensure .claude directory exists
            self.claude_config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.claude_config_path, 'w') as f:
                json.dump(claude_config, f, indent=2)
            saved_files['claude_config'] = str(self.claude_config_path)
            logger.info(f"Saved Claude Desktop config to: {self.claude_config_path}")
        
        return saved_files
    
    def test_mcp_server(self) -> Dict[str, Any]:
        """Test MCP server functionality"""
        test_results = {
            'mcp_server_available': False,
            'config_valid': False,
            'erpnext_connection': False,
            'tools_functional': False,
            'errors': []
        }
        
        try:
            # 1. Check if frappe-mcp-server is available
            result = subprocess.run(['npx', 'frappe-mcp-server', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                test_results['mcp_server_available'] = True
                logger.info("✅ frappe-mcp-server is available")
            else:
                test_results['errors'].append("frappe-mcp-server not found")
        except Exception as e:
            test_results['errors'].append(f"Error checking MCP server: {str(e)}")
        
        # 2. Validate config files
        if self.mcp_config_path.exists():
            try:
                with open(self.mcp_config_path, 'r') as f:
                    config = json.load(f)
                test_results['config_valid'] = bool(config.get('erpnext'))
                logger.info("✅ MCP configuration is valid")
            except Exception as e:
                test_results['errors'].append(f"Invalid MCP config: {str(e)}")
        
        # 3. Test ERPNext connection
        connection_status = self.erpnext.test_connection()
        test_results['erpnext_connection'] = connection_status['connected']
        if connection_status['connected']:
            logger.info("✅ ERPNext connection working")
        else:
            test_results['errors'].append("ERPNext connection failed")
        
        # 4. Test basic tool functionality
        try:
            from multi_agent_workflows import MultiAgentOrchestrator
            orchestrator = MultiAgentOrchestrator()
            # Simple test task
            result = orchestrator.execute_workflow("test workflow")
            test_results['tools_functional'] = result.get('status') == 'completed'
            if test_results['tools_functional']:
                logger.info("✅ Multi-agent tools working")
        except Exception as e:
            test_results['errors'].append(f"Tool test failed: {str(e)}")
        
        return test_results
    
    def get_setup_instructions(self) -> List[str]:
        """Get setup instructions for MCP integration"""
        instructions = [
            "## MCP Server Setup Instructions",
            "",
            "1. **Install frappe-mcp-server globally:**",
            "   ```bash",
            "   npm install -g frappe-mcp-server",
            "   ```",
            "",
            "2. **Configuration files created:**",
            f"   - MCP Config: {self.mcp_config_path}",
            f"   - Claude Desktop: {self.claude_config_path}",
            "",
            "3. **Start ERPNext instance:**",
            "   - Ensure ERPNext is running on http://localhost:8000",
            "   - Or update the configuration with your ERPNext URL",
            "",
            "4. **Restart Claude Desktop:**",
            "   - Close and reopen Claude Desktop application",
            "   - The ERPNext AI Agent tools should appear in the interface",
            "",
            "5. **Available Tools:**",
            "   - search_documents: Semantic search in ERPNext",
            "   - analyze_requirements: Business requirements analysis", 
            "   - design_architecture: System architecture design",
            "   - design_database: DocType and schema design",
            "   - query_knowledge_graph: Relationship queries",
            "",
            "6. **Test the integration:**",
            "   - Try asking Claude: 'Search for customer documents'",
            "   - Or: 'Design a sales order management system'",
        ]
        
        return instructions

def main():
    """Configure MCP server for ERPNext"""
    configurator = ERPNextMCPConfig()
    
    print("🔧 Configuring ERPNext MCP Server...")
    
    # 1. Detect ERPNext instances
    instances = configurator.detect_erpnext_instances()
    print(f"📋 Found {len(instances)} ERPNext instance(s)")
    
    # 2. Save configurations
    saved_files = configurator.save_configurations()
    print("💾 Configuration files saved:")
    for config_type, path in saved_files.items():
        print(f"   {config_type}: {path}")
    
    # 3. Test MCP server
    test_results = configurator.test_mcp_server()
    print(f"\n🧪 MCP Server Test Results:")
    print(f"   MCP Server Available: {'✅' if test_results['mcp_server_available'] else '❌'}")
    print(f"   Config Valid: {'✅' if test_results['config_valid'] else '❌'}")
    print(f"   ERPNext Connection: {'✅' if test_results['erpnext_connection'] else '❌'}")
    print(f"   Tools Functional: {'✅' if test_results['tools_functional'] else '❌'}")
    
    if test_results['errors']:
        print(f"\n⚠️ Errors: {len(test_results['errors'])}")
        for error in test_results['errors']:
            print(f"   • {error}")
    
    # 4. Show setup instructions
    instructions = configurator.get_setup_instructions()
    print("\n" + "\n".join(instructions))

if __name__ == "__main__":
    main()