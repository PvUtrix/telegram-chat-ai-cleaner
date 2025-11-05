"""
Template: topic_extraction
Description: Extract and categorize main discussion topics
"""

async def analyze(chat_data: str, llm_manager, **kwargs):
    """
    Extract and categorize main discussion topics from the chat
    
    Args:
        chat_data: Cleaned chat text
        llm_manager: LLMManager instance configured with OpenRouter
        **kwargs: Additional options (model, temperature, max_tokens, etc.)
    
    Returns:
        dict with keys: 'result' (str), 'format' (str), 'metadata' (dict)
    """
    # Extract parameters with defaults
    model = kwargs.get('model', 'openai/gpt-4')  # Good for topic extraction
    temperature = kwargs.get('temperature', 0.3)  # Lower for more consistent categorization
    max_tokens = kwargs.get('max_tokens', 4000)
    provider = kwargs.get('provider', 'openrouter')
    prompt = """Please analyze this Telegram chat and extract the main discussion topics. Provide a comprehensive topic analysis including:

## Primary Topics
- List the 5-10 most discussed topics
- For each topic, provide:
  - Topic name and brief description
  - Frequency of discussion
  - Key participants involved
  - Time period when most discussed

## Topic Categories
- Group topics by category (e.g., Work, Personal, News, Technical, etc.)
- Identify any recurring themes or patterns
- Note topics that span multiple categories

## Topic Evolution
- How topics developed over time
- Which topics gained or lost interest
- Connections between different topics
- Topic transitions and flow

## Key Insights
- Most important or impactful discussions
- Topics that generated the most engagement
- Controversial or divisive topics
- Topics that led to action or decisions

## Topic Recommendations
- Topics that might need follow-up
- Areas for deeper discussion
- Topics that could benefit from external resources

Please format your response with clear headings and include specific examples from the chat when possible.

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
        'format': 'markdown',
        'metadata': {
            'template': 'topic_extraction',
            'provider': provider,
            'model': model,
            'temperature': temperature,
            'max_tokens': max_tokens,
            'analysis_type': 'topics',
            'focus': 'content_categorization'
        }
    }
