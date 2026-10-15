"""
CareerPilot AI — Matching Evaluation Dataset Validation & Adapters

Provides schema definitions, data validation, and adapters to convert
benchmark JSON datasets into production CandidateEvidence and Opportunity
model objects for offline matching evaluation.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional
from uuid import UUID, uuid5, NAMESPACE_DNS

from app.models.opportunity import Opportunity, OpportunitySkill
from app.models.profile import Skill
from app.services.matching import CandidateEvidence, normalize_text


def deterministic_skill_id(skill_name: str) -> str:
    """Derive a stable UUID string for a skill based on its normalized name."""
    norm = normalize_text(skill_name)
    return str(uuid5(NAMESPACE_DNS, f"careerpilot.skill.{norm}"))


@dataclass
class DatasetMetadata:
    dataset_version: str
    created_at: str
    dataset_type: str  # "synthetic_smoke_fixture" | "benchmark_template" | "adjudicated_benchmark"
    annotation_status: str  # "synthetic" | "draft_unverified" | "validated"
    description: str
    relevance_scale: dict[str, str] = field(
        default_factory=lambda: {
            "0": "Not relevant — critical skill, domain, role, or experience mismatch",
            "1": "Partially relevant — adjacent role, partial skill match, or negotiable fit",
            "2": "Highly relevant — strong skill match, aligned role, domain, and experience",
        }
    )
    annotators: list[str] = field(default_factory=list)


@dataclass
class CandidateProfileSpec:
    id: str
    full_name: str
    desired_roles: list[str]
    candidate_skills: list[str]
    work_model: list[str] = field(default_factory=list)
    locations: list[str] = field(default_factory=list)
    preferred_domains: list[str] = field(default_factory=list)
    years_exp: float = 0.0
    education_text: list[str] = field(default_factory=list)
    notes: Optional[str] = None


@dataclass
class OpportunitySpec:
    id: str
    title: str
    company_name: str
    domain: str
    opportunity_type: str  # "Full-time" | "Internship"
    work_model: str  # "Remote" | "Hybrid" | "On-site"
    locations: list[str] = field(default_factory=list)
    required_skills: list[str] = field(default_factory=list)
    required_experience_min: Optional[float] = 0.0
    required_experience_max: Optional[float] = None
    education_requirements: Optional[str] = None
    status: str = "Published"
    notes: Optional[str] = None


@dataclass
class RelevanceJudgment:
    profile_id: str
    opportunity_id: str
    relevance: int  # 0, 1, or 2
    annotator_1: Optional[int] = None
    annotator_2: Optional[int] = None
    adjudicated: bool = False
    evidence: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class BenchmarkDataset:
    metadata: DatasetMetadata
    candidate_profiles: list[CandidateProfileSpec]
    opportunities: list[OpportunitySpec]
    judgments: list[RelevanceJudgment]


def validate_benchmark_dict(data: dict[str, Any]) -> tuple[bool, list[str]]:
    """
    Validates the structure, integrity, and constraints of a benchmark dataset dictionary.

    Returns:
    - (is_valid, error_messages)
    """
    errors: list[str] = []

    # 1. Root structure
    required_keys = ["metadata", "candidate_profiles", "opportunities", "judgments"]
    for key in required_keys:
        if key not in data:
            errors.append(f"Missing required top-level key: '{key}'")

    if errors:
        return False, errors

    # 2. Metadata validation
    meta = data.get("metadata", {})
    if not meta.get("dataset_version"):
        errors.append("metadata.dataset_version is missing or empty")
    if not meta.get("dataset_type"):
        errors.append("metadata.dataset_type is missing or empty")
    if not meta.get("annotation_status"):
        errors.append("metadata.annotation_status is missing or empty")

    # 3. Candidate Profiles validation
    profiles = data.get("candidate_profiles", [])
    if not isinstance(profiles, list) or len(profiles) == 0:
        errors.append("candidate_profiles must be a non-empty list")

    profile_ids: set[str] = set()
    for idx, prof in enumerate(profiles):
        pid = prof.get("id")
        if not pid or not isinstance(pid, str):
            errors.append(f"Profile at index {idx} has missing or non-string 'id'")
        elif pid in profile_ids:
            errors.append(f"Duplicate profile id: '{pid}'")
        else:
            profile_ids.add(pid)

        if not prof.get("full_name"):
            errors.append(f"Profile '{pid or idx}' missing 'full_name'")
        if not isinstance(prof.get("desired_roles"), list):
            errors.append(f"Profile '{pid or idx}' desired_roles must be a list")
        if not isinstance(prof.get("candidate_skills"), list):
            errors.append(f"Profile '{pid or idx}' candidate_skills must be a list")

    # 4. Opportunities validation
    opportunities = data.get("opportunities", [])
    if not isinstance(opportunities, list) or len(opportunities) == 0:
        errors.append("opportunities must be a non-empty list")

    opp_ids: set[str] = set()
    for idx, opp in enumerate(opportunities):
        oid = opp.get("id")
        if not oid or not isinstance(oid, str):
            errors.append(f"Opportunity at index {idx} has missing or non-string 'id'")
        elif oid in opp_ids:
            errors.append(f"Duplicate opportunity id: '{oid}'")
        else:
            opp_ids.add(oid)

        if not opp.get("title"):
            errors.append(f"Opportunity '{oid or idx}' missing 'title'")
        if not opp.get("domain"):
            errors.append(f"Opportunity '{oid or idx}' missing 'domain'")
        if opp.get("status") != "Published":
            errors.append(f"Opportunity '{oid or idx}' status is '{opp.get('status')}'; matching requires 'Published'")

    # 5. Judgments validation
    judgments = data.get("judgments", [])
    if not isinstance(judgments, list) or len(judgments) == 0:
        errors.append("judgments must be a non-empty list")

    seen_pairs: set[tuple[str, str]] = set()
    for idx, j in enumerate(judgments):
        pid = j.get("profile_id")
        oid = j.get("opportunity_id")
        rel = j.get("relevance")

        if not pid or pid not in profile_ids:
            errors.append(f"Judgment at index {idx} references unknown profile_id: '{pid}'")
        if not oid or oid not in opp_ids:
            errors.append(f"Judgment at index {idx} references unknown opportunity_id: '{oid}'")

        if pid and oid:
            pair = (pid, oid)
            if pair in seen_pairs:
                errors.append(f"Duplicate judgment for pair ({pid}, {oid})")
            seen_pairs.add(pair)

        if rel is None or not isinstance(rel, int) or rel not in (0, 1, 2):
            errors.append(
                f"Judgment for pair ({pid}, {oid}) has invalid relevance: '{rel}'. Must be integer 0, 1, or 2."
            )

        # Multi-annotator consistency checks
        a1 = j.get("annotator_1")
        a2 = j.get("annotator_2")
        if a1 is not None and (not isinstance(a1, int) or a1 not in (0, 1, 2)):
            errors.append(f"Judgment ({pid}, {oid}) has invalid annotator_1 value: {a1}")
        if a2 is not None and (not isinstance(a2, int) or a2 not in (0, 1, 2)):
            errors.append(f"Judgment ({pid}, {oid}) has invalid annotator_2 value: {a2}")

    return len(errors) == 0, errors


def load_benchmark_dataset(file_path: str | Path) -> BenchmarkDataset:
    """
    Loads and validates a benchmark dataset from a JSON file.
    Raises ValueError with descriptive diagnostics if validation fails.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Dataset file not found: {path}")

    try:
        with open(path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Malformed JSON in dataset file '{path}': {e}") from e

    is_valid, errors = validate_benchmark_dict(raw_data)
    if not is_valid:
        error_summary = "\n  - " + "\n  - ".join(errors[:20])
        if len(errors) > 20:
            error_summary += f"\n  ... and {len(errors) - 20} more errors."
        raise ValueError(f"Dataset validation failed for '{path}':{error_summary}")

    # Build typed objects
    meta_dict = raw_data["metadata"]
    metadata = DatasetMetadata(
        dataset_version=meta_dict["dataset_version"],
        created_at=meta_dict["created_at"],
        dataset_type=meta_dict["dataset_type"],
        annotation_status=meta_dict["annotation_status"],
        description=meta_dict["description"],
        relevance_scale=meta_dict.get("relevance_scale", {}),
        annotators=meta_dict.get("annotators", []),
    )

    profiles = [
        CandidateProfileSpec(
            id=p["id"],
            full_name=p["full_name"],
            desired_roles=p.get("desired_roles", []),
            candidate_skills=p.get("candidate_skills", []),
            work_model=p.get("work_model", []),
            locations=p.get("locations", []),
            preferred_domains=p.get("preferred_domains", []),
            years_exp=float(p.get("years_exp", 0.0)),
            education_text=p.get("education_text", []),
            notes=p.get("notes"),
        )
        for p in raw_data["candidate_profiles"]
    ]

    opportunities = [
        OpportunitySpec(
            id=o["id"],
            title=o["title"],
            company_name=o.get("company_name", "Test Company"),
            domain=o["domain"],
            opportunity_type=o.get("opportunity_type", "Full-time"),
            work_model=o.get("work_model", "Remote"),
            locations=o.get("locations", []),
            required_skills=o.get("required_skills", []),
            required_experience_min=o.get("required_experience_min", 0.0),
            required_experience_max=o.get("required_experience_max"),
            education_requirements=o.get("education_requirements"),
            status=o.get("status", "Published"),
            notes=o.get("notes"),
        )
        for o in raw_data["opportunities"]
    ]

    judgments = [
        RelevanceJudgment(
            profile_id=j["profile_id"],
            opportunity_id=j["opportunity_id"],
            relevance=j["relevance"],
            annotator_1=j.get("annotator_1"),
            annotator_2=j.get("annotator_2"),
            adjudicated=bool(j.get("adjudicated", False)),
            evidence=j.get("evidence"),
            notes=j.get("notes"),
        )
        for j in raw_data["judgments"]
    ]

    return BenchmarkDataset(
        metadata=metadata,
        candidate_profiles=profiles,
        opportunities=opportunities,
        judgments=judgments,
    )


# ============================================================================
# Matching Engine Adapters
# ============================================================================

def spec_to_candidate_evidence(profile: CandidateProfileSpec) -> CandidateEvidence:
    """
    Converts a CandidateProfileSpec into production CandidateEvidence.
    Uses deterministic skill IDs derived from normalized skill names.
    """
    skill_ids = {deterministic_skill_id(s) for s in profile.candidate_skills}

    return CandidateEvidence(
        candidate_skill_ids=skill_ids,
        desired_roles=list(profile.desired_roles),
        work_model=list(profile.work_model),
        locations=list(profile.locations),
        preferred_domains=list(profile.preferred_domains),
        years_exp=profile.years_exp,
        education_text=list(profile.education_text),
    )


def spec_to_opportunity_model(spec: OpportunitySpec) -> Opportunity:
    """
    Converts an OpportunitySpec into an in-memory SQLAlchemy Opportunity model
    with attached OpportunitySkill records for execution in calculate_match_with_evidence.
    """
    opp = Opportunity()
    opp.id = UUID(deterministic_skill_id(spec.id))  # Stable synthetic UUID
    opp.title = spec.title
    opp.company_name = spec.company_name
    opp.domain = spec.domain
    opp.opportunity_type = spec.opportunity_type
    opp.work_model = spec.work_model
    opp.locations = list(spec.locations)
    opp.required_experience_min = spec.required_experience_min
    opp.required_experience_max = spec.required_experience_max
    opp.education_requirements = spec.education_requirements
    opp.status = spec.status

    # Attach skills
    opp_skills = []
    for skill_name in spec.required_skills:
        s_id = UUID(deterministic_skill_id(skill_name))
        skill = Skill()
        skill.id = s_id
        skill.name = skill_name
        skill.normalized_name = normalize_text(skill_name)

        os_rel = OpportunitySkill()
        os_rel.opportunity_id = opp.id
        os_rel.skill_id = s_id
        os_rel.skill = skill
        opp_skills.append(os_rel)

    opp.skills = opp_skills
    return opp
