"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  AlertCircle,
  Award,
  BookOpen,
  Briefcase,
  Check,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Compass,
  FileText,
  Info,
  Plus,
  RefreshCw,
  Search,
  Sparkles,
  Target,
  TrendingUp,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { createClient } from "@/lib/supabase/client";

interface JobEvidenceItem {
  opportunity_id: string;
  title: string;
  company_name: string;
  is_required: boolean;
}

interface AcquiredSkillItem {
  skill_id: string | null;
  name: string;
  source: "profile" | "resume" | "both";
  proficiency: string | null;
  resume_evidence: string | null;
  is_saved_to_profile: boolean;
  category: string | null;
}

interface MissingSkillItem {
  skill_id: string | null;
  name: string;
  priority_tier: "high" | "medium" | "low";
  demand_frequency: number;
  demand_percentage: number;
  requirement_level: "required" | "desired" | "common";
  required_count: number;
  desired_count: number;
  evidence_jobs: JobEvidenceItem[];
  rationale: string;
  category: string | null;
}

interface LearningSequenceStage {
  stage_number: number;
  title: string;
  description: string;
  skills: MissingSkillItem[];
}

interface SkillCoverageSummary {
  total_market_skills: number;
  acquired_skills_count: number;
  missing_skills_count: number;
  coverage_percentage: number;
  disclaimer: string;
}

interface InsufficientDataStatus {
  has_insufficient_profile: boolean;
  profile_message: string | null;
  has_insufficient_jobs: boolean;
  jobs_message: string | null;
}

interface SkillGapRoadmapData {
  target_role: string | null;
  available_target_roles: string[];
  total_analyzed_opportunities: number;
  coverage: SkillCoverageSummary;
  data_status: InsufficientDataStatus;
  acquired_skills: AcquiredSkillItem[];
  missing_skills: MissingSkillItem[];
  learning_sequence: LearningSequenceStage[];
}

