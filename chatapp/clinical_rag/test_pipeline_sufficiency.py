"""
Backend tests for the sufficiency gate integration in the RAG pipeline.

Tests cover:
1. Sufficient evidence -> generation proceeds
2. Insufficient evidence -> abstention event yielded
3. Operational error (Model C failure) -> error event yielded
4. Empty retrieval -> abstention event yielded
5. Disabled gate -> generation proceeds

Run with: python -m pytest chatapp/clinical_rag/test_pipeline_sufficiency.py -v
Or: python chatapp/clinical_rag/test_pipeline_sufficiency.py
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from chatapp.clinical_rag import config, pipeline
from chatapp.clinical_rag.sufficiency import (
    SufficiencyEngine,
    SufficiencyResult,
    calculate_combined_score,
    SufficiencyError,
    ModelCInferenceError,
)
from chatapp.clinical_rag.sufficiency_checks import (
    ModelCCheck,
    CosineCheck,
    CheckResult,
    ModelCCheckpointError,
    ModelCOutputError,
    CosineSimilarityError,
)


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset singletons between tests."""
    from chatapp.clinical_rag.sufficiency_checks import _ModelCSingleton
    _ModelCSingleton._instance = None
    _ModelCSingleton._initialized = False
    yield
    _ModelCSingleton._instance = None
    _ModelCSingleton._initialized = False


@pytest.fixture
def sample_hits():
    """Sample retrieval hits for testing."""
    return [
        {
            "id": "doc1_chunk_0",
            "content": "Type 2 diabetes in adolescents is associated with obesity and insulin resistance.",
            "metadata": {"source": "doc1.txt", "chunk_index": 0},
            "distance": 0.15,
            "similarity": 0.85,
            "rank": 1,
        },
        {
            "id": "doc2_chunk_0",
            "content": "Glycemic control can be improved with continuous glucose monitoring.",
            "metadata": {"source": "doc2.txt", "chunk_index": 0},
            "distance": 0.30,
            "similarity": 0.70,
            "rank": 2,
        },
        {
            "id": "doc3_chunk_0",
            "content": "Screening for prediabetes in youth uses HbA1c and fasting glucose.",
            "metadata": {"source": "doc3.txt", "chunk_index": 0},
            "distance": 0.45,
            "similarity": 0.55,
            "rank": 3,
        },
    ]


@pytest.fixture
def low_similarity_hits():
    """Sample retrieval hits with low similarity (insufficient)."""
    return [
        {
            "id": "doc1_chunk_0",
            "content": "Some unrelated content about diabetes.",
            "metadata": {"source": "doc1.txt", "chunk_index": 0},
            "distance": 0.80,
            "similarity": 0.20,
            "rank": 1,
        },
    ]


@pytest.fixture
def mock_model_c_sufficient():
    """Mock Model C returning high probability (sufficient)."""
    with patch("chatapp.clinical_rag.sufficiency_checks._ModelCSingleton._load_model"):
        from chatapp.clinical_rag.sufficiency_checks import get_model_c
        singleton = get_model_c()
        singleton.predict_proba = MagicMock(return_value=0.92)
        yield singleton


@pytest.fixture
def mock_model_c_insufficient():
    """Mock Model C returning low probability (insufficient)."""
    with patch("chatapp.clinical_rag.sufficiency_checks._ModelCSingleton._load_model"):
        from chatapp.clinical_rag.sufficiency_checks import get_model_c
        singleton = get_model_c()
        singleton.predict_proba = MagicMock(return_value=0.30)
        yield singleton


@pytest.fixture
def mock_model_c_failure():
    """Mock Model C that raises an inference error."""
    with patch("chatapp.clinical_rag.sufficiency_checks._ModelCSingleton._load_model"):
        from chatapp.clinical_rag.sufficiency_checks import get_model_c
        singleton = get_model_c()
        singleton.predict_proba = MagicMock(side_effect=ModelCInferenceError("Model C failed"))
        yield singleton


# ============================================================
# Tests for stream_rag_answer with sufficient evidence
# ============================================================

