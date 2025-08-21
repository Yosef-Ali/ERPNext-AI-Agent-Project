# 🚀 ERPNext AI Agent - Quick Start Guide

## Ready for Immediate Use!

All integration components are built and ready. Follow these 4 simple steps:

## 1️⃣ Start ERPNext Instance

Choose one option:

### Option A: Automatic Startup
```bash
python start_erpnext_ai_agent.py
```
*This will auto-detect and start your ERPNext instance*

### Option B: Manual Startup
```bash
# If you have frappe-bench:
cd /path/to/your/frappe-bench
bench start

# Or start your Docker ERPNext:
docker compose up -d

# Ensure ERPNext is accessible at http://localhost:8000
```

## 2️⃣ Run Integration Report
```bash
cd integrations
python final_integration_report.py
```
*Verify all components are working correctly*

## 3️⃣ Begin Intelligent Assistance

### Via Python:
```python
from integrations.multi_agent_workflows import MultiAgentOrchestrator

# Create orchestrator
orchestrator = MultiAgentOrchestrator()

# Try a workflow
result = orchestrator.execute_workflow(
    "Design a customer management system with order tracking"
)

print(result['final_deliverables'])
```

### Via Document Search:
```python
from integrations.document_indexer import ERPNextDocumentIndexer

# Search your ERPNext documents
indexer = ERPNextDocumentIndexer()
results = indexer.search_documents("customer orders")
```

### Via Knowledge Graph:
```python
from integrations.knowledge_graph_builder import ERPNextKnowledgeGraph

# Analyze relationships
kg = ERPNextKnowledgeGraph()
stats = kg.get_graph_statistics()
```

## 4️⃣ Watch AI Optimize Your Business

### Available AI Agents:

- **🔍 requirements-analyzer**: Convert business needs → technical specs
- **🏗️ erpnext-architect**: Design system architectures  
- **🗄️ db-architect**: Create DocTypes and database schemas
- **🤖 multi-agent**: Orchestrate complex workflows

### Real Examples to Try:

```python
# 1. Sales Management System
result = orchestrator.execute_workflow(
    "Create a complete sales management system with quotes, orders, and invoicing"
)

# 2. Inventory Optimization
result = orchestrator.execute_workflow(
    "Design inventory management with automated reordering and stock alerts"
)

# 3. Project Management
result = orchestrator.execute_workflow(
    "Build project management system with time tracking and resource allocation"
)

# 4. Customer Service
result = orchestrator.execute_workflow(
    "Implement customer support system with ticket escalation and SLA tracking"
)
```

## 🎯 What You Get

### ✅ Real ERPNext Integration
- Live connection to your ERPNext instance
- Real document indexing and search
- Actual DocType analysis and relationships

### ✅ AI-Powered Intelligence
- Semantic search across all your ERPNext data
- Knowledge graph of business relationships  
- Multi-agent workflows for complex tasks
- Reinforcement learning from usage patterns

### ✅ Production-Ready Features
- Claude Desktop integration via MCP
- Persistent vector storage with ChromaDB
- NetworkX knowledge graphs
- Comprehensive error handling and logging

## 🔧 Troubleshooting

### ERPNext Not Starting?
```bash
# Check if bench is installed
which bench

# Check running processes
ps aux | grep frappe

# Try manual bench start
cd /your/bench/path
bench start --port 8000
```

### Import Errors?
```bash
# Activate virtual environment
source venv/bin/activate

# Install missing dependencies
pip install -r requirements.txt
```

### No Documents Found?
- Ensure ERPNext has sample data
- Check DocType permissions
- Verify API access is enabled

## 📚 Advanced Usage

### Custom Agent Workflows
```python
# Create custom agents
from integrations.multi_agent_workflows import ERPNextAgent

class CustomAgent(ERPNextAgent):
    def __init__(self):
        super().__init__(
            name="custom-agent",
            role="Custom Business Analyst", 
            capabilities=["custom", "analysis"]
        )
    
    def execute_task(self, task, context):
        # Your custom logic here
        return {"result": "Custom analysis complete"}
```

### Real-Time Document Monitoring
```python
# Monitor new documents
def monitor_erpnext_changes():
    # Check for new documents
    new_docs = connector.get_sample_documents("Sales Order", 10)
    
    # Auto-index new documents
    for doc in new_docs:
        indexer.index_document(doc)
    
    # Update knowledge graph
    kg_builder.add_document_relationships(new_docs)
```

### Claude Desktop Integration
1. Install MCP server globally: `npm install -g frappe-mcp-server`
2. Configuration files are auto-created in `~/.claude/`
3. Restart Claude Desktop to see ERPNext tools

## 🏆 Success Metrics

When working properly, you should see:

- ✅ ERPNext accessible at http://localhost:8000
- ✅ Documents indexed in ChromaDB collections
- ✅ Knowledge graph with nodes and relationships
- ✅ AI agents responding to workflow requests
- ✅ MCP tools available in Claude Desktop

## 🚀 Ready to Transform Your ERP Experience!

The ERPNext AI Agent provides intelligent assistance that learns and optimizes your business processes. Start with the examples above and watch as the AI discovers patterns in your data and suggests improvements to your workflows.

---

**Need Help?** Check the integration report for detailed component status and troubleshooting guidance.