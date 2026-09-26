from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, Field


@dataclass(slots=True)
class Clause:
    id: str
    text: str
    page: int | None = None


@dataclass(slots=True)
class DocumentState:
    document_id: str
    filename: str
    language: str
    clauses: list[Clause]
    text: str
    vectorizer: Any = None
    matrix: Any = None


class AskRequest(BaseModel):
    document_id: str = Field(min_length=1, max_length=64)
    question: str = Field(min_length=1, max_length=2_000)
    language: str = Field(default="English", min_length=1, max_length=30)
