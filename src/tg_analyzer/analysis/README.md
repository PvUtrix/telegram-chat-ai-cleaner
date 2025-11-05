# Analysis Module

This module provides the core functionality for template-based chat analysis using LLM models. It manages analysis templates, workspaces, and script execution.

## Overview

The analysis module consists of three main components:

1. **TemplateManager** - Discovers and manages analysis templates
2. **WorkspaceManager** - Creates and manages analysis workspaces
3. **ScriptRunner** - Executes analysis scripts with LLM injection

## Architecture

```
src/tg_analyzer/analysis/
├── __init__.py              # Module exports
├── template_manager.py      # Template discovery and management
├── workspace_manager.py     # Workspace creation and management
├── script_runner.py         # Script execution with LLM
└── README.md               # This file
```

## Components

### TemplateManager

**Purpose**: Discovers, validates, and manages analysis templates

**Key Features**:
- Discovers templates in `analysis_templates/` directory
- Validates template structure and requirements
- Provides template metadata and descriptions
- Supports template creation and deletion

**Usage**:
```python
from src.tg_analyzer.analysis import TemplateManager
from src.tg_analyzer.config.config_manager import ConfigManager

config = ConfigManager()
template_manager = TemplateManager(config)

# Discover all templates
templates = template_manager.discover_templates()

# Get specific template
template = template_manager.get_template('sentiment_analysis')

# Validate template
errors = template_manager.validate_template('sentiment_analysis')

# Create new template
template_manager.create_template('my_analysis', 'My custom analysis')
```

### WorkspaceManager

**Purpose**: Creates and manages analysis workspaces for individual chats

**Key Features**:
- Creates chat-specific workspaces with date extraction
- Manages source file copying and organization
- Handles result file saving and organization
- Provides workspace listing and cleanup

**Usage**:
```python
from src.tg_analyzer.analysis import WorkspaceManager
from src.tg_analyzer.config.config_manager import ConfigManager

config = ConfigManager()
workspace_manager = WorkspaceManager(config)

# Create workspace for cleaned file
workspace_info = workspace_manager.create_workspace('path/to/cleaned/file.txt')

# Save analysis result
result_path = workspace_manager.save_result(
    workspace_info=workspace_info,
    template_name='sentiment_analysis',
    result='Analysis result text',
    format_type='markdown'
)

# List all workspaces
workspaces = workspace_manager.list_workspaces()
```

### ScriptRunner

**Purpose**: Executes analysis scripts with LLM injection

**Key Features**:
- Runs analysis scripts in isolated context
- Provides LLM manager injection
- Handles errors gracefully
- Supports multiple script execution
- Captures and validates results

**Usage**:
```python
from src.tg_analyzer.analysis import ScriptRunner
from src.tg_analyzer.config.config_manager import ConfigManager
from src.tg_analyzer.llm.llm_manager import LLMManager

config = ConfigManager()
llm_manager = LLMManager(config)
script_runner = ScriptRunner(config, llm_manager)

# Run single script
result = await script_runner.run_script(
    script_path='analysis_templates/sentiment_analysis/script.py',
    chat_data=cleaned_chat_text,
    template_name='sentiment_analysis'
)

# Run multiple scripts
scripts = [
    {'name': 'sentiment_analysis', 'script_path': '...'},
    {'name': 'topic_extraction', 'script_path': '...'}
]
results = await script_runner.run_multiple_scripts(scripts, chat_data)
```

## Template System

### Template Structure

Each analysis template must follow this structure:

```
analysis_templates/
└── template_name/
    ├── script.py          # Required: Main analysis script
    └── config.yaml        # Optional: Template metadata
```

### Script Requirements

Every template script must implement:

**Note:** When creating a new template using `create_template()`, it generates a placeholder that you need to customize before use. The placeholder includes TODO comments and notes indicating what needs to be implemented.

```python
async def analyze(chat_data: str, llm_manager, **kwargs):
    """
    NOTE: This is a placeholder implementation. You should customize:
    - The analysis prompt to match your specific analysis goals
    - The model and parameters for optimal results
    - The metadata returned for better tracking
    
    Args:
        chat_data: Cleaned chat text
        llm_manager: LLMManager instance
        **kwargs: Additional options (model, temperature, max_tokens, etc.)
    
    Returns:
        dict with keys: 'result' (str), 'format' (str), 'metadata' (dict)
    """
    # TODO: Customize these parameters for your analysis
    model = kwargs.get('model', 'openai/gpt-4')
    temperature = kwargs.get('temperature', 0.7)
    max_tokens = kwargs.get('max_tokens', 4000)
    provider = kwargs.get('provider', 'openrouter')
    
    # TODO: Customize this prompt for your specific analysis needs
    prompt = "Your custom analysis prompt"
    
    result = await llm_manager.generate(
        input_data=chat_data,
        prompt=prompt,
        provider=provider,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens
    )
    
    return {
        'result': result,
        'format': 'markdown',
        'metadata': {
            'template': 'template_name',
            'provider': provider,
            'model': model,
            'temperature': temperature,
            'max_tokens': max_tokens
        }
    }
```

### Template Discovery

Templates are automatically discovered by scanning the `analysis_templates/` directory:

1. **Directory Scan**: Scans for subdirectories in `analysis_templates/`
2. **Script Validation**: Checks for required `script.py` file
3. **Metadata Loading**: Loads optional `config.yaml` metadata
4. **Template Registration**: Registers valid templates

### Template Validation

Templates are validated for:

- **Required Files**: Must have `script.py`
- **Function Signature**: Must have `analyze` function with correct signature
- **Return Format**: Must return dictionary with required keys
- **LLM Usage**: Must use `llm_manager` parameter

## Workspace System