export function SkillGapRoadmap() {
  const router = useRouter();
  const supabase = createClient();
  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<SkillGapRoadmapData | null>(null);
  const [selectedRole, setSelectedRole] = useState<string | null>(null);
  const [customRoleInput, setCustomRoleInput] = useState("");
  const [activeTab, setActiveTab] = useState<"sequence" | "missing" | "acquired">("sequence");
  const [expandedSkill, setExpandedSkill] = useState<string | null>(null);
  const [savingSkill, setSavingSkill] = useState<string | null>(null);
  const [saveSuccessMessage, setSaveSuccessMessage] = useState<string | null>(null);
  const [missingSearch, setMissingSearch] = useState("");
  const [priorityFilter, setPriorityFilter] = useState<"all" | "high" | "medium" | "low">("all");

  const loadRoadmap = useCallback(
    async (roleToQuery?: string | null) => {
      setLoading(true);
      setError(null);
      setSaveSuccessMessage(null);

      try {
        const {
          data: { session },
        } = await supabase.auth.getSession();

        if (!session) {
          router.push("/login");
          return;
        }

        const queryParams = new URLSearchParams();
        if (roleToQuery !== undefined && roleToQuery !== null && roleToQuery.trim() !== "") {
          queryParams.set("target_role", roleToQuery.trim());
        }

        const url = `${API_URL}/api/v1/copilot/skill-gap-roadmap${
          queryParams.toString() ? `?${queryParams.toString()}` : ""
        }`;

        const res = await fetch(url, {
          headers: {
            Authorization: `Bearer ${session.access_token}`,
          },
        });

        if (!res.ok) {
          throw new Error(`Failed to load skill-gap roadmap (${res.status})`);
        }

        const json: SkillGapRoadmapData = await res.json();
        setData(json);
        if (roleToQuery === undefined) {
          setSelectedRole(json.target_role);
        }
      } catch (err: unknown) {
        console.error(err);
        setError(err instanceof Error ? err.message : String(err));
      } finally {
        setLoading(false);
      }
    },
    [API_URL, router, supabase.auth]
  );

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadRoadmap();
  }, [loadRoadmap]);

  const handleSelectRole = (role: string | null) => {
    setSelectedRole(role);
    setCustomRoleInput("");
    loadRoadmap(role);
  };

  const handleCustomRoleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (customRoleInput.trim()) {
      setSelectedRole(customRoleInput.trim());
      loadRoadmap(customRoleInput.trim());
    }
  };

  const handleAddSkillToProfile = async (skillName: string) => {
    setSavingSkill(skillName);
    setSaveSuccessMessage(null);

    try {
      const {
        data: { session },
      } = await supabase.auth.getSession();

      if (!session) {
        router.push("/login");
        return;
      }

      const res = await fetch(`${API_URL}/api/v1/profile/skills`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${session.access_token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          skill_name: skillName,
          proficiency: "intermediate",
        }),
      });

      if (!res.ok) {
        const errJson = await res.json().catch(() => null);
        throw new Error(errJson?.detail || "Failed to add skill to profile");
      }

      setSaveSuccessMessage(`Added "${skillName}" to your profile skills!`);
      // Reload the roadmap to update acquired skills and recalculate coverage
      await loadRoadmap(selectedRole);
    } catch (err: unknown) {
      console.error(err);
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSavingSkill(null);
    }
  };

  if (loading && !data) {
    return (
      <div className="space-y-6">
        <div className="h-28 rounded-2xl bg-white border border-[#DAE3DC] p-6 animate-pulse flex items-center justify-between" />
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-28 rounded-xl bg-white border border-[#DAE3DC] animate-pulse" />
          ))}
        </div>
        <div className="h-64 rounded-2xl bg-white border border-[#DAE3DC] animate-pulse" />
      </div>
    );
  }

  if (error && !data) {
    return (
      <Card className="border-red-200 bg-red-50/50">
        <CardContent className="p-8 text-center space-y-4">
          <div className="mx-auto w-12 h-12 rounded-full bg-red-100 flex items-center justify-center text-red-600">
            <AlertCircle className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Unable to load Skill-Gap Roadmap</h3>
            <p className="text-sm text-gray-600 mt-1">{error}</p>
          </div>
          <Button onClick={() => loadRoadmap(selectedRole)} variant="outline" className="gap-2">
            <RefreshCw className="w-4 h-4" /> Try Again
          </Button>
        </CardContent>
      </Card>
    );
  }

  if (!data) return null;

  // Filter missing skills for tab 2
  const filteredMissingSkills = data.missing_skills.filter((skill) => {
    const matchesSearch =
      missingSearch.trim() === "" ||
      skill.name.toLowerCase().includes(missingSearch.toLowerCase()) ||
      (skill.category && skill.category.toLowerCase().includes(missingSearch.toLowerCase()));

    const matchesPriority = priorityFilter === "all" || skill.priority_tier === priorityFilter;

    return matchesSearch && matchesPriority;
  });

  return (
    <div className="space-y-6">
      {/* 1. Target Role Selector Bar */}
      <Card className="border-[#DAE3DC] bg-white shadow-sm overflow-hidden">
        <CardContent className="p-5 sm:p-6 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <div className="flex items-center gap-2">
                <Target className="w-4 h-4 text-[#1B5E3B]" />
                <span className="text-xs font-semibold uppercase tracking-wider text-[#5A7362]">
                  Target Career Role
                </span>
              </div>
              <h2 className="text-xl sm:text-2xl font-bold text-[#14261C] mt-0.5">
                {data.target_role || "General Market Demand"}
              </h2>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => loadRoadmap(selectedRole)}
                disabled={loading}
                className="text-xs h-9 gap-1.5 border-[#DAE3DC] hover:bg-[#F6FAF7]"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
                Refresh Data
              </Button>
              <Link href="/profile">
                <Button size="sm" variant="outline" className="text-xs h-9 border-[#DAE3DC] hover:bg-[#F6FAF7]">
                  Edit Career Preferences
                </Button>
              </Link>
            </div>
          </div>

          {/* Role selection pills */}
          <div className="pt-2 border-t border-[#DAE3DC]/60 flex flex-wrap items-center gap-2">
            <span className="text-xs text-[#5A7362] font-medium mr-1">Switch Focus:</span>
            {data.available_target_roles.map((role) => {
              const isSelected = selectedRole?.toLowerCase() === role.toLowerCase();
              return (
                <button
                  key={role}
                  type="button"
                  onClick={() => handleSelectRole(role)}
                  className={`text-xs px-3 py-1.5 rounded-full font-medium transition-all ${
                    isSelected
                      ? "bg-[#1B5E3B] text-white shadow-xs"
                      : "bg-[#F0F5F1] text-[#14261C] hover:bg-[#DAE3DC]/60"
                  }`}
                >
                  {role}
                </button>
              );
            })}
            <button
              type="button"
              onClick={() => handleSelectRole(null)}
              className={`text-xs px-3 py-1.5 rounded-full font-medium transition-all ${
                selectedRole === null
                  ? "bg-[#1B5E3B] text-white shadow-xs"
                  : "bg-[#F0F5F1] text-[#14261C] hover:bg-[#DAE3DC]/60"
              }`}
            >
              All Relevant Postings
            </button>

            {/* Custom role search form */}
            <form onSubmit={handleCustomRoleSubmit} className="flex items-center gap-1.5 ml-auto w-full sm:w-auto">
              <Input
                placeholder="Or test another role..."
                value={customRoleInput}
                onChange={(e) => setCustomRoleInput(e.target.value)}
                className="h-8 text-xs w-full sm:w-48 bg-[#F6FAF7] border-[#DAE3DC]"
              />
              <Button type="submit" size="sm" variant="outline" className="h-8 text-xs px-2.5">
                <Search className="w-3 h-3" />
              </Button>
            </form>
          </div>
        </CardContent>
      </Card>

      {/* 2. Success Banner (e.g. after adding a skill to profile) */}
      {saveSuccessMessage && (
        <div className="bg-[#E5EDE7] border border-[#1B5E3B]/30 text-[#14261C] px-4 py-3 rounded-xl flex items-center justify-between text-sm shadow-xs animate-in fade-in">
          <div className="flex items-center gap-2.5">
            <CheckCircle2 className="w-4 h-4 text-[#1B5E3B]" />
            <span>{saveSuccessMessage}</span>
          </div>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => setSaveSuccessMessage(null)}
            className="h-7 text-xs text-[#5A7362] hover:text-[#14261C]"
          >
            Dismiss
          </Button>
        </div>
      )}

      {/* 3. Insufficient Data Alerts (Truthful handling, no hallucinations) */}
      {data.data_status.has_insufficient_profile && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 flex items-start gap-3 text-sm text-amber-900 shadow-xs">
          <AlertCircle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <h4 className="font-semibold text-amber-950">Incomplete Profile Preferences</h4>
            <p className="text-xs sm:text-sm text-amber-800 leading-relaxed">
              {data.data_status.profile_message}
            </p>
            <div className="pt-2">
              <Link href="/profile">
                <Button size="sm" variant="outline" className="h-7 text-xs border-amber-300 bg-white hover:bg-amber-100">
                  Configure Preferences in Profile
                </Button>
              </Link>
            </div>
          </div>
        </div>
      )}

      {data.data_status.has_insufficient_jobs && (
        <div className="bg-sky-50 border border-sky-200 rounded-xl p-4 flex items-start gap-3 text-sm text-sky-950 shadow-xs">
          <Info className="w-5 h-5 text-sky-600 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <h4 className="font-semibold text-sky-950">No Verified Job Data Available</h4>
            <p className="text-xs sm:text-sm text-sky-800 leading-relaxed">
              {data.data_status.jobs_message}
            </p>
            <p className="text-xs text-sky-700">
              CareerPilot AI adheres to strict data integrity: skill demand is never invented or simulated when live employer postings are absent.
            </p>
          </div>
        </div>
      )}

      {/* 4. Metric Cards & Skill Coverage Overview */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* Coverage Percentage */}
        <Card className="border-[#DAE3DC] bg-white shadow-xs">
          <CardContent className="p-4 sm:p-5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-[#5A7362]">Skill Coverage</span>
              <Award className="w-4 h-4 text-[#1B5E3B]" />
            </div>
            <div className="mt-2 flex items-baseline gap-2">
              <span className="text-2xl sm:text-3xl font-extrabold text-[#1B5E3B]">
                {data.coverage.coverage_percentage}%
              </span>
              <span className="text-xs text-[#5A7362]">
                ({data.coverage.acquired_skills_count}/{data.coverage.total_market_skills})
              </span>
            </div>
            {/* Visual progress bar */}
            <div className="mt-3 w-full bg-[#F0F5F1] h-2 rounded-full overflow-hidden">
              <div
                className="bg-[#1B5E3B] h-full rounded-full transition-all duration-500"
                style={{ width: `${Math.min(100, data.coverage.coverage_percentage)}%` }}
              />
            </div>
          </CardContent>
        </Card>

        {/* Analyzed Opportunities */}
        <Card className="border-[#DAE3DC] bg-white shadow-xs">
          <CardContent className="p-4 sm:p-5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-[#5A7362]">Active Postings</span>
              <Briefcase className="w-4 h-4 text-[#5A7362]" />
            </div>
            <div className="mt-2">
              <span className="text-2xl sm:text-3xl font-extrabold text-[#14261C]">
                {data.total_analyzed_opportunities}
              </span>
            </div>
            <p className="mt-2 text-xs text-[#5A7362]">Published jobs analyzed for this role</p>
          </CardContent>
        </Card>

        {/* Acquired Skills */}
        <Card className="border-[#DAE3DC] bg-white shadow-xs">
          <CardContent className="p-4 sm:p-5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-[#5A7362]">Your Skills</span>
              <CheckCircle2 className="w-4 h-4 text-[#1B5E3B]" />
            </div>
            <div className="mt-2">
              <span className="text-2xl sm:text-3xl font-extrabold text-[#14261C]">
                {data.acquired_skills.length}
              </span>
            </div>
            <p className="mt-2 text-xs text-[#5A7362]">From manual profile &amp; active resume</p>
          </CardContent>
        </Card>

        {/* Missing Skills */}
        <Card className="border-[#DAE3DC] bg-white shadow-xs">
          <CardContent className="p-4 sm:p-5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-[#5A7362]">Skill Gaps</span>
              <TrendingUp className="w-4 h-4 text-[#F59E0B]" />
            </div>
            <div className="mt-2">
              <span className="text-2xl sm:text-3xl font-extrabold text-[#F59E0B]">
                {data.missing_skills.length}
              </span>
            </div>
            <p className="mt-2 text-xs text-[#5A7362]">Demanded by postings, not in profile</p>
          </CardContent>
        </Card>
      </div>

      {/* 5. Score Integrity & Heuristic Disclaimer */}
      <div className="bg-white border border-[#DAE3DC] rounded-xl p-4 flex items-start gap-3 text-xs text-[#5A7362] shadow-xs">
        <Info className="w-4 h-4 text-[#5A7362] shrink-0 mt-0.5" />
        <p className="leading-relaxed">
          <strong className="text-[#14261C]">Score Integrity Disclaimer: </strong>
          {data.coverage.disclaimer}
        </p>
      </div>

      {/* 6. Tabs Header */}
      <div className="flex items-center border-b border-[#DAE3DC] space-x-1 sm:space-x-4">
        <button
          type="button"
          onClick={() => setActiveTab("sequence")}
          className={`flex items-center gap-2 py-3 px-3 text-sm font-semibold border-b-2 transition-all ${
            activeTab === "sequence"
              ? "border-[#1B5E3B] text-[#1B5E3B]"
              : "border-transparent text-[#5A7362] hover:text-[#14261C]"
          }`}
        >
          <Compass className="w-4 h-4" />
          Learning Roadmap ({data.learning_sequence.length} Stages)
        </button>

        <button
          type="button"
          onClick={() => setActiveTab("missing")}
          className={`flex items-center gap-2 py-3 px-3 text-sm font-semibold border-b-2 transition-all ${
            activeTab === "missing"
              ? "border-[#1B5E3B] text-[#1B5E3B]"
              : "border-transparent text-[#5A7362] hover:text-[#14261C]"
          }`}
        >
          <Sparkles className="w-4 h-4" />
          Missing Skills Gap ({data.missing_skills.length})
        </button>

        <button
          type="button"
          onClick={() => setActiveTab("acquired")}
          className={`flex items-center gap-2 py-3 px-3 text-sm font-semibold border-b-2 transition-all ${
            activeTab === "acquired"
              ? "border-[#1B5E3B] text-[#1B5E3B]"
              : "border-transparent text-[#5A7362] hover:text-[#14261C]"
          }`}
        >
          <CheckCircle2 className="w-4 h-4" />
          Your Acquired Skills ({data.acquired_skills.length})
        </button>
      </div>

      {/* 7. Tab 1: Practical Learning Sequence (Step-by-Step Roadmap) */}
      {activeTab === "sequence" && (
        <div className="space-y-8">
          {data.learning_sequence.length === 0 ? (
            <Card className="border-[#DAE3DC] bg-white text-center p-12">
              <div className="w-12 h-12 rounded-full bg-[#E5EDE7] text-[#1B5E3B] mx-auto flex items-center justify-center mb-4">
                <Check className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-[#14261C]">No Missing Skills Identified</h3>
              <p className="text-sm text-[#5A7362] max-w-md mx-auto mt-1">
                {data.total_analyzed_opportunities === 0
                  ? "Select a target role with published job postings to generate an evidence-backed learning roadmap."
                  : "Congratulations! Your profile and active resume already cover all skills demanded by published listings for this role."}
              </p>
              <div className="mt-5 flex items-center justify-center gap-3">
                <Link href="/matches">
                  <Button className="bg-[#1B5E3B] hover:bg-[#2E7D4F] text-white text-xs h-9">
                    Explore Your Matches
                  </Button>
                </Link>
                <Link href="/profile">
                  <Button variant="outline" className="text-xs h-9">
                    Manage Profile
                  </Button>
                </Link>
              </div>
            </Card>
          ) : (
            <div className="relative pl-6 sm:pl-8 space-y-8 before:absolute before:left-3 before:top-4 before:bottom-4 before:w-0.5 before:bg-[#DAE3DC]">
              {data.learning_sequence.map((stage) => (
                <div key={stage.stage_number} className="relative space-y-4">
                  {/* Stage Timeline Dot */}
                  <div className="absolute -left-6 sm:-left-8 top-1 w-6 h-6 rounded-full bg-[#1B5E3B] text-white flex items-center justify-center text-xs font-bold ring-4 ring-[#F6FAF7]">
                    {stage.stage_number}
                  </div>

                  {/* Stage Header */}
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <h3 className="text-lg font-bold text-[#14261C]">{stage.title}</h3>
                      <Badge variant="outline" className="text-[10px] bg-white border-[#DAE3DC]">
                        {stage.skills.length} {stage.skills.length === 1 ? "Skill" : "Skills"}
                      </Badge>
                    </div>
                    <p className="text-xs sm:text-sm text-[#5A7362] leading-relaxed max-w-2xl">
                      {stage.description}
                    </p>
                  </div>

                  {/* Skill Cards Grid for this Stage */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {stage.skills.map((skill) => (
                      <SkillCard
                        key={skill.name}
                        skill={skill}
                        isExpanded={expandedSkill === skill.name}
                        onToggleExpand={() =>
                          setExpandedSkill(expandedSkill === skill.name ? null : skill.name)
                        }
                        onAddSkill={handleAddSkillToProfile}
                        isSaving={savingSkill === skill.name}
                      />
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* 8. Tab 2: Missing Skills (Detailed Analysis) */}
      {activeTab === "missing" && (
        <div className="space-y-4">
          {/* Search & Filter Bar */}
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 bg-white p-3 rounded-xl border border-[#DAE3DC]">
            <div className="relative flex-1">
              <Search className="w-4 h-4 text-[#5A7362] absolute left-3 top-1/2 -translate-y-1/2" />
              <Input
                placeholder="Filter missing skills by name or category..."
                value={missingSearch}
                onChange={(e) => setMissingSearch(e.target.value)}
                className="pl-9 h-9 text-xs bg-[#F6FAF7] border-[#DAE3DC]"
              />
            </div>
            <div className="flex items-center gap-1.5 overflow-x-auto">
              <span className="text-xs text-[#5A7362] mr-1 shrink-0">Priority:</span>
              {(["all", "high", "medium", "low"] as const).map((p) => (
                <button
                  key={p}
                  type="button"
                  onClick={() => setPriorityFilter(p)}
                  className={`text-xs px-2.5 py-1 rounded-md font-medium capitalize transition-all ${
                    priorityFilter === p
                      ? "bg-[#1B5E3B] text-white"
                      : "bg-[#F0F5F1] text-[#5A7362] hover:text-[#14261C]"
                  }`}
                >
                  {p}
                </button>
              ))}
            </div>
          </div>

          {filteredMissingSkills.length === 0 ? (
            <Card className="border-[#DAE3DC] bg-white p-8 text-center">
              <p className="text-sm text-[#5A7362]">No missing skills match the selected filter.</p>
            </Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {filteredMissingSkills.map((skill) => (
                <SkillCard
                  key={skill.name}
                  skill={skill}
                  isExpanded={expandedSkill === skill.name}
                  onToggleExpand={() =>
                    setExpandedSkill(expandedSkill === skill.name ? null : skill.name)
                  }
                  onAddSkill={handleAddSkillToProfile}
                  isSaving={savingSkill === skill.name}
                />
              ))}
            </div>
          )}
        </div>
      )}

      {/* 9. Tab 3: Acquired Skills (Your Foundation) */}
      {activeTab === "acquired" && (
        <div className="space-y-6">
          <div className="bg-[#E5EDE7]/40 border border-[#DAE3DC] rounded-xl p-4 flex items-start gap-3 text-xs text-[#14261C]">
            <CheckCircle2 className="w-4 h-4 text-[#1B5E3B] shrink-0 mt-0.5" />
            <div className="space-y-1">
              <p className="font-medium">Observed Candidate Skills Inventory</p>
              <p className="text-[#5A7362] leading-relaxed">
                Skills below are detected either from your manually recorded Profile Skills or extracted with evidence from your Active Resume. Resume-extracted skills are not claimed to be manually verified until you confirm them.
              </p>
            </div>
          </div>

          {data.acquired_skills.length === 0 ? (
            <Card className="border-[#DAE3DC] bg-white p-12 text-center space-y-3">
              <div className="w-12 h-12 rounded-full bg-[#F0F5F1] text-[#5A7362] mx-auto flex items-center justify-center">
                <BookOpen className="w-6 h-6" />
              </div>
              <h4 className="text-base font-bold text-[#14261C]">No Skills Currently Recorded</h4>
              <p className="text-xs text-[#5A7362] max-w-sm mx-auto">
                Add skills manually to your profile or upload your resume to establish your baseline foundation.
              </p>
              <div className="pt-2">
                <Link href="/profile">
                  <Button size="sm" className="bg-[#1B5E3B] text-white text-xs h-8">
                    Add Profile Skills
                  </Button>
                </Link>
              </div>
            </Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {data.acquired_skills.map((skill) => (
                <Card
                  key={skill.name}
                  className="border-[#DAE3DC] bg-white shadow-xs hover:border-[#1B5E3B]/40 transition-all"
                >
                  <CardContent className="p-4 sm:p-5 space-y-3">
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <h4 className="text-base font-bold text-[#14261C]">{skill.name}</h4>
                        {skill.category && (
                          <span className="text-[11px] text-[#5A7362]">{skill.category}</span>
                        )}
                      </div>

                      {/* Source badge */}
                      <div className="flex items-center gap-1.5">
                        {skill.source === "both" && (
                          <Badge className="bg-[#1B5E3B] text-white text-[10px]">
                            Profile &amp; Resume
                          </Badge>
                        )}
                        {skill.source === "profile" && (
                          <Badge variant="outline" className="border-[#1B5E3B] text-[#1B5E3B] text-[10px]">
                            Profile Skill
                          </Badge>
                        )}
                        {skill.source === "resume" && (
                          <Badge variant="outline" className="border-[#F59E0B] text-[#B45309] bg-amber-50 text-[10px]">
                            From Active Resume
                          </Badge>
                        )}
                      </div>
                    </div>

                    {/* Metadata details */}
                    <div className="text-xs space-y-1.5 pt-2 border-t border-[#DAE3DC]/60">
                      {skill.proficiency && (
                        <div className="flex items-center gap-2">
                          <span className="text-[#5A7362]">Proficiency:</span>
                          <span className="font-medium capitalize text-[#14261C]">{skill.proficiency}</span>
                        </div>
                      )}

                      {skill.resume_evidence && (
                        <div className="bg-[#F6FAF7] border border-[#DAE3DC]/60 rounded-md p-2 mt-1">
                          <div className="flex items-center gap-1 text-[11px] font-semibold text-[#5A7362]">
                            <FileText className="w-3 h-3 text-[#1B5E3B]" />
                            <span>Resume Evidence:</span>
                          </div>
                          <p className="text-[11px] text-[#14261C] italic mt-0.5 line-clamp-2">
                            &ldquo;{skill.resume_evidence}&rdquo;
                          </p>
                        </div>
                      )}
                    </div>

                    {/* Action for resume-only skills to save to profile */}
                    {!skill.is_saved_to_profile && (
                      <div className="pt-2 flex items-center justify-between">
                        <span className="text-[11px] text-amber-700">Not yet saved to profile</span>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleAddSkillToProfile(skill.name)}
                          disabled={savingSkill === skill.name}
                          className="text-xs h-7 gap-1 border-[#1B5E3B] text-[#1B5E3B] hover:bg-[#E5EDE7]"
                        >
                          <Plus className="w-3 h-3" />
                          {savingSkill === skill.name ? "Saving..." : "Save to Profile"}
                        </Button>
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}

      {/* 10. Bottom Navigation & Helpful CTAs */}
      <div className="pt-6 border-t border-[#DAE3DC] flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-[#5A7362]">
        <div className="flex items-center gap-2">
          <span>Career Copilot • Phase 7.1 Personalized Skill-Gap Roadmap</span>
        </div>
        <div className="flex items-center gap-3">
          <Link href="/matches">
            <Button variant="outline" size="sm" className="text-xs h-8 border-[#DAE3DC]">
              View Matching Jobs
            </Button>
          </Link>
          <Link href="/profile">
            <Button variant="outline" size="sm" className="text-xs h-8 border-[#DAE3DC]">
              Update Profile Skills
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
}

// Sub-component for individual Missing Skill card with evidence accordion
function SkillCard({
  skill,
  isExpanded,
  onToggleExpand,
  onAddSkill,
  isSaving,
}: {
  skill: MissingSkillItem;
  isExpanded: boolean;
  onToggleExpand: () => void;
  onAddSkill: (skillName: string) => void;
  isSaving: boolean;
}) {
  const tierColor =
    skill.priority_tier === "high"
      ? "bg-[#1B5E3B] text-white"
      : skill.priority_tier === "medium"
      ? "bg-sky-600 text-white"
      : "bg-slate-500 text-white";

  const reqColor =
    skill.requirement_level === "required"
      ? "border-red-300 text-red-700 bg-red-50"
      : skill.requirement_level === "desired"
      ? "border-amber-300 text-amber-700 bg-amber-50"
      : "border-purple-300 text-purple-700 bg-purple-50";

  return (
    <Card className="border-[#DAE3DC] bg-white shadow-xs hover:shadow-sm transition-all flex flex-col justify-between">
      <CardContent className="p-4 sm:p-5 space-y-3">
        {/* Top Badges & Name */}
        <div className="flex items-start justify-between gap-2">
          <div className="space-y-0.5">
            <h4 className="text-base font-bold text-[#14261C] flex items-center gap-2">
              {skill.name}
            </h4>
            {skill.category && (
              <span className="text-[11px] text-[#5A7362] block">{skill.category}</span>
            )}
          </div>

          <div className="flex items-center gap-1.5 shrink-0">
            <Badge className={`text-[10px] uppercase font-bold px-2 py-0.5 ${tierColor}`}>
              {skill.priority_tier}
            </Badge>
            <Badge variant="outline" className={`text-[10px] capitalize px-2 py-0.5 ${reqColor}`}>
              {skill.requirement_level}
            </Badge>
          </div>
        </div>

        {/* Demand & Evidence summary */}
        <div className="space-y-1.5 text-xs text-[#5A7362]">
          <div className="flex items-center justify-between">
            <span>Market Demand:</span>
            <span className="font-semibold text-[#14261C]">
              {skill.demand_percentage}% ({skill.demand_frequency} postings)
            </span>
          </div>
          <div className="w-full bg-[#F0F5F1] h-1.5 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full ${
                skill.priority_tier === "high"
                  ? "bg-[#1B5E3B]"
                  : skill.priority_tier === "medium"
                  ? "bg-sky-600"
                  : "bg-slate-500"
              }`}
              style={{ width: `${Math.min(100, skill.demand_percentage)}%` }}
            />
          </div>
        </div>

        {/* Plain-Language Rationale */}
        <p className="text-xs text-[#14261C] leading-relaxed bg-[#F6FAF7] border border-[#DAE3DC]/60 p-2.5 rounded-lg">
          {skill.rationale}
        </p>

        {/* Expandable Verified Job Evidence */}
        {skill.evidence_jobs.length > 0 && (
          <div className="pt-1">
            <button
              type="button"
              onClick={onToggleExpand}
              className="flex items-center justify-between w-full text-xs text-[#1B5E3B] font-semibold hover:underline"
            >
              <span className="flex items-center gap-1.5">
                <Briefcase className="w-3.5 h-3.5" />
                Verified Job Evidence ({skill.evidence_jobs.length})
              </span>
              {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
            </button>

            {isExpanded && (
              <div className="mt-2 space-y-1.5 bg-white border border-[#DAE3DC] rounded-lg p-2.5 text-xs">
                {skill.evidence_jobs.map((job) => (
                  <div key={job.opportunity_id} className="flex items-center justify-between py-1 border-b border-[#F0F5F1] last:border-b-0">
                    <div>
                      <span className="font-medium text-[#14261C]">{job.company_name}</span>
                      <span className="text-[#5A7362] ml-1.5 text-[11px]">— {job.title}</span>
                    </div>
                    <Badge variant="outline" className="text-[9px] px-1.5 py-0 h-4">
                      {job.is_required ? "Required" : "Preferred"}
                    </Badge>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </CardContent>

      {/* Card Footer Action: Add to Profile */}
      <div className="px-4 py-3 bg-[#F6FAF7] border-t border-[#DAE3DC] flex items-center justify-between">
        <span className="text-[11px] text-[#5A7362]">Already know this skill?</span>
        <Button
          size="sm"
          variant="outline"
          onClick={() => onAddSkill(skill.name)}
          disabled={isSaving}
          className="text-xs h-7 px-2.5 border-[#1B5E3B] text-[#1B5E3B] hover:bg-[#E5EDE7]"
        >
          <Plus className="w-3 h-3 mr-1" />
          {isSaving ? "Adding..." : "Add to Profile"}
        </Button>
      </div>
    </Card>
  );
}
