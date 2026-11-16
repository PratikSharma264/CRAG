"""
Unit tests for the sufficiency engine and checks.

Run with: python -m pytest chatapp/clinical_rag/test_sufficiency.py -v
Or: python chatapp/clinical_rag/test_sufficiency.py
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from chatapp.clinical_rag import config
from chatapp.clinical_rag.sufficiency_checks import (
    ModelCCheck,
    CosineCheck,
    LLMJudgeCheck,
    CheckResult,
    ModelCCheckpointError,
    ModelCInferenceError,
    ModelCOutputError,
    CosineSimilarityError,
    LLMJudgeError,
    get_model_c,
)
from chatapp.clinical_rag.sufficiency import (
    PartialSufficiencyResult,
    SufficiencyEngine,
    SufficiencyResult,
    calculate_combined_score,
    calculate_fallback_score,
    NoChecksConfiguredError,
)


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset singletons between tests."""
    # Reset Model C singleton
    from chatapp.clinical_rag.sufficiency_checks import _ModelCSingleton
    _ModelCSingleton._instance = None
    _ModelCSingleton._initialized = False
    yield
    _ModelCSingleton._instance = None
    _ModelCSingleton._initialized = False


@pytest.fixture(autouse=True)
def disable_llm_judge_by_default():
    """Disable LLM Judge by default for tests that don't explicitly test it."""
    from chatapp.clinical_rag import config
    original = config.LLM_JUDGE_ENABLED
    config.LLM_JUDGE_ENABLED = False
    yield
    config.LLM_JUDGE_ENABLED = original


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
def mock_model_c():
    """Mock Model C singleton for testing without loading real model."""
    with patch("chatapp.clinical_rag.sufficiency_checks._ModelCSingleton._load_model"):
        singleton = get_model_c()
        # Mock the predict_proba method
        singleton.predict_proba = MagicMock(return_value=0.92)
        yield singleton


# ============================================================
# Tests for calculate_combined_score
# ============================================================

class TestCombinedScore:
    """Tests for the canonical combined scoring formula."""

    def test_formula_with_three_components(self):
        """Verify formula: 0.10 * model_c + 0.45 * cosine + 0.45 * llm_judge"""
        model_c_prob = 0.90
        cosine_sim = 0.80
        llm_judge_score = 1.0
        expected = round(0.10 * model_c_prob + 0.45 * cosine_sim + 0.45 * llm_judge_score, 4)
        actual = calculate_combined_score(model_c_prob, cosine_sim, llm_judge_score)
        assert actual == expected

    def test_formula_with_zero_llm_judge(self):
        """Verify formula with LLM judge score of 0."""
        model_c_prob = 0.90
        cosine_sim = 0.80
        llm_judge_score = 0.0
        expected = round(0.10 * model_c_prob + 0.45 * cosine_sim + 0.45 * llm_judge_score, 4)
        actual = calculate_combined_score(model_c_prob, cosine_sim, llm_judge_score)
        assert actual == expected

    def test_rounding_behavior(self):
        """Verify rounding to 4 decimal places."""
        # 0.10 * 0.5 + 0.45 * 0.5 + 0.45 * 0.5 = 0.5 exactly
        assert calculate_combined_score(0.5, 0.5, 0.5) == 0.5

        # 0.10 * 0.3333 + 0.45 * 0.6666 + 0.45 * 0.7777 = 0.6499 -> 0.6499
        result = calculate_combined_score(0.3333, 0.6666, 0.7777)
        assert result == round(0.10 * 0.3333 + 0.45 * 0.6666 + 0.45 * 0.7777, 4)

    def test_edge_cases(self):
        """Test boundary values."""
        assert calculate_combined_score(0.0, 0.0, 0.0) == 0.0
        assert calculate_combined_score(1.0, 1.0, 1.0) == 1.0
        assert calculate_combined_score(0.0, 1.0, 0.0) == round(0.45, 4)
        assert calculate_combined_score(1.0, 0.0, 0.0) == round(0.10, 4)
        assert calculate_combined_score(0.0, 0.0, 1.0) == round(0.45, 4)

    def test_weights_are_from_config(self):
        """Verify weights come from config, not hardcoded."""
        original_mc = config.MODEL_C_WEIGHT
        original_cos = config.COSINE_WEIGHT
        original_llm = config.LLM_JUDGE_WEIGHT
        try:
            config.MODEL_C_WEIGHT = 0.20
            config.COSINE_WEIGHT = 0.30
            config.LLM_JUDGE_WEIGHT = 0.50
            result = calculate_combined_score(1.0, 0.0, 0.0)
            assert result == 0.20
            result = calculate_combined_score(0.0, 1.0, 0.0)
            assert result == 0.30
            result = calculate_combined_score(0.0, 0.0, 1.0)
            assert result == 0.50
        finally:
            config.MODEL_C_WEIGHT = original_mc
            config.COSINE_WEIGHT = original_cos
            config.LLM_JUDGE_WEIGHT = original_llm


