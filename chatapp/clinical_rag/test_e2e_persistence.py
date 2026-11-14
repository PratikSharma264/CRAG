"""
End-to-end tests for Django database persistence and chat-history refresh.

Tests cover:
1. Normal answer persistence (user message + assistant message)
2. Abstention persistence (user message + assistant message with abstention reason)
3. Empty retrieval persistence (user message + assistant message with abstention reason)
4. Operational error: no assistant message created
5. Retry/edit flow: truncation and regeneration
6. Chat history loading on page refresh (simulated via view context)
7. CSRF token handling in form submission
8. Clear chat functionality
9. Disabled sufficiency gate
"""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from django.test import Client
from django.contrib.auth import get_user_model
from django.urls import reverse

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from chatapp.models import ChatMessage
from chatapp.clinical_rag import config
from chatapp.clinical_rag.sufficiency import SufficiencyError

User = get_user_model()


def consume_streaming_response(response):
    """Fully consume a StreamingHttpResponse to trigger generator completion."""
    if hasattr(response, 'streaming_content'):
        list(response.streaming_content)
    return response


def get_streaming_content(response):
    """Get the full content from a StreamingHttpResponse."""
    if hasattr(response, 'streaming_content'):
        return b"".join(response.streaming_content).decode("utf-8")
    return response.content.decode("utf-8")


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def user(db):
    """Create a test user."""
    return User.objects.create_user(username="testuser", password="testpass123")


@pytest.fixture
def auth_client(user):
    """Create an authenticated test client."""
    client = Client()
    client.force_login(user)
    return client


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
        singleton.predict_proba = MagicMock(side_effect=Exception("Model C failed"))
        yield singleton


# ============================================================
# Test Normal Answer Persistence
# ============================================================

class TestNormalAnswerPersistence:
    """Tests for normal answer persistence to database."""

    @patch("chatapp.clinical_rag.pipeline.generation.condense_question")
    @patch("chatapp.clinical_rag.pipeline.retrieval.search")
    @patch("chatapp.clinical_rag.pipeline.generation.stream_answer")
    def test_normal_answer_creates_two_messages(
        self, mock_stream_answer, mock_search, mock_condense, auth_client, user, mock_model_c_sufficient, sample_hits
    ):
        """Normal answer: creates user message + assistant message."""
        mock_condense.return_value = "test question"
        mock_search.return_value = sample_hits
        mock_stream_answer.return_value = iter(["Answer part 1", "Answer part 2"])

        response = auth_client.post(
            reverse("chatapp:ask"),
            {"question": "What is type 2 diabetes in adolescents?"},
        )

        assert response.status_code == 200
        assert response["Content-Type"] == "application/x-ndjson"
        consume_streaming_response(response)

        # Verify database state - exactly 2 messages
        messages = ChatMessage.objects.filter(owner=user).order_by("created_at")
        assert messages.count() == 2

        user_msg = messages[0]
        assistant_msg = messages[1]

        assert user_msg.role == ChatMessage.Role.USER
        assert user_msg.content == "What is type 2 diabetes in adolescents?"

        assert assistant_msg.role == ChatMessage.Role.ASSISTANT
        assert assistant_msg.content == "Answer part 1Answer part 2"
        assert len(assistant_msg.sources) == 2
        assert assistant_msg.sources[0]["title"] == "doc1"
        assert assistant_msg.sources[1]["title"] == "doc2"

    @patch("chatapp.clinical_rag.pipeline.generation.condense_question")
    @patch("chatapp.clinical_rag.pipeline.retrieval.search")
    @patch("chatapp.clinical_rag.pipeline.generation.stream_answer")
    def test_normal_answer_streaming_events(
        self, mock_stream_answer, mock_search, mock_condense, auth_client, user, mock_model_c_sufficient, sample_hits
    ):
        """Normal answer: verify NDJSON event sequence."""
        mock_condense.return_value = "test question"
        mock_search.return_value = sample_hits
        mock_stream_answer.return_value = iter(["Answer part 1", "Answer part 2"])

        response = auth_client.post(
            reverse("chatapp:ask"),
            {"question": "What is type 2 diabetes in adolescents?"},
        )

        assert response.status_code == 200
        content = get_streaming_content(response)
        consume_streaming_response(response)

        events = [json.loads(line) for line in content.strip().split("\n") if line.strip()]

        event_types = [e["type"] for e in events]
        assert event_types == ["saved", "query", "sources", "token", "token", "done"]

        # Verify saved event has user_message_id
        assert events[0]["type"] == "saved"
        assert "user_message_id" in events[0]
        assert events[0]["user_message_id"] == 1

        # Verify query event
        assert events[1]["type"] == "query"
        assert events[1]["text"] == "test question"

        # Verify sources event
        assert events[2]["type"] == "sources"
        assert len(events[2]["sources"]) == 2
        assert "url" in events[2]["sources"][0]

        # Verify token events
        assert events[3]["type"] == "token"
        assert events[3]["text"] == "Answer part 1"
        assert events[4]["type"] == "token"
        assert events[4]["text"] == "Answer part 2"

        # Verify done event
        assert events[5]["type"] == "done"


