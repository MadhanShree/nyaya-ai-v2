from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _int_env(name: str, default: int, minimum: int = 1) -> int:
    raw = os.getenv(name, str(default))
    try:
        value = int(raw)
    except ValueError:
        return default
    return max(value, minimum)


@dataclass(frozen=True, slots=True)
class Settings:
    max_upload_mb: int = _int_env("MAX_UPLOAD_MB", 5)
    max_pages: int = _int_env("MAX_PAGES", 40)
    max_document_chars: int = _int_env("MAX_DOCUMENT_CHARS", 120_000)
    max_context_chars: int = _int_env("MAX_CONTEXT_CHARS", 18_000)
    max_question_chars: int = _int_env("MAX_QUESTION_CHARS", 2_000)
    max_documents: int = _int_env("MAX_DOCUMENTS", 20)
    max_risks: int = _int_env("MAX_RISKS", 6)
    max_retrieval: int = _int_env("MAX_RETRIEVAL", 6)
    rate_limit_per_min: int = _int_env("RATE_LIMIT_PER_MIN", 20)
    groq_model: str = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024


settings = Settings()
