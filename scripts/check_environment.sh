#!/bin/bash
# ERPNext AI Agent - Local Environment Verification

echo "🔍 Checking Local Environment for ERPNext AI Agent Project"
echo "============================================================"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check functions
check_command() {
    if command -v $1 &> /dev/null; then
        echo -e "✅ ${GREEN}$1${NC} is available"
        return 0
    else
        echo -e "❌ ${RED}$1${NC} is not installed"
        return 1
    fi
}

check_docker_status() {
    if docker info &> /dev/null; then
        echo -e "✅ ${GREEN}Docker${NC} is running"
        return 0
    else
        echo -e "❌ ${RED}Docker${NC} is not running"
        return 1
    fi
}

# System checks
echo "📋 System Requirements:"
check_command "docker"
check_command "python3"
check_command "node"
check_command "npm"
check_command "git"

echo ""
echo "🐳 Docker Status:"
check_docker_status

# Check current Docker images
echo ""
echo "📦 Available Docker Images:"
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}" 2>/dev/null || echo "❌ Cannot access Docker images"

# Check current containers
echo ""
echo "🔄 Running Containers:"
RUNNING_CONTAINERS=$(docker ps -q 2>/dev/null | wc -l)
echo "Currently running: $RUNNING_CONTAINERS containers"

if [ $RUNNING_CONTAINERS -gt 0 ]; then
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
fi

# Check project structure
echo ""
echo "📁 Project Structure:"
PROJECT_DIR="/Users/mekdesyared/mekdesyared/erpnext-ai-agent"

if [ -d "$PROJECT_DIR" ]; then
    echo -e "✅ ${GREEN}Project directory${NC} exists at $PROJECT_DIR"
    
    # Check key files
    KEY_FILES=(
        "README.md"
        "requirements.txt"
        "docker/docker-compose.foundation.yml"
        "scripts/setup.sh"
        "phase1-foundation/mcp-server/setup_mcp.py"
        "phase1-foundation/vector-search/setup_vector_search.py"
        "phase1-foundation/knowledge-graph/setup_knowledge_graph.py"
    )
    
    echo "📄 Key Files:"
    for file in "${KEY_FILES[@]}"; do
        if [ -f "$PROJECT_DIR/$file" ]; then
            echo -e "  ✅ ${GREEN}$file${NC}"
        else
            echo -e "  ❌ ${RED}$file${NC}"
        fi
    done
else
    echo -e "❌ ${RED}Project directory${NC} not found at $PROJECT_DIR"
fi

# Check network connectivity
echo ""
echo "🌐 Network Connectivity:"
if ping -c 1 google.com &> /dev/null; then
    echo -e "✅ ${GREEN}Internet connection${NC} available"
else
    echo -e "❌ ${RED}Internet connection${NC} not available"
fi

# Available resources summary
echo ""
echo "💾 System Resources:"
echo "Memory: $(sysctl hw.memsize 2>/dev/null | awk '{print int($2/1024/1024/1024)"GB"}' || echo "Unknown")"
echo "CPU Cores: $(sysctl -n hw.ncpu 2>/dev/null || echo "Unknown")"
echo "Disk Space: $(df -h . 2>/dev/null | tail -1 | awk '{print $4}' || echo "Unknown") available"

# Python packages check
echo ""
echo "🐍 Python Environment:"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
    echo "Python version: $PYTHON_VERSION"
    
    # Check if virtual environment exists
    if [ -d "$PROJECT_DIR/venv" ]; then
        echo -e "✅ ${GREEN}Virtual environment${NC} exists"
    else
        echo -e "⚠️  ${YELLOW}Virtual environment${NC} not created yet"
    fi
else
    echo -e "❌ ${RED}Python 3${NC} not available"
fi

# Node.js packages check
echo ""
echo "📦 Node.js Environment:"
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo "Node.js version: $NODE_VERSION"
    
    # Check if frappe-mcp-server is installed
    if npm list -g frappe-mcp-server &> /dev/null; then
        echo -e "✅ ${GREEN}frappe-mcp-server${NC} installed globally"
    else
        echo -e "⚠️  ${YELLOW}frappe-mcp-server${NC} not installed yet"
    fi
else
    echo -e "❌ ${RED}Node.js${NC} not available"
fi

# Recommendations
echo ""
echo "🎯 Next Steps:"
echo "1. If Docker is not running: Start Docker Desktop"
echo "2. If project not found: Run the scaffolding again"
echo "3. If setup incomplete: cd $PROJECT_DIR && ./scripts/setup.sh"
echo "4. If APIs needed: Configure docker/.env with your API keys"

echo ""
echo "📚 Documentation:"
echo "- Project status: $PROJECT_DIR/docs/PROJECT_STATUS.md"
echo "- Docker setup: $PROJECT_DIR/docker/README.md"
echo "- Main README: $PROJECT_DIR/README.md"

echo ""
echo "🔗 Useful URLs (once services are running):"
echo "- ERPNext: http://localhost:8000"
echo "- ChromaDB: http://localhost:8001"
echo "- Neo4j: http://localhost:7474"
echo ""
echo "✨ Environment check complete!"
