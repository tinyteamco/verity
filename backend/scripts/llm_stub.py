#!/usr/bin/env python3
"""
Lightweight LLM API stub for E2E testing.

This provides a minimal Claude API-compatible endpoint for testing without
making actual API calls to Anthropic.

Endpoint implemented:
- POST /v1/messages - Claude messages API (compatible with pydantic-ai)

Runs on dynamic port specified by LLM_STUB_PORT environment variable.
"""

import os
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

app = FastAPI(title="LLM Stub")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Message(BaseModel):
    """Message in Claude API format"""

    role: str
    content: str | list[dict[str, Any]]


class MessagesRequest(BaseModel):
    """Claude messages API request format"""

    model: str
    messages: list[Message]
    max_tokens: int = 1024
    system: str | None = None


def generate_study_title_from_topic(topic: str) -> str:
    """Generate a slug from the topic for testing"""
    # Simple slug generation: lowercase, replace spaces with hyphens
    slug = topic.lower().replace(" ", "-")
    slug = "".join(c for c in slug if c.isalnum() or c == "-")
    # Truncate to reasonable length and remove trailing hyphens
    slug = slug[:50].strip("-")
    return slug or "research-study"


def generate_interview_guide_from_topic(topic: str) -> str:
    """Generate a mock interview guide for testing"""
    return f"""# Welcome to the Interview

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


@app.get("/")
def root() -> dict[str, str]:
    """Health check"""
    return {"status": "LLM Stub running", "version": "1.0.0"}


@app.post("/v1/messages")
async def create_message(request: MessagesRequest) -> JSONResponse:
    """
    Claude messages API endpoint (compatible with pydantic-ai)

    Analyzes the system prompt to determine if this is a title or guide generation request.
    """
    # Extract the user message content
    user_message = ""
    for msg in request.messages:
        if msg.role == "user":
            if isinstance(msg.content, str):
                user_message = msg.content
            elif isinstance(msg.content, list) and len(msg.content) > 0:
                # Handle list of content blocks
                for block in msg.content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        user_message = block.get("text", "")
                        break

    # Determine response type based on system prompt
    system_prompt = request.system or ""
    is_title_gen = "slug" in system_prompt.lower() and "2-5 words" in system_prompt
    is_guide_gen = "interview guide" in system_prompt.lower()

    # Generate appropriate response
    if is_title_gen:
        # Extract topic from user message (it's usually just the topic string)
        response_text = generate_study_title_from_topic(user_message)
    elif is_guide_gen:
        # Extract topic from user message (usually "Research topic: {topic}")
        topic = user_message.replace("Research topic:", "").strip()
        response_text = generate_interview_guide_from_topic(topic)
    else:
        # Default fallback
        response_text = "Mock LLM response"

    # Return Claude API-compatible response
    return JSONResponse(
        {
            "id": "msg_stub_123",
            "type": "message",
            "role": "assistant",
            "content": [{"type": "text", "text": response_text}],
            "model": request.model,
            "stop_reason": "end_turn",
            "stop_sequence": None,
            "usage": {"input_tokens": 10, "output_tokens": 20},
        }
    )


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("LLM_STUB_PORT", "9100"))

    print(f"🤖 Starting LLM Stub on http://localhost:{port}")
    print("   This provides a mock Claude API for testing")
    print()

    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
