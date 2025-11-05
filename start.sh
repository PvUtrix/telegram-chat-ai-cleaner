#!/bin/bash

# Telegram Chat Analyzer Launcher Script
# This script activates the virtual environment and runs the CLI

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
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

print_header() {
    echo -e "${PURPLE}🚀 $1${NC}"
}

print_command() {
    echo -e "${CYAN}❯ $1${NC}"
}

# Check if we're in the right directory
check_directory() {
    if [ ! -f "setup.py" ] || [ ! -d "src" ]; then
        print_error "Please run this script from the telegram_chat_analyzer root directory"
        exit 1
    fi
}

# Check if virtual environment exists
check_venv() {
    if [ ! -d "venv" ]; then
        print_warning "Virtual environment not found. Creating one..."
        python3 -m venv venv
        print_success "Virtual environment created!"
    fi
}

# Activate virtual environment
activate_venv() {
    source venv/bin/activate
    print_success "Virtual environment activated"
}

# Show usage information
show_usage() {
    echo ""
    print_header "Telegram Chat Analyzer"
    echo ""
    echo "Usage:"
    echo "  ./start.sh                        # Show help"
    echo "  ./start.sh --help                # Show CLI help"
    echo "  ./start.sh clean [file]          # Clean a chat file (auto-selects if no file given)"
    echo "  ./start.sh analyze [file]        # Analyze with LLM (auto-selects if no file given)"
    echo "  ./start.sh vectorize [file]      # Create embeddings (auto-selects if no file given)"
    echo "  ./start.sh search <query>        # Search vector database"
    echo "  ./start.sh templates             # List available analysis templates"
    echo "  ./start.sh config <command>      # Manage configuration and API keys"
    echo "  ./start.sh watch                 # Watch input directory and auto-process files"
    echo "  ./start.sh web                   # Start web interface"
    echo ""
    echo "Cleaning Options:"
    echo "  --approach [privacy|size|context]    # Cleaning approach (default: privacy)"
    echo "  --level [1|2|3]                      # Cleaning level (default: 2)"
    echo "  --format [text|json|markdown|csv]    # Output format (default: text)"
    echo "  --interactive, -i                    # Interactive mode - numbered menu for approach/level"
    echo "  --batch                              # Process all files in input directory"
    echo "  --output <file>                      # Custom output file path"
    echo ""
    echo "Analysis Options:"
    echo "  --template <name>                    # Use predefined prompt template"
    echo "  --prompt <text>                      # Custom analysis prompt"
    echo "  --provider [openai|anthropic|google|groq|ollama]  # LLM provider"
    echo "  --model <model>                      # Specific model to use"
    echo "  --stream                             # Stream output in real-time"
    echo "  --output <file>                      # Save results to file"
    echo ""
    echo "Vectorization Options:"
    echo "  --provider [openai|google|ollama]    # Embedding provider"
    echo "  --model <model>                      # Embedding model"
    echo "  --chunk-strategy [fixed_size|sentence|paragraph|overlap]  # Text chunking"
    echo "  --chunk-size <number>                # Text chunk size"
    echo ""
    echo "Configuration Commands:"
    echo "  ./start.sh config list               # Show current configuration"
    echo "  ./start.sh config set <key> <value>  # Set configuration value"
    echo "  ./start.sh config get <key>          # Get configuration value"
    echo ""
    echo "Examples:"
    echo "  ./start.sh clean                           # Auto-select file from data/input/"
    echo "  ./start.sh clean --interactive             # Interactive menu: select 1-3 for approach/level"
    echo "  ./start.sh clean --approach privacy --level 3 --format markdown"
    echo "  ./start.sh clean --batch                   # Process all files"
    echo "  ./start.sh analyze                        # Auto-select and analyze"
    echo "  ./start.sh analyze --template summary --provider openai"
    echo "  ./start.sh analyze --prompt 'Analyze sentiment' --stream"
    echo "  ./start.sh vectorize --provider openai --chunk-strategy overlap"
    echo "  ./start.sh search 'machine learning'       # Search vector database"
    echo "  ./start.sh templates                       # List all templates"
    echo "  ./start.sh config list                     # Show current config"
    echo "  ./start.sh config set OPENAI_API_KEY your-key-here"
    echo "  ./start.sh web --host 0.0.0.0 --port 8001 # Start web interface"
    echo ""
    print_info "First time? Copy env.example to .env and add your API keys!"
    print_info "Put your Telegram JSON exports in data/input/ for auto-selection!"
    print_info "For interactive prompts, run commands directly in your terminal!"
    print_info "Example: source venv/bin/activate && tg-analyzer clean --interactive"
}

# Main function
main() {
    check_directory
    check_venv
    activate_venv

    # If no arguments provided, show usage
    if [ $# -eq 0 ]; then
        show_usage
        return
    fi

    # Check if help is requested
    if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
        show_usage
        return
    fi

    # Run the CLI command
    print_command "tg-analyzer $@"
    echo ""

    # Execute the command
    exec tg-analyzer "$@"
}

# Run main function with all arguments
main "$@"
