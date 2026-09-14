from __future__ import annotations

import os
from typing import Optional

from langchain_openai import ChatOpenAI

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
DEFAULT_GEMINI_MODEL = "gemini-3.6-flash"
DEFAULT_OLLAMA_MODEL = "llama3.2"


def get_llm(
    provider: str = "gemini",
    model: Optional[str] = None,
    temperature: float = 0.3,
) -> ChatOpenAI:
    if provider == "gemini":
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY ist nicht gesetzt. Key in .env eintragen oder "
                "provider='ollama' für ein lokales Modell verwenden."
            )
        return ChatOpenAI(
            api_key=api_key,
            model=model or DEFAULT_GEMINI_MODEL,
            base_url=GEMINI_BASE_URL,
            temperature=temperature,
        )

    if provider == "ollama":
        return ChatOpenAI(
            api_key="ollama",
            model=model or DEFAULT_OLLAMA_MODEL,
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
            temperature=temperature,
        )

    raise ValueError(f"Unbekannter LLM-Provider: {provider!r} (erwartet 'gemini' oder 'ollama')")
