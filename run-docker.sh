#!/bin/bash

# Telegram Chat Analyzer Docker Launcher
# This script helps you run the Telegram Chat Analyzer with Docker

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
}

# Check if .env file exists
check_env() {
    if [ ! -f ".env" ]; then
        print_warning ".env file not found. Copying from env.example..."
        cp env.example .env
        print_warning "Please edit .env file with your API keys before running!"
        echo ""
    fi
}

# Main menu
show_menu() {
    echo "========================================"
    echo "  Telegram Chat Analyzer - Docker Menu"
    echo "========================================"
    echo ""
    echo "Choose an option:"
    echo "1) 🚀 Start web interface only"
    echo "2) 🤖 Start with local Ollama support"
    echo "3) 🗄️  Start with local PostgreSQL + pgvector"
    echo "4) 🔄 Start full stack (web + Ollama + PostgreSQL)"
    echo "5) 🛑 Stop all services"
    echo "6) 📊 Show status"
    echo "7) 🧹 Clean up (remove containers and volumes)"
    echo "8) ❓ Help"
    echo "9) Exit"
    echo ""
}

# Start web interface only
start_web() {
    print_info "Starting Telegram Chat Analyzer web interface..."
    docker-compose up -d tg-analyzer
    print_success "Web interface started! Visit http://localhost:8000"
    print_info "To view logs: docker-compose logs -f tg-analyzer"
}

# Start with Ollama
start_with_ollama() {
    print_info "Starting with Ollama support..."
    docker-compose --profile with-ollama up -d
    print_success "Services started with Ollama support!"
    print_info "Web interface: http://localhost:8000"
    print_info "Ollama API: http://localhost:11434"
}

# Start with PostgreSQL
start_with_postgres() {
    print_info "Starting with PostgreSQL + pgvector..."
    docker-compose --profile with-postgres up -d
    print_success "Services started with PostgreSQL!"
    print_info "Web interface: http://localhost:8000"
    print_info "PostgreSQL: localhost:5432 (user: tguser, pass: tgpass)"
}

# Start full stack
start_full() {
    print_info "Starting full stack (web + Ollama + PostgreSQL)..."
    docker-compose --profile with-ollama --profile with-postgres up -d
    print_success "Full stack started!"
    print_info "Web interface: http://localhost:8000"
    print_info "Ollama API: http://localhost:11434"
    print_info "PostgreSQL: localhost:5432 (user: tguser, pass: tgpass)"
}

# Stop all services
stop_services() {
    print_info "Stopping all services..."
    docker-compose down
    print_success "All services stopped!"
}

# Show status
show_status() {
    print_info "Service status:"
    docker-compose ps
    echo ""
    print_info "Disk usage:"
    docker system df
}

# Clean up
cleanup() {
    print_warning "This will remove all containers, volumes, and networks!"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Cleaning up..."
        docker-compose down -v --remove-orphans
        docker system prune -f
        print_success "Cleanup completed!"
    else
        print_info "Cleanup cancelled."
    fi
}

# Help
show_help() {
    echo "Telegram Chat Analyzer - Docker Helper"
    echo ""
    echo "This script helps you run the Telegram Chat Analyzer using Docker."
    echo ""
    echo "Prerequisites:"
    echo "  - Docker and Docker Compose installed"
    echo "  - .env file configured with your API keys"
    echo ""
    echo "Usage:"
    echo "  ./run-docker.sh"
    echo ""
    echo "Options:"
    echo "  1. Web only: Just the main application"
    echo "  2. + Ollama: Run LLMs locally with Ollama"
    echo "  3. + PostgreSQL: Local vector database"
    echo "  4. Full stack: Everything together"
    echo ""
    echo "Configuration:"
    echo "  - Edit .env file for API keys"
    echo "  - Data persists in ./data/ directory"
    echo "  - Logs available via 'docker-compose logs'"
    echo ""
}

# Main script
main() {
    check_docker
    check_env

    while true; do
        show_menu
        read -p "Enter your choice (1-9): " choice
        echo ""

        case $choice in
            1)
                start_web
                ;;
            2)
                start_with_ollama
                ;;
            3)
                start_with_postgres
                ;;
            4)
                start_full
                ;;
            5)
                stop_services
                ;;
            6)
                show_status
                ;;
            7)
                cleanup
                ;;
            8)
                show_help
                ;;
            9)
                print_info "Goodbye! 👋"
                exit 0
                ;;
            *)
                print_error "Invalid option. Please choose 1-9."
                ;;
        esac

        echo ""
        read -p "Press Enter to continue..."
        clear
    done
}

# Run main function
main "$@"

