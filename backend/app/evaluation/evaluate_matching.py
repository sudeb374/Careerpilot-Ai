"""
CareerPilot AI — Offline Matching Evaluation Runner & CLI Harness

Executes the production explainable matching engine (calculate_match_with_evidence)
against benchmark candidate-opportunity pairs, compares predicted rankings with
explicit relevance judgments, and computes standard IR metrics (Precision@K,
Recall@K, NDCG@K, MRR).

Usage:
  python -m app.evaluation.evaluate_matching --dataset ../docs/benchmarks/synthetic_smoke_fixture.json
  python -m app.evaluation.evaluate_matching --dataset ../docs/benchmarks/matching_eval_dataset.json --validate-only
"""

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from app.evaluation.dataset import (
    BenchmarkDataset,
    load_benchmark_dataset,
    spec_to_candidate_evidence,
    spec_to_opportunity_model,
    validate_benchmark_dict,
)
from app.evaluation.metrics import (
    compute_profile_metrics,
    macro_average_metrics,
)
from app.services.matching import calculate_match_with_evidence


async def evaluate_dataset(
    dataset: BenchmarkDataset,
) -> dict[str, Any]:
    """
    Evaluates the matching engine on all judged queries in the benchmark dataset.

    Returns a comprehensive dictionary containing:
    - evaluation_metadata
    - dataset_summary
    - macro_metrics
    - per_profile_results
    - excluded_profiles
    """
    # Index opportunities
    opps_by_id = {opp.id: opp for opp in dataset.opportunities}

    # Group judgments by profile
    judgments_by_profile: dict[str, dict[str, int]] = {}
    for j in dataset.judgments:
        if j.profile_id not in judgments_by_profile:
            judgments_by_profile[j.profile_id] = {}
        judgments_by_profile[j.profile_id][j.opportunity_id] = j.relevance

    per_profile_results: list[dict[str, Any]] = []
    excluded_profiles: list[dict[str, Any]] = []

    for profile in dataset.candidate_profiles:
        profile_judgments = judgments_by_profile.get(profile.id, {})
        if not profile_judgments:
            excluded_profiles.append({
                "profile_id": profile.id,
                "full_name": profile.full_name,
                "reason": "No judgments available for this candidate query.",
            })
            continue

        evidence = spec_to_candidate_evidence(profile)

        # Run production matching engine on all judged opportunities for this candidate
        scored_items: list[dict[str, Any]] = []
        for opp_id, ground_truth_rel in profile_judgments.items():
            opp_spec = opps_by_id.get(opp_id)
            if not opp_spec:
                continue

            opp_model = spec_to_opportunity_model(opp_spec)
            match_res = await calculate_match_with_evidence(opp_model, evidence)

            score_val = match_res.score if match_res.score is not None else 0.0

            scored_items.append({
                "opportunity_id": opp_id,
                "title": opp_spec.title,
                "company_name": opp_spec.company_name,
                "domain": opp_spec.domain,
                "match_score": score_val,
                "score_label": match_res.score_label,
                "data_coverage": match_res.data_coverage,
                "ground_truth_relevance": ground_truth_rel,
            })

        # Rank opportunities descending by score; deterministic tie-breaking on opportunity_id
        scored_items.sort(key=lambda item: (-item["match_score"], item["opportunity_id"]))

        ranked_relevances = [item["ground_truth_relevance"] for item in scored_items]
        all_judged_relevances = list(profile_judgments.values())

        metrics = compute_profile_metrics(ranked_relevances, all_judged_relevances)

        per_profile_results.append({
            "profile_id": profile.id,
            "full_name": profile.full_name,
            "desired_roles": profile.desired_roles,
            "metrics": metrics,
            "ranked_opportunities": scored_items,
        })

    # Macro-average across evaluated profiles
    just_metrics = [p["metrics"] for p in per_profile_results]
    macro_metrics = macro_average_metrics(just_metrics)

    eval_meta = {
        "evaluation_timestamp": datetime.now(timezone.utc).isoformat(),
        "scoring_engine": "CareerPilot Heuristic Matching Engine v1.0",
        "score_nature_disclaimer": (
            "Scores are heuristic recommendations based on profile metadata, skill overlap, "
            "and domain alignment. They are not hiring probabilities, qualification guarantees, "
            "or employer endorsements."
        ),
        "is_synthetic_fixture": (
            dataset.metadata.dataset_type == "synthetic_smoke_fixture"
            or dataset.metadata.annotation_status == "synthetic"
        ),
        "is_unverified_benchmark": (
            dataset.metadata.annotation_status in ("draft_unverified", "pending_review")
        ),
        "metric_definitions": {
            "Precision@K": "Fraction of top-K recommendations with relevance >= 1. K in [3, 5, 10].",
            "Recall@K": "Fraction of total judged relevant items in pool retrieved in top-K. K in [5, 10].",
            "NDCG@K": "Normalized Discounted Cumulative Gain with exponential gain (2^rel - 1). K in [5, 10].",
            "MRR_highly_relevant": "Mean Reciprocal Rank of the first item with relevance == 2 (primary metric).",
            "MRR_any_relevant": "Mean Reciprocal Rank of the first item with relevance >= 1 (secondary metric).",
        },
    }

    dataset_summary = {
        "dataset_version": dataset.metadata.dataset_version,
        "dataset_type": dataset.metadata.dataset_type,
        "annotation_status": dataset.metadata.annotation_status,
        "total_candidate_profiles": len(dataset.candidate_profiles),
        "total_opportunities": len(dataset.opportunities),
        "total_judgments": len(dataset.judgments),
        "evaluated_profiles_count": len(per_profile_results),
        "excluded_profiles_count": len(excluded_profiles),
    }

    return {
        "metadata": eval_meta,
        "dataset_summary": dataset_summary,
        "macro_metrics": macro_metrics,
        "per_profile_results": per_profile_results,
        "excluded_profiles": excluded_profiles,
    }


