# ERPNext AI Agent - Docker Environment

## Available Images Analysis
Current local Docker resources (minimal):
- docker/jcat (349kB)
- docker/labs-vscode-installer (31.2MB)

## Required Containers for Full Stack

### Phase 1: Foundation Stack
1. **ERPNext Development**
   - frappe/erpnext:latest
   - mariadb:latest
   - redis:alpine

2. **Vector Database**
   - chromadb/chroma:latest (lightweight)
   - Alternative: weaviate/weaviate:latest (production)

3. **Knowledge Graph**
   - neo4j:latest
   - Alternative: memgraph/memgraph:latest

### Phase 2: Intelligence Stack
4. **RL Framework**
   - pytorch/pytorch:latest
   - Custom veRL container

5. **Multi-Agent Framework**
   - Custom CrewAI container
   - LangChain environment

### Phase 3: Scale Stack
6. **Production Services**
   - nginx:alpine (reverse proxy)
   - prometheus:latest (monitoring)
   - grafana/grafana:latest (dashboards)

## Resource Requirements

### Minimum (Development)
- CPU: 4 cores
- RAM: 8GB
- Storage: 20GB

### Recommended (Production)
- CPU: 8+ cores
- RAM: 16GB+
- Storage: 100GB+
- GPU: NVIDIA RTX 4060+ (for RL training)

## Quick Setup Commands

```bash
# Pull required images
docker pull frappe/erpnext:latest
docker pull chromadb/chroma:latest
docker pull neo4j:latest
docker pull redis:alpine
docker pull mariadb:latest

# Start foundation stack
docker-compose -f docker-compose.foundation.yml up -d

# Verify containers
docker ps
```

## Container Resource Allocation

| Container | CPU | Memory | Storage | Port |
|-----------|-----|--------|---------|------|
| ERPNext   | 2   | 4GB    | 10GB    | 8000 |
| MariaDB   | 1   | 2GB    | 5GB     | 3306 |
| Redis     | 0.5 | 512MB  | 1GB     | 6379 |
| Chroma    | 1   | 2GB    | 5GB     | 8001 |
| Neo4j     | 1   | 2GB    | 5GB     | 7474 |

Total: ~5.5 CPU cores, ~10.5GB RAM, ~26GB storage

## Network Configuration

```yaml
networks:
  erpnext-ai:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

## Volume Mapping

- ERPNext sites: `./volumes/erpnext/sites`
- Database: `./volumes/mariadb/data`
- Vector DB: `./volumes/chroma/data`
- Knowledge Graph: `./volumes/neo4j/data`
- Logs: `./volumes/logs`

## Environment Variables

See `.env.example` for complete configuration.

Key variables:
- `ERPNEXT_ADMIN_PASSWORD`
- `MYSQL_ROOT_PASSWORD`
- `NEO4J_AUTH`
- `CHROMA_AUTH_CREDENTIALS`

## Health Checks

All containers include health checks:
- ERPNext: HTTP GET /api/method/ping
- MariaDB: mysqladmin ping
- Redis: redis-cli ping
- Chroma: HTTP GET /api/v1/heartbeat
- Neo4j: cypher-shell query

## Scaling Strategy

### Horizontal Scaling
- Multiple ERPNext workers
- Read replicas for databases
- Load balancer configuration

### Vertical Scaling
- Increase container resources
- GPU acceleration for ML workloads
- SSD storage for databases

## Monitoring

- Container metrics via Prometheus
- Application logs via ELK stack
- Performance dashboards in Grafana
- Custom AI agent metrics

## Security

- Non-root container users
- Encrypted inter-container communication
- Secrets management via Docker secrets
- Network isolation between services

## Backup Strategy

- Automated database backups
- Vector index snapshots
- Knowledge graph exports
- Configuration backups

## Development vs Production

### Development
- Single-node deployment
- Local storage volumes
- Development SSL certificates
- Debug logging enabled

### Production
- Multi-node swarm/k8s
- Persistent storage classes
- Production SSL certificates
- Structured logging

## Troubleshooting

Common issues and solutions:
1. **Memory issues**: Increase Docker memory allocation
2. **Port conflicts**: Check port availability
3. **Permission errors**: Fix volume ownership
4. **Network issues**: Verify bridge configuration

## Docker Commands Reference

```bash
# View logs
docker-compose logs -f [service]

# Access container shell
docker exec -it [container] bash

# Restart service
docker-compose restart [service]

# Update images
docker-compose pull && docker-compose up -d

# Clean up
docker system prune -a
```