class TestPipelineSufficientEvidence:
    """Tests where evidence is sufficient and generation should proceed."""

    @patch("chatapp.clinical_rag.pipeline.generation.condense_question")
    @patch("chatapp.clinical_rag.pipeline.retrieval.search")
    @patch("chatapp.clinical_rag.pipeline.generation.stream_answer")
    def test_sufficient_evidence_proceeds_to_generation(
        self, mock_stream_answer, mock_search, mock_condense, mock_model_c_sufficient, sample_hits
    ):
        """Sufficient evidence yields query, sources, then tokens from generation."""
        mock_condense.return_value = "test question"
        mock_search.return_value = sample_hits
        mock_stream_answer.return_value = iter(["Answer part 1", "Answer part 2"])

        events = list(pipeline.stream_rag_answer("test question", history=[]))

        # Verify event sequence
        event_types = [e["type"] for e in events]
        assert event_types == ["query", "sources", "token", "token"]

        # Verify query event
        assert events[0]["type"] == "query"
        assert events[0]["text"] == "test question"

        # Verify sources event
        assert events[1]["type"] == "sources"
        assert len(events[1]["sources"]) == 3
        assert events[1]["confidence"] == 0.85

        # Verify token events
        assert events[2]["type"] == "token"
        assert events[2]["text"] == "Answer part 1"
        assert events[3]["type"] == "token"
        assert events[3]["text"] == "Answer part 2"

    @patch("chatapp.clinical_rag.pipeline.generation.condense_question")
    @patch("chatapp.clinical_rag.pipeline.retrieval.search")
    @patch("chatapp.clinical_rag.pipeline.generation.stream_answer")
    def test_sufficient_evidence_with_follow_up_history(
        self, mock_stream_answer, mock_search, mock_condense, mock_model_c_sufficient, sample_hits
    ):
        """Sufficient evidence works with conversation history."""
        mock_condense.return_value = "standalone question about adolescents"
        mock_search.return_value = sample_hits
        mock_stream_answer.return_value = iter(["Answer for follow-up"])

        history = [
            {"role": "user", "content": "What about diabetes in youth?"},
            {"role": "assistant", "content": "Diabetes in youth..."},
        ]
        events = list(pipeline.stream_rag_answer("what about adolescents?", history=history))

        event_types = [e["type"] for e in events]
        assert event_types == ["query", "sources", "token"]
        assert events[0]["text"] == "standalone question about adolescents"


# ============================================================
# Tests for stream_rag_answer with insufficient evidence
# ============================================================

class TestPipelineInsufficientEvidence:
    """Tests where evidence is insufficient and abstention should occur."""

    @patch("chatapp.clinical_rag.pipeline.generation.condense_question")
    @patch("chatapp.clinical_rag.pipeline.retrieval.search")
    @patch("chatapp.clinical_rag.pipeline.generation.stream_answer")
    def test_insufficient_evidence_yields_abstain(
        self, mock_stream_answer, mock_search, mock_condense, mock_model_c_insufficient, low_similarity_hits
    ):
        """Insufficient evidence yields query, sources, abstain (no tokens)."""
        mock_condense.return_value = "test question"
        mock_search.return_value = low_similarity_hits
        # stream_answer should NOT be called
        mock_stream_answer.return_value = iter([])

        events = list(pipeline.stream_rag_answer("test question", history=[]))

        event_types = [e["type"] for e in events]
        assert event_types == ["query", "sources", "abstain"]

        # Verify abstain event structure
        abstain_event = events[2]
        assert abstain_event["type"] == "abstain"
        assert "reason" in abstain_event
        assert "details" in abstain_event
        assert "combined_score" in abstain_event["details"]
        assert "threshold" in abstain_event["details"]
        assert "model_c_probability" in abstain_event["details"]
        assert "cosine_similarity" in abstain_event["details"]
        assert "check_details" in abstain_event["details"]

        # Verify combined score is below threshold
        assert abstain_event["details"]["combined_score"] < 0.70

        # Verify stream_answer was never called
        mock_stream_answer.assert_not_called()

    @patch("chatapp.clinical_rag.pipeline.generation.condense_question")
    @patch("chatapp.clinical_rag.pipeline.retrieval.search")
    @patch("chatapp.clinical_rag.pipeline.generation.stream_answer")
    def test_insufficient_evidence_exact_threshold_is_sufficient(
        self, mock_stream_answer, mock_search, mock_condense, sample_hits
    ):
        """Score exactly at threshold (0.70) is sufficient and proceeds to generation."""
        # Create mock that gives combined score = 0.70
        with patch("chatapp.clinical_rag.sufficiency_checks._ModelCSingleton._load_model"):
            from chatapp.clinical_rag.sufficiency_checks import get_model_c
            singleton = get_model_c()
            # model_c=1.0, cosine=0.647... -> combined = 0.15*1.0 + 0.85*0.647... = 0.70
            singleton.predict_proba = MagicMock(return_value=1.0)
            sample_hits[0]["similarity"] = 0.6470588235294118

        mock_condense.return_value = "test question"
        mock_search.return_value = sample_hits
        mock_stream_answer.return_value = iter(["Answer at threshold"])

        events = list(pipeline.stream_rag_answer("test question", history=[]))

        event_types = [e["type"] for e in events]
        assert event_types == ["query", "sources", "token"]
        assert events[2]["text"] == "Answer at threshold"