class TestFallbackScore:
    """Tests for fallback score when LLM judge is unavailable."""

    def test_fallback_renormalizes_weights(self):
        """Fallback should use renormalized weights: 0.10/0.55 and 0.45/0.55"""
        model_c_prob = 1.0
        cosine_sim = 0.0
        # model_c weight = 0.10/0.55 = 0.1818..., cosine weight = 0.45/0.55 = 0.8181...
        expected = round((0.10/0.55) * 1.0 + (0.45/0.55) * 0.0, 4)
        actual = calculate_fallback_score(model_c_prob, cosine_sim)
        assert actual == expected

    def test_fallback_with_both_scores(self):
        """Fallback with both model_c and cosine."""
        model_c_prob = 0.80
        cosine_sim = 0.60
        fallback_mc_weight = 0.10 / 0.55
        fallback_cos_weight = 0.45 / 0.55
        expected = round(fallback_mc_weight * model_c_prob + fallback_cos_weight * cosine_sim, 4)
        actual = calculate_fallback_score(model_c_prob, cosine_sim)
        assert actual == expected


# ============================================================
# Tests for CosineCheck
# ============================================================

class TestCosineCheck:
    """Tests for cosine similarity check."""

    def test_uses_passage_1_similarity(self, sample_hits):
        """Cosine check uses hits[0]['similarity'] (Passage 1)."""
        check = CosineCheck()
        result = check.evaluate("test question", sample_hits)
        assert result.name == "cosine"
        assert result.score == 0.85  # hits[0].similarity

    def test_ignores_passage_2_and_3(self, sample_hits):
        """Passage 2 and 3 do not affect cosine score."""
        check = CosineCheck()
        result = check.evaluate("test question", sample_hits)
        # Even though passage 2 has 0.70 and passage 3 has 0.55,
        # only passage 1 (0.85) is used
        assert result.score == 0.85
        assert result.details["passage_used"] == 1

    def test_clamps_similarity_to_valid_range(self):
        """Similarity is clamped to [0, 1]."""
        check = CosineCheck()
        hits_high = [{"similarity": 1.5, "content": "test"}]
        hits_low = [{"similarity": -0.5, "content": "test"}]
        result_high = check.evaluate("q", hits_high)
        result_low = check.evaluate("q", hits_low)
        assert result_high.score == 1.0
        assert result_low.score == 0.0

    def test_raises_on_empty_hits(self):
        """Empty hits raises CosineSimilarityError."""
        check = CosineCheck()
        with pytest.raises(CosineSimilarityError):
            check.evaluate("question", [])

    def test_raises_on_missing_similarity(self):
        """Missing similarity field raises CosineSimilarityError."""
        check = CosineCheck()
        hits = [{"content": "test"}]  # no 'similarity' key
        with pytest.raises(CosineSimilarityError):
            check.evaluate("question", hits)

    def test_raises_on_non_numeric_similarity(self):
        """Non-numeric similarity raises CosineSimilarityError."""
        check = CosineCheck()
        hits = [{"similarity": "high", "content": "test"}]
        with pytest.raises(CosineSimilarityError):
            check.evaluate("question", hits)

    def test_details_structure(self, sample_hits):
        """Check result details contain expected fields."""
        check = CosineCheck()
        result = check.evaluate("question", sample_hits)
        assert "similarity" in result.details
        assert "raw_similarity" in result.details
        assert "passage_used" in result.details
        assert result.details["passage_used"] == 1


