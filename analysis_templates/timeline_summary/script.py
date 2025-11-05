"""
Template: timeline_summary
Description: Create chronological summary of key events and developments
"""

async def analyze(chat_data: str, llm_manager, **kwargs):
    """
    Create a chronological summary of key events and developments
    
    Args:
        chat_data: Cleaned chat text
        llm_manager: LLMManager instance configured with OpenRouter
        **kwargs: Additional options (model, temperature, max_tokens, etc.)
    
    Returns:
        dict with keys: 'result' (str), 'format' (str), 'metadata' (dict)
    """
    # Extract parameters with defaults
    model = kwargs.get('model', 'openai/gpt-4')  # Good for chronological analysis
    temperature = kwargs.get('temperature', 0.4)  # Lower for more factual timeline
    max_tokens = kwargs.get('max_tokens', 4000)
    provider = kwargs.get('provider', 'openrouter')
    prompt = """Please analyze this Telegram chat and create a comprehensive timeline summary of key events and developments. Include:

## Chronological Timeline
Create a timeline showing:
- **Major events** and their dates/times
- **Important announcements** or decisions
- **Key discussions** and their outcomes
- **Milestones** or achievements
- **Changes in direction** or focus

## Event Categories
Organize events by type:
- **Decisions made** (what was decided and when)
- **Problems encountered** (issues that arose and how they were handled)
- **Solutions implemented** (how problems were solved)
- **External events** (things that happened outside the chat that affected the conversation)
- **Internal developments** (changes within the group or project)

## Key Turning Points
Identify and explain:
- **Critical moments** that changed the direction of discussions
- **Breakthrough insights** or realizations
- **Conflict resolution** moments
- **Collaboration milestones**
- **Decision points** where choices were made

## Impact Analysis
For each major event, assess:
- **Immediate impact** (what happened right after)
- **Long-term consequences** (how it affected later discussions)
- **Participant reactions** (how different people responded)
- **Group dynamics changes** (how relationships or roles shifted)

## Summary Insights
- **Overall narrative** (the story of this chat)
- **Major themes** that developed over time
- **Success patterns** (what worked well)
- **Challenge patterns** (recurring issues)
- **Growth indicators** (how the group or project evolved)

## Recommendations
- **Follow-up actions** needed based on the timeline
- **Lessons learned** from the chronological analysis
- **Pattern recognition** for future reference
- **Timeline gaps** that might need attention

Please format your response with clear chronological sections and include specific dates/times when available.

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
            'template': 'timeline_summary',
            'provider': provider,
            'model': model,
            'temperature': temperature,
            'max_tokens': max_tokens,
            'analysis_type': 'timeline',
            'focus': 'chronological_events'
        }
    }
