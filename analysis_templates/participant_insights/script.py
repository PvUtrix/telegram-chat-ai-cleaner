"""
Template: participant_insights
Description: Profile key participants and their roles in the conversation
"""

async def analyze(chat_data: str, llm_manager, **kwargs):
    """
    Analyze participant behavior and roles in the chat
    
    Args:
        chat_data: Cleaned chat text
        llm_manager: LLMManager instance configured with OpenRouter
        **kwargs: Additional options (model, temperature, max_tokens, etc.)
    
    Returns:
        dict with keys: 'result' (str), 'format' (str), 'metadata' (dict)
    """
    # Extract parameters with defaults
    model = kwargs.get('model', 'anthropic/claude-3-sonnet')  # Good for social analysis
    temperature = kwargs.get('temperature', 0.6)  # Balanced for personality insights
    max_tokens = kwargs.get('max_tokens', 4000)
    provider = kwargs.get('provider', 'openrouter')
    prompt = """Please analyze the participants in this Telegram chat and provide insights about their roles, behaviors, and contributions. Include:

## Participant Profiles
For each active participant, provide:
- **Role in the group** (leader, contributor, observer, etc.)
- **Communication style** (formal, casual, technical, etc.)
- **Contribution patterns** (frequency, type of messages, topics they engage with)
- **Influence level** (how much others respond to their messages)
- **Specialization areas** (what topics they're most knowledgeable about)

## Group Dynamics
- **Leadership patterns** (formal vs informal leaders)
- **Communication flow** (who initiates conversations, who responds)
- **Collaboration patterns** (who works well together)
- **Conflict resolution** (how disagreements are handled)
- **Decision-making process** (how group decisions are made)

## Engagement Analysis
- **Most active participants** (by message count and engagement)
- **Lurkers vs contributors** (who reads but doesn't participate much)
- **Topic specialists** (who contributes to specific subject areas)
- **Social connectors** (who helps facilitate group cohesion)

## Behavioral Insights
- **Response patterns** (who responds quickly, who takes time)
- **Question patterns** (who asks questions, who provides answers)
- **Support patterns** (who offers help, who seeks assistance)
- **Humor and personality** (who brings levity, who's more serious)

## Recommendations
- **Group health** (overall group dynamics assessment)
- **Participation balance** (suggestions for encouraging quieter members)
- **Role optimization** (how roles could be better distributed)
- **Communication improvements** (suggestions for better group communication)

Please format your response with clear sections and include specific examples from the chat when possible.

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
            'template': 'participant_insights',
            'provider': provider,
            'model': model,
            'temperature': temperature,
            'max_tokens': max_tokens,
            'analysis_type': 'participants',
            'focus': 'social_dynamics'
        }
    }