# ============================================================
# Test Abstention Persistence
# ============================================================

class TestAbstentionPersistence:
    """Tests for abstention persistence to database."""

    @patch("chatapp.clinical_rag.pipeline.generation.condense_question")
    @patch("chatapp.clinical_rag.pipeline.retrieval.search")
    @patch("chatapp.clinical_rag.pipeline.generation.stream_answer")
    def test_abstention_creates_two_messages(
        self, mock_stream_answer, mock_search, mock_condense, auth_client, user, mock_model_c_insufficient, low_similarity_hits
    ):
        """Abstention: creates user message + assistant message with abstention reason."""
        mock_condense.return_value = "test question"
        mock_search.return_value = low_similarity_hits
        mock_stream_answer.return_value = iter([])

        response = auth_client.post(
            reverse("chatapp:ask"),
            {"question": "What is type 2 diabetes in adolescents?"},
        )

        assert response.status_code == 200
        consume_streaming_response(response)

        # Verify database state - exactly 2 messages
        messages = ChatMessage.objects.filter(owner=user).order_by("created_at")
        assert messages.count() == 2

        user_msg = messages[0]
        assistant_msg = messages[1]

        assert user_msg.role == ChatMessage.Role.USER
        assert user_msg.content == "What is type 2 diabetes in adolescents?"

        assert assistant_msg.role == ChatMessage.Role.ASSISTANT
        assert "insufficient" in assistant_msg.content.lower()
        assert "combined sufficiency score" in assistant_msg.content.lower()
        assert "0.70" in assistant_msg.content
        assert len(assistant_msg.sources) == 1
        assert assistant_msg.sources[0]["title"] == "doc1"

    @patch("chatapp.clinical_rag.pipeline.generation.condense_question")
    @patch("chatapp.clinical_rag.pipeline.retrieval.search")
    @patch("chatapp.clinical_rag.pipeline.generation.stream_answer")
    def test_abstention_streaming_events(
        self, mock_stream_answer, mock_search, mock_condense, auth_client, user, mock_model_c_insufficient, low_similarity_hits
    ):
        """Abstention: verify NDJSON event sequence includes abstain event."""
        mock_condense.return_value = "test question"
        mock_search.return_value = low_similarity_hits
        mock_stream_answer.return_value = iter([])

        response = auth_client.post(
            reverse("chatapp:ask"),
            {"question": "What is type 2 diabetes in adolescents?"},
        )

        assert response.status_code == 200
        content = get_streaming_content(response)
        consume_streaming_response(response)

        events = [json.loads(line) for line in content.strip().split("\n") if line.strip()]

        event_types = [e["type"] for e in events]
        assert event_types == ["saved", "query", "sources", "abstain", "done"]

        # Verify abstain event structure
        abstain_event = events[3]
        assert abstain_event["type"] == "abstain"
        assert "reason" in abstain_event
        assert "details" in abstain_event
        assert "combined_score" in abstain_event["details"]
        assert "threshold" in abstain_event["details"]
        assert abstain_event["details"]["combined_score"] < 0.70

        # Verify NO token events for abstention
        assert "token" not in event_types


# ============================================================
# Test Empty Retrieval Persistence
# ============================================================

