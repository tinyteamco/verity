"""LLM service for AI-powered text generation using Pydantic AI."""

import asyncio
import os
import re
from collections.abc import Coroutine
from typing import Any

from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel


def _get_test_model_for_slug() -> TestModel:
    """Get test model for slug generation."""
    return TestModel(custom_output_text="freelancer-project-management")


def _get_test_model_for_guide(topic: str) -> TestModel:
    """Get test model for interview guide generation."""
    guide_content = f"""# Welcome to the Interview

Thank you for participating in this research study about: {topic}

## Background and Context

1. Can you tell me about your current experience with this topic?
2. What challenges have you encountered?
3. How do you currently approach this?

## Deep Dive Questions

1. Walk me through a recent example of when you dealt with this.
2. What factors influence your decisions in this area?
3. How do you evaluate different options?

## Future Outlook

1. What improvements would you like to see?
2. How do you think this might change in the future?
3. Is there anything else you'd like to share?"""

    return TestModel(custom_output_text=guide_content)


def _is_test_mode() -> bool:
    """Check if we're in test mode (no real API calls)."""
    return os.getenv("APP_ENV") == "local" and os.getenv("ANTHROPIC_API_KEY") is None


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
    model = _get_test_model_for_slug() if _is_test_mode() else "anthropic:claude-3-5-sonnet-latest"

    agent = Agent(
        model,
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
    model = (
        _get_test_model_for_guide(topic)
        if _is_test_mode()
        else "anthropic:claude-3-5-sonnet-latest"
    )

    agent = Agent(
        model,
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


def _run_async(coro: Coroutine[Any, Any, str]) -> str:
    """Run async coroutine in sync context, handling existing event loop."""
    try:
        # Try to get the current event loop
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # We're in an async context, create a new task
            import nest_asyncio

            nest_asyncio.apply()
            return loop.run_until_complete(coro)
    except RuntimeError:
        pass

    # No event loop or not running, create a new one
    return asyncio.run(coro)


def generate_study_title(topic: str) -> str:
    """
    Generate a short, URL-safe slug from a research topic (sync wrapper).

    DEPRECATED: Use generate_study_title_async() directly in async contexts.

    Args:
        topic: The research topic provided by the user

    Returns:
        A lowercase, hyphenated slug (2-5 words)

    Example:
        >>> generate_study_title("How do freelancers choose project management tools?")
        "freelancer-project-management"
    """
    return _run_async(generate_study_title_async(topic))


def generate_interview_guide(topic: str) -> str:
    """
    Generate a comprehensive interview guide from a research topic (sync wrapper).

    DEPRECATED: Use generate_interview_guide_async() directly in async contexts.

    Args:
        topic: The research topic provided by the user

    Returns:
        Markdown-formatted interview guide with sections and questions

    Example:
        >>> guide = generate_interview_guide("How do people shop in supermarkets?")
        >>> "# Welcome" in guide
        True
    """
    return _run_async(generate_interview_guide_async(topic))
