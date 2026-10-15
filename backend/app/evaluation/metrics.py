"""
CareerPilot AI — Recommendation Evaluation Metrics

Offline implementation of standard Information Retrieval (IR) metrics:
- Precision@K (K = 3, 5, 10)
- Recall@K (K = 5, 10)
- Normalized Discounted Cumulative Gain (NDCG@K with gain = 2^rel - 1)
- Mean Reciprocal Rank (MRR: primary on first highly relevant item, secondary on any relevant item)

All functions are purely mathematical, deterministic, and free of external network dependencies.
"""

import math
from typing import Optional


def precision_at_k(ranked_relevances: list[int], k: int, threshold: int = 1) -> float:
    """
    Calculate Precision@K.

    Precision@K is the proportion of recommended items in the top-K positions
    that are relevant (relevance >= threshold).

    Parameters:
    - ranked_relevances: Ground-truth relevance scores of items sorted by model ranking.
    - k: Cutoff rank (e.g., 3, 5, 10). Must be > 0.
    - threshold: Minimum score to consider an item relevant (default: 1).

    Edge Cases:
    - If k <= 0: returns 0.0.
    - If fewer than k items are ranked: denominator remains k (penalizing shortfall per standard IR).
    """
    if k <= 0:
        return 0.0

    top_k = ranked_relevances[:k]
    relevant_count = sum(1 for r in top_k if r >= threshold)
    return relevant_count / float(k)


def recall_at_k(
    ranked_relevances: list[int],
    total_relevant: int,
    k: int,
    threshold: int = 1,
) -> Optional[float]:
    """
    Calculate Recall@K.

    Recall@K is the proportion of all relevant items in the query's judged pool
    that appear within the top-K recommendations.

    Parameters:
    - ranked_relevances: Ground-truth relevance scores of items sorted by model ranking.
    - total_relevant: Total count of relevant items (relevance >= threshold) in the judged pool.
    - k: Cutoff rank.
    - threshold: Minimum score to consider an item relevant (default: 1).

    Edge Cases:
    - If total_relevant == 0: returns None (undefined/not applicable, excluded from macro-average).
    - If k <= 0: returns 0.0.
    """
    if total_relevant <= 0:
        return None
    if k <= 0:
        return 0.0

    top_k = ranked_relevances[:k]
    retrieved_relevant = sum(1 for r in top_k if r >= threshold)
    return min(1.0, retrieved_relevant / float(total_relevant))


def dcg_at_k(ranked_relevances: list[int], k: int) -> float:
    """
    Compute Discounted Cumulative Gain (DCG@K) using standard exponential gain:
    gain(rel) = 2^rel - 1
    discount(i) = log2(i + 1) for 1-indexed position i.
    """
    if k <= 0:
        return 0.0

    dcg = 0.0
    for i, rel in enumerate(ranked_relevances[:k], start=1):
        gain = float(2**rel - 1)
        discount = math.log2(i + 1)
        dcg += gain / discount
    return dcg


def ndcg_at_k(
    ranked_relevances: list[int],
    all_judged_relevances: list[int],
    k: int,
) -> float:
    """
    Calculate Normalized Discounted Cumulative Gain (NDCG@K).

    Parameters:
    - ranked_relevances: Relevance labels of items in predicted model order.
    - all_judged_relevances: All judged relevance scores for the candidate query.
    - k: Cutoff rank.

    Edge Cases:
    - If ideal DCG (IDCG@K) == 0.0 (no relevant items in ground truth pool):
      returns 1.0 (ranking is trivially optimal when nothing relevant exists).
    - If k <= 0: returns 0.0.
    """
    if k <= 0:
        return 0.0

    actual_dcg = dcg_at_k(ranked_relevances, k)
    ideal_relevances = sorted(all_judged_relevances, reverse=True)
    ideal_dcg = dcg_at_k(ideal_relevances, k)

    if ideal_dcg == 0.0:
        return 1.0

    return min(1.0, max(0.0, actual_dcg / ideal_dcg))


