from nyayaai.models import Clause, DocumentState
from nyayaai.services.retrieval_service import build_index, retrieve


def make_state() -> DocumentState:
    return DocumentState(
        "abc",
        "agreement.txt",
        "English",
        [
            Clause("C1", "The agreement may be terminated with thirty days notice."),
            Clause("C2", "The parties will meet at the registered office."),
            Clause("C3", "Payment is due on the first day of each month."),
        ],
        "",
    )


def test_retrieval_prefers_relevant_clause() -> None:
    state = make_state()
    build_index(state)
    result = retrieve(state, "How can I terminate the agreement?")
    assert result
    assert result[0].id == "C1"


def test_retrieval_respects_requested_limit() -> None:
    state = make_state()
    build_index(state)
    result = retrieve(state, "agreement payment termination", limit=1)
    assert len(result) == 1


def test_retrieval_returns_empty_for_unknown_query() -> None:
    state = make_state()
    build_index(state)
    assert retrieve(state, "quantum mechanics") == []
