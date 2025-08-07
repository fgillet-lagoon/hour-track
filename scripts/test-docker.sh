#!/bin/bash

# Test script for Docker deployment of Lagoon Time Tracker
echo "🏗️  Testing Lagoon Time Tracker Docker deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "ℹ $1"
}

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker first."
    exit 1
fi

print_success "Docker is running"

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    print_error "docker-compose is not installed or not in PATH"
    exit 1
fi

print_success "docker-compose is available"

# Start the application
print_info "Starting Lagoon Time Tracker with Docker Compose..."
docker-compose up -d

# Wait for services to be ready
print_info "Waiting for services to start..."
sleep 30

# Check if containers are running
if [ "$(docker-compose ps -q)" ]; then
    print_success "Containers are running"
else
    print_error "Failed to start containers"
    docker-compose logs
    exit 1
fi

# Test database connectivity
print_info "Testing database connectivity..."
if docker-compose exec -T db pg_isready -U lagoon_user -d lagoon_timetracker > /dev/null 2>&1; then
    print_success "Database is ready"
else
    print_error "Database is not ready"
    docker-compose logs db
    exit 1
fi

# Test web application
print_info "Testing web application..."
sleep 10

# Check if the application responds
if curl -f http://localhost:5000/ > /dev/null 2>&1; then
    print_success "Web application is responding"
else
    print_error "Web application is not responding"
    docker-compose logs web
    exit 1
fi

# Test login page
if curl -f http://localhost:5000/login > /dev/null 2>&1; then
    print_success "Login page is accessible"
else
    print_warning "Login page might not be accessible"
fi

# Show running services
print_info "Running services:"
docker-compose ps

print_info "Application URLs:"
echo "  Main Application: http://localhost:5000"
echo "  Database: localhost:5432"
echo "  pgAdmin (if started with --profile tools): http://localhost:8080"

print_info "Default login credentials:"
echo "  Admin: fgillet / fgillet"
echo "  User:  htepa / htepa"

print_success "Docker deployment test completed successfully!"
print_info "To stop the application, run: docker-compose down"
print_info "To view logs, run: docker-compose logs -f"