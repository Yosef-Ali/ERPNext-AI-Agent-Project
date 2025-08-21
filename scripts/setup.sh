#!/bin/bash
# ERPNext AI Agent Setup Script

set -e

echo "🚀 Setting up ERPNext AI Agent Project..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}$1${NC}"
}

# Check prerequisites
check_prerequisites() {
    print_header "Checking Prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker Desktop."
        exit 1
    fi
    
    # Check Docker Compose
    if ! docker compose version &> /dev/null; then
        print_error "Docker Compose is not available. Please update Docker Desktop."
        exit 1
    fi
    
    # Check Node.js (for MCP server)
    if ! command -v node &> /dev/null; then
        print_warning "Node.js not found. Installing via brew..."
        if command -v brew &> /dev/null; then
            brew install node
        else
            print_error "Please install Node.js manually: https://nodejs.org/"
            exit 1
        fi
    fi
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is required. Please install Python 3.8+."
        exit 1
    fi
    
    print_status "Prerequisites check completed ✅"
}

# Setup environment
setup_environment() {
    print_header "Setting up Environment..."
    
    # Copy environment file
    if [ ! -f "docker/.env" ]; then
        cp docker/.env.example docker/.env
        print_status "Created docker/.env file"
        print_warning "Please edit docker/.env with your configuration"
    fi
    
    # Create local directories
    mkdir -p volumes/{erpnext,mariadb,redis,chroma,neo4j,logs}
    mkdir -p models
    mkdir -p datasets
    mkdir -p exports
    
    print_status "Environment setup completed ✅"
}

# Install Python dependencies
install_python_deps() {
    print_header "Installing Python Dependencies..."
    
    # Create virtual environment
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        print_status "Created virtual environment"
    fi    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install requirements
    pip install --upgrade pip
    pip install -r requirements.txt
    
    print_status "Python dependencies installed ✅"
}

# Install Node.js dependencies
install_node_deps() {
    print_header "Installing Node.js Dependencies..."
    
    # Install MCP server
    npm install -g frappe-mcp-server
    
    print_status "Node.js dependencies installed ✅"
}

# Pull Docker images
pull_docker_images() {
    print_header "Pulling Docker Images..."
    
    # Pull required images
    docker pull frappe/erpnext:latest
    docker pull mariadb:10.6
    docker pull redis:7-alpine
    docker pull chromadb/chroma:latest
    docker pull neo4j:5
    
    print_status "Docker images pulled ✅"
}

# Start foundation services
start_foundation() {
    print_header "Starting Foundation Services..."
    
    cd docker
    docker compose -f docker-compose.foundation.yml up -d
    cd ..
    
    print_status "Foundation services started ✅"
    print_status "Services available at:"
    print_status "  - ERPNext: http://localhost:8000"
    print_status "  - ChromaDB: http://localhost:8001"
    print_status "  - Neo4j: http://localhost:7474"
    print_status "  - MariaDB: localhost:3306"
    print_status "  - Redis: localhost:6379"
}

# Health check
health_check() {
    print_header "Running Health Checks..."
    
    sleep 30  # Wait for services to start
    
    # Check ERPNext
    if curl -f http://localhost:8000/api/method/ping &> /dev/null; then
        print_status "ERPNext: Healthy ✅"
    else
        print_warning "ERPNext: Not ready yet ⏳"
    fi
    
    # Check ChromaDB
    if curl -f http://localhost:8001/api/v1/heartbeat &> /dev/null; then
        print_status "ChromaDB: Healthy ✅"
    else
        print_warning "ChromaDB: Not ready yet ⏳"
    fi
    
    # Check Neo4j
    if curl -f http://localhost:7474 &> /dev/null; then
        print_status "Neo4j: Healthy ✅"
    else
        print_warning "Neo4j: Not ready yet ⏳"
    fi
}

# Main setup flow
main() {
    print_header "🤖 ERPNext AI Agent Setup"
    print_status "Project: /Users/mekdesyared/mekdesyared/erpnext-ai-agent"
    
    check_prerequisites
    setup_environment
    install_python_deps
    install_node_deps
    pull_docker_images
    start_foundation
    health_check
    
    print_header "🎉 Setup Complete!"
    print_status "Next steps:"
    print_status "1. Edit docker/.env with your API keys"
    print_status "2. Run: cd phase1-foundation && python setup_mcp.py"
    print_status "3. Check services: docker ps"
    print_status "4. View logs: docker compose -f docker/docker-compose.foundation.yml logs -f"
    
    print_status "Documentation: docs/setup.md"
}

# Run main function
main "$@"