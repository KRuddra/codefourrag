"""
LLM client for response generation using OpenAI API.
"""

import logging
from typing import Optional, Dict, Any
from openai import OpenAI
from backend.config import settings

logger = logging.getLogger(__name__)

# Global OpenAI client
_openai_client: Optional[OpenAI] = None


def get_openai_client() -> OpenAI:
    """Get or create global OpenAI client."""
    global _openai_client
    
    if _openai_client is None:
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required for LLM generation. Please set it in .env file.")
        
        _openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        logger.info("OpenAI client initialized")
    
    return _openai_client


def generate(
    prompt: str,
    system_prompt: Optional[str] = None,
    model: str = "gpt-3.5-turbo",
    temperature: float = 0.0,
    max_tokens: Optional[int] = None
) -> str:
    """
    Generate response using OpenAI LLM.
    
    Args:
        prompt: User prompt/message
        system_prompt: System prompt (optional)
        model: Model name (default: gpt-3.5-turbo)
        temperature: Temperature for generation (0.0 for deterministic)
        max_tokens: Maximum tokens to generate (None = model default)
        
    Returns:
        Generated text response
    """
    client = get_openai_client()
    
    messages = []
    
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    
    messages.append({"role": "user", "content": prompt})
    
    try:
        logger.debug(f"Calling OpenAI API with model {model}")
        
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        generated_text = response.choices[0].message.content
        
        logger.debug(f"Generated {len(generated_text)} characters")
        
        return generated_text
        
    except Exception as e:
        logger.error(f"Error generating response with OpenAI: {e}")
        raise