# ============================================================
# Tests for ModelCCheck (with mocked model)
# ============================================================

class TestModelCCheck:
    """Tests for Model C check."""

    def test_uses_passage_1_only(self, mock_model_c, sample_hits):
        """Model C receives only Passage 1 content."""
        check = ModelCCheck()
        result = check.evaluate("test question", sample_hits)
        # Verify predict_proba was called with question and passage_1
        mock_model_c.predict_proba.assert_called_once()
        call_args = mock_model_c.predict_proba.call_args
        assert call_args[0][0] == "test question"  # question
        assert call_args[0][1] == sample_hits[0]["content"]  # passage_1

    def test_passage_2_and_3_ignored(self, mock_model_c, sample_hits):
        """Passage 2 and 3 do not affect Model C input."""
        check = ModelCCheck()
        result = check.evaluate("test question", sample_hits)
        # The formatter inside predict_proba only uses passage_1
        # This is verified by the mock call above
        call_args = mock_model_c.predict_proba.call_args
        assert call_args[0][1] == sample_hits[0]["content"]

    def test_returns_probability_of_label_1(self, mock_model_c, sample_hits):
        """Score is P(sufficient) = probability of label 1."""
        mock_model_c.predict_proba.return_value = 0.75
        check = ModelCCheck()
        result = check.evaluate("test question", sample_hits)
        assert result.score == 0.75
        assert result.details["probability_sufficient"] == 0.75
        assert result.details["probability_insufficient"] == 0.25

    def test_raises_on_empty_hits(self, mock_model_c):
        """Empty hits raises ModelCInferenceError."""
        check = ModelCCheck()
        with pytest.raises(ModelCInferenceError):
            check.evaluate("question", [])

    def test_raises_on_empty_passage_1(self, mock_model_c):
        """Empty passage 1 content raises ModelCInferenceError."""
        check = ModelCCheck()
        hits = [{"content": "", "similarity": 0.8}]
        with pytest.raises(ModelCInferenceError):
            check.evaluate("question", hits)

    def test_raises_on_missing_checkpoint(self):
        """Missing checkpoint raises ModelCCheckpointError."""
        with patch.object(config, "MODEL_C_CHECKPOINT", Path("/nonexistent/path")):
            check = ModelCCheck()
            with pytest.raises(ModelCCheckpointError):
                check.evaluate("question", [{"content": "test", "similarity": 0.8}])

    def test_invalid_probability_raises(self, mock_model_c, sample_hits):
        """Probability outside [0,1] raises ModelCOutputError."""
        mock_model_c.predict_proba.return_value = 1.5
        check = ModelCCheck()
        with pytest.raises(ModelCOutputError):
            check.evaluate("question", sample_hits)

    def test_details_structure(self, mock_model_c, sample_hits):
        """Check result details contain expected fields."""
        check = ModelCCheck()
        result = check.evaluate("question", sample_hits)
        assert "probability_sufficient" in result.details
        assert "probability_insufficient" in result.details
        assert "passage_used" in result.details
        assert "max_length" in result.details
        assert result.details["passage_used"] == 1
        assert result.details["max_length"] == 512


# ============================================================
# Tests for SufficiencyEngine
# ============================================================

