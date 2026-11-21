"""
Template: song_generation
Description: Generate a song based on the chat content, themes, participants, and sentiment
"""

from pathlib import Path


async def analyze(chat_data: str, llm_manager, **kwargs):
    """
    Generate a song based on the chat content
    
    Args:
        chat_data: Cleaned chat text
        llm_manager: LLMManager instance configured with OpenRouter
        **kwargs: Additional options (model, temperature, max_tokens,
                  prompt_language: 'en' (default) or 'ru')
    
    Returns:
        dict with keys: 'result' (str), 'format' (str), 'metadata' (dict)
    """
    # Extract parameters with defaults
    model = kwargs.get('model', 'gpt-4-turbo')  # Good for creative content
    temperature = kwargs.get('temperature', 0.9)  # Higher creativity for song writing
    max_tokens = kwargs.get('max_tokens', 3000)  # Enough for a full song
    provider = kwargs.get('provider', 'openai')
    
    # The English prompt is the default; prompt_language="ru" uses the Russian
    # original in prompt-ru.md. Either way the song is written in the chat's language.
    prompt_language = kwargs.get('prompt_language', 'en')
    prompt_file = 'prompt-ru.md' if prompt_language == 'ru' else 'prompt.md'
    prompt = (Path(__file__).parent / prompt_file).read_text(encoding='utf-8')

    try:
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
                'template': 'song_generation',
                'provider': provider,
                'model': model,
                'temperature': temperature,
                'max_tokens': max_tokens,
                'analysis_type': 'creative',
                'focus': 'song_generation'
            }
        }
    except Exception as e:
        return {
            'result': f"Song generation failed: {str(e)}",
            'format': 'text',
            'metadata': {
                'template': 'song_generation',
                'error': str(e),
                'success': False
            }
        }