def generate_markdown_report(eval_result: dict[str, Any]) -> str:
    """Generates a structured, human-readable Markdown evaluation report."""
    meta = eval_result["metadata"]
    summary = eval_result["dataset_summary"]
    macro = eval_result["macro_metrics"]

    lines = [
        "# CareerPilot AI — Matching Evaluation Report",
        "",
        f"**Generated:** {meta['evaluation_timestamp']}  ",
        f"**Dataset Version:** `{summary['dataset_version']}` ({summary['dataset_type']})  ",
        f"**Annotation Status:** `{summary['annotation_status']}`  ",
        "",
    ]

    # Warning alert if synthetic or unverified
    if meta.get("is_synthetic_fixture"):
        lines.extend([
            "> [!WARNING]",
            "> **SYNTHETIC SMOKE-TEST FIXTURE**: This evaluation ran against a synthetic test fixture ",
            "> designed solely to verify metric formulas and edge cases. These numbers must **not** ",
            "> be cited as real-world recommendation quality or system performance.",
            "",
        ])
    elif meta.get("is_unverified_benchmark"):
        lines.extend([
            "> [!NOTE]",
            "> **DRAFT / UNVERIFIED BENCHMARK**: Ground truth judgments in this benchmark are draft ",
            "> annotations that have not yet completed multi-annotator human adjudication. Metrics ",
            "> reflect preliminary verification rather than certified production evaluation.",
            "",
        ])

    lines.extend([
        "> [!IMPORTANT]",
        "> **Heuristic Recommendation Disclaimer**: " + meta["score_nature_disclaimer"],
        "",
        "## 1. Dataset Overview",
        "",
        f"- **Candidate Profiles:** {summary['total_candidate_profiles']} ({summary['evaluated_profiles_count']} evaluated, {summary['excluded_profiles_count']} excluded)",
        f"- **Total Opportunities:** {summary['total_opportunities']}",
        f"- **Total Judgments:** {summary['total_judgments']}",
        "",
        "## 2. Macro-Averaged Retrieval Metrics",
        "",
        "| Metric | Value | Description |",
        "| :--- | :--- | :--- |",
        f"| **Precision@3** | `{macro['precision@3']:.4f}` | Relevant items (rel >= 1) in top 3 |",
        f"| **Precision@5** | `{macro['precision@5']:.4f}` | Relevant items (rel >= 1) in top 5 |",
        f"| **Precision@10** | `{macro['precision@10']:.4f}` | Relevant items (rel >= 1) in top 10 |",
        f"| **Recall@5** | `{macro['recall@5'] if macro['recall@5'] is not None else 'N/A'}` | Judged relevant pool recovered in top 5 (across {macro.get('recall@5_profile_count', 0)} queries) |",
        f"| **Recall@10** | `{macro['recall@10'] if macro['recall@10'] is not None else 'N/A'}` | Judged relevant pool recovered in top 10 (across {macro.get('recall@10_profile_count', 0)} queries) |",
        f"| **NDCG@5** | `{macro['ndcg@5']:.4f}` | Normalized DCG with exponential gain (2^rel - 1) |",
        f"| **NDCG@10** | `{macro['ndcg@10']:.4f}` | Normalized DCG with exponential gain (2^rel - 1) |",
        f"| **MRR (Highly Relevant)** | `{macro['mrr_highly_relevant']:.4f}` | Reciprocal rank of first highly relevant item (rel == 2) |",
        f"| **MRR (Any Relevant)** | `{macro['mrr_any_relevant']:.4f}` | Reciprocal rank of first relevant item (rel >= 1) |",
        "",
        "## 3. Per-Profile Breakdown",
        "",
        "| Profile ID | Candidate Name | Desired Roles | Judged | Rel / High | P@3 | P@5 | R@5 | NDCG@5 | MRR (High) |",
        "| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
    ])

    for prof in eval_result["per_profile_results"]:
        m = prof["metrics"]
        roles = ", ".join(prof["desired_roles"][:2]) or "Any"
        r5_str = f"{m['recall@5']:.2f}" if m['recall@5'] is not None else "N/A"
        lines.append(
            f"| `{prof['profile_id']}` | {prof['full_name']} | {roles} | "
            f"{m['total_judged']} | {m['total_relevant']}/{m['total_highly_relevant']} | "
            f"{m['precision@3']:.2f} | {m['precision@5']:.2f} | {r5_str} | "
            f"{m['ndcg@5']:.2f} | {m['mrr_highly_relevant']:.2f} |"
        )

    lines.append("")
    return "\n".join(lines)