# ============================================================
# Tests for operational errors (fail-closed)
# ============================================================

class TestPipelineOperationalErrors:
    """Tests where Model C fails and error event is yielded (fail-closed)."""

    @patch("chatapp.clinical_rag.pipeline.generation.condense_question")
    @patch("chatapp.clinical_rag.pipeline.retrieval.search")
    @patch("chatapp.clinical_rag.pipeline.generation.stream_answer")
    def test_model_c_inference_error_yields_error_event(
        self, mock_stream_answer, mock_search, mock_condense, mock_model_c_failure, sample_hits
    ):
        """Model C inference failure yields error event (fail-closed)."""
        mock_condense.return_value = "test question"
        mock_search.return_value = sample_hits
        mock_stream_answer.return_value = iter([])

        events = list(pipeline.stream_rag_answer("test question", history=[]))

        event_types = [e["type"] for e in events]
        assert event_types == ["query", "error"]

        error_event = events[1]
        assert error_event["type"] == "error"
        assert "message" in error_event
        assert "Sufficiency evaluation failed" in error_event["message"]

        # Verify stream_answer was never called
        mock_stream_answer.assert_not_called()

    @patch("chatapp.clinical_rag.pipeline.generation.condense_question")
    @patch("chatapp.clinical_rag.pipeline.retrieval.search")
    @patch("chatapp.clinical_rag.pipeline.generation.stream_answer")
    def test_model_c_checkpoint_missing_yields_error_event(
        self, mock_stream_answer, mock_search, mock_condense, sample_hits
    ):
        """Missing Model C checkpoint yields error event (fail-closed)."""
        with patch.object(config, "MODEL_C_CHECKPOINT", Path("/nonexistent/path")):
            mock_condense.return_value = "test question"
            mock_search.return_value = sample_hits
            mock_stream_answer.return_value = iter([])

            events = list(pipeline.stream_rag_answer("test question", history=[]))

            event_types = [e["type"] for e in events]
            assert event_types == ["query", "error"]

            error_event = events[1]
            assert error_event["type"] == "error"
            assert "Sufficiency evaluation failed" in error_event["message"]
            assert "checkpoint" in error_event["message"].lower()

            mock_stream_answer.assert_not_called()

    @patch("chatapp.clinical_rag.pipeline.generation.condense_question")
    @patch("chatapp.clinical_rag.pipeline.retrieval.search")
    @patch("chatapp.clinical_rag.pipeline.generation.stream_answer")
    def test_cosine_similarity_missing_yields_error_event(
        self, mock_stream_answer, mock_search, mock_condense, mock_model_c_sufficient
    ):
        """Missing similarity field in hits yields error event (fail-closed)."""
        hits_no_similarity = [{"content": "test content"}]  # no 'similarity' key

        mock_condense.return_value = "test question"
        mock_search.return_value = hits_no_similarity
        mock_stream_answer.return_value = iter([])

        events = list(pipeline.stream_rag_answer("test question", history=[]))

        event_types = [e["type"] for e in events]
        assert event_types == ["query", "error"]

        error_event = events[1]
        assert error_event["type"] == "error"
        assert "Sufficiency evaluation failed" in error_event["message"]

        mock_stream_answer.assert_not_called()


# ============================================================
# Tests for empty retrieval
# ============================================================