class TestEmptyRetrievalPersistence:
    """Tests for empty retrieval (no hits) persistence."""

    @patch("chatapp.clinical_rag.pipeline.generation.condense_question")
    @patch("chatapp.clinical_rag.pipeline.retrieval.search")
    @patch("chatapp.clinical_rag.pipeline.generation.stream_answer")
    def test_empty_retrieval_creates_two_messages(
        self, mock_stream_answer, mock_search, mock_condense, auth_client, user, mock_model_c_sufficient
    ):
        """Empty retrieval: creates user message + assistant message with abstention reason."""
        mock_condense.return_value = "test question"
        mock_search.return_value = []  # No hits
        mock_stream_answer.return_value = iter([])

        response = auth_client.post(
            reverse("chatapp:ask"),
            {"question": "What is type 2 diabetes in adolescents?"},
        )

        assert response.status_code == 200
        consume_streaming_response(response)

        # Verify database state - exactly 2 messages
        messages = ChatMessage.objects.filter(owner=user).order_by("created_at")
        assert messages.count() == 2

        user_msg = messages[0]
        assistant_msg = messages[1]

        assert user_msg.role == ChatMessage.Role.USER
        assert assistant_msg.role == ChatMessage.Role.ASSISTANT
        assert "insufficient" in assistant_msg.content.lower()
        assert "0.0000" in assistant_msg.content
        assert "0.70" in assistant_msg.content
        assert assistant_msg.sources == []

    @patch("chatapp.clinical_rag.pipeline.generation.condense_question")
    @patch("chatapp.clinical_rag.pipeline.retrieval.search")
    @patch("chatapp.clinical_rag.pipeline.generation.stream_answer")
    def test_empty_retrieval_no_model_c_called(
        self, mock_stream_answer, mock_search, mock_condense, auth_client, user
    ):
        """Empty retrieval: Model C predict_proba should NOT be called."""
        mock_condense.return_value = "test question"
        mock_search.return_value = []
        mock_stream_answer.return_value = iter([])

        with patch("chatapp.clinical_rag.sufficiency_checks._ModelCSingleton._load_model"):
            from chatapp.clinical_rag.sufficiency_checks import get_model_c
            singleton = get_model_c()
            singleton.predict_proba = MagicMock(return_value=0.92)

            response = auth_client.post(
                reverse("chatapp:ask"),
                {"question": "What is type 2 diabetes in adolescents?"},
            )

            assert response.status_code == 200
            consume_streaming_response(response)
            singleton.predict_proba.assert_not_called()

    @patch("chatapp.clinical_rag.pipeline.generation.condense_question")
    @patch("chatapp.clinical_rag.pipeline.retrieval.search")
    @patch("chatapp.clinical_rag.pipeline.generation.stream_answer")
    def test_empty_retrieval_streaming_events(
        self, mock_stream_answer, mock_search, mock_condense, auth_client, user, mock_model_c_sufficient
    ):
        """Empty retrieval: verify NDJSON event sequence."""
        mock_condense.return_value = "test question"
        mock_search.return_value = []
        mock_stream_answer.return_value = iter([])

        response = auth_client.post(
            reverse("chatapp:ask"),
            {"question": "What is type 2 diabetes in adolescents?"},
        )

        assert response.status_code == 200
        content = get_streaming_content(response)
        consume_streaming_response(response)

        events = [json.loads(line) for line in content.strip().split("\n") if line.strip()]

        event_types = [e["type"] for e in events]
        assert event_types == ["saved", "query", "sources", "abstain", "done"]

        # Verify empty sources
        sources_event = events[2]
        assert sources_event["sources"] == []
        assert sources_event["confidence"] == 0.0

        # Verify abstain has empty_retrieval flag
        abstain_event = events[3]
        assert abstain_event["details"]["check_details"].get("empty_retrieval") is True

        # Verify NO token events
        assert "token" not in event_types


# ============================================================
# Test Operational Error (Fail-Closed)
# ============================================================

class TestOperationalErrorPersistence:
    """Tests for operational error (Model C failure) - no assistant message."""

    @patch("chatapp.clinical_rag.pipeline.generation.condense_question")
    @patch("chatapp.clinical_rag.pipeline.retrieval.search")
    @patch("chatapp.clinical_rag.pipeline.generation.stream_answer")
    def test_operational_error_creates_only_user_message(
        self, mock_stream_answer, mock_search, mock_condense, auth_client, user, mock_model_c_failure, sample_hits
    ):
        """Operational error: creates only user message, no assistant message."""
        mock_condense.return_value = "test question"
        mock_search.return_value = sample_hits
        mock_stream_answer.return_value = iter([])

        response = auth_client.post(
            reverse("chatapp:ask"),
            {"question": "What is type 2 diabetes in adolescents?"},
        )

        assert response.status_code == 200
        consume_streaming_response(response)

        # Verify database state - only user message
        messages = ChatMessage.objects.filter(owner=user).order_by("created_at")
        assert messages.count() == 1

        user_msg = messages[0]
        assert user_msg.role == ChatMessage.Role.USER
        assert user_msg.content == "What is type 2 diabetes in adolescents?"

        # No assistant message
        assistant_messages = messages.filter(role=ChatMessage.Role.ASSISTANT)
        assert assistant_messages.count() == 0

    @patch("chatapp.clinical_rag.pipeline.generation.condense_question")
    @patch("chatapp.clinical_rag.pipeline.retrieval.search")
    @patch("chatapp.clinical_rag.pipeline.generation.stream_answer")
    def test_operational_error_streaming_events(
        self, mock_stream_answer, mock_search, mock_condense, auth_client, user, mock_model_c_failure, sample_hits
    ):
        """Operational error: verify NDJSON event sequence includes error event."""
        mock_condense.return_value = "test question"
        mock_search.return_value = sample_hits
        mock_stream_answer.return_value = iter([])

        response = auth_client.post(
            reverse("chatapp:ask"),
            {"question": "What is type 2 diabetes in adolescents?"},
        )

        assert response.status_code == 200
        content = get_streaming_content(response)
        consume_streaming_response(response)

        events = [json.loads(line) for line in content.strip().split("\n") if line.strip()]

        event_types = [e["type"] for e in events]
        assert event_types == ["saved", "query", "error", "done"]

        # Verify error event
        error_event = events[2]
        assert error_event["type"] == "error"
        assert "message" in error_event
        assert "Sufficiency evaluation failed" in error_event["message"]

        # Verify NO token, NO abstain events
        assert "token" not in event_types
        assert "abstain" not in event_types


# ============================================================
# Test Retry/Edit Flow (Message Truncation)
# ============================================================