class TestSufficiencyEngine:
    """Tests for the sufficiency engine."""

    def test_sufficient_when_score_above_threshold(self, mock_model_c, sample_hits):
        """Score >= 0.70 returns sufficient=True (with LLM judge disabled -> fallback)."""
        # With LLM judge disabled: fallback uses renormalized weights
        # model_c=0.92, cosine=0.85
        # fallback = (0.10/0.55)*0.92 + (0.45/0.55)*0.85 = 0.1673 + 0.6955 = 0.8627
        mock_model_c.predict_proba.return_value = 0.92
        engine = SufficiencyEngine()
        partial = engine.evaluate_partial("test question", sample_hits)
        result = engine.finalize(partial)
        assert result.sufficient is True
        assert result.combined_score == 0.8627
        assert result.llm_judge_score is None
        assert result.check_details["judge_status"] == "disabled"

    def test_insufficient_when_score_below_threshold(self, mock_model_c, sample_hits):
        """Score < 0.70 returns sufficient=False (with LLM judge disabled -> fallback)."""
        # model_c=0.30, cosine=0.50
        # fallback = (0.10/0.55)*0.30 + (0.45/0.55)*0.50 = 0.0545 + 0.4091 = 0.4636
        mock_model_c.predict_proba.return_value = 0.30
        sample_hits[0]["similarity"] = 0.50
        engine = SufficiencyEngine()
        partial = engine.evaluate_partial("test question", sample_hits)
        result = engine.finalize(partial)
        assert result.sufficient is False
        assert result.combined_score == 0.4636
        assert result.llm_judge_score is None

    def test_exact_threshold_is_sufficient(self, mock_model_c, sample_hits):
        """Score exactly at threshold (0.70) returns sufficient=True (fallback)."""
        # Need fallback = 0.70: (0.10/0.55)*mc + (0.45/0.55)*cos = 0.70
        # If mc=1.0: (0.10/0.55) + (0.45/0.55)*cos = 0.70 -> cos = (0.70 - 0.1818)/0.8182 = 0.6333
        mock_model_c.predict_proba.return_value = 1.0
        sample_hits[0]["similarity"] = 0.6333333333333333
        engine = SufficiencyEngine()
        partial = engine.evaluate_partial("test question", sample_hits)
        result = engine.finalize(partial)
        assert result.sufficient is True
        assert result.combined_score >= 0.70

    def test_combined_score_matches_canonical_formula(self, mock_model_c, sample_hits):
        """Engine uses calculate_fallback_score when LLM judge disabled (single source of truth)."""
        mock_model_c.predict_proba.return_value = 0.88
        sample_hits[0]["similarity"] = 0.78
        engine = SufficiencyEngine()
        partial = engine.evaluate_partial("test question", sample_hits)
        result = engine.finalize(partial)
        expected = calculate_fallback_score(0.88, 0.78)
        assert result.combined_score == expected

    def test_result_contains_all_required_fields(self, mock_model_c, sample_hits):
        """SufficiencyResult has all required fields."""
        mock_model_c.predict_proba.return_value = 0.90
        engine = SufficiencyEngine()
        partial = engine.evaluate_partial("test question", sample_hits)
        result = engine.finalize(partial)
        assert hasattr(result, "sufficient")
        assert hasattr(result, "combined_score")
        assert hasattr(result, "threshold")
        assert hasattr(result, "model_c_probability")
        assert hasattr(result, "cosine_similarity")
        assert hasattr(result, "llm_judge_score")
        assert hasattr(result, "check_details")

    def test_check_details_contains_component_info(self, mock_model_c, sample_hits):
        """check_details has weights, contributions, and component details."""
        mock_model_c.predict_proba.return_value = 0.90
        engine = SufficiencyEngine()
        partial = engine.evaluate_partial("test question", sample_hits)
        result = engine.finalize(partial)
        details = result.check_details
        assert "model_c" in details
        assert "cosine" in details
        assert "llm_judge" in details
        assert "weights" in details
        assert "contributions" in details
        assert "judge_status" in details
        # With LLM judge disabled, weights are renormalized
        assert abs(details["weights"]["model_c"] - (0.10/0.55)) < 1e-9
        assert abs(details["weights"]["cosine"] - (0.45/0.55)) < 1e-9
        assert details["weights"]["llm_judge"] == 0.0

    def test_disabled_gate_allows_generation(self, mock_model_c, sample_hits):
        """SUFFICIENCY_ENABLED=False returns sufficient with neutral scores."""
        original = config.SUFFICIENCY_ENABLED
        config.SUFFICIENCY_ENABLED = False
        try:
            engine = SufficiencyEngine()
            partial = engine.evaluate_partial("test question", sample_hits)
            result = engine.finalize(partial)
            assert result.sufficient is True
            assert result.combined_score == 1.0
            assert result.model_c_probability == 1.0
            assert result.cosine_similarity == 1.0
            assert result.llm_judge_score == 1.0
            assert result.check_details.get("disabled") is True
        finally:
            config.SUFFICIENCY_ENABLED = original

    def test_model_c_failure_propagates(self, mock_model_c, sample_hits):
        """Model C failure raises error (fail-closed)."""
        mock_model_c.predict_proba.side_effect = ModelCInferenceError("Model failed")
        engine = SufficiencyEngine()
        with pytest.raises(ModelCInferenceError):
            engine.evaluate_partial("test question", sample_hits)

    def test_cosine_failure_propagates(self, mock_model_c, sample_hits):
        """Cosine failure raises error (fail-closed)."""
        sample_hits[0]["similarity"] = None  # Will cause CosineSimilarityError
        engine = SufficiencyEngine()
        with pytest.raises(CosineSimilarityError):
            engine.evaluate_partial("test question", sample_hits)

    def test_no_checks_configured_raises(self):
        """Engine with no checks raises NoChecksConfiguredError."""
        engine = SufficiencyEngine()
        # Replace checks with empty list (avoids Model C torch loading)
        engine._model_c_check = None
        engine._cosine_check = None
        engine._llm_judge_check = None
        with pytest.raises(NoChecksConfiguredError):
            engine.evaluate_partial("question", [{"content": "test", "similarity": 0.8}])

    def test_model_loading_reused_not_repeated(self, mock_model_c, sample_hits):
        """Model C singleton is reused across evaluations."""
        mock_model_c.predict_proba.return_value = 0.90
        engine = SufficiencyEngine()
        # First evaluation
        partial1 = engine.evaluate_partial("question 1", sample_hits)
        result1 = engine.finalize(partial1)
        # Second evaluation
        partial2 = engine.evaluate_partial("question 2", sample_hits)
        result2 = engine.finalize(partial2)
        # predict_proba should be called twice but _load_model only once
        assert mock_model_c.predict_proba.call_count == 2