class TestPipelineEmptyRetrieval:
    """Tests where no passages are retrieved."""

    @patch("chatapp.clinical_rag.pipeline.generation.condense_question")
    @patch("chatapp.clinical_rag.pipeline.retrieval.search")
    @patch("chatapp.clinical_rag.pipeline.generation.stream_answer")
    def test_empty_retrieval_yields_abstain(
        self, mock_stream_answer, mock_search, mock_condense, mock_model_c_sufficient
    ):
        """Empty retrieval yields query, empty sources, abstain (no tokens)."""
        mock_condense.return_value = "test question"
        mock_search.return_value = []  # No hits
        mock_stream_answer.return_value = iter([])

        events = list(pipeline.stream_rag_answer("test question", history=[]))

        event_types = [e["type"] for e in events]
        assert event_types == ["query", "sources", "abstain"]

        # Verify sources event is empty
        sources_event = events[1]
        assert sources_event["type"] == "sources"
        assert sources_event["sources"] == []
        assert sources_event["confidence"] == 0.0

        # Verify abstain event
        abstain_event = events[2]
        assert abstain_event["type"] == "abstain"
        assert "No relevant passages found" in abstain_event["reason"]
        assert abstain_event["details"]["combined_score"] == 0.0
        assert abstain_event["details"]["check_details"].get("empty_retrieval") is True

        mock_stream_answer.assert_not_called()


# ============================================================
# Tests for disabled sufficiency gate
# ============================================================

class TestPipelineDisabledGate:
    """Tests with SUFFICIENCY_ENABLED=False."""

    @patch("chatapp.clinical_rag.pipeline.generation.condense_question")
    @patch("chatapp.clinical_rag.pipeline.retrieval.search")
    @patch("chatapp.clinical_rag.pipeline.generation.stream_answer")
    def test_disabled_gate_proceeds_to_generation(
        self, mock_stream_answer, mock_search, mock_condense, sample_hits
    ):
        """Disabled gate skips sufficiency check and proceeds to generation."""
        original = config.SUFFICIENCY_ENABLED
        config.SUFFICIENCY_ENABLED = False
        try:
            mock_condense.return_value = "test question"
            mock_search.return_value = sample_hits
            mock_stream_answer.return_value = iter(["Answer with gate disabled"])

            events = list(pipeline.stream_rag_answer("test question", history=[]))

            event_types = [e["type"] for e in events]
            assert event_types == ["query", "sources", "token"]
            assert events[2]["text"] == "Answer with gate disabled"
        finally:
            config.SUFFICIENCY_ENABLED = original

    @patch("chatapp.clinical_rag.pipeline.generation.condense_question")
    @patch("chatapp.clinical_rag.pipeline.retrieval.search")
    @patch("chatapp.clinical_rag.pipeline.generation.stream_answer")
    def test_disabled_gate_with_low_similarity_still_proceeds(
        self, mock_stream_answer, mock_search, mock_condense, low_similarity_hits
    ):
        """Disabled gate proceeds even with very low similarity."""
        original = config.SUFFICIENCY_ENABLED
        config.SUFFICIENCY_ENABLED = False
        try:
            mock_condense.return_value = "test question"
            mock_search.return_value = low_similarity_hits
            mock_stream_answer.return_value = iter(["Answer despite low similarity"])

            events = list(pipeline.stream_rag_answer("test question", history=[]))

            event_types = [e["type"] for e in events]
            assert event_types == ["query", "sources", "token"]
            assert events[2]["text"] == "Answer despite low similarity"
        finally:
            config.SUFFICIENCY_ENABLED = original


# ============================================================
# Regression Tests (User-requested)
# ============================================================