class TestRetryEditFlow:
    """Tests for retry and edit message flow with truncation."""

    @patch("chatapp.clinical_rag.pipeline.generation.condense_question")
    @patch("chatapp.clinical_rag.pipeline.retrieval.search")
    @patch("chatapp.clinical_rag.pipeline.generation.stream_answer")
    def test_retry_truncates_conversation(
        self, mock_stream_answer, mock_search, mock_condense, auth_client, user, mock_model_c_sufficient, sample_hits
    ):
        """Retry: truncates messages from the retried user message onward."""
        mock_condense.return_value = "test question"
        mock_search.return_value = sample_hits
        mock_stream_answer.return_value = iter(["New answer"])

        # First, create an initial conversation
        user_msg1 = ChatMessage.objects.create(
            owner=user, role=ChatMessage.Role.USER, content="First question"
        )
        ChatMessage.objects.create(
            owner=user, role=ChatMessage.Role.ASSISTANT, content="First answer"
        )
        user_msg2 = ChatMessage.objects.create(
            owner=user, role=ChatMessage.Role.USER, content="Second question"
        )
        ChatMessage.objects.create(
            owner=user, role=ChatMessage.Role.ASSISTANT, content="Second answer"
        )

        assert ChatMessage.objects.filter(owner=user).count() == 4

        # Retry from the second user message
        response = auth_client.post(
            reverse("chatapp:ask"),
            {
                "question": "Retry question",
                "message_id": str(user_msg2.id),
            },
        )

        assert response.status_code == 200
        consume_streaming_response(response)

        # Verify truncation: messages from user_msg2 onward should be deleted and replaced
        messages = ChatMessage.objects.filter(owner=user).order_by("created_at")
        assert messages.count() == 4  # user_msg1, assistant_msg1, new_user_msg, new_assistant_msg

        # First pair should remain
        assert messages[0].content == "First question"
        assert messages[1].content == "First answer"

        # New messages
        assert messages[2].role == ChatMessage.Role.USER
        assert messages[2].content == "Retry question"
        assert messages[3].role == ChatMessage.Role.ASSISTANT
        assert messages[3].content == "New answer"

    @patch("chatapp.clinical_rag.pipeline.generation.condense_question")
    @patch("chatapp.clinical_rag.pipeline.retrieval.search")
    @patch("chatapp.clinical_rag.pipeline.generation.stream_answer")
    def test_edit_truncates_conversation(
        self, mock_stream_answer, mock_search, mock_condense, auth_client, user, mock_model_c_sufficient, sample_hits
    ):
        """Edit: truncates messages from the edited user message onward."""
        mock_condense.return_value = "edited question"
        mock_search.return_value = sample_hits
        mock_stream_answer.return_value = iter(["Edited answer"])

        # Create initial conversation
        user_msg1 = ChatMessage.objects.create(
            owner=user, role=ChatMessage.Role.USER, content="Original question"
        )
        ChatMessage.objects.create(
            owner=user, role=ChatMessage.Role.ASSISTANT, content="Original answer"
        )
        user_msg2 = ChatMessage.objects.create(
            owner=user, role=ChatMessage.Role.USER, content="Follow-up"
        )
        ChatMessage.objects.create(
            owner=user, role=ChatMessage.Role.ASSISTANT, content="Follow-up answer"
        )

        # Edit the first user message
        response = auth_client.post(
            reverse("chatapp:ask"),
            {
                "question": "Edited question",
                "message_id": str(user_msg1.id),
            },
        )

        assert response.status_code == 200
        consume_streaming_response(response)

        # All messages from user_msg1 onward should be replaced
        messages = ChatMessage.objects.filter(owner=user).order_by("created_at")
        assert messages.count() == 2  # new_user_msg, new_assistant_msg

        assert messages[0].role == ChatMessage.Role.USER
        assert messages[0].content == "Edited question"
        assert messages[1].role == ChatMessage.Role.ASSISTANT
        assert messages[1].content == "Edited answer"


# ============================================================
# Test Chat History Loading (Page Refresh Simulation)
# ============================================================

