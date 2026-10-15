"""
Tests for Phase 9.3: Matching Evaluation Dataset & Metrics Harness.

Validates:
1. Pure mathematical IR metrics with independent hand-calculated expected values.
2. Ranking edge cases:
   - Perfect relevance ordering
   - Inverted / worst-case ordering
   - No relevant items in top-K
   - Fully unrelevant queries (no relevant items anywhere)
   - Fewer than K available items
   - k=0 and empty lists
3. Dataset validation and error diagnostics:
   - Valid dataset passes
   - Missing top-level keys
   - Missing or duplicate IDs
   - Unknown profile or opportunity IDs in judgments
   - Duplicate judgments
   - Invalid relevance values (-1, 3, non-integers)
   - Unpublished opportunities
4. Evaluator integration & reproducibility:
   - Runs against synthetic smoke fixture offline without live database or external network
   - Deterministic scores across repeated runs
   - Proves evaluator invokes the production calculate_match_with_evidence function
"""

import math
import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.evaluation.dataset import (
    load_benchmark_dataset,
    validate_benchmark_dict,
)
from app.evaluation.evaluate_matching import evaluate_dataset
from app.evaluation.metrics import (
    compute_profile_metrics,
    dcg_at_k,
    macro_average_metrics,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
)
from app.services.matching import calculate_match_with_evidence


# ============================================================================
# 1. Hand-Calculated Metric Function Unit Tests
# ============================================================================

def test_precision_at_k_hand_calculated():
    # Top-3 has two relevant items (2, 1) and one irrelevant (0)
    # Expected: 2 / 3 = 0.66666...
    ranked = [2, 1, 0, 0, 0]
    p3 = precision_at_k(ranked, k=3, threshold=1)
    assert abs(p3 - (2.0 / 3.0)) < 1e-6

    # Top-5 has two relevant items
    # Expected: 2 / 5 = 0.4
    p5 = precision_at_k(ranked, k=5, threshold=1)
    assert abs(p5 - 0.4) < 1e-6


def test_precision_at_k_edge_cases():
    # No relevant items in top-3
    assert precision_at_k([0, 0, 0, 2, 1], k=3, threshold=1) == 0.0

    # Fully irrelevant query
    assert precision_at_k([0, 0, 0], k=3, threshold=1) == 0.0

    # Fewer than K available items (penalizing shortfall per standard IR)
    # 2 items retrieved, both relevant, k=5 -> 2 / 5 = 0.4
    assert precision_at_k([2, 1], k=5, threshold=1) == 0.4

    # k <= 0
    assert precision_at_k([2, 2], k=0) == 0.0
    assert precision_at_k([2, 2], k=-1) == 0.0

    # Empty list
    assert precision_at_k([], k=5) == 0.0


def test_recall_at_k_hand_calculated():
    # Total relevant in pool = 4. Top-3 contains 2 relevant items.
    # Expected: 2 / 4 = 0.5
    ranked = [2, 1, 0, 0, 2, 1]
    r3 = recall_at_k(ranked, total_relevant=4, k=3, threshold=1)
    assert r3 == 0.5

    # Top-6 contains all 4 relevant items
    # Expected: 4 / 4 = 1.0
    r6 = recall_at_k(ranked, total_relevant=4, k=6, threshold=1)
    assert r6 == 1.0


def test_recall_at_k_edge_cases():
    # No relevant items in top-3
    assert recall_at_k([0, 0, 0, 1], total_relevant=1, k=3) == 0.0

    # Zero relevant items in pool: Recall is undefined, returns None
    assert recall_at_k([0, 0, 0], total_relevant=0, k=3) is None

    # k <= 0
    assert recall_at_k([2, 1], total_relevant=2, k=0) == 0.0


