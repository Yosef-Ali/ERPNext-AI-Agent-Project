# ERPNext AI Agent Project

## Overview
Advanced AI agent system for ERPNext with reinforcement learning-based retrieval, multi-agent orchestration, and intelligent document processing.

Based on cutting-edge research:
- Search R1: RL-based search and reasoning
- UR2: Unified RAG and reasoning through RL
- Graph-R1: Agentic GraphRAG framework
- Enterprise MCP integrations

## Project Structure

### Phase 1: Foundation (Weeks 1-4)
- **mcp-server/**: Frappe MCP server integration
- **vector-search/**: Chroma-based semantic search
- **knowledge-graph/**: NetworkX relationship mapping

### Phase 2: Intelligence (Weeks 5-12)
- **search-r1/**: RL-enhanced retrieval framework
- **multi-agent/**: CrewAI-based agent orchestration

### Phase 3: Scale (Months 4-6)
- **enterprise/**: Production-ready scaling solutions

## Quick Start

1. **Setup Environment**
   ```bash
   cd /Users/mekdesyared/mekdesyared/erpnext-ai-agent
   ./scripts/setup.sh
   ```

2. **Start Phase 1 Development**
   ```bash
   cd phase1-foundation
   docker-compose up -d
   ```

3. **Install MCP Server**
   ```bash
   npm install -g frappe-mcp-server
   ```

## Local Docker Resources

Current Docker images:
- docker/jcat (349kB) - Available
- docker/labs-vscode-installer (31.2MB) - Available

Recommended additional containers:
- ERPNext development environment
- Neo4j knowledge graph database
- ChromaDB vector database
- Redis for caching

## Architecture

```
ERPNext ← → MCP Server ← → AI Agent ← → Knowledge Graph
                ↓              ↓              ↓
         Vector Search  RL Framework  Multi-Agent System
```

## Development Phases

### Phase 1: Foundation ✅
- [x] Project scaffolding
- [ ] MCP server deployment
- [ ] Basic vector search
- [ ] Simple knowledge graph

### Phase 2: Intelligence
- [ ] Search R1 integration
- [ ] Multi-agent workflows
- [ ] RL training pipeline
- [ ] Advanced reasoning

### Phase 3: Scale
- [ ] Enterprise deployment
- [ ] Production optimization
- [ ] Monitoring & analytics
- [ ] Security hardening

## Key Technologies

- **MCP**: Model Context Protocol for ERPNext integration
- **RL**: Reinforcement learning for adaptive retrieval
- **Vector DB**: Chroma/Weaviate for semantic search
- **Knowledge Graph**: Neo4j/NetworkX for relationships
- **Multi-Agent**: CrewAI for orchestration
- **Frameworks**: veRL, PyTorch, LangChain

## Resources and Dependencies

### Available Community Projects
- appliedrelevance/frappe_mcp_server
- buildswithpaul/Frappe_Assistant_Core
- KorucuTech/kai (CrewAI integration)
- PeterGriffinJin/Search-R1
- LHRLAB/Graph-R1

### Required Docker Containers
See `docker/` directory for complete setup.

## Documentation

- [Setup Guide](docs/setup.md)
- [Architecture Overview](docs/architecture.md)
- [API Reference](docs/api.md)
- [Deployment Guide](docs/deployment.md)

## License

MIT License - See LICENSE file for details.

## Contributing

1. Fork the repository
2. Create feature branch
3. Follow development phases
4. Submit pull request

---

**Status**: Initial scaffolding complete ✅  
**Next**: Phase 1 MCP server deployment  
**Goal**: Production-ready intelligent ERPNext agent system
