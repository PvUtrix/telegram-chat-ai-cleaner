# Analysis Templates

This directory contains analysis script templates that can be used to analyze Telegram chat data using LLM models through OpenRouter.

## Overview

Analysis templates are Python scripts that define how to analyze cleaned chat data. Each template is a self-contained analysis that can be run independently or in combination with other templates.

## Directory Structure

```
analysis_templates/
├── sentiment_analysis/          # Analyze emotional tone and sentiment
│   ├── script.py               # Main analysis script
│   └── config.yaml             # Template metadata
├── topic_extraction/           # Extract and categorize topics
│   ├── script.py
│   └── config.yaml
├── participant_insights/       # Profile participants and roles
│   ├── script.py
│   └── config.yaml
└── timeline_summary/           # Create chronological summaries
    ├── script.py
    └── config.yaml
```

## Built-in Templates

### 1. Sentiment Analysis
- **Purpose**: Analyze emotional tone and sentiment shifts
- **Output**: Markdown report with sentiment patterns, emotional profiles, and recommendations
- **Use Case**: Understanding group dynamics and emotional health

### 2. Topic Extraction
- **Purpose**: Extract and categorize main discussion topics
- **Output**: Organized topic breakdown with frequency and participant involvement
- **Use Case**: Understanding what the group discusses most

### 3. Participant Insights
- **Purpose**: Profile key participants and their roles
- **Output**: Detailed participant analysis with communication patterns
- **Use Case**: Understanding group leadership and collaboration

### 4. Timeline Summary
- **Purpose**: Create chronological summary of key events
- **Output**: Timeline of important events and developments
- **Use Case**: Understanding the progression of discussions over time

## Creating New Analysis Templates

### Step 1: Create Template Directory

```bash
mkdir analysis_templates/my_new_analysis
```

### Step 2: Create Script File

Create `analysis_templates/my_new_analysis/script.py`:

**Note:** If you use `tg-analyzer` CLI to create a template, it will generate a placeholder that you need to customize. The placeholder includes TODO comments indicating what needs to be implemented.

```python
"""
Template: my_new_analysis
Description: Brief description of what this analysis does

NOTE: This is a placeholder template. You need to customize the analyze function
with your specific analysis logic and prompts before using it.
"""

async def analyze(chat_data: str, llm_manager, **kwargs):
    """
    Analyze chat data using LLM
    
    NOTE: This is a placeholder implementation. You should customize:
    - The analysis prompt to match your specific analysis goals
    - The model and parameters for optimal results
    - The metadata returned for better tracking
    
    Args:
        chat_data: Cleaned chat text
        llm_manager: LLMManager instance configured with OpenRouter
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
    prompt = """Please analyze this Telegram chat and provide insights about:
    
1. [Your specific analysis focus]
2. [Another aspect to analyze]
3. [Key insights to extract]

Please format your response with clear sections and include specific examples.

Chat data:
{chat_data}"""

    result = await llm_manager.generate(
        input_data=chat_data,
        prompt=prompt.format(chat_data=chat_data),
        provider=provider,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens
    )
    
    return {
        'result': result,
        'format': 'markdown',  # or 'json', 'text'
        'metadata': {
            'template': 'my_new_analysis',
            'provider': provider,
            'model': model,
            'temperature': temperature,
            'max_tokens': max_tokens
        }
    }
```

### Step 3: Create Config File

Create `analysis_templates/my_new_analysis/config.yaml`:

```yaml
name: my_new_analysis
description: Brief description of what this analysis does
version: "1.0.0"
author: "Your Name"
tags: ["tag1", "tag2", "tag3"]

# LLM Configuration for this template
llm_config:
  model: "anthropic/claude-3-sonnet"  # Best model for this analysis
  temperature: 0.7  # Default creativity level
  max_tokens: 4000  # Default response length
  provider: "openrouter"
```

### Step 4: Test Your Template

```bash
# Run the interactive analyzer to test your new template
tg-analyzer analyze
```

## Template Script Requirements

### Required Function Signature

Every template script must have an `analyze` function with this exact signature:

```python
async def analyze(chat_data: str, llm_manager, **kwargs):
```

### Required Return Format

The function must return a dictionary with these keys:

```python
{
    'result': str,        # The analysis result text
    'format': str,        # Output format: 'markdown', 'json', or 'text'
    'metadata': dict      # Optional metadata about the analysis
}
```