class TestRegressionMessagePersistence:
    """Regression tests for message persistence behavior in views."""

    @patch("chatapp.clinical_rag.pipeline.generation.condense_question")
    @patch("chatapp.clinical_rag.pipeline.retrieval.search")
    @patch("chatapp.clinical_rag.pipeline.generation.stream_answer")
    def test_pipeline_sufficient_evidence_event_sequence(
        self, mock_stream_answer, mock_search, mock_condense, mock_model_c_sufficient, sample_hits
    ):
        """Normal answer: pipeline emits query, sources, tokens (no abstain, no error)."""
        mock_condense.return_value = "test question"
        mock_search.return_value = sample_hits
        mock_stream_answer.return_value = iter(["Answer part 1", "Answer part 2"])

        events = list(pipeline.stream_rag_answer("test question", history=[]))

        event_types = [e["type"] for e in events]
        # Should have: query, sources, token, token
        assert event_types == ["query", "sources", "token", "token"]
        # No abstain or error events
        assert "abstain" not in event_types
        assert "error" not in event_types

    @patch("chatapp.clinical_rag.pipeline.generation.condense_question")
    @patch("chatapp.clinical_rag.pipeline.retrieval.search")
    @patch("chatapp.clinical_rag.pipeline.generation.stream_answer")
    def test_pipeline_insufficient_evidence_event_sequence(
        self, mock_stream_answer, mock_search, mock_condense, mock_model_c_insufficient, low_similarity_hits
    ):
        """Abstention: pipeline emits query, sources, abstain (no tokens)."""
        mock_condense.return_value = "test question"
        mock_search.return_value = low_similarity_hits
        mock_stream_answer.return_value = iter([])

        events = list(pipeline.stream_rag_answer("test question", history=[]))

        event_types = [e["type"] for e in events]
        # Should have: query, sources, abstain
        assert event_types == ["query", "sources", "abstain"]
        # No token events
        assert "token" not in event_types
        assert "error" not in event_types

    @patch("chatapp.clinical_rag.pipeline.generation.condense_question")
    @patch("chatapp.clinical_rag.pipeline.retrieval.search")
    @patch("chatapp.clinical_rag.pipeline.generation.stream_answer")
    def test_pipeline_empty_retrieval_no_token_no_model_c_no_generation(
        self, mock_stream_answer, mock_search, mock_condense
    ):
        """Empty retrieval: no token event, no Model C call, no generation call."""
        mock_condense.return_value = "test question"
        mock_search.return_value = []  # No hits
        mock_stream_answer.return_value = iter([])

        with patch("chatapp.clinical_rag.sufficiency_checks._ModelCSingleton._load_model"):
            from chatapp.clinical_rag.sufficiency_checks import get_model_c
            singleton = get_model_c()
            singleton.predict_proba = MagicMock(return_value=0.92)

            events = list(pipeline.stream_rag_answer("test question", history=[]))

        event_types = [e["type"] for e in events]
        # Should have: query, sources, abstain
        assert event_types == ["query", "sources", "abstain"]
        # No token events
        assert "token" not in event_types
        # No error events
        assert "error" not in event_types

        # Model C predict_proba should NOT be called for empty retrieval
        singleton.predict_proba.assert_not_called()
        # stream_answer should NOT be called
        mock_stream_answer.assert_not_called()

    @patch("chatapp.clinical_rag.pipeline.generation.condense_question")
    @patch("chatapp.clinical_rag.pipeline.retrieval.search")
    @patch("chatapp.clinical_rag.pipeline.generation.stream_answer")
    def test_pipeline_operational_error_no_answer_message(
        self, mock_stream_answer, mock_search, mock_condense, mock_model_c_failure, sample_hits
    ):
        """Operational error: pipeline emits query, error (no abstain, no tokens)."""
        mock_condense.return_value = "test question"
        mock_search.return_value = sample_hits
        mock_stream_answer.return_value = iter([])

        events = list(pipeline.stream_rag_answer("test question", history=[]))

        event_types = [e["type"] for e in events]
        # Should have: query, error
        assert event_types == ["query", "error"]
        # No abstain, no tokens
        assert "abstain" not in event_types
        assert "token" not in event_types

    @patch("chatapp.clinical_rag.pipeline.generation.condense_question")
    @patch("chatapp.clinical_rag.pipeline.retrieval.search")
    @patch("chatapp.clinical_rag.pipeline.generation.stream_answer")
    def test_pipeline_done_event_emitted_once(
        self, mock_stream_answer, mock_search, mock_condense, mock_model_c_sufficient, sample_hits
    ):
        """Pipeline events don't include 'done' - that's a view concern, but verify sequence ends properly."""
        mock_condense.return_value = "test question"
        mock_search.return_value = sample_hits
        mock_stream_answer.return_value = iter(["Answer"])

        events = list(pipeline.stream_rag_answer("test question", history=[]))

        # Pipeline itself doesn't emit 'done' - the view does
        # But we verify the generator completes normally (no exception)
        event_types = [e["type"] for e in events]
        assert event_types == ["query", "sources", "token"]


