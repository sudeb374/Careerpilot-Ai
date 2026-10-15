# CareerPilot AI — Matching Evaluation Report

**Generated:** 2026-10-15T07:51:24.648932+00:00  
**Dataset Version:** `1.0.0-draft` (benchmark_template)  
**Annotation Status:** `draft_unverified`  

> [!NOTE]
> **DRAFT / UNVERIFIED BENCHMARK**: Ground truth judgments in this benchmark are draft 
> annotations that have not yet completed multi-annotator human adjudication. Metrics 
> reflect preliminary verification rather than certified production evaluation.

> [!IMPORTANT]
> **Heuristic Recommendation Disclaimer**: Scores are heuristic recommendations based on profile metadata, skill overlap, and domain alignment. They are not hiring probabilities, qualification guarantees, or employer endorsements.

## 1. Dataset Overview

- **Candidate Profiles:** 15 (15 evaluated, 0 excluded)
- **Total Opportunities:** 50
- **Total Judgments:** 96

## 2. Macro-Averaged Retrieval Metrics

| Metric | Value | Description |
| :--- | :--- | :--- |
| **Precision@3** | `1.0000` | Relevant items (rel >= 1) in top 3 |
| **Precision@5** | `0.8400` | Relevant items (rel >= 1) in top 5 |
| **Precision@10** | `0.4600` | Relevant items (rel >= 1) in top 10 |
| **Recall@5** | `0.9276` | Judged relevant pool recovered in top 5 (across 15 queries) |
| **Recall@10** | `1.0` | Judged relevant pool recovered in top 10 (across 15 queries) |
| **NDCG@5** | `0.9736` | Normalized DCG with exponential gain (2^rel - 1) |
| **NDCG@10** | `0.9925` | Normalized DCG with exponential gain (2^rel - 1) |
| **MRR (Highly Relevant)** | `1.0000` | Reciprocal rank of first highly relevant item (rel == 2) |
| **MRR (Any Relevant)** | `1.0000` | Reciprocal rank of first relevant item (rel >= 1) |

## 3. Per-Profile Breakdown

| Profile ID | Candidate Name | Desired Roles | Judged | Rel / High | P@3 | P@5 | R@5 | NDCG@5 | MRR (High) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `cand_archetype_01` | Aarav Sharma (Frontend Web) | Frontend Engineer, UI Developer | 8 | 5/3 | 1.00 | 1.00 | 1.00 | 0.98 | 1.00 |
| `cand_archetype_02` | Priya Patel (Backend Go) | Backend Developer, Golang Engineer | 8 | 7/5 | 1.00 | 1.00 | 0.71 | 0.86 | 1.00 |
| `cand_archetype_03` | Rohan Gupta (Python/Django Backend) | Python Developer, Backend Engineer | 7 | 5/3 | 1.00 | 1.00 | 1.00 | 0.98 | 1.00 |
| `cand_archetype_04` | Ananya Sen (Full Stack TypeScript) | Full Stack Engineer, Software Engineer | 6 | 4/2 | 1.00 | 0.80 | 1.00 | 1.00 | 1.00 |
| `cand_archetype_05` | Vikram Nair (Mobile App) | Mobile Developer, Flutter Developer | 5 | 3/2 | 1.00 | 0.60 | 1.00 | 1.00 | 1.00 |
| `cand_archetype_06` | Sneha Roy (Data Analytics Fresher) | Data Analyst, Business Intelligence Analyst | 7 | 5/3 | 1.00 | 0.80 | 0.80 | 0.95 | 1.00 |
| `cand_archetype_07` | Kavya Menon (Data Science & ML) | Data Scientist, Machine Learning Engineer | 6 | 5/3 | 1.00 | 0.80 | 0.80 | 0.95 | 1.00 |
| `cand_archetype_08` | Aditya Verma (AI/NLP Specialist) | NLP Engineer, AI Engineer | 6 | 4/2 | 1.00 | 0.80 | 1.00 | 1.00 | 1.00 |
| `cand_archetype_09` | Deepak Joshi (Data Engineering) | Data Engineer, ETL Developer | 6 | 4/2 | 1.00 | 0.80 | 1.00 | 1.00 | 1.00 |
| `cand_archetype_10` | Siddharth Rao (DevOps & Cloud) | DevOps Engineer, Cloud Engineer | 6 | 5/3 | 1.00 | 0.80 | 0.80 | 0.95 | 1.00 |
| `cand_archetype_11` | Neha Kulkarni (Cybersecurity Intern) | Security Analyst, Information Security Intern | 6 | 4/3 | 1.00 | 0.80 | 1.00 | 1.00 | 1.00 |
| `cand_archetype_12` | Arjun Das (QA & Test Automation) | QA Automation Engineer, Software Test Engineer | 6 | 4/3 | 1.00 | 0.80 | 1.00 | 1.00 | 1.00 |
| `cand_archetype_13` | Tanvi Kapoor (UI/UX Design) | UI/UX Designer, Product Designer | 6 | 5/3 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| `cand_archetype_14` | Karthik Reddy (Product Management) | Associate Product Manager, Product Analyst | 6 | 5/3 | 1.00 | 0.80 | 0.80 | 0.95 | 1.00 |
| `cand_archetype_15` | Varun Mehta (Embedded & Systems) | Embedded Software Engineer, Firmware Engineer | 7 | 4/4 | 1.00 | 0.80 | 1.00 | 1.00 | 1.00 |
