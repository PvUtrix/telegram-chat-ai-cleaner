# Telegram Chat Analyzer

An open-source tool for cleaning, analyzing, and vectorizing Telegram chat exports with multiple deployment options (CLI, Docker, Web UI).

## Features

- **Smart File Selection**: Automatically detects and selects files from input directory - no manual paths needed!
- **Multiple Cleaning Strategies**: 9 different cleaning approaches optimized for privacy, size, or context
- **LLM Integration**: Support for OpenAI, Anthropic, Google Gemini, Groq, OpenRouter, and local Ollama models
- **Vector Database**: Store chat embeddings in Supabase for semantic search
- **Batch Processing**: Drop multiple chat exports and process them automatically
- **Multiple Interfaces**: CLI for power users, web UI for ease of use, Docker for deployment
- **Flexible Output**: Cleaned data in text, JSON, or Markdown formats

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/telegram-chat-analyzer.git
cd telegram-chat-analyzer

# Install dependencies
pip install -r requirements.txt

# Or install as package
pip install -e .
```

### Basic Usage

1. **Export your Telegram chat** as JSON from Telegram Desktop
2. **Drop the JSON file** in the `data/input/` directory
3. **Configure your API keys** (see Configuration section)
4. **Run analysis**:

```bash
# Interactive analysis with templates
tg-analyzer analyze

# Just clean the data
tg-analyzer clean data/input/your_chat.json --approach privacy --level 2

# Create embeddings for vector search
tg-analyzer vectorize data/input/your_chat.json
```

## Data Directory Structure

```
data/
├── input/           # Drop your Telegram JSON exports here
├── output/          # Cleaned files organized by cleaning strategy
│   ├── privacy_basic/
│   ├── privacy_medium/
│   └── context_full/
├── analysis/        # Analysis workspaces with results
│   └── {chat_name}_{dates}/
│       ├── source.txt
│       └── results/
└── vectors/         # Vector embeddings metadata

analysis_templates/  # Analysis script templates
├── sentiment_analysis/
├── topic_extraction/
└── participant_insights/
```

## Cleaning Strategies

### Privacy-Focused Cleaning
- **Level 1 (Basic)**: Names + content only, anonymized user IDs - Perfect for sharing conversations while protecting participant privacy
- **Level 2 (Medium)**: + timestamps + reply structure - Balances privacy with conversation context for better analysis
- **Level 3 (Full)**: + all metadata, original user identifiers - Complete data preservation for comprehensive analysis while maintaining original structure

### Size-Focused Cleaning
- **Level 1 (Basic)**: Text only, minimal metadata - Ideal for creating compact text files for basic analysis or storage
- **Level 2 (Medium)**: + links + basic sender/date info - Strikes a balance between file size and useful context information
- **Level 3 (Full)**: + all media references, reactions, edits - Preserves complete conversation richness for detailed analysis

### Context-Focused Cleaning
- **Level 1 (Basic)**: Flat chronological message list - Simple linear format perfect for basic text analysis and keyword searches
- **Level 2 (Medium)**: + reply chains and threaded structure - Maintains conversation flow and context for better understanding of discussions
- **Level 3 (Full)**: + reactions + complete conversation graph - Preserves all interaction patterns for advanced social network analysis

## Analysis Templates

The new interactive analysis system uses template-based scripts for comprehensive chat analysis:

### Built-in Templates
- **Sentiment Analysis**: Analyze emotional tone and sentiment shifts - Discover mood patterns and emotional dynamics throughout your conversations
- **Topic Extraction**: Identify and categorize main discussion topics - Automatically surface key themes and subjects from your chat history
- **Participant Insights**: Profile key participants and their roles - Understand who contributes what and how different people engage in discussions
- **Timeline Summary**: Create chronological summary of key events - Get a structured overview of important moments and developments over time

### Interactive Workflow
1. **Select cleaned file** from `data/output/` directory - Pick from your processed chat files with different cleaning levels
2. **Choose analysis templates** (single or multiple) - Select one or combine multiple analysis approaches for comprehensive insights
3. **Run analysis scripts** with real-time results - Watch as AI processes your data and generates detailed analysis reports
4. **Save results** to organized workspace - Automatically organize findings in structured directories for easy access
5. **View results** in dedicated chat workspace - Browse through formatted results with clear visual presentation

### Creating Custom Templates
Create new analysis templates in `analysis_templates/` directory:

**Note:** When creating a new template using the CLI, it generates a placeholder that you need to customize before use. The placeholder includes TODO comments indicating what needs to be implemented.

```python
# analysis_templates/my_analysis/script.py
async def analyze(chat_data: str, llm_manager, **kwargs):
    # TODO: Customize the prompt and parameters for your analysis
    result = await llm_manager.generate(
        input_data=chat_data,
        prompt="Your custom analysis prompt",  # Customize this!
        provider="openrouter",
        model=kwargs.get('model', 'openai/gpt-4'),
        temperature=kwargs.get('temperature', 0.7),
        max_tokens=kwargs.get('max_tokens', 4000)
    )
    return {
        'result': result,
        'format': 'markdown',
        'metadata': {'template': 'my_analysis'}
    }