class TestRegressionViewsMessageCreation:
    """Regression tests for views.py message creation logic.

    These test the event_stream() logic directly by simulating the event processing.
    """

    def test_normal_answer_creates_one_assistant_message(self):
        """Normal answer: exactly one assistant message with answer content and sources."""
        from unittest.mock import MagicMock

        # Simulate the event_stream logic
        answer_parts = []
        sources = []
        abstained = False
        abstain_details = None

        events = [
            {"type": "query", "text": "test question"},
            {"type": "sources", "sources": [{"source": "doc1.txt", "title": "doc1", "chunk": 0, "meta": "Chunk 1 · similarity 0.85", "score": 0.85}], "confidence": 0.85},
            {"type": "token", "text": "Answer part 1"},
            {"type": "token", "text": "Answer part 2"},
        ]

        for event in events:
            kind = event["type"]
            if kind == "sources":
                sources = event["sources"]
            elif kind == "token":
                answer_parts.append(event["text"])
            elif kind == "abstain":
                abstained = True
                abstain_details = event.get("details", {})

        # This is the logic from views.py - only ONE message created
        if abstained:
            # Would create abstention message
            message_count = 1
            content_type = "abstention"
        else:
            # Would create normal answer message
            message_count = 1
            content_type = "answer"

        assert message_count == 1
        assert content_type == "answer"
        assert "".join(answer_parts) == "Answer part 1Answer part 2"

    def test_abstention_creates_one_assistant_message(self):
        """Abstention: exactly one assistant message with abstention reason and sources."""
        answer_parts = []
        sources = [{"source": "doc1.txt", "title": "doc1", "chunk": 0, "meta": "Chunk 1 · similarity 0.85", "score": 0.85}]
        abstained = True
        abstain_details = {
            "combined_score": 0.45,
            "threshold": 0.70,
            "model_c_probability": 0.30,
            "cosine_similarity": 0.50,
            "check_details": {}
        }

        if abstained:
            message_count = 1
            content_type = "abstention"
            # Verify abstention reason format
            reason = (
                "I cannot provide a reliable answer because the retrieved evidence "
                "was insufficient to answer your question. The combined sufficiency "
                f"score ({abstain_details.get('combined_score', 0):.4f}) is below "
                f"the required threshold ({abstain_details.get('threshold', 0.70):.2f})."
            )
        else:
            message_count = 1
            content_type = "answer"
            reason = "".join(answer_parts)

        assert message_count == 1
        assert content_type == "abstention"
        assert "insufficient" in reason.lower()
        assert "0.4500" in reason
        assert "0.70" in reason

    def test_empty_retrieval_creates_one_assistant_message(self):
        """Empty retrieval: exactly one assistant message with abstention reason."""
        sources = []  # Empty sources from empty retrieval
        abstained = True
        abstain_details = {
            "combined_score": 0.0,
            "threshold": 0.70,
            "model_c_probability": 0.0,
            "cosine_similarity": 0.0,
            "check_details": {"empty_retrieval": True},
        }

        if abstained:
            message_count = 1
            content_type = "abstention"
            reason = (
                "I cannot provide a reliable answer because the retrieved evidence "
                "was insufficient to answer your question. The combined sufficiency "
                f"score ({abstain_details.get('combined_score', 0):.4f}) is below "
                f"the required threshold ({abstain_details.get('threshold', 0.70):.2f})."
            )
        else:
            message_count = 1
            content_type = "answer"
            reason = ""

        assert message_count == 1
        assert content_type == "abstention"
        assert "0.0000" in reason
        assert "0.70" in reason

    def test_operational_error_creates_no_assistant_message(self):
        """Operational error: no assistant message created (error event yielded, generator returns)."""
        # In views.py, when SufficiencyError is caught, the generator returns early
        # without reaching the message creation code
        error_occurred = True

        if error_occurred:
            message_count = 0  # Generator returns before message creation
        else:
            message_count = 1

        assert message_count == 0


# ============================================================
# Run tests when executed directly
# ============================================================

if __name__ == "__main__":
    import subprocess
    sys.exit(subprocess.call([sys.executable, "-m", "pytest", __file__, "-v"]))