"""LLM service for AI-powered text generation using Pydantic AI."""

import re

from pydantic_ai import Agent


async def generate_study_title_async(topic: str) -> str:
    """
    Generate a short, URL-safe slug from a research topic (async).

    Args:
        topic: The research topic provided by the user

    Returns:
        A lowercase, hyphenated slug (2-5 words)

    Example:
        >>> title = await generate_study_title_async(
        ...     "How do freelancers choose project management tools?"
        ... )
        >>> title
        "freelancer-project-management"
    """
    agent = Agent(
        "anthropic:claude-3-5-sonnet-latest",
        system_prompt="""Given this research topic, generate a short, descriptive slug.
Requirements: 2-5 words, lowercase, hyphens only.

Return only the slug, no explanation.""",
    )

    result = await agent.run(topic)
    slug = str(result.output).strip()

    # Sanitize: ensure lowercase, alphanumeric + hyphens only
    slug = re.sub(r"[^a-z0-9-]", "", slug.lower().replace(" ", "-"))
    slug = re.sub(r"-+", "-", slug)  # Remove duplicate hyphens
    slug = slug.strip("-")  # Remove leading/trailing hyphens

    return slug


async def generate_interview_guide_async(topic: str) -> str:
    """
    Generate a comprehensive interview guide from a research topic (async).

    Args:
        topic: The research topic provided by the user

    Returns:
        Markdown-formatted interview guide with sections and questions

    Example:
        >>> guide = await generate_interview_guide_async(
        ...     "How do people shop in supermarkets?"
        ... )
        >>> "# Welcome" in guide
        True
    """
    agent = Agent(
        "anthropic:claude-3-5-sonnet-latest",
        system_prompt="""You are a UX researcher creating an interview guide.

Generate a comprehensive interview guide with:
1. A welcoming introduction (2-3 sentences)
2. 4-5 thematic sections
3. 3-5 questions per section
4. Questions should be open-ended and conversational

Format as markdown with clear section headers.""",
    )

    result = await agent.run(f"Research topic: {topic}")
    guide = str(result.output).strip()

    return guide