```

## Configuration

1. Copy the example configuration:
```bash
cp env.example .env
```

2. Edit `.env` with your API keys:
```bash
# Required for LLM analysis
OPENAI_API_KEY=sk-your-key-here
ANTHROPIC_API_KEY=sk-ant-your-key-here

# Optional: for vector storage
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key-here
```

## Command Line Interface

```bash
# Show all commands - Display comprehensive help with all available options and usage examples
tg-analyzer --help

# Clean a chat export - Process and clean your Telegram chat data with specific privacy and format settings
tg-analyzer clean input/chat.json --approach privacy --level 2 --format text

# Analyze with LLM - Use AI to extract insights and answer questions about your chat content
tg-analyzer analyze input/chat.json --prompt "What are the main topics?" --provider openai

# Batch process all files in input directory - Automatically process multiple chat files with consistent settings
tg-analyzer batch --approach context --level 3

# Start file watcher for automatic processing - Monitor input directory and process new files automatically
tg-analyzer watch

# Manage configuration - Set up and manage your API keys and settings
tg-analyzer config set OPENAI_API_KEY sk-your-key-here
tg-analyzer config list
```

## Web Interface

Start the web server:

```bash
# Development mode
tg-analyzer web --host 0.0.0.0 --port 8000

# Or run directly
python -m uvicorn src.tg_analyzer.web.backend.app:app --reload
```

Then open http://localhost:8000 in your browser.

Features:
- **Drag & drop file upload** - Simply drag your Telegram JSON files to start processing without complex file navigation
- **Visual cleaning level selection** - Choose cleaning strategies with intuitive visual indicators and clear descriptions
- **Prompt templates and editor** - Use pre-built analysis prompts or create custom ones with a user-friendly editor
- **Real-time progress updates** - Watch processing status and get immediate feedback on analysis progress
- **API key management** - Securely configure and manage your LLM provider API keys through the interface
- **Vector search interface** - Search through your chat embeddings with semantic search capabilities

## Docker Deployment

The easiest way to run Telegram Chat Analyzer is using Docker. We've provided several deployment options:

## Quick Start

### Option 1: Local Installation (Recommended)

```bash
# 1. Clone and enter the directory
git clone <repository-url>
cd telegram-chat-analyzer

# 2. Configure your API keys
cp env.example .env
# Edit .env with your API keys (OpenAI, Anthropic, etc.)

# 3. Use the convenient launcher script (handles venv automatically)
./start.sh templates                          # List available templates - Browse all analysis templates with descriptions
./start.sh clean                              # Auto-select file and clean (uses defaults) - Quick cleaning with sensible defaults
./start.sh clean --interactive                # Interactive menu: select numbers 1-3 for options - Step-by-step guided cleaning process
./start.sh clean --approach privacy --level 2 # Clean with specific settings - Custom cleaning with exact parameters
./start.sh analyze                            # Auto-select and analyze with LLM - Quick analysis with file auto-detection
./start.sh analyze --template summary         # Analyze with specific template - Run analysis using a particular template
./start.sh web                                # Start web interface - Launch the user-friendly web interface
```

### Option 2: Docker Deployment

```bash
# 1. Clone and enter the directory
git clone <repository-url>
cd telegram-chat-analyzer

# 2. Configure your API keys
cp env.example .env
# Edit .env with your API keys (OpenAI, Anthropic, etc.)

# 3. Run the interactive Docker launcher - Guided setup with multiple deployment options
./run-docker.sh
```

The launcher will guide you through different deployment options.

### Manual Docker Commands

#### Basic Web Interface
```bash
# Build and start web interface only - Quick deployment with just the web UI
docker-compose up --build tg-analyzer

# Access at http://localhost:8000 - Open your browser to use the web interface
```

#### With Local Ollama Support
```bash
# Start with local LLM support - Run AI analysis locally without external API costs
docker-compose --profile with-ollama up -d