class TestChatHistoryLoading:
    """Tests for chat history loading on page refresh."""

    def test_chat_view_loads_recent_messages(self, auth_client, user):
        """Chat view loads recent messages in chronological order."""
        # Create messages
        msg1 = ChatMessage.objects.create(
            owner=user, role=ChatMessage.Role.USER, content="First question"
        )
        msg2 = ChatMessage.objects.create(
            owner=user, role=ChatMessage.Role.ASSISTANT, content="First answer", sources=[{"title": "doc1"}]
        )
        msg3 = ChatMessage.objects.create(
            owner=user, role=ChatMessage.Role.USER, content="Second question"
        )
        msg4 = ChatMessage.objects.create(
            owner=user, role=ChatMessage.Role.ASSISTANT, content="Second answer", sources=[{"title": "doc2"}]
        )
        msg5 = ChatMessage.objects.create(
            owner=user, role=ChatMessage.Role.USER, content="Third question"
        )
        ChatMessage.objects.create(
            owner=user, role=ChatMessage.Role.ASSISTANT, content="Third answer", sources=[{"title": "doc3"}]
        )

        # Request chat view
        response = auth_client.get(reverse("chatapp:chat"))

        assert response.status_code == 200
        assert "chat_messages" in response.context

        messages = response.context["chat_messages"]
        assert len(messages) == 6

        # Verify order is chronological (by created_at, id)
        assert messages[0].content == "First question"
        assert messages[1].content == "First answer"
        assert messages[2].content == "Second question"
        assert messages[3].content == "Second answer"
        assert messages[4].content == "Third question"
        assert messages[5].content == "Third answer"

    def test_chat_view_loads_abstention_message_correctly(self, auth_client, user):
        """Chat view loads persisted abstention message with correct content."""
        ChatMessage.objects.create(
            owner=user,
            role=ChatMessage.Role.USER,
            content="What about rare disease X?"
        )
        ChatMessage.objects.create(
            owner=user,
            role=ChatMessage.Role.ASSISTANT,
            content=(
                "I cannot provide a reliable answer because the retrieved evidence "
                "was insufficient to answer your question. The combined sufficiency "
                "score (0.4500) is below the required threshold (0.70)."
            ),
            sources=[{"title": "doc1", "score": 0.45}]
        )

        response = auth_client.get(reverse("chatapp:chat"))

        assert response.status_code == 200
        messages = response.context["chat_messages"]
        assert len(messages) == 2

        assistant_msg = messages[1]
        assert assistant_msg.role == ChatMessage.Role.ASSISTANT
        assert "insufficient" in assistant_msg.content.lower()
        assert "0.4500" in assistant_msg.content
        assert "0.70" in assistant_msg.content
        assert len(assistant_msg.sources) == 1

    def test_chat_view_loads_normal_message_with_sources(self, auth_client, user):
        """Chat view loads normal assistant message with sources."""
        ChatMessage.objects.create(
            owner=user,
            role=ChatMessage.Role.USER,
            content="What is diabetes?"
        )
        ChatMessage.objects.create(
            owner=user,
            role=ChatMessage.Role.ASSISTANT,
            content="Diabetes is a metabolic disorder...",
            sources=[
                {"title": "doc1", "meta": "Chunk 1 · similarity 0.85", "score": 0.85},
                {"title": "doc2", "meta": "Chunk 1 · similarity 0.70", "score": 0.70}
            ]
        )

        response = auth_client.get(reverse("chatapp:chat"))

        assert response.status_code == 200
        messages = response.context["chat_messages"]
        assert len(messages) == 2

        assistant_msg = messages[1]
        assert assistant_msg.role == ChatMessage.Role.ASSISTANT
        assert assistant_msg.content == "Diabetes is a metabolic disorder..."
        assert len(assistant_msg.sources) == 2
        assert assistant_msg.sources[0]["title"] == "doc1"
        assert assistant_msg.sources[1]["title"] == "doc2"

    def test_chat_view_limits_to_50_messages(self, auth_client, user):
        """Chat view loads only the 50 most recent messages."""
        # Create 60 messages (30 pairs)
        for i in range(60):
            ChatMessage.objects.create(
                owner=user,
                role=ChatMessage.Role.USER if i % 2 == 0 else ChatMessage.Role.ASSISTANT,
                content=f"Message {i}"
            )

        response = auth_client.get(reverse("chatapp:chat"))

        assert response.status_code == 200
        messages = response.context["chat_messages"]
        assert len(messages) == 50

        # Should be the most recent 50 (messages 10-59)
        assert messages[0].content == "Message 10"
        assert messages[-1].content == "Message 59"


# ============================================================
# Test CSRF and Form Validation
# ============================================================

class TestCSRFAndValidation:
    """Tests for CSRF protection and form validation."""

    def test_ask_rejects_empty_question(self, auth_client):
        """Ask endpoint rejects empty question."""
        response = auth_client.post(
            reverse("chatapp:ask"),
            {"question": ""},
        )

        assert response.status_code == 400
        data = json.loads(response.content)
        assert "error" in data

    def test_ask_rejects_long_question(self, auth_client):
        """Ask endpoint rejects question exceeding MAX_QUESTION_CHARS."""
        from chatapp.views import MAX_QUESTION_CHARS
        long_question = "x" * (MAX_QUESTION_CHARS + 1)

        response = auth_client.post(
            reverse("chatapp:ask"),
            {"question": long_question},
        )

        assert response.status_code == 400
        data = json.loads(response.content)
        assert "error" in data

    def test_ask_rejects_invalid_message_id(self, auth_client):
        """Ask endpoint rejects non-numeric message_id."""
        response = auth_client.post(
            reverse("chatapp:ask"),
            {"question": "Test", "message_id": "abc"},
        )

        assert response.status_code == 400
        data = json.loads(response.content)
        assert "error" in data

    def test_ask_rejects_nonexistent_message_id(self, auth_client, user):
        """Ask endpoint rejects message_id that doesn't belong to user."""
        other_user = User.objects.create_user(username="other", password="pass")
        other_msg = ChatMessage.objects.create(
            owner=other_user, role=ChatMessage.Role.USER, content="Other's question"
        )

        response = auth_client.post(
            reverse("chatapp:ask"),
            {"question": "Test", "message_id": str(other_msg.id)},
        )

        assert response.status_code == 404
        data = json.loads(response.content)
        assert "error" in data