def reciprocal_rank(
    ranked_relevances: list[int],
    target_relevance: int = 2,
    greater_or_equal: bool = False,
) -> float:
    """
    Calculate Reciprocal Rank (RR).

    Parameters:
    - ranked_relevances: Relevance labels of items in predicted model order.
    - target_relevance: The relevance value defining the target hit.
    - greater_or_equal: If True, matches any r >= target_relevance.
                        If False, matches r == target_relevance.

    Primary metric uses target_relevance=2, greater_or_equal=False
    (first highly relevant item).
    """
    for rank, rel in enumerate(ranked_relevances, start=1):
        is_hit = (rel >= target_relevance) if greater_or_equal else (rel == target_relevance)
        if is_hit:
            return 1.0 / float(rank)
    return 0.0


def compute_profile_metrics(
    ranked_relevances: list[int],
    all_judged_relevances: list[int],
) -> dict:
    """
    Computes all standard evaluation metrics for a single candidate profile.

    Returns a dictionary of metrics:
    - precision@3, precision@5, precision@10
    - recall@5, recall@10
    - ndcg@5, ndcg@10
    - mrr_highly_relevant (primary: rank of first rel == 2)
    - mrr_any_relevant (secondary: rank of first rel >= 1)
    - total_judged_count
    - total_relevant_count
    - total_highly_relevant_count
    """
    total_relevant = sum(1 for r in all_judged_relevances if r >= 1)
    total_highly_relevant = sum(1 for r in all_judged_relevances if r == 2)

    return {
        "precision@3": round(precision_at_k(ranked_relevances, k=3, threshold=1), 4),
        "precision@5": round(precision_at_k(ranked_relevances, k=5, threshold=1), 4),
        "precision@10": round(precision_at_k(ranked_relevances, k=10, threshold=1), 4),
        "recall@5": (
            round(recall_at_k(ranked_relevances, total_relevant, k=5, threshold=1), 4)
            if total_relevant > 0
            else None
        ),
        "recall@10": (
            round(recall_at_k(ranked_relevances, total_relevant, k=10, threshold=1), 4)
            if total_relevant > 0
            else None
        ),
        "ndcg@5": round(ndcg_at_k(ranked_relevances, all_judged_relevances, k=5), 4),
        "ndcg@10": round(ndcg_at_k(ranked_relevances, all_judged_relevances, k=10), 4),
        "mrr_highly_relevant": round(
            reciprocal_rank(ranked_relevances, target_relevance=2, greater_or_equal=False), 4
        ),
        "mrr_any_relevant": round(
            reciprocal_rank(ranked_relevances, target_relevance=1, greater_or_equal=True), 4
        ),
        "total_judged": len(all_judged_relevances),
        "total_relevant": total_relevant,
        "total_highly_relevant": total_highly_relevant,
    }


def macro_average_metrics(per_profile_metrics: list[dict]) -> dict:
    """
    Computes macro-averaged metrics across all evaluated candidate queries.

    Handles queries with zero relevant items by averaging Recall only across
    profiles where Recall is defined (reporting the number of included profiles).
    """
    if not per_profile_metrics:
        return {
            "num_evaluated_profiles": 0,
            "precision@3": 0.0,
            "precision@5": 0.0,
            "precision@10": 0.0,
            "recall@5": None,
            "recall@10": None,
            "ndcg@5": 0.0,
            "ndcg@10": 0.0,
            "mrr_highly_relevant": 0.0,
            "mrr_any_relevant": 0.0,
        }

    n = len(per_profile_metrics)

    def avg_metric(key: str) -> float:
        values = [m[key] for m in per_profile_metrics if m[key] is not None]
        return round(sum(values) / len(values), 4) if values else 0.0

    def avg_optional_metric(key: str) -> tuple[Optional[float], int]:
        values = [m[key] for m in per_profile_metrics if m.get(key) is not None]
        if not values:
            return None, 0
        return round(sum(values) / len(values), 4), len(values)

    rec_5, rec_5_count = avg_optional_metric("recall@5")
    rec_10, rec_10_count = avg_optional_metric("recall@10")

    return {
        "num_evaluated_profiles": n,
        "precision@3": avg_metric("precision@3"),
        "precision@5": avg_metric("precision@5"),
        "precision@10": avg_metric("precision@10"),
        "recall@5": rec_5,
        "recall@5_profile_count": rec_5_count,
        "recall@10": rec_10,
        "recall@10_profile_count": rec_10_count,
        "ndcg@5": avg_metric("ndcg@5"),
        "ndcg@10": avg_metric("ndcg@10"),
        "mrr_highly_relevant": avg_metric("mrr_highly_relevant"),
        "mrr_any_relevant": avg_metric("mrr_any_relevant"),
    }
