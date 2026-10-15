# CareerPilot AI — Matching Evaluation Benchmark & Metrics Framework

This directory contains the offline evaluation dataset schema, synthetic validation fixture, evaluation benchmark template, and documentation for measuring the ranking quality of the CareerPilot AI explainable job-matching engine.

---

## 1. Core Principles & Philosophy

### 1.1 Heuristic Recommendations vs. Hiring Probabilities
CareerPilot AI matching scores ($0 - 100$) are **heuristic recommendations** computed from transparent, rule-based and semantic criteria:
- **Required Skills:** $40\%$
- **Desired Role Alignment:** $20\%$
- **Work Model & Location:** $15\%$
- **Experience & Education:** $15\%$
- **Preferred Domain:** $10\%$

> [!IMPORTANT]
> **Matching scores are NOT hiring probabilities.**  
> A high score indicates that a candidate's recorded skills and profile preferences align with the structured requirements of an opportunity. It does **not** estimate likelihood of selection, resume competitiveness against other applicants, interview performance, employer hiring intent, or job offer probability. Evaluation metrics must never be reported as "prediction accuracy of hire".

### 1.2 Separation of Smoke Fixtures and Production Benchmarks
To guarantee scientific integrity and prevent false claims of real-world accuracy:
- **`synthetic_smoke_fixture.json`**: A small, deterministic, hand-crafted dataset used exclusively for automated regression testing of metric formulas and edge cases.
- **`matching_eval_dataset.json`**: The benchmark dataset template covering 15 standardized candidate archetypes and 50 realistic entry-level opportunities. Judgments are explicitly marked as `draft_unverified` until multi-annotator human adjudication is completed.

---

## 2. Dataset Schema & Structure

Both datasets adhere to the JSON schema validated by `app.evaluation.dataset.validate_benchmark_dict`:

```json
{
  "metadata": {
    "dataset_version": "1.0.0-draft",
    "created_at": "2026-10-15T12:00:00Z",
    "dataset_type": "benchmark_template",
    "annotation_status": "draft_unverified",
    "description": "Dataset description...",
    "relevance_scale": {
      "0": "Not relevant...",
      "1": "Partially relevant...",
      "2": "Highly relevant..."
    },
    "annotators": ["annotator_1", "annotator_2"]
  },
  "candidate_profiles": [
    {
      "id": "cand_archetype_01",
      "full_name": "Aarav Sharma (Frontend Web)",
      "desired_roles": ["Frontend Engineer", "UI Developer"],
      "candidate_skills": ["React", "TypeScript", "TailwindCSS"],
      "work_model": ["Remote", "Hybrid"],
      "locations": ["Bangalore", "Remote"],
      "preferred_domains": ["Technology", "SaaS"],
      "years_exp": 1.0,
      "education_text": ["B.Tech in Computer Science"],
      "notes": "Candidate profile notes..."
    }
  ],
  "opportunities": [
    {
      "id": "opp_eval_01",
      "title": "Junior React Developer",
      "company_name": "PixelCraft Technologies",
      "domain": "Technology",
      "opportunity_type": "Full-time",
      "work_model": "Remote",
      "locations": ["Bangalore", "Remote"],
      "required_skills": ["React", "TypeScript", "TailwindCSS"],
      "required_experience_min": 0.5,
      "required_experience_max": 2.0,
      "education_requirements": "B.Tech in CS/IT",
      "status": "Published"
    }
  ],
  "judgments": [
    {
      "profile_id": "cand_archetype_01",
      "opportunity_id": "opp_eval_01",
      "relevance": 2,
      "annotator_1": 2,
      "annotator_2": null,
      "adjudicated": false,
      "evidence": "Direct role match, 100% skill overlap, remote model aligns."
    }
  ]
}
```

---

## 3. Graded Relevance Scale & Annotation Guidelines

Relevance judgments use an explicit 3-point graded scale ($0, 1, 2$):

