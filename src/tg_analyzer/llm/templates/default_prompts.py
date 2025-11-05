"""
Default prompt templates for common analysis tasks
"""

from typing import Dict, Any


DEFAULT_PROMPTS = {
    "summary": """
Please provide a comprehensive summary of this Telegram chat. Include:

1. **Main Topics**: What are the primary subjects discussed?
2. **Key Participants**: Who are the most active contributors?
3. **Timeline**: When did major discussions happen?
4. **Sentiment**: What is the overall tone and mood?
5. **Key Insights**: Any important conclusions or decisions reached?

Chat Data:
{chat_data}

Please structure your response with clear headings and be concise but thorough.
""",

    "sentiment_analysis": """
Analyze the sentiment and emotional tone of this Telegram chat. Please provide:

1. **Overall Sentiment**: Positive, negative, or neutral?
2. **Emotional Patterns**: What emotions are expressed (excitement, frustration, etc.)?
3. **Participant Sentiments**: How do different people's sentiments vary?
4. **Context Factors**: What events or topics trigger strong emotions?
5. **Recommendations**: Any suggestions for improving communication?

Chat Data:
{chat_data}

Focus on specific examples from the conversation.
""",

    "topic_modeling": """
Identify and categorize the main topics discussed in this Telegram chat. Please:

1. **Topic Categories**: Group messages by subject matter
2. **Topic Frequency**: Which topics are discussed most?
3. **Topic Evolution**: How do topics change over time?
4. **Cross-cutting Themes**: Any themes that appear across multiple topics?
5. **Missing Topics**: Important subjects that might not be covered?

Chat Data:
{chat_data}

Use clear topic labels and provide message counts for each category.
""",

    "participant_analysis": """
Analyze the participants and their roles in this Telegram chat. Please cover:

1. **Activity Levels**: Who posts most frequently?
2. **Communication Styles**: How do people express themselves?
3. **Expertise Areas**: What topics does each person specialize in?
4. **Social Dynamics**: How do participants interact with each other?
5. **Influence Patterns**: Who influences the conversation direction?

Chat Data:
{chat_data}

Include specific examples and quantitative data where possible.
""",

    "temporal_analysis": """
Analyze how this Telegram conversation evolves over time. Please examine:

1. **Activity Patterns**: When are people most active?
2. **Topic Shifts**: How do discussion topics change?
3. **Momentum Changes**: Periods of high vs low engagement?
4. **Response Times**: How quickly do people respond to each other?
5. **Conversation Flow**: How does the discussion progress chronologically?

Chat Data:
{chat_data}

Include timestamps and correlate with content changes.
""",

    "link_resource_analysis": """
Extract and analyze all links and resources shared in this Telegram chat:

1. **Link Categories**: Websites, articles, videos, tools, etc.
2. **Resource Quality**: Assess the usefulness/reliability of shared resources
3. **Sharing Patterns**: Who shares what types of links?
4. **Topic Correlation**: Which topics have the most resource sharing?
5. **Resource Summary**: Create a curated list of the best resources

Chat Data:
{chat_data}

Focus on practical, actionable resources that would be valuable to others.
""",

    "action_items": """
Extract all action items, tasks, and commitments from this Telegram chat:

1. **Explicit Tasks**: Clear assignments and deadlines
2. **Implicit Actions**: Things that should be done based on context
3. **Responsible Parties**: Who is supposed to do what?
4. **Status Tracking**: What's been completed vs still pending?
5. **Follow-up Needed**: Items requiring future discussion or action

Chat Data:
{chat_data}

Format as a clear task list with owners, deadlines, and status.
""",

    "decision_making": """
Analyze the decision-making process in this Telegram chat:

1. **Decisions Made**: What choices were finalized?
2. **Decision Process**: How were decisions reached?
3. **Alternatives Considered**: What options were discussed?
4. **Consensus Building**: How was agreement achieved?
5. **Outstanding Decisions**: What still needs to be decided?

Chat Data:
{chat_data}

Focus on concrete outcomes and the process that led to them.
""",

    "custom": """
{user_prompt}

Chat Data:
{chat_data}
"""
}


def get_prompt_template(template_name: str) -> str:
    """
    Get a prompt template by name

    Args:
        template_name: Name of the template

    Returns:
        Prompt template string

    Raises:
        ValueError: If template doesn't exist
    """
    if template_name not in DEFAULT_PROMPTS:
        available = list(DEFAULT_PROMPTS.keys())
        raise ValueError(f"Unknown template '{template_name}'. Available: {available}")

    return DEFAULT_PROMPTS[template_name]


def list_available_templates() -> Dict[str, str]:
    """
    Get all available prompt templates with descriptions

    Returns:
        Dict mapping template names to descriptions
    """
    descriptions = {
        "summary": "Comprehensive overview of chat content and themes",
        "sentiment_analysis": "Emotional tone and sentiment patterns",
        "topic_modeling": "Categorization of discussion topics",
        "participant_analysis": "User behavior and interaction patterns",
        "temporal_analysis": "How conversation evolves over time",
        "link_resource_analysis": "Shared links and resources evaluation",
        "action_items": "Tasks, commitments, and follow-ups",
        "decision_making": "Decision processes and outcomes",
        "custom": "Custom prompt template",
    }

    return descriptions


def format_prompt(template: str, chat_data: str, **kwargs) -> str:
    """
    Format a prompt template with data and variables

    Args:
        template: Prompt template string
        chat_data: Chat data to insert
        **kwargs: Additional variables for template

    Returns:
        Formatted prompt
    """
    # Create format variables
    variables = {
        "chat_data": chat_data,
        **kwargs
    }

    try:
        return template.format(**variables)
    except KeyError as e:
        raise ValueError(f"Missing required variable for template: {e}")