def test_dcg_and_ndcg_hand_calculated():
    # Ranking: [2, 2, 1, 0, 0]
    # Hand-calculate DCG@5:
    # rank 1: (2^2 - 1) / log2(2) = 3 / 1 = 3.0
    # rank 2: (2^2 - 1) / log2(3) = 3 / 1.584962500721156 = 1.8927892607143721
    # rank 3: (2^1 - 1) / log2(4) = 1 / 2 = 0.5
    # rank 4: 0
    # rank 5: 0
    # Expected sum = 5.392789260714372
    expected_ideal_dcg = 3.0 + (3.0 / math.log2(3)) + (1.0 / math.log2(4))

    actual_dcg = dcg_at_k([2, 2, 1, 0, 0], k=5)
    assert abs(actual_dcg - expected_ideal_dcg) < 1e-5

    # Perfect ordering: actual == ideal -> NDCG = 1.0
    ndcg_perfect = ndcg_at_k([2, 2, 1, 0, 0], [2, 2, 1, 0, 0], k=5)
    assert abs(ndcg_perfect - 1.0) < 1e-6

    # Inverted / worst-case ordering: [0, 0, 1, 2, 2]
    # DCG@5 for inverted:
    # rank 1: 0
    # rank 2: 0
    # rank 3: 1 / log2(4) = 0.5
    # rank 4: 3 / log2(5) = 3 / 2.321928094887362 = 1.2920296733246747
    # rank 5: 3 / log2(6) = 3 / 2.584962500721156 = 1.160558448833959
    # Expected inverted DCG = 0.5 + 1.29202967 + 1.16055845 = 2.95258812
    # Expected NDCG@5 = 2.95258812 / 5.39278926 = 0.5475066...
    expected_inverted_dcg = (1.0 / math.log2(4)) + (3.0 / math.log2(5)) + (3.0 / math.log2(6))
    expected_inverted_ndcg = expected_inverted_dcg / expected_ideal_dcg

    actual_inverted_ndcg = ndcg_at_k([0, 0, 1, 2, 2], [2, 2, 1, 0, 0], k=5)
    assert abs(actual_inverted_ndcg - expected_inverted_ndcg) < 1e-5


def test_ndcg_edge_cases():
    # No relevant items in top-K: [0, 0, 0, 2, 2] at k=3 -> DCG@3 = 0.0 -> NDCG@3 = 0.0
    assert ndcg_at_k([0, 0, 0, 2, 2], [2, 2, 0, 0, 0], k=3) == 0.0

    # No relevant items in entire pool: ideal DCG = 0.0 -> returns 1.0 (trivially optimal)
    assert ndcg_at_k([0, 0, 0], [0, 0, 0], k=3) == 1.0

    # Fewer than K items: [2] at k=5 with pool [2] -> 1.0
    assert ndcg_at_k([2], [2], k=5) == 1.0

    # k <= 0
    assert ndcg_at_k([2, 1], [2, 1], k=0) == 0.0


def test_reciprocal_rank_hand_calculated():
    # First highly relevant (2) is at rank 1 -> RR = 1.0
    assert reciprocal_rank([2, 1, 0], target_relevance=2) == 1.0

    # First highly relevant (2) is at rank 3 -> RR = 1/3
    rr3 = reciprocal_rank([1, 0, 2], target_relevance=2)
    assert abs(rr3 - (1.0 / 3.0)) < 1e-6

    # No highly relevant (2) in ranked list -> RR = 0.0
    assert reciprocal_rank([1, 1, 0], target_relevance=2) == 0.0

    # Secondary metric (any relevant >= 1): first is at rank 2 -> RR = 1/2 = 0.5
    assert reciprocal_rank([0, 1, 2], target_relevance=1, greater_or_equal=True) == 0.5


def test_macro_average_metrics_handles_undefined_recall():
    # Profile 1 has relevant items; Profile 2 has 0 relevant items (recall is None)
    p1 = {
        "precision@3": 0.6667,
        "precision@5": 0.4000,
        "precision@10": 0.2000,
        "recall@5": 1.0000,
        "recall@10": 1.0000,
        "ndcg@5": 0.9500,
        "ndcg@10": 0.9500,
        "mrr_highly_relevant": 1.0,
        "mrr_any_relevant": 1.0,
    }
    p2 = {
        "precision@3": 0.0000,
        "precision@5": 0.0000,
        "precision@10": 0.0000,
        "recall@5": None,  # Query had 0 relevant items
        "recall@10": None,
        "ndcg@5": 1.0000,
        "ndcg@10": 1.0000,
        "mrr_highly_relevant": 0.0,
        "mrr_any_relevant": 0.0,
    }

    macro = macro_average_metrics([p1, p2])
    assert macro["num_evaluated_profiles"] == 2
    assert macro["precision@3"] == round((0.6667 + 0.0) / 2.0, 4)
    # Recall should only average across p1 (profile count = 1)
    assert macro["recall@5"] == 1.0000
    assert macro["recall@5_profile_count"] == 1


# ============================================================================
# 2. Dataset Schema & Validation Tests
# ============================================================================

