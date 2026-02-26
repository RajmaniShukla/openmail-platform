#!/bin/bash
# OpenMail Platform Deployment Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 OpenMail Platform Deployment${NC}"
echo "=================================="

# Check for required tools
check_requirements() {
    echo -e "\n${YELLOW}Checking requirements...${NC}"
    
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker is not installed${NC}"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        echo -e "${RED}❌ Docker Compose is not installed${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ All requirements met${NC}"
}

# Generate secrets if not exists
generate_secrets() {
    echo -e "\n${YELLOW}Generating secrets...${NC}"
    
    if [ ! -f .env ]; then
        cp .env.example .env
        
        # Generate random secrets
        POSTGRES_PASSWORD=$(openssl rand -base64 32 | tr -dc 'a-zA-Z0-9' | head -c 32)
        JWT_SECRET=$(openssl rand -base64 64 | tr -dc 'a-zA-Z0-9' | head -c 64)
        ENCRYPTION_KEY=$(openssl rand -base64 32 | tr -dc 'a-zA-Z0-9' | head -c 32)
        
        # Update .env file
        sed -i "s/POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=${POSTGRES_PASSWORD}/" .env
        sed -i "s/JWT_SECRET=.*/JWT_SECRET=${JWT_SECRET}/" .env
        sed -i "s/ENCRYPTION_KEY=.*/ENCRYPTION_KEY=${ENCRYPTION_KEY}/" .env
        
        echo -e "${GREEN}✓ Secrets generated${NC}"
    else
        echo -e "${GREEN}✓ Using existing .env file${NC}"
    fi
}

# Generate SSL certificates
generate_certs() {
    echo -e "\n${YELLOW}Generating SSL certificates...${NC}"
    
    CERTS_DIR="./certs"
    mkdir -p $CERTS_DIR
    
    if [ ! -f "$CERTS_DIR/server.crt" ]; then
        # Generate self-signed certificate for development
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout $CERTS_DIR/server.key \
            -out $CERTS_DIR/server.crt \
            -subj "/C=US/ST=State/L=City/O=OpenMail/CN=localhost" \
            2>/dev/null
        
        # Generate DH params
        openssl dhparam -out $CERTS_DIR/dhparam.pem 2048 2>/dev/null
        
        echo -e "${GREEN}✓ Self-signed certificates generated${NC}"
        echo -e "${YELLOW}⚠️  For production, replace with valid certificates${NC}"
    else
        echo -e "${GREEN}✓ Using existing certificates${NC}"
    fi
}

# Build images
build_images() {
    echo -e "\n${YELLOW}Building Docker images...${NC}"
    
    docker compose build --parallel
    
    echo -e "${GREEN}✓ Images built${NC}"
}

# Initialize database
init_database() {
    echo -e "\n${YELLOW}Initializing database...${NC}"
    
    # Start only PostgreSQL first
    docker compose up -d postgres
    
    # Wait for PostgreSQL to be ready
    echo "Waiting for PostgreSQL..."
    until docker compose exec -T postgres pg_isready -U openmail > /dev/null 2>&1; do
        sleep 1
    done
    
    # Run migrations
    docker compose run --rm backend alembic upgrade head
    
    echo -e "${GREEN}✓ Database initialized${NC}"
}

# Start services
start_services() {
    echo -e "\n${YELLOW}Starting services...${NC}"
    
    docker compose up -d
    
    echo -e "${GREEN}✓ Services started${NC}"
}

# Health check
health_check() {
    echo -e "\n${YELLOW}Running health checks...${NC}"
    
    sleep 10  # Wait for services to stabilize
    
    services=("frontend:3000" "backend:8000" "postgres:5432" "redis:6379")
    
    for service in "${services[@]}"; do
        name="${service%:*}"
        port="${service#*:}"
        
        if docker compose exec -T $name sh -c "exit 0" 2>/dev/null; then
            echo -e "  ${GREEN}✓ $name${NC}"
        else
            echo -e "  ${RED}✗ $name${NC}"
        fi
    done
}

# Print access information
print_info() {
    echo -e "\n${GREEN}🎉 Deployment Complete!${NC}"
    echo "========================"
    echo ""
    echo "Access your OpenMail instance:"
    echo "  📧 Webmail:    https://localhost"
    echo "  🔧 API:        https://localhost/api/v1"
    echo "  📊 Grafana:    http://localhost:3001 (admin/admin)"
    echo "  📈 Prometheus: http://localhost:9090"
    echo ""
    echo "Mail server ports:"
    echo "  📤 SMTP:       25, 587 (submission), 465 (TLS)"
    echo "  📥 IMAP:       143, 993 (TLS)"
    echo "  📥 POP3:       110, 995 (TLS)"
    echo ""
    echo "Useful commands:"
    echo "  docker compose logs -f       # View logs"
    echo "  docker compose ps            # Check status"
    echo "  docker compose down          # Stop services"
    echo "  docker compose restart       # Restart services"
}

# Main deployment flow
main() {
    cd "$(dirname "$0")/.."
    
    check_requirements
    generate_secrets
    generate_certs
    build_images
    init_database
    start_services
    health_check
    print_info
}

# Parse arguments
case "${1:-}" in
    --build-only)
        check_requirements
        build_images
        ;;
    --start)
        start_services
        health_check
        print_info
        ;;
    --stop)
        docker compose down
        echo -e "${GREEN}✓ Services stopped${NC}"
        ;;
    --restart)
        docker compose restart
        health_check
        ;;
    --logs)
        docker compose logs -f "${2:-}"
        ;;
    --status)
        docker compose ps
        ;;
    *)
        main
        ;;
esac
