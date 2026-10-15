"""
CareerPilot AI — Matching Evaluation Package

Provides offline dataset validation, metrics computation (Precision@K, Recall@K,
NDCG@K, MRR), and an evaluation harness for the job recommendation engine.
"""

from app.evaluation.metrics import (
    precision_at_k,
    recall_at_k,
    dcg_at_k,
    ndcg_at_k,
    reciprocal_rank,
    compute_profile_metrics,
    macro_average_metrics,
)

__all__ = [
    "precision_at_k",
    "recall_at_k",
    "dcg_at_k",
    "ndcg_at_k",
    "reciprocal_rank",
    "compute_profile_metrics",
    "macro_average_metrics",
]
