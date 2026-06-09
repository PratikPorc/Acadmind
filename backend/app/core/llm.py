from enum import Enum
from functools import lru_cache
from typing import Any

from app.config import get_settings


class LLMProvider(str, Enum):
    gemini = "gemini"
    openai = "openai"
    ollama = "ollama"


class EmbeddingProvider(str, Enum):
    gemini = "gemini"
    openai = "openai"
    local = "local"


def check_llm_config() -> tuple[bool, str]:
    settings = get_settings()
    provider = settings.llm_provider.lower()

    if provider == LLMProvider.gemini.value:
        if not settings.gemini_api_key:
            return False, "set GEMINI_API_KEY (free at https://aistudio.google.com/apikey)"
        return True, f"gemini · {settings.gemini_model}"

    if provider == LLMProvider.openai.value:
        if not settings.openai_api_key:
            return False, "set OPENAI_API_KEY"
        return True, f"openai · {settings.openai_model}"

    if provider == LLMProvider.ollama.value:
        return True, f"ollama · {settings.ollama_model} @ {settings.ollama_base_url}"

    return False, f"unknown LLM_PROVIDER '{settings.llm_provider}'"


@lru_cache
def get_chat_model() -> Any:
    """Return a LangChain chat model for the configured provider."""
    settings = get_settings()
    provider = settings.llm_provider.lower()

    if provider == LLMProvider.gemini.value:
        from langchain_google_genai import ChatGoogleGenerativeAI

        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is required when LLM_PROVIDER=gemini")
        return ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            google_api_key=settings.gemini_api_key,
            temperature=0.2,
        )

    if provider == LLMProvider.openai.value:
        from langchain_openai import ChatOpenAI

        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")
        return ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=0.2,
        )

    if provider == LLMProvider.ollama.value:
        from langchain_ollama import ChatOllama

        return ChatOllama(
            model=settings.ollama_model,
            base_url=settings.ollama_base_url,
            temperature=0.2,
        )

    raise ValueError(f"Unsupported LLM_PROVIDER: {settings.llm_provider}")


@lru_cache
def get_embeddings() -> Any:
    """Return a LangChain embeddings model for RAG (Phase 2+)."""
    settings = get_settings()
    provider = settings.embedding_provider.lower()

    if provider == EmbeddingProvider.gemini.value:
        from langchain_google_genai import GoogleGenerativeAIEmbeddings

        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is required when EMBEDDING_PROVIDER=gemini")
        return GoogleGenerativeAIEmbeddings(
            model=settings.gemini_embedding_model,
            google_api_key=settings.gemini_api_key,
        )

    if provider == EmbeddingProvider.openai.value:
        from langchain_openai import OpenAIEmbeddings

        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when EMBEDDING_PROVIDER=openai")
        return OpenAIEmbeddings(
            model=settings.embedding_model,
            api_key=settings.openai_api_key,
        )

    raise ValueError(
        f"Unsupported EMBEDDING_PROVIDER: {settings.embedding_provider}. "
        "Use 'gemini' or 'openai'."
    )