| Grade | Label | Operational Definition & Criteria | Example |
| :---: | :--- | :--- | :--- |
| **`2`** | **Highly Relevant** | Target role title aligns closely with candidate's desired roles; candidate satisfies core required skills ($\ge 75\%$ overlap); work model and location match candidate preferences; candidate meets experience thresholds. | Frontend React graduate matched with Junior React Developer (Remote). |
| **`1`** | **Partially Relevant** | Adjacent role title or transferable engineering domain; partial skill overlap ($25\% - 74\%$); minor negotiable preference gap (e.g. candidate prefers Remote, job is Hybrid in candidate's city); or candidate slightly below preferred experience. | React frontend candidate matched with Full Stack Web Developer (Node/React). |
| **`0`** | **Not Relevant** | Fundamental discipline mismatch (e.g., UI Designer vs C++ Embedded Engineer); disjoint required skills; hard experience barrier (e.g., 5+ years required for fresher); or incompatible on-site location in a distant city. | React frontend candidate matched with Senior Embedded C++ Engineer. |

### Annotation Integrity Rules:
1. **No Circularity:** Never use CareerPilot AI matching scores to establish ground-truth relevance labels. Labels must be independently derived from objective job requirements and candidate profiles.
2. **Missing Profile Data:** If candidate profile lacks preferred domains or work models, evaluate relevance based purely on demonstrated skills, education, and role alignment without penalizing unstated preferences.
3. **Ambiguous Titles:** Evaluate against the job's actual required skills and description rather than relying solely on non-standard recruiter titles (e.g., "Member of Technical Staff").
4. **Double Annotation:** Final production benchmarks require two independent human annotators. Any disagreement ($|a_1 - a_2| > 0$) must be resolved through documented consensus adjudication.

---

## 4. Evaluation Metrics & Formulations

The offline metrics harness computes standard Information Retrieval (IR) metrics macro-averaged across evaluated candidate queries:

### 4.1 Precision@K ($K \in \{3, 5, 10\}$)
Measures the proportion of top-$K$ recommended opportunities that are relevant ($rel \ge 1$):
$$\text{Precision@K} = \frac{\sum_{i=1}^{\min(K, m)} \mathbb{I}(r_i \ge 1)}{K}$$
- **Shortfall Policy:** When fewer than $K$ opportunities are available in the candidate's pool, the denominator remains $K$, strictly penalizing insufficient retrieval.

### 4.2 Recall@K ($K \in \{5, 10\}$)
Measures the fraction of all known relevant items ($rel \ge 1$) in the candidate's judged pool that are retrieved in the top-$K$:
$$\text{Recall@K} = \frac{\sum_{i=1}^{\min(K, m)} \mathbb{I}(r_i \ge 1)}{R}$$
- **Zero-Relevant Policy:** If a query has $R = 0$ relevant items in its judged pool, Recall is mathematically undefined. Such queries are excluded from macro Recall averaging and reported separately with an explicit candidate count.

### 4.3 Normalized Discounted Cumulative Gain (NDCG@K, $K \in \{5, 10\}$)
Measures graded ranking quality, heavily rewarding placing highly relevant items ($rel=2$) above partially relevant ($rel=1$) and irrelevant items ($rel=0$):
$$\text{gain}(r_i) = 2^{r_i} - 1, \quad \text{discount}(i) = \log_2(i + 1)$$
$$\text{DCG@K} = \sum_{i=1}^{\min(K, m)} \frac{2^{r_i} - 1}{\log_2(i + 1)}$$
$$\text{NDCG@K} = \frac{\text{DCG@K}}{\text{IDCG@K}}$$
where $\text{IDCG@K}$ is the maximum possible DCG obtained by sorting all judged items in descending order of relevance. If $\text{IDCG@K} = 0$, $\text{NDCG@K}$ is defined as $1.0$.

### 4.4 Mean Reciprocal Rank (MRR)
- **Primary MRR ($\text{MRR}_{\text{high}}$):** Reciprocal rank $\frac{1}{\text{rank}}$ of the **first highly relevant item** ($rel = 2$). If no item with $rel = 2$ is retrieved, score is $0.0$.
- **Secondary MRR ($\text{MRR}_{\text{any}}$):** Reciprocal rank of the **first relevant item** ($rel \ge 1$).

---

## 5. How to Run Evaluations

All evaluation tools are completely offline, deterministic, and require no running database or external APIs.

### 5.1 Run Smoke-Test Metric Validation
```bash
cd backend
python -m app.evaluation.evaluate_matching \
  --dataset ../docs/benchmarks/synthetic_smoke_fixture.json \
  --output-dir ../docs/benchmarks/results
```

### 5.2 Validate Benchmark Dataset Syntax Only
```bash
python -m app.evaluation.evaluate_matching \
  --dataset ../docs/benchmarks/matching_eval_dataset.json \
  --validate-only
```

### 5.3 Run Benchmark Evaluation
```bash
python -m app.evaluation.evaluate_matching \
  --dataset ../docs/benchmarks/matching_eval_dataset.json \
  --output-dir ../docs/benchmarks/results \
  --format both
```

Generated reports are written to:
- `docs/benchmarks/results/<dataset_name>_results.json` (Machine-readable)
- `docs/benchmarks/results/<dataset_name>_results.md` (Human-readable summary)

---

## 6. Limitations, Threats to Validity & Future Requirements

Before any metrics can be published as certified evidence of real-world matching performance, the following requirements must be satisfied:

1. **Multi-Annotator Human Adjudication:**
   - Current labels in `matching_eval_dataset.json` are draft templates.
   - At least 2 qualified human annotators (e.g. career advisors or technical hiring managers) must independently annotate all candidate-opportunity pairs.
   - Inter-annotator agreement (Cohen's or Fleiss' Kappa) must be reported.
2. **Incomplete Job Pool Bias:**
   - In offline evaluation, candidates are scored only against judged opportunities. In production, candidates are scored across the entire database. Expanding the candidate's retrieval pool to include unjudged distractors is necessary for large-scale retrieval testing.
3. **Evaluation Leakage Prevention:**
   - Candidate archetypes and benchmark opportunities must remain strictly isolated from any heuristic rule tuning or prompt engineering.
4. **Candidate Privacy:**
   - No personal candidate data, real contact details, or proprietary employer postings are stored in version control. All candidate profiles represent generalized student archetypes.