# Pull a model in Ollama container - Download and set up your preferred language model
docker exec -it telegram-chat-analyzer_ollama_1 ollama pull llama2
```

#### With Local PostgreSQL + pgvector
```bash
# Start with local vector database - Enable semantic search with local vector storage
docker-compose --profile with-postgres up -d

# PostgreSQL available at localhost:5432 - Connect to your local database
# User: tguser, Password: tgpass, Database: tg_analyzer - Default credentials for database access
```

#### Full Stack Deployment
```bash
# Start everything (web + Ollama + PostgreSQL) - Complete local setup with all features
docker-compose --profile with-ollama --profile with-postgres up -d
```

### Docker Data Persistence

- **Configuration**: Mount your `.env` file for API keys - Keep your settings secure and persistent across container restarts
- **Data**: All chat files and results persist in the `./data/` directory - Your analysis results and chat data remain available after container updates
- **Models**: Ollama models persist in Docker volumes - Downloaded language models stay cached for faster subsequent runs
- **Database**: PostgreSQL data persists in Docker volumes - Vector embeddings and analysis results are preserved across deployments

### Using CLI in Docker

```bash
# Run CLI commands in the container - Execute commands inside the running Docker container
docker-compose exec tg-analyzer tg-analyzer --help

# Clean a chat file (auto-selects from data/input/) - Process files with automatic file detection
docker-compose exec tg-analyzer tg-analyzer clean

# Clean with specific settings - Apply custom cleaning parameters to your chat data
docker-compose exec tg-analyzer tg-analyzer clean --approach privacy --level 2

# Analyze with LLM (auto-selects file) - Run AI analysis with automatic file selection
docker-compose exec tg-analyzer tg-analyzer analyze --template summary
```

### Production Deployment

For production use:

1. **Use external databases**: Configure Supabase or managed PostgreSQL - Ensure reliable data storage and backup for production workloads
2. **Set proper environment variables**: Don't mount .env file - Use secure environment variable injection for API keys and configuration
3. **Configure reverse proxy**: Use nginx or similar for SSL termination - Add SSL encryption and load balancing for production security
4. **Set resource limits**: Configure Docker memory/CPU limits - Prevent resource exhaustion and ensure stable performance
5. **Enable logging**: Set up proper log aggregation - Monitor application health and troubleshoot issues in production

```bash
# Example production docker-compose override
version: '3.8'
services:
  tg-analyzer:
    environment:
      - SUPABASE_URL=https://your-project.supabase.co
      - SUPABASE_KEY=your-anon-key
      - OPENAI_API_KEY=your-key-here
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
```

## Privacy and Data Handling

- This project processes sensitive chat data. Your source files and outputs live under `data/` on your machine and are ignored by git by default.
- Do not commit files from `data/` or any `.env` files. The repository includes `.gitignore` and `.dockerignore` rules to prevent accidental publication.
- Copy `env.example` to `.env` and add your own API keys locally. Never share `.env`.
- When filing issues or sharing examples, redact or synthesize data; never upload real conversations.

## API Usage

```python
from tg_analyzer import TelegramAnalyzer

# Initialize
analyzer = TelegramAnalyzer()

# Clean data
cleaned_data = analyzer.clean("data/input/chat.json", approach="privacy", level=2)

# Analyze with LLM
result = analyzer.analyze(cleaned_data, prompt="Summarize key insights")

# Create embeddings
vectors = analyzer.vectorize(cleaned_data, provider="openai")
```

## Supported LLM Providers

- **OpenAI**: GPT-4, GPT-3.5-turbo, text-embedding-3-small/large
- **Anthropic**: Claude-3 Opus, Sonnet, Haiku
- **Google**: Gemini Pro, Gemini Ultra
- **Groq**: Fast inference with Llama 2, Mixtral
- **Ollama**: Local models (Llama 2, Mistral, etc.)

## Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src/
isort src/

# Type checking
mypy src/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Roadmap

- [ ] Plugin system for custom cleaning strategies
- [ ] Support for additional chat platforms (Discord, Slack)
- [ ] Advanced analytics dashboard
- [ ] Multi-language support
- [ ] Real-time chat monitoring
- [ ] Integration with popular vector databases (Pinecone, Weaviate)

## Support

- Issues: [GitHub Issues](https://github.com/yourusername/telegram-chat-analyzer/issues)
- Discussions: [GitHub Discussions](https://github.com/yourusername/telegram-chat-analyzer/discussions)
- Documentation: [Wiki](https://github.com/yourusername/telegram-chat-analyzer/wiki)
