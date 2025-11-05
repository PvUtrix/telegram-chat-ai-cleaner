"""
Template: sentiment_analysis
Description: Analyze emotional tone and sentiment shifts in the chat
"""

async def analyze(chat_data: str, llm_manager, **kwargs):
    """
    Analyze sentiment and emotional tone of the chat
    
    Args:
        chat_data: Cleaned chat text
        llm_manager: LLMManager instance configured with OpenRouter
        **kwargs: Additional options (model, temperature, max_tokens, etc.)
    
    Returns:
        dict with keys: 'result' (str), 'format' (str), 'metadata' (dict)
    """
    # Extract parameters with defaults
    model = kwargs.get('model', 'anthropic/claude-3-sonnet')  # Best for sentiment analysis
    temperature = kwargs.get('temperature', 0.5)  # More consistent for sentiment
    max_tokens = kwargs.get('max_tokens', 4000)
    provider = kwargs.get('provider', 'openrouter')
    prompt = """Please analyze the sentiment and emotional tone of this Telegram chat conversation. Provide a comprehensive analysis including:

## Overall Sentiment
- Overall emotional tone (positive, negative, neutral, mixed)
- Dominant emotions expressed
- Sentiment distribution across participants

## Sentiment Shifts
- Key moments where sentiment changed significantly
- Triggers that caused emotional shifts
- Patterns in emotional responses

## Participant Emotional Profiles
- Individual emotional patterns and tendencies
- Who tends to be more positive/negative
- Emotional leadership in the group

## Emotional Context
- Stress indicators or tension points
- Celebratory or joyful moments
- Supportive or empathetic exchanges
- Conflicts or disagreements

## Recommendations
- Suggestions for improving group dynamics
- Areas where emotional support might be needed
- Positive patterns to encourage

Please format your response in clear sections with specific examples from the chat when possible.

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
            'template': 'sentiment_analysis',
            'provider': provider,
            'model': model,
            'temperature': temperature,
            'max_tokens': max_tokens,
            'analysis_type': 'sentiment',
            'focus': 'emotional_tone'
        }
    }