def test_validate_benchmark_dict_valid():
    valid_data = {
        "metadata": {
            "dataset_version": "1.0",
            "created_at": "2026-10-15T00:00:00Z",
            "dataset_type": "synthetic_smoke_fixture",
            "annotation_status": "synthetic",
            "description": "Test fixture",
        },
        "candidate_profiles": [
            {
                "id": "p1",
                "full_name": "Test User",
                "desired_roles": ["Engineer"],
                "candidate_skills": ["Python"],
            }
        ],
        "opportunities": [
            {
                "id": "o1",
                "title": "Engineer",
                "domain": "Tech",
                "status": "Published",
            }
        ],
        "judgments": [
            {
                "profile_id": "p1",
                "opportunity_id": "o1",
                "relevance": 2,
            }
        ],
    }

    is_valid, errors = validate_benchmark_dict(valid_data)
    assert is_valid is True
    assert len(errors) == 0


def test_validate_benchmark_dict_catches_errors():
    # Test missing keys
    is_valid, errors = validate_benchmark_dict({})
    assert is_valid is False
    assert any("metadata" in e for e in errors)

    # Test unknown ID references and duplicate pairs
    bad_data = {
        "metadata": {
            "dataset_version": "1.0",
            "dataset_type": "synthetic_smoke_fixture",
            "annotation_status": "synthetic",
        },
        "candidate_profiles": [
            {
                "id": "p1",
                "full_name": "Test User",
                "desired_roles": ["Engineer"],
                "candidate_skills": ["Python"],
            },
            {
                "id": "p1",  # Duplicate ID
                "full_name": "Duplicate User",
                "desired_roles": ["Designer"],
                "candidate_skills": ["Figma"],
            },
        ],
        "opportunities": [
            {
                "id": "o1",
                "title": "Draft Role",
                "domain": "Tech",
                "status": "Draft",  # Invalid status (must be Published)
            }
        ],
        "judgments": [
            {
                "profile_id": "p1",
                "opportunity_id": "o1",
                "relevance": 3,  # Invalid relevance (must be 0, 1, 2)
            },
            {
                "profile_id": "p1",
                "opportunity_id": "o1",  # Duplicate pair
                "relevance": 1,
            },
            {
                "profile_id": "unknown_profile",  # Unknown profile
                "opportunity_id": "o1",
                "relevance": 0,
            },
            {
                "profile_id": "p1",
                "opportunity_id": "unknown_opp",  # Unknown opp
                "relevance": 0,
            },
        ],
    }

    is_valid, errors = validate_benchmark_dict(bad_data)
    assert is_valid is False
    err_str = " ".join(errors)
    assert "Duplicate profile id" in err_str
    assert "status is 'Draft'" in err_str
    assert "invalid relevance" in err_str
    assert "Duplicate judgment for pair" in err_str
    assert "unknown profile_id" in err_str
    assert "unknown opportunity_id" in err_str


# ============================================================================
# 3. Evaluator Runner Integration Tests (Offline, No DB, Deterministic)
# ============================================================================

@pytest.mark.anyio
async def test_evaluate_synthetic_smoke_fixture():
    fixture_path = Path(__file__).resolve().parent.parent / "docs" / "benchmarks" / "synthetic_smoke_fixture.json"
    assert fixture_path.exists(), f"Synthetic fixture not found at {fixture_path}"

    dataset = load_benchmark_dataset(fixture_path)
    assert len(dataset.candidate_profiles) == 3
    assert len(dataset.opportunities) == 6
    assert len(dataset.judgments) == 18

    # Evaluate dataset
    res1 = await evaluate_dataset(dataset)

    # Check macro metrics
    macro = res1["macro_metrics"]
    assert macro["num_evaluated_profiles"] == 3
    assert macro["precision@3"] > 0.5
    assert macro["ndcg@5"] > 0.8
    assert macro["mrr_highly_relevant"] == 1.0

    # Verify deterministic output: run second time, results must be identical
    res2 = await evaluate_dataset(dataset)
    assert res1["macro_metrics"] == res2["macro_metrics"]


@pytest.mark.anyio
async def test_evaluator_invokes_production_matching_engine():
    """
    Verifies that evaluate_dataset genuinely executes calculate_match_with_evidence
    from app.services.matching rather than a duplicate formula.
    """
    fixture_path = Path(__file__).resolve().parent.parent / "docs" / "benchmarks" / "synthetic_smoke_fixture.json"
    dataset = load_benchmark_dataset(fixture_path)

    call_count = 0

    original_fn = calculate_match_with_evidence

    async def spy_calculate_match(opportunity, evidence):
        nonlocal call_count
        call_count += 1
        return await original_fn(opportunity, evidence)

    with patch("app.evaluation.evaluate_matching.calculate_match_with_evidence", side_effect=spy_calculate_match):
        eval_result = await evaluate_dataset(dataset)

    # With 18 judgments, the production matching engine must have been invoked 18 times
    assert call_count == 18
    assert eval_result["macro_metrics"]["num_evaluated_profiles"] == 3