async def main_async(args: argparse.Namespace) -> int:
    dataset_path = Path(args.dataset)
    if not dataset_path.exists():
        print(f"Error: Dataset file not found at '{dataset_path}'", file=sys.stderr)
        return 1

    print(f"[*] Loading dataset from {dataset_path}...")
    try:
        dataset = load_benchmark_dataset(dataset_path)
    except Exception as e:
        print(f"[!] Validation error: {e}", file=sys.stderr)
        return 1

    print(f"[+] Dataset validation passed successfully!")
    print(f"    Version: {dataset.metadata.dataset_version}")
    print(f"    Type: {dataset.metadata.dataset_type}")
    print(f"    Status: {dataset.metadata.annotation_status}")
    print(f"    Candidate Profiles: {len(dataset.candidate_profiles)}")
    print(f"    Opportunities: {len(dataset.opportunities)}")
    print(f"    Judgments: {len(dataset.judgments)}")

    if args.validate_only:
        print("[+] --validate-only specified. Exiting with success.")
        return 0

    print("[*] Running matching evaluation harness...")
    eval_result = await evaluate_dataset(dataset)

    macro = eval_result["macro_metrics"]
    print("\n" + "=" * 50)
    print("MATCHING EVALUATION RESULTS (MACRO AVERAGE)")
    print("=" * 50)
    print(f"Evaluated Profiles:    {macro['num_evaluated_profiles']}")
    print(f"Precision@3:           {macro['precision@3']:.4f}")
    print(f"Precision@5:           {macro['precision@5']:.4f}")
    print(f"Precision@10:          {macro['precision@10']:.4f}")
    print(f"Recall@5:              {macro['recall@5'] if macro['recall@5'] is not None else 'N/A'}")
    print(f"Recall@10:             {macro['recall@10'] if macro['recall@10'] is not None else 'N/A'}")
    print(f"NDCG@5:                {macro['ndcg@5']:.4f}")
    print(f"NDCG@10:               {macro['ndcg@10']:.4f}")
    print(f"MRR (Highly Relevant): {macro['mrr_highly_relevant']:.4f}")
    print(f"MRR (Any Relevant):    {macro['mrr_any_relevant']:.4f}")
    print("=" * 50 + "\n")

    # Write output reports
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    dataset_stem = dataset_path.stem
    json_path = output_dir / f"{dataset_stem}_results.json"
    md_path = output_dir / f"{dataset_stem}_results.md"

    if args.format in ("json", "both"):
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(eval_result, f, indent=2)
        print(f"[+] Saved JSON report to: {json_path}")

    if args.format in ("markdown", "both"):
        md_content = generate_markdown_report(eval_result)
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)
        print(f"[+] Saved Markdown summary to: {md_path}")

    return 0


def main():
    parser = argparse.ArgumentParser(
        description="CareerPilot AI — Offline Matching Evaluation Harness"
    )
    parser.add_argument(
        "--dataset",
        type=str,
        required=True,
        help="Path to the benchmark dataset JSON file",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Validate dataset syntax and constraints without running evaluation",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="docs/benchmarks/results",
        help="Directory to save evaluation reports (default: docs/benchmarks/results)",
    )
    parser.add_argument(
        "--format",
        type=str,
        choices=["json", "markdown", "both"],
        default="both",
        help="Output report format (default: both)",
    )

    args = parser.parse_args()
    exit_code = asyncio.run(main_async(args))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
