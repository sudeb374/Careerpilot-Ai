# CareerPilot AI — Matching Evaluation Report

**Generated:** 2026-10-15T07:10:46.411771+00:00  
**Dataset Version:** `1.0.0-smoke` (synthetic_smoke_fixture)  
**Annotation Status:** `synthetic`  

> [!WARNING]
> **SYNTHETIC SMOKE-TEST FIXTURE**: This evaluation ran against a synthetic test fixture 
> designed solely to verify metric formulas and edge cases. These numbers must **not** 
> be cited as real-world recommendation quality or system performance.

> [!IMPORTANT]
> **Heuristic Recommendation Disclaimer**: Scores are heuristic recommendations based on profile metadata, skill overlap, and domain alignment. They are not hiring probabilities, qualification guarantees, or employer endorsements.

## 1. Dataset Overview

- **Candidate Profiles:** 3 (3 evaluated, 0 excluded)
- **Total Opportunities:** 6
- **Total Judgments:** 18

## 2. Macro-Averaged Retrieval Metrics

| Metric | Value | Description |
| :--- | :--- | :--- |
| **Precision@3** | `0.6667` | Relevant items (rel >= 1) in top 3 |
| **Precision@5** | `0.4667` | Relevant items (rel >= 1) in top 5 |
| **Precision@10** | `0.2333` | Relevant items (rel >= 1) in top 10 |
| **Recall@5** | `1.0` | Judged relevant pool recovered in top 5 (across 3 queries) |
| **Recall@10** | `1.0` | Judged relevant pool recovered in top 10 (across 3 queries) |
| **NDCG@5** | `0.9944` | Normalized DCG with exponential gain (2^rel - 1) |
| **NDCG@10** | `0.9944` | Normalized DCG with exponential gain (2^rel - 1) |
| **MRR (Highly Relevant)** | `1.0000` | Reciprocal rank of first highly relevant item (rel == 2) |
| **MRR (Any Relevant)** | `1.0000` | Reciprocal rank of first relevant item (rel >= 1) |

## 3. Per-Profile Breakdown

| Profile ID | Candidate Name | Desired Roles | Judged | Rel / High | P@3 | P@5 | R@5 | NDCG@5 | MRR (High) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `cand_smoke_01` | Alex Rivera (Frontend Archetype) | Frontend Engineer, UI Developer | 6 | 2/1 | 0.67 | 0.40 | 1.00 | 1.00 | 1.00 |
| `cand_smoke_02` | Maya Chen (Data Science Archetype) | Data Scientist, Data Analyst | 6 | 3/1 | 0.67 | 0.60 | 1.00 | 0.98 | 1.00 |
| `cand_smoke_03` | Jordan Lee (Product Management Archetype) | Associate Product Manager, Product Analyst | 6 | 2/1 | 0.67 | 0.40 | 1.00 | 1.00 | 1.00 |