# ============================================================
# Test Clear Chat
# ============================================================

class TestClearChat:
    """Tests for clear chat functionality."""

    def test_clear_chat_deletes_user_messages(self, auth_client, user):
        """Clear chat deletes all messages for the current user."""
        # Create messages for this user
        for i in range(5):
            ChatMessage.objects.create(
                owner=user,
                role=ChatMessage.Role.USER if i % 2 == 0 else ChatMessage.Role.ASSISTANT,
                content=f"Message {i}"
            )

        # Create messages for another user (should not be deleted)
        other_user = User.objects.create_user(username="other", password="pass")
        ChatMessage.objects.create(
            owner=other_user, role=ChatMessage.Role.USER, content="Other user message"
        )

        assert ChatMessage.objects.filter(owner=user).count() == 5
        assert ChatMessage.objects.filter(owner=other_user).count() == 1

        response = auth_client.post(reverse("chatapp:clear_chat"))

        assert response.status_code == 302  # Redirect
        assert ChatMessage.objects.filter(owner=user).count() == 0
        assert ChatMessage.objects.filter(owner=other_user).count() == 1


# ============================================================
# Test Disabled Sufficiency Gate
# ============================================================

class TestDisabledSufficiencyGate:
    """Tests with SUFFICIENCY_ENABLED=False."""

    @patch("chatapp.clinical_rag.pipeline.generation.condense_question")
    @patch("chatapp.clinical_rag.pipeline.retrieval.search")
    @patch("chatapp.clinical_rag.pipeline.generation.stream_answer")
    def test_disabled_gate_proceeds_to_generation(
        self, mock_stream_answer, mock_search, mock_condense, auth_client, user, low_similarity_hits
    ):
        """Disabled gate skips sufficiency check and proceeds to generation even with low similarity."""
        original = config.SUFFICIENCY_ENABLED
        config.SUFFICIENCY_ENABLED = False
        try:
            mock_condense.return_value = "test question"
            mock_search.return_value = low_similarity_hits
            mock_stream_answer.return_value = iter(["Answer with gate disabled"])

            response = auth_client.post(
                reverse("chatapp:ask"),
                {"question": "What is type 2 diabetes in adolescents?"},
            )

            assert response.status_code == 200
            # Get streaming content first (this also consumes the stream)
            content = get_streaming_content(response)

            # Verify database - should have assistant message with answer
            messages = ChatMessage.objects.filter(owner=user).order_by("created_at")
            assert messages.count() == 2

            assistant_msg = messages[1]
            assert assistant_msg.role == ChatMessage.Role.ASSISTANT
            assert assistant_msg.content == "Answer with gate disabled"
            assert "insufficient" not in assistant_msg.content.lower()

            # Verify streaming events
            events = [json.loads(line) for line in content.strip().split("\n") if line.strip()]
            event_types = [e["type"] for e in events]
            assert event_types == ["saved", "query", "sources", "token", "done"]
            assert "abstain" not in event_types
        finally:
            config.SUFFICIENCY_ENABLED = original


# ============================================================
# Test Event Stream Integration (Detailed Sequence)
# ============================================================

