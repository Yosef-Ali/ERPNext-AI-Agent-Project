#!/usr/bin/env python3
"""
ERPNext Multi-Agent Workflows
Real workflow orchestration for ERPNext tasks using specialized agents
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio

from erpnext_connector import ERPNextConnector
from document_indexer import ERPNextDocumentIndexer  
from knowledge_graph_builder import ERPNextKnowledgeGraph

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ERPNextAgent:
    """Base class for ERPNext specialized agents"""
    
    def __init__(self, name: str, role: str, capabilities: List[str]):
        self.name = name
        self.role = role
        self.capabilities = capabilities
        self.memory = []
        
    def can_handle(self, task: str) -> bool:
        """Check if agent can handle a specific task"""
        return any(cap.lower() in task.lower() for cap in self.capabilities)
    
    def add_memory(self, interaction: Dict[str, Any]):
        """Add interaction to agent memory"""
        interaction['timestamp'] = datetime.now().isoformat()
        self.memory.append(interaction)
        
    def execute_task(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task (base implementation)"""
        return {
            'agent': self.name,
            'task': task,
            'status': 'completed',
            'result': f"Task '{task}' processed by {self.role}",
            'context': context
        }

class RequirementsAnalyzerAgent(ERPNextAgent):
    """Agent for analyzing business requirements and converting to technical specs"""
    
    def __init__(self):
        super().__init__(
            name="requirements-analyzer",
            role="Business Requirements Analyst", 
            capabilities=["requirements", "analysis", "specification", "business needs"]
        )
        self.erpnext = ERPNextConnector()
        
    def execute_task(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze business requirements"""
        result = {
            'agent': self.name,
            'task': task,
            'status': 'completed',
            'technical_specs': [],
            'recommended_doctypes': [],
            'workflow_suggestions': []
        }
        
        # Analyze task for ERPNext context
        if "customer" in task.lower():
            result['recommended_doctypes'].extend(['Customer', 'Contact', 'Address'])
            result['technical_specs'].append("Customer relationship management functionality")
            
        if "order" in task.lower():
            result['recommended_doctypes'].extend(['Sales Order', 'Purchase Order'])
            result['technical_specs'].append("Order processing workflow")
            
        if "invoice" in task.lower():
            result['recommended_doctypes'].extend(['Sales Invoice', 'Purchase Invoice'])
            result['technical_specs'].append("Invoicing and payment tracking")
            
        if "inventory" in task.lower():
            result['recommended_doctypes'].extend(['Item', 'Stock Entry', 'Warehouse'])
            result['technical_specs'].append("Inventory management system")
            
        # Add workflow suggestions
        result['workflow_suggestions'] = [
            "Implement proper validation rules",
            "Set up automated notifications", 
            "Configure approval workflows",
            "Add custom fields as needed"
        ]
        
        self.add_memory({'task': task, 'result': result})
        return result

class ERPNextArchitectAgent(ERPNextAgent):
    """Agent for designing ERPNext system architecture"""
    
    def __init__(self):
        super().__init__(
            name="erpnext-architect",
            role="System Architect",
            capabilities=["architecture", "design", "system", "integration", "scalability"]
        )
        self.kg_builder = ERPNextKnowledgeGraph()
        
    def execute_task(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Design system architecture"""
        result = {
            'agent': self.name,
            'task': task,
            'status': 'completed',
            'architecture_components': [],
            'integration_points': [],
            'scalability_considerations': []
        }
        
        # Analyze requirements from context
        requirements = context.get('technical_specs', [])
        doctypes = context.get('recommended_doctypes', [])
        
        # Design architecture components
        if doctypes:
            result['architecture_components'].append({
                'component': 'DocType Layer',
                'doctypes': doctypes,
                'description': 'Core data models and business entities'
            })
            
        if "workflow" in str(requirements).lower():
            result['architecture_components'].append({
                'component': 'Workflow Engine', 
                'features': ['State transitions', 'Approval flows', 'Notifications'],
                'description': 'Automated business process management'
            })
            
        if "api" in task.lower() or "integration" in task.lower():
            result['integration_points'].extend([
                'REST API endpoints',
                'Webhook configurations',
                'External system connectors'
            ])
            
        # Scalability recommendations
        result['scalability_considerations'] = [
            'Database indexing strategy',
            'Caching implementation',
            'Background job queues',
            'Performance monitoring'
        ]
        
        self.add_memory({'task': task, 'result': result})
        return result

class DBArchitectAgent(ERPNextAgent):
    """Agent for database and DocType design"""
    
    def __init__(self):
        super().__init__(
            name="db-architect", 
            role="Database Architect",
            capabilities=["database", "doctype", "schema", "fields", "relationships"]
        )
        self.erpnext = ERPNextConnector()
        
    def execute_task(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Design database schema and DocTypes"""
        result = {
            'agent': self.name,
            'task': task,
            'status': 'completed',
            'doctype_designs': [],
            'field_specifications': [],
            'relationship_mappings': []
        }
        
        # Extract DocTypes from context
        doctypes = context.get('recommended_doctypes', [])
        
        for doctype in doctypes:
            design = self.design_doctype_fields(doctype)
            if design:
                result['doctype_designs'].append(design)
        
        # Add relationship mappings
        result['relationship_mappings'] = self.map_doctype_relationships(doctypes)
        
        self.add_memory({'task': task, 'result': result})
        return result
        
    def design_doctype_fields(self, doctype: str) -> Dict[str, Any]:
        """Design fields for a DocType"""
        common_fields = {
            'Customer': [
                {'fieldname': 'customer_name', 'fieldtype': 'Data', 'required': 1},
                {'fieldname': 'customer_type', 'fieldtype': 'Select', 'options': 'Individual\\nCompany'},
                {'fieldname': 'territory', 'fieldtype': 'Link', 'options': 'Territory'},
                {'fieldname': 'customer_group', 'fieldtype': 'Link', 'options': 'Customer Group'}
            ],
            'Item': [
                {'fieldname': 'item_name', 'fieldtype': 'Data', 'required': 1},
                {'fieldname': 'item_group', 'fieldtype': 'Link', 'options': 'Item Group'},
                {'fieldname': 'uom', 'fieldtype': 'Link', 'options': 'UOM'},
                {'fieldname': 'valuation_rate', 'fieldtype': 'Currency'}
            ]
        }
        
        if doctype in common_fields:
            return {
                'doctype': doctype,
                'fields': common_fields[doctype],
                'custom_fields': []
            }
        
        return None
        
    def map_doctype_relationships(self, doctypes: List[str]) -> List[Dict[str, Any]]:
        """Map relationships between DocTypes"""
        relationships = []
        
        if 'Customer' in doctypes and 'Sales Order' in doctypes:
            relationships.append({
                'from_doctype': 'Sales Order',
                'to_doctype': 'Customer', 
                'relationship_type': 'Link',
                'field': 'customer'
            })
            
        if 'Item' in doctypes and 'Sales Order' in doctypes:
            relationships.append({
                'from_doctype': 'Sales Order Item',
                'to_doctype': 'Item',
                'relationship_type': 'Link', 
                'field': 'item_code'
            })
            
        return relationships

class MultiAgentOrchestrator:
    """Orchestrates multiple agents for complex ERPNext tasks"""
    
    def __init__(self):
        # Initialize specialized agents
        self.agents = {
            'requirements-analyzer': RequirementsAnalyzerAgent(),
            'erpnext-architect': ERPNextArchitectAgent(), 
            'db-architect': DBArchitectAgent()
        }
        
        # Initialize supporting systems
        self.erpnext = ERPNextConnector()
        self.indexer = None  # Initialize only when needed
        self.kg_builder = ERPNextKnowledgeGraph()
        
        logger.info(f"Multi-Agent Orchestrator initialized with {len(self.agents)} agents")
    
    def analyze_task_requirements(self, task: str) -> List[str]:
        """Analyze which agents are needed for a task"""
        needed_agents = []
        
        for agent_name, agent in self.agents.items():
            if agent.can_handle(task):
                needed_agents.append(agent_name)
        
        # Ensure proper workflow order
        agent_order = ['requirements-analyzer', 'erpnext-architect', 'db-architect']
        return sorted(needed_agents, key=lambda x: agent_order.index(x) if x in agent_order else 999)
    
    def execute_workflow(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a multi-agent workflow"""
        if context is None:
            context = {}
            
        workflow_result = {
            'task': task,
            'timestamp': datetime.now().isoformat(),
            'agent_results': [],
            'final_deliverables': {},
            'status': 'completed'
        }
        
        # Determine required agents
        needed_agents = self.analyze_task_requirements(task)
        logger.info(f"Task '{task}' requires agents: {needed_agents}")
        
        # Execute agents in sequence, passing context forward
        current_context = context.copy()
        
        for agent_name in needed_agents:
            try:
                agent = self.agents[agent_name]
                logger.info(f"Executing agent: {agent_name}")
                
                agent_result = agent.execute_task(task, current_context)
                workflow_result['agent_results'].append(agent_result)
                
                # Update context with agent results
                current_context.update(agent_result)
                
            except Exception as e:
                error_result = {
                    'agent': agent_name,
                    'error': str(e),
                    'status': 'failed'
                }
                workflow_result['agent_results'].append(error_result)
                logger.error(f"Agent {agent_name} failed: {e}")
        
        # Compile final deliverables
        workflow_result['final_deliverables'] = self.compile_deliverables(workflow_result['agent_results'])
        
        return workflow_result
    
    def compile_deliverables(self, agent_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compile final deliverables from all agent results"""
        deliverables = {
            'requirements': [],
            'architecture': [],
            'database_design': [],
            'implementation_guide': []
        }
        
        for result in agent_results:
            if result.get('agent') == 'requirements-analyzer':
                deliverables['requirements'] = result.get('technical_specs', [])
                
            elif result.get('agent') == 'erpnext-architect':
                deliverables['architecture'] = result.get('architecture_components', [])
                
            elif result.get('agent') == 'db-architect':
                deliverables['database_design'] = result.get('doctype_designs', [])
        
        # Generate implementation guide
        deliverables['implementation_guide'] = [
            "1. Create DocTypes with specified fields",
            "2. Set up workflows and approval processes", 
            "3. Configure user permissions and roles",
            "4. Test with sample data",
            "5. Deploy to production with monitoring"
        ]
        
        return deliverables
    
    def save_workflow_result(self, result: Dict[str, Any]) -> str:
        """Save workflow result to file"""
        output_dir = Path("../volumes/workflow_results")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"workflow_result_{timestamp}.json"
        filepath = output_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        
        logger.info(f"Workflow result saved to: {filepath}")
        return str(filepath)

def main():
    """Test multi-agent workflows"""
    orchestrator = MultiAgentOrchestrator()
    
    print("🤖 Testing Multi-Agent Workflows...")
    
    # Test workflow 1: Customer Management System
    task1 = "Design a customer management system with order tracking and invoicing capabilities"
    
    print(f"\n📋 Task: {task1}")
    result1 = orchestrator.execute_workflow(task1)
    
    print(f"Agents used: {[r.get('agent') for r in result1['agent_results']]}")
    print(f"Deliverables: {list(result1['final_deliverables'].keys())}")
    
    # Save results
    saved_path = orchestrator.save_workflow_result(result1)
    print(f"Results saved to: {saved_path}")
    
    # Test workflow 2: Inventory Management
    task2 = "Create an inventory management system with stock tracking and procurement workflows"
    
    print(f"\n📋 Task: {task2}")  
    result2 = orchestrator.execute_workflow(task2)
    
    print(f"Agents used: {[r.get('agent') for r in result2['agent_results']]}")
    print(f"Deliverables: {list(result2['final_deliverables'].keys())}")

if __name__ == "__main__":
    main()