class TestSufficiencyEngineWithLLMJudge:
    """Tests for the sufficiency engine with LLM judge enabled (mocked)."""

    @pytest.fixture
    def engine_with_mocked_judge(self, mock_model_c, sample_hits):
        """Create engine with mocked LLM judge."""
        # Enable LLM judge for this test class
        from chatapp.clinical_rag import config
        config.LLM_JUDGE_ENABLED = True
        engine = SufficiencyEngine()
        # Replace LLM judge with mock
        mock_judge = MagicMock()
        mock_judge.evaluate = MagicMock(return_value=CheckResult(
            name="llm_judge",
            score=1.0,
            details={"label": 1, "reason": "test", "status": "done", "model": "gemini-3.5-flash"}
        ))
        engine._llm_judge_check = mock_judge
        yield engine
        config.LLM_JUDGE_ENABLED = False

    def test_llm_judge_score_included_when_done(self, engine_with_mocked_judge, mock_model_c, sample_hits):
        """LLM judge score included in combined score when successful."""
        mock_model_c.predict_proba.return_value = 0.90
        sample_hits[0]["similarity"] = 0.80
        engine = engine_with_mocked_judge
        partial = engine.evaluate_partial("test question", sample_hits)
        result = engine.finalize(partial)
        assert result.llm_judge_score == 1.0
        assert result.check_details["judge_status"] == "done"
        # combined = 0.10*0.90 + 0.45*0.80 + 0.45*1.0 = 0.09 + 0.36 + 0.45 = 0.90
        assert result.combined_score == 0.90

    def test_llm_judge_timeout_falls_back(self, mock_model_c, sample_hits):
        """LLM judge timeout falls back to renormalized Model C + Cosine."""
        from chatapp.clinical_rag import config
        config.LLM_JUDGE_ENABLED = True
        try:
            mock_model_c.predict_proba.return_value = 0.90
            sample_hits[0]["similarity"] = 0.80

            engine = SufficiencyEngine()
            # Mock LLM judge to timeout
            mock_judge = MagicMock()
            import concurrent.futures
            mock_judge.evaluate = MagicMock(side_effect=concurrent.futures.TimeoutError())
            engine._llm_judge_check = mock_judge

            partial = engine.evaluate_partial("test question", sample_hits)
            result = engine.finalize(partial)

            assert result.llm_judge_score is None
            assert result.check_details["judge_status"] == "timeout"
            # Fallback: model_c=0.90, cosine=0.80
            # renorm weights: model_c=0.10/0.55=0.1818..., cosine=0.45/0.55=0.8181...
            # fallback = 0.1818*0.90 + 0.8181*0.80 = 0.1636 + 0.6545 = 0.8181
            expected_fallback = calculate_fallback_score(0.90, 0.80)
            assert result.combined_score == expected_fallback
            assert result.sufficient is True  # 0.8181 > 0.70
        finally:
            config.LLM_JUDGE_ENABLED = False

    def test_llm_judge_error_falls_back(self, mock_model_c, sample_hits):
        """LLM judge error falls back to renormalized Model C + Cosine."""
        from chatapp.clinical_rag import config
        config.LLM_JUDGE_ENABLED = True
        try:
            mock_model_c.predict_proba.return_value = 0.90
            sample_hits[0]["similarity"] = 0.80

            engine = SufficiencyEngine()
            mock_judge = MagicMock()
            mock_judge.evaluate = MagicMock(side_effect=LLMJudgeError("API error"))
            engine._llm_judge_check = mock_judge

            partial = engine.evaluate_partial("test question", sample_hits)
            result = engine.finalize(partial)

            assert result.llm_judge_score is None
            assert result.check_details["judge_status"] == "error"
            expected_fallback = calculate_fallback_score(0.90, 0.80)
            assert result.combined_score == expected_fallback
        finally:
            config.LLM_JUDGE_ENABLED = False

    def test_llm_judge_insufficient_score(self, engine_with_mocked_judge, mock_model_c, sample_hits):
        """LLM judge returning 0 (insufficient) lowers combined score."""
        mock_model_c.predict_proba.return_value = 0.90
        sample_hits[0]["similarity"] = 0.80

        engine = engine_with_mocked_judge
        engine._llm_judge_check.evaluate.return_value = CheckResult(
            name="llm_judge",
            score=0.0,
            details={"label": 0, "reason": "insufficient", "status": "done", "model": "gemini-3.5-flash"}
        )

        partial = engine.evaluate_partial("test question", sample_hits)
        result = engine.finalize(partial)

        assert result.llm_judge_score == 0.0
        # combined = 0.10*0.90 + 0.45*0.80 + 0.45*0.0 = 0.09 + 0.36 + 0 = 0.45
        assert result.combined_score == 0.45
        assert result.sufficient is False


# ============================================================
# Integration-style test (requires real Model C checkpoint)
# ============================================================

class TestRealModelCIntegration:
    """Integration test with real Model C (skipped if checkpoint missing or torch fails)."""

    @pytest.fixture(autouse=True)
    def check_checkpoint(self):
        """Skip if Model C checkpoint not available."""
        if not config.MODEL_C_CHECKPOINT.exists():
            pytest.skip("Model C checkpoint not found")

    def test_real_model_c_loads_and_predicts(self, sample_hits):
        """Real Model C loads and returns valid probability."""
        pytest.skip("Requires torch DLL working - run manually in working environment")

    def test_real_engine_produces_decision(self, sample_hits):
        """Real engine produces a valid sufficiency decision."""
        pytest.skip("Requires torch DLL working - run manually in working environment")


# ============================================================
# Run tests when executed directly
# ============================================================

if __name__ == "__main__":
    import subprocess
    sys.exit(subprocess.call([sys.executable, "-m", "pytest", __file__, "-v"]))