### Workspace Creation

Workspaces are created automatically when starting an analysis session:

1. **File Selection**: User selects cleaned file from `data/output/`
2. **Name Extraction**: Extracts chat name and dates from filename
3. **Directory Creation**: Creates `data/analysis/{chat_name}_{dates}/`
4. **Source Copy**: Copies cleaned file to workspace as `source.txt`
5. **Results Directory**: Creates `results/` subdirectory

### Workspace Structure

```
data/analysis/{chat_name}_{dates}/
├── source.txt              # Copy of cleaned chat file
└── results/                # Analysis results
    ├── template1_timestamp.md
    ├── template2_timestamp.json
    └── template3_timestamp.txt
```

### Result Management

Results are saved with automatic naming:

- **Format**: `{template_name}_{timestamp}.{extension}`
- **Timestamp**: `YYYYMMDD_HHMMSS`
- **Extension**: Based on result format (`.md`, `.json`, `.txt`)

## Error Handling

### Script Execution Errors

- **Graceful Failure**: Scripts that fail don't crash the entire analysis
- **Error Reporting**: Clear error messages for debugging
- **Continue Option**: Option to continue with remaining scripts

### Template Validation Errors

- **Missing Files**: Clear error for missing `script.py`
- **Invalid Signature**: Error for incorrect function signature
- **Return Format**: Validation of return dictionary format

### LLM Errors

- **Provider Errors**: Handles LLM provider failures
- **Token Limits**: Manages token limit exceeded errors
- **Network Issues**: Handles network connectivity problems

## Configuration

### Required Configuration

```python
# LLM Configuration
OPENROUTER_API_KEY=sk-or-your-key-here
DEFAULT_LLM_PROVIDER=openrouter

# Data Directory Configuration
DATA_DIR=data
ANALYSIS_DIR=analysis
```

### Optional Configuration

```python
# Template Directory
TEMPLATES_DIR=analysis_templates

# Default Models
DEFAULT_LLM_MODEL=openai/gpt-4

# Logging
LOG_LEVEL=INFO
```

## Integration

### CLI Integration

The analysis module integrates with the CLI through the `analyze` command:

```python
# CLI command implementation
@cli.command()
def analyze():
    # Initialize components
    template_manager = TemplateManager(ctx.config)
    workspace_manager = WorkspaceManager(ctx.config)
    script_runner = ScriptRunner(ctx.config, ctx.analyzer.llm_manager)
    
    # Interactive workflow
    # 1. Select cleaned file
    # 2. Create workspace
    # 3. Select templates
    # 4. Run analysis
    # 5. Save results
```

### LLM Integration

The analysis module integrates with the LLM system:

```python
# LLM Manager injection
script_runner = ScriptRunner(config, llm_manager)

# Script execution with LLM access
result = await script_runner.run_script(
    script_path=template['script_path'],
    chat_data=chat_data,
    template_name=template['name']
)
```

## Development

### Adding New Components

To add new analysis functionality:

1. **Create Component**: Add new class to analysis module
2. **Update Exports**: Add to `__init__.py`
3. **Add Tests**: Create tests for new functionality
4. **Update Documentation**: Update this README

### Extending Template System

To extend the template system:

1. **Add Template Types**: Support new template categories
2. **Enhance Validation**: Add new validation rules
3. **Improve Discovery**: Add new discovery mechanisms
4. **Update Metadata**: Support new metadata fields

### Performance Optimization

For better performance:

1. **Caching**: Cache template discovery results
2. **Parallel Execution**: Run multiple scripts in parallel
3. **Streaming**: Support streaming for long analyses
4. **Resource Management**: Better memory and CPU usage

## Testing

### Unit Tests

```python
# Test template discovery
def test_template_discovery():
    template_manager = TemplateManager(config)
    templates = template_manager.discover_templates()
    assert len(templates) > 0

# Test workspace creation
def test_workspace_creation():
    workspace_manager = WorkspaceManager(config)
    workspace_info = workspace_manager.create_workspace('test_file.txt')
    assert workspace_info['workspace_path'].exists()

# Test script execution
async def test_script_execution():
    script_runner = ScriptRunner(config, llm_manager)
    result = await script_runner.run_script(
        script_path='test_template/script.py',
        chat_data='test data',
        template_name='test_template'
    )
    assert 'result' in result
```

### Integration Tests

```python
# Test full analysis workflow
async def test_analysis_workflow():
    # Initialize components
    template_manager = TemplateManager(config)
    workspace_manager = WorkspaceManager(config)
    script_runner = ScriptRunner(config, llm_manager)
    
    # Create workspace
    workspace_info = workspace_manager.create_workspace('test_file.txt')
    
    # Run analysis
    result = await script_runner.run_script(
        script_path='analysis_templates/sentiment_analysis/script.py',
        chat_data='test chat data',
        template_name='sentiment_analysis'
    )
    
    # Save result
    result_path = workspace_manager.save_result(
        workspace_info=workspace_info,
        template_name='sentiment_analysis',
        result=result['result'],
        format_type=result['format']
    )
    
    assert Path(result_path).exists()
```

## Troubleshooting

### Common Issues

1. **Template Not Found**: Check template directory structure
2. **Script Errors**: Verify script function signature
3. **LLM Errors**: Check API key configuration
4. **Workspace Errors**: Verify file permissions

### Debug Mode

Enable debug logging for detailed error information:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Error Recovery

The system includes error recovery mechanisms:

- **Script Failures**: Continue with remaining scripts
- **LLM Errors**: Retry with different provider
- **File Errors**: Create fallback workspaces
- **Network Issues**: Handle connectivity problems

This analysis module provides a robust foundation for template-based chat analysis with comprehensive error handling and flexible configuration options.