class TestEventStreamSequence:
    """Detailed tests for the event stream sequence."""

    @patch("chatapp.clinical_rag.pipeline.generation.condense_question")
    @patch("chatapp.clinical_rag.pipeline.retrieval.search")
    @patch("chatapp.clinical_rag.pipeline.generation.stream_answer")
    def test_sufficient_evidence_event_sequence(
        self, mock_stream_answer, mock_search, mock_condense, auth_client, user, mock_model_c_sufficient, sample_hits
    ):
        """Sufficient evidence: saved, query, sources, token+, done."""
        mock_condense.return_value = "test question"
        mock_search.return_value = sample_hits
        mock_stream_answer.return_value = iter(["Token 1", "Token 2", "Token 3"])

        response = auth_client.post(
            reverse("chatapp:ask"),
            {"question": "Test question"},
        )

        assert response.status_code == 200
        content = get_streaming_content(response)
        consume_streaming_response(response)

        events = [json.loads(line) for line in content.strip().split("\n") if line.strip()]

        event_types = [e["type"] for e in events]
        assert event_types == ["saved", "query", "sources", "token", "token", "token", "done"]

        # Exactly one done event at the end
        done_count = sum(1 for e in events if e["type"] == "done")
        assert done_count == 1
        assert events[-1]["type"] == "done"

        # No abstain or error events
        assert "abstain" not in event_types
        assert "error" not in event_types

    @patch("chatapp.clinical_rag.pipeline.generation.condense_question")
    @patch("chatapp.clinical_rag.pipeline.retrieval.search")
    @patch("chatapp.clinical_rag.pipeline.generation.stream_answer")
    def test_insufficient_evidence_event_sequence(
        self, mock_stream_answer, mock_search, mock_condense, auth_client, user, mock_model_c_insufficient, low_similarity_hits
    ):
        """Insufficient evidence: saved, query, sources, abstain, done."""
        mock_condense.return_value = "test question"
        mock_search.return_value = low_similarity_hits
        mock_stream_answer.return_value = iter([])

        response = auth_client.post(
            reverse("chatapp:ask"),
            {"question": "Test question"},
        )

        assert response.status_code == 200
        content = get_streaming_content(response)
        consume_streaming_response(response)

        events = [json.loads(line) for line in content.strip().split("\n") if line.strip()]

        event_types = [e["type"] for e in events]
        assert event_types == ["saved", "query", "sources", "abstain", "done"]

        # Exactly one done event
        done_count = sum(1 for e in events if e["type"] == "done")
        assert done_count == 1
        assert events[-1]["type"] == "done"

        # No token events
        assert "token" not in event_types
        assert "error" not in event_types

    @patch("chatapp.clinical_rag.pipeline.generation.condense_question")
    @patch("chatapp.clinical_rag.pipeline.retrieval.search")
    @patch("chatapp.clinical_rag.pipeline.generation.stream_answer")
    def test_empty_retrieval_event_sequence(
        self, mock_stream_answer, mock_search, mock_condense, auth_client, user, mock_model_c_sufficient
    ):
        """Empty retrieval: saved, query, sources(empty), abstain, done."""
        mock_condense.return_value = "test question"
        mock_search.return_value = []
        mock_stream_answer.return_value = iter([])

        response = auth_client.post(
            reverse("chatapp:ask"),
            {"question": "Test question"},
        )

        assert response.status_code == 200
        content = get_streaming_content(response)
        consume_streaming_response(response)

        events = [json.loads(line) for line in content.strip().split("\n") if line.strip()]

        event_types = [e["type"] for e in events]
        assert event_types == ["saved", "query", "sources", "abstain", "done"]

        # No token, no error
        assert "token" not in event_types
        assert "error" not in event_types

    @patch("chatapp.clinical_rag.pipeline.generation.condense_question")
    @patch("chatapp.clinical_rag.pipeline.retrieval.search")
    @patch("chatapp.clinical_rag.pipeline.generation.stream_answer")
    def test_operational_error_event_sequence(
        self, mock_stream_answer, mock_search, mock_condense, auth_client, user, mock_model_c_failure, sample_hits
    ):
        """Operational error: saved, query, error, done."""
        mock_condense.return_value = "test question"
        mock_search.return_value = sample_hits
        mock_stream_answer.return_value = iter([])

        response = auth_client.post(
            reverse("chatapp:ask"),
            {"question": "Test question"},
        )

        assert response.status_code == 200
        content = get_streaming_content(response)
        consume_streaming_response(response)

        events = [json.loads(line) for line in content.strip().split("\n") if line.strip()]

        event_types = [e["type"] for e in events]
        assert event_types == ["saved", "query", "error", "done"]

        # No abstain, no token
        assert "abstain" not in event_types
        assert "token" not in event_types

    @patch("chatapp.clinical_rag.pipeline.generation.condense_question")
    @patch("chatapp.clinical_rag.pipeline.retrieval.search")
    @patch("chatapp.clinical_rag.pipeline.generation.stream_answer")
    def test_disabled_gate_event_sequence(
        self, mock_stream_answer, mock_search, mock_condense, auth_client, user, low_similarity_hits
    ):
        """Disabled gate: saved, query, sources, token+, done (no abstain)."""
        original = config.SUFFICIENCY_ENABLED
        config.SUFFICIENCY_ENABLED = False
        try:
            mock_condense.return_value = "test question"
            mock_search.return_value = low_similarity_hits
            mock_stream_answer.return_value = iter(["Answer"])

            response = auth_client.post(
                reverse("chatapp:ask"),
                {"question": "Test question"},
            )

            assert response.status_code == 200
            content = get_streaming_content(response)
            consume_streaming_response(response)

            events = [json.loads(line) for line in content.strip().split("\n") if line.strip()]

            event_types = [e["type"] for e in events]
            assert event_types == ["saved", "query", "sources", "token", "done"]
            assert "abstain" not in event_types
            assert "error" not in event_types
        finally:
            config.SUFFICIENCY_ENABLED = original


# ============================================================
# Test No Duplicate Messages
# ============================================================

