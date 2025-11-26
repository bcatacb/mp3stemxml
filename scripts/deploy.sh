#!/bin/bash

# Audio to MIDI Converter Deployment Script
# This script handles the complete deployment process

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="mp3stemxml"
DOCKER_REGISTRY="${DOCKER_REGISTRY:-}"
TAG="${TAG:-latest}"

echo -e "${GREEN}🎵 Starting Audio to MIDI Converter Deployment${NC}"
echo "=================================================="

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check if .env file exists
    if [ ! -f .env ]; then
        print_warning ".env file not found. Creating from template..."
        cp .env.production .env
        print_warning "Please edit .env file with your configuration before continuing."
        read -p "Press Enter to continue after editing .env file..."
    fi
    
    print_status "Prerequisites check completed ✓"
}

# Build and deploy
deploy() {
    print_status "Building and deploying application..."
    
    # Stop existing services
    print_status "Stopping existing services..."
    docker-compose down
    
    # Build new images
    print_status "Building Docker images..."
    docker-compose build --no-cache
    
    # Start services
    print_status "Starting services..."
    docker-compose up -d
    
    # Wait for services to be ready
    print_status "Waiting for services to be ready..."
    sleep 30
    
    # Check service health
    check_health
    
    print_status "Deployment completed successfully! 🎉"
}

# Health check
check_health() {
    print_status "Performing health checks..."
    
    # Check backend
    if curl -f http://localhost:8001/ > /dev/null 2>&1; then
        print_status "Backend health check passed ✓"
    else
        print_error "Backend health check failed"
        docker-compose logs backend
        exit 1
    fi
    
    # Check frontend
    if curl -f http://localhost/ > /dev/null 2>&1; then
        print_status "Frontend health check passed ✓"
    else
        print_error "Frontend health check failed"
        docker-compose logs frontend
        exit 1
    fi
    
    # Check MongoDB
    if docker-compose exec -T mongodb mongosh --eval "db.adminCommand('ping')" > /dev/null 2>&1; then
        print_status "MongoDB health check passed ✓"
    else
        print_error "MongoDB health check failed"
        docker-compose logs mongodb
        exit 1
    fi
}

# Show logs
show_logs() {
    print_status "Showing recent logs..."
    docker-compose logs --tail=50
}

# Cleanup
cleanup() {
    print_status "Cleaning up old containers and images..."
    docker system prune -f
    docker volume prune -f
}

# Update
update() {
    print_status "Updating application..."
    git pull
    deploy
}

# Main menu
case "${1:-deploy}" in
    "deploy")
        check_prerequisites
        deploy
        ;;
    "health")
        check_health
        ;;
    "logs")
        show_logs
        ;;
    "cleanup")
        cleanup
        ;;
    "update")
        update
        ;;
    "stop")
        print_status "Stopping services..."
        docker-compose down
        ;;
    "restart")
        print_status "Restarting services..."
        docker-compose restart
        ;;
    *)
        echo "Usage: $0 {deploy|health|logs|cleanup|update|stop|restart}"
        echo ""
        echo "Commands:"
        echo "  deploy   - Deploy the application (default)"
        echo "  health   - Check health of all services"
        echo "  logs     - Show recent logs"
        echo "  cleanup  - Clean up old containers and images"
        echo "  update   - Update and redeploy application"
        echo "  stop     - Stop all services"
        echo "  restart  - Restart all services"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}🎵 Audio to MIDI Converter deployment complete!${NC}"
echo "Frontend URL: http://localhost"
echo "Backend API: http://localhost:8001/api"
echo ""
echo "To view logs: docker-compose logs -f"
echo "To stop: docker-compose down"