### LLM Manager Usage

The `llm_manager` parameter provides access to the LLM system:

```python
# Generate analysis
    result = await llm_manager.generate(
        input_data=chat_data,
        prompt="Your analysis prompt",
        provider=provider,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens
    )

# Stream results (for long analyses)
async for chunk in llm_manager.generate_stream(
    input_data=chat_data,
    prompt="Your analysis prompt",
    provider="openrouter"
):
    # Process streaming chunks
    pass
```

## Best Practices

### 1. Clear Prompts
- Write specific, detailed prompts for better results
- Include examples of desired output format
- Specify the type of analysis you want

### 2. Error Handling
- Your script should handle errors gracefully
- Return meaningful error messages in the result
- Don't let exceptions crash the analysis

### 3. Metadata
- Include useful metadata about your analysis
- Specify the analysis type and focus
- Add version information

### 4. Output Format
- Use Markdown for human-readable results
- Use JSON for structured data
- Use Text for simple outputs

### 5. Performance
- Keep prompts concise but comprehensive
- Consider token limits for very long chats
- Use streaming for long analyses

## Example: Custom Analysis Template

Here's a complete example of a custom analysis template:

```python
"""
Template: engagement_analysis
Description: Analyze participant engagement and activity patterns
"""

async def analyze(chat_data: str, llm_manager, **kwargs):
    """
    Analyze participant engagement in the chat
    
    Args:
        chat_data: Cleaned chat text
        llm_manager: LLMManager instance configured with OpenRouter
        **kwargs: Additional options
    
    Returns:
        dict with keys: 'result' (str), 'format' (str), 'metadata' (dict)
    """
    prompt = """Please analyze the engagement patterns in this Telegram chat. Focus on:

## Participation Analysis
- Who are the most active participants?
- Who participates least?
- What are the participation patterns over time?

## Engagement Quality
- Which messages generate the most responses?
- What types of content get the most engagement?
- Are there any engagement trends or patterns?

## Group Dynamics
- How does participation affect group dynamics?
- Are there any participation imbalances?
- What could improve overall engagement?

## Recommendations
- How could engagement be improved?
- What strategies might increase participation?
- Are there any barriers to engagement?

Please provide specific examples and actionable insights.

Chat data:
{chat_data}"""

    try:
        result = await llm_manager.generate(
            input_data=chat_data,
            prompt=prompt.format(chat_data=chat_data),
            provider="openrouter"
        )
        
        return {
            'result': result,
            'format': 'markdown',
            'metadata': {
                'template': 'engagement_analysis',
                'provider': 'openrouter',
                'analysis_type': 'engagement',
                'focus': 'participation_patterns'
            }
        }
    except Exception as e:
        return {
            'result': f"Analysis failed: {str(e)}",
            'format': 'text',
            'metadata': {
                'template': 'engagement_analysis',
                'error': str(e),
                'success': False
            }
        }
```

## Troubleshooting

### Common Issues

1. **Template not found**: Make sure your template directory is in `analysis_templates/`
2. **Script errors**: Check that your `analyze` function has the correct signature
3. **LLM errors**: Verify your OpenRouter API key is configured
4. **Import errors**: Ensure all required dependencies are installed

### Debugging

Enable verbose logging to see detailed error messages:

```bash
tg-analyzer analyze --verbose
```

### Testing Templates

You can test your template by running it directly:

```python
# test_template.py
import asyncio
from src.tg_analyzer.analysis import ScriptRunner
from src.tg_analyzer.config.config_manager import ConfigManager
from src.tg_analyzer.llm.llm_manager import LLMManager

async def test_template():
    config = ConfigManager()
    llm_manager = LLMManager(config)
    script_runner = ScriptRunner(config, llm_manager)
    
    # Load your chat data
    with open('path/to/cleaned/chat.txt', 'r') as f:
        chat_data = f.read()
    
    # Run your template
    result = await script_runner.run_script(
        script_path='analysis_templates/my_template/script.py',
        chat_data=chat_data,
        template_name='my_template'
    )
    
    print(result)

asyncio.run(test_template())
```

## Contributing

When adding new templates:

1. Follow the naming convention: `snake_case`
2. Include comprehensive docstrings
3. Add appropriate tags in `config.yaml`
4. Test with real chat data
5. Update this README if adding new template categories
