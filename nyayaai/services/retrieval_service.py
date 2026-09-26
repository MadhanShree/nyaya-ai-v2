from __future__ import annotations

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from ..config import settings
from ..models import Clause, DocumentState


def build_index(state: DocumentState) -> None:
    if not state.clauses:
        return
    state.vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
        min_df=1,
        sublinear_tf=True,
    )
    state.matrix = state.vectorizer.fit_transform(clause.text for clause in state.clauses)


def retrieve(
    state: DocumentState,
    query: str,
    limit: int | None = None,
) -> list[Clause]:
    if state.vectorizer is None or state.matrix is None:
        return []
    requested = min(limit or settings.max_retrieval, settings.max_retrieval)
    query_vector = state.vectorizer.transform([query])
    scores = cosine_similarity(query_vector, state.matrix)[0]
    ranked = sorted(enumerate(scores), key=lambda item: item[1], reverse=True)
    return [state.clauses[i] for i, score in ranked[:requested] if score > 0]