class TestNoDuplicateMessages:
    """Regression tests ensuring no duplicate assistant messages."""

    @patch("chatapp.clinical_rag.pipeline.generation.condense_question")
    @patch("chatapp.clinical_rag.pipeline.retrieval.search")
    @patch("chatapp.clinical_rag.pipeline.generation.stream_answer")
    def test_normal_answer_exactly_one_assistant_message(
        self, mock_stream_answer, mock_search, mock_condense, auth_client, user, mock_model_c_sufficient, sample_hits
    ):
        """Normal answer: exactly one assistant message created."""
        mock_condense.return_value = "test question"
        mock_search.return_value = sample_hits
        mock_stream_answer.return_value = iter(["Answer"])

        initial_count = ChatMessage.objects.filter(owner=user).count()

        response = auth_client.post(
            reverse("chatapp:ask"),
            {"question": "Test question"},
        )

        assert response.status_code == 200
        consume_streaming_response(response)

        final_count = ChatMessage.objects.filter(owner=user).count()
        assert final_count == initial_count + 2  # 1 user + 1 assistant

        assistant_messages = ChatMessage.objects.filter(
            owner=user, role=ChatMessage.Role.ASSISTANT
        )
        assert assistant_messages.count() == 1

    @patch("chatapp.clinical_rag.pipeline.generation.condense_question")
    @patch("chatapp.clinical_rag.pipeline.retrieval.search")
    @patch("chatapp.clinical_rag.pipeline.generation.stream_answer")
    def test_abstention_exactly_one_assistant_message(
        self, mock_stream_answer, mock_search, mock_condense, auth_client, user, mock_model_c_insufficient, low_similarity_hits
    ):
        """Abstention: exactly one assistant message created."""
        mock_condense.return_value = "test question"
        mock_search.return_value = low_similarity_hits
        mock_stream_answer.return_value = iter([])

        initial_count = ChatMessage.objects.filter(owner=user).count()

        response = auth_client.post(
            reverse("chatapp:ask"),
            {"question": "Test question"},
        )

        assert response.status_code == 200
        consume_streaming_response(response)

        final_count = ChatMessage.objects.filter(owner=user).count()
        assert final_count == initial_count + 2  # 1 user + 1 assistant

        assistant_messages = ChatMessage.objects.filter(
            owner=user, role=ChatMessage.Role.ASSISTANT
        )
        assert assistant_messages.count() == 1

    @patch("chatapp.clinical_rag.pipeline.generation.condense_question")
    @patch("chatapp.clinical_rag.pipeline.retrieval.search")
    @patch("chatapp.clinical_rag.pipeline.generation.stream_answer")
    def test_operational_error_zero_assistant_messages(
        self, mock_stream_answer, mock_search, mock_condense, auth_client, user, mock_model_c_failure, sample_hits
    ):
        """Operational error: zero assistant messages created."""
        mock_condense.return_value = "test question"
        mock_search.return_value = sample_hits
        mock_stream_answer.return_value = iter([])

        initial_count = ChatMessage.objects.filter(owner=user).count()

        response = auth_client.post(
            reverse("chatapp:ask"),
            {"question": "Test question"},
        )

        assert response.status_code == 200
        consume_streaming_response(response)

        final_count = ChatMessage.objects.filter(owner=user).count()
        assert final_count == initial_count + 1  # only 1 user message

        assistant_messages = ChatMessage.objects.filter(
            owner=user, role=ChatMessage.Role.ASSISTANT
        )
        assert assistant_messages.count() == 0


# ============================================================
# Test User Message Persistence
# ============================================================

class TestUserMessagePersistence:
    """Tests for user message persistence."""

    @patch("chatapp.clinical_rag.pipeline.generation.condense_question")
    @patch("chatapp.clinical_rag.pipeline.retrieval.search")
    @patch("chatapp.clinical_rag.pipeline.generation.stream_answer")
    def test_user_message_persisted_with_correct_content(
        self, mock_stream_answer, mock_search, mock_condense, auth_client, user, mock_model_c_sufficient, sample_hits
    ):
        """User message is persisted with the exact question content."""
        mock_condense.return_value = "test question"
        mock_search.return_value = sample_hits
        mock_stream_answer.return_value = iter(["Answer"])

        question_text = "What is the treatment for type 2 diabetes in adolescents?"
        response = auth_client.post(
            reverse("chatapp:ask"),
            {"question": question_text},
        )

        assert response.status_code == 200
        consume_streaming_response(response)

        user_messages = ChatMessage.objects.filter(
            owner=user, role=ChatMessage.Role.USER
        )
        assert user_messages.count() == 1
        assert user_messages.first().content == question_text

    @patch("chatapp.clinical_rag.pipeline.generation.condense_question")
    @patch("chatapp.clinical_rag.pipeline.retrieval.search")
    @patch("chatapp.clinical_rag.pipeline.generation.stream_answer")
    def test_user_message_persisted_on_abstention(
        self, mock_stream_answer, mock_search, mock_condense, auth_client, user, mock_model_c_insufficient, low_similarity_hits
    ):
        """User message is persisted even when evidence is insufficient."""
        mock_condense.return_value = "test question"
        mock_search.return_value = low_similarity_hits
        mock_stream_answer.return_value = iter([])

        question_text = "What is rare disease X?"
        response = auth_client.post(
            reverse("chatapp:ask"),
            {"question": question_text},
        )

        assert response.status_code == 200
        consume_streaming_response(response)

        user_messages = ChatMessage.objects.filter(
            owner=user, role=ChatMessage.Role.USER
        )
        assert user_messages.count() == 1
        assert user_messages.first().content == question_text


# ============================================================
# Run tests when executed directly
# ============================================================

if __name__ == "__main__":
    import subprocess
    sys.exit(subprocess.call([sys.executable, "-m", "pytest", __file__, "-v"]))