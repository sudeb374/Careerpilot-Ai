"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import {
  AlertCircle,
  AlertTriangle,
  ArrowRight,
  Briefcase,
  Check,
  CheckCircle2,
  Copy,
  FileCheck,
  FileText,
  FolderGit2,
  GraduationCap,
  Info,
  Loader2,
  MapPin,
  RefreshCw,
  Search,
  ShieldCheck,
  Sparkles,
  Target,
  Wand2,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { createClient } from "@/lib/supabase/client";

interface OpportunityOption {
  id: string;
  title: string;
  company_name: string;
  opportunity_type: string;
  work_model: string;
  locations?: string[];
  domain?: string | null;
  skills?: { id: string; name: string }[];
}

interface ActiveResumeSummary {
  resume_id: string;
  original_filename: string;
  file_size: number;
  file_type: string;
  has_parsed_text: boolean;
  has_structured_data: boolean;
  has_analysis: boolean;
  completeness_score?: number | null;
  score_label?: string | null;
  uploaded_at: string;
}

interface ContextResponse {
  opportunity_id: string;
  opportunity_title: string;
  company_name: string;
  opportunity_type: string;
  work_model: string;
  domain?: string | null;
  locations: string[];
  deadline?: string | null;
  has_description: boolean;
  description_char_count: number;
  skills_required: string[];
  active_resume?: ActiveResumeSummary | null;
  is_ready_for_analysis: boolean;
  readiness_notes: string[];
}

interface RelevantStrengthItem {
  category: "skill" | "project" | "experience" | "education" | string;
  title: string;
  source: "profile" | "resume" | "both" | string;
  evidence: string;
  relevance_explanation: string;
}

interface RequirementGapItem {
  skill_name: string;
  requirement_level: "required" | "desired" | string;
  gap_type: "missing_requirement" | "undetermined_incomplete_info" | string;
  explanation: string;
  student_guidance: string;
}

interface ActionableImprovementItem {
  category: "emphasis" | "bullet_rewrite" | "keyword_alignment" | "section_content" | string;
  priority: "high" | "medium" | "low" | string;
  title: string;
  original_content?: string | null;
  suggested_wording?: string | null;
  reason: string;
  evidence_support?: string | null;
  is_gemini_assisted: boolean;
}

interface AtsGuidanceItem {
  area: "headings" | "readability" | "keyword_placement" | "section_structure" | string;
  status: "good" | "improvement_needed" | "info" | string;
  title: string;
  recommendation: string;
  rationale: string;
}

interface DataSufficiencyInfo {
  has_active_resume: boolean;
  has_resume_text: boolean;
  has_job_description: boolean;
  has_job_skills: boolean;
  status: "sufficient" | "partial" | "insufficient" | string;
  details: string[];
}

interface JobResumeAnalysisResponse {
  opportunity_id: string;
  opportunity_title: string;
  company_name: string;
  resume_id?: string | null;
  resume_filename?: string | null;
  resume_completeness_score?: number | null;
  resume_completeness_label?: string | null;
  data_sufficiency: DataSufficiencyInfo;
  strengths: RelevantStrengthItem[];
  gaps: RequirementGapItem[];
  improvements: ActionableImprovementItem[];
  ats_guidance: AtsGuidanceItem[];
  disclaimers: string[];
  provider: "gemini" | "deterministic" | string;
  provider_model?: string | null;
  created_at: string;
}

export function JobResumeRecommendations() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const supabase = createClient();
  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const preselectedId = searchParams.get("opportunity_id");

  // State
  const [opportunities, setOpportunities] = useState<OpportunityOption[]>([]);
  const [selectedOpportunityId, setSelectedOpportunityId] = useState<string>(preselectedId || "");
  const [loadingOpportunities, setLoadingOpportunities] = useState(true);
  const [searchFilter, setSearchFilter] = useState("");

  const [contextData, setContextData] = useState<ContextResponse | null>(null);
  const [loadingContext, setLoadingContext] = useState(false);

  const [includeBulletRewrites, setIncludeBulletRewrites] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [analysisResult, setAnalysisResult] = useState<JobResumeAnalysisResponse | null>(null);

  const [activeTab, setActiveTab] = useState<"overview" | "strengths" | "gaps" | "improvements" | "ats">("overview");
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [copiedAll, setCopiedAll] = useState(false);

  // 1. Fetch published opportunities
  const loadOpportunities = useCallback(async () => {
    setLoadingOpportunities(true);
    try {
      const {
        data: { session },
      } = await supabase.auth.getSession();

      if (!session) {
        router.push("/login");
        return;
      }

      const res = await fetch(`${API_URL}/api/v1/opportunities?page=1&page_size=50`, {
        headers: { Authorization: `Bearer ${session.access_token}` },
      });

      if (res.ok) {
        const json = await res.json();
        const items = json.items || [];
        setOpportunities(items);
        if (!selectedOpportunityId && items.length > 0 && !preselectedId) {
          setSelectedOpportunityId(items[0].id);
        }
      }
    } catch (err: unknown) {
      console.error("Failed to load opportunities:", err);
    } finally {
      setLoadingOpportunities(false);
    }
  }, [API_URL, preselectedId, router, selectedOpportunityId, supabase.auth]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadOpportunities();
  }, [loadOpportunities]);

  useEffect(() => {
    if (preselectedId) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setSelectedOpportunityId(preselectedId);
    }
  }, [preselectedId]);

  // 2. Fetch Context when selectedOpportunityId changes
  const loadContext = useCallback(
    async (oppId: string) => {
      if (!oppId) return;
      setLoadingContext(true);
      setAnalysisError(null);
      try {
        const {
          data: { session },
        } = await supabase.auth.getSession();
        if (!session) return;

        const res = await fetch(`${API_URL}/api/v1/copilot/resume-recommendations/context/${oppId}`, {
          headers: { Authorization: `Bearer ${session.access_token}` },
        });

        if (res.ok) {
          const json = await res.json();
          setContextData(json);
        } else {
          const errJson = await res.json().catch(() => ({}));
          setAnalysisError(errJson.detail || "Failed to load opportunity context.");
        }
      } catch (err: unknown) {
        console.error("Error loading resume recommendations context:", err);
        setAnalysisError("Network error while verifying opportunity and resume status.");
      } finally {
        setLoadingContext(false);
      }
    },
    [API_URL, supabase.auth]
  );

  useEffect(() => {
    if (selectedOpportunityId) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      loadContext(selectedOpportunityId);
    }
  }, [selectedOpportunityId, loadContext]);

  // Filtered opportunities list
  const filteredOpportunities = useMemo(() => {
    if (!searchFilter.trim()) return opportunities;
    const q = searchFilter.toLowerCase();
    return opportunities.filter(
      (o) =>
        o.title.toLowerCase().includes(q) ||
        o.company_name.toLowerCase().includes(q) ||
        (o.domain && o.domain.toLowerCase().includes(q))
    );
  }, [opportunities, searchFilter]);

  // 3. Run Analysis
  const handleAnalyze = async () => {
    if (!selectedOpportunityId) {
      setAnalysisError("Please select a published opportunity first.");
      return;
    }

    setAnalyzing(true);
    setAnalysisError(null);

    try {
      const {
        data: { session },
      } = await supabase.auth.getSession();

      if (!session) {
        router.push("/login");
        return;
      }

      const res = await fetch(`${API_URL}/api/v1/copilot/resume-recommendations/analyze`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({
          opportunity_id: selectedOpportunityId,
          include_bullet_rewrites: includeBulletRewrites,
        }),
      });

      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.detail || `Analysis request failed with status ${res.status}`);
      }

      const data: JobResumeAnalysisResponse = await res.json();
      setAnalysisResult(data);
      setActiveTab("overview");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to analyze resume.";
      setAnalysisError(msg);
    } finally {
      setAnalyzing(false);
    }
  };

  // Copy helper for individual bullet rewrites
  const handleCopyText = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2500);
  };

  // Copy all recommendations report
  const handleCopyAll = () => {
    if (!analysisResult) return;

    const sections: string[] = [
      `=== CAREERPILOT AI RESUME RECOMMENDATIONS ===`,
      `Target Role: ${analysisResult.opportunity_title} at ${analysisResult.company_name}`,
      `Resume Analyzed: ${analysisResult.resume_filename || "Active Resume"}`,
      `Generated: ${new Date(analysisResult.created_at).toLocaleDateString()}`,
      `Provider: ${analysisResult.provider === "gemini" ? "Gemini AI" : "Deterministic Engine"}`,
      `\n--- KEY STRENGTHS ---`,
      ...analysisResult.strengths.map((s) => `• [${s.category.toUpperCase()}] ${s.title}: ${s.relevance_explanation}`),
      `\n--- REQUIREMENT GAPS ---`,
      ...analysisResult.gaps.map((g) => `• [${g.requirement_level.toUpperCase()}] ${g.skill_name}: ${g.explanation}\n  Guidance: ${g.student_guidance}`),
      `\n--- ACTIONABLE IMPROVEMENTS & BULLET REWRITES ---`,
      ...analysisResult.improvements.map((imp) => {
        let block = `• [${imp.priority.toUpperCase()}] ${imp.title}\n  Reason: ${imp.reason}`;
        if (imp.original_content) block += `\n  Original: "${imp.original_content}"`;
        if (imp.suggested_wording) block += `\n  Suggested: "${imp.suggested_wording}"`;
        return block;
      }),
      `\n--- ATS FORMATTING GUIDANCE ---`,
      ...analysisResult.ats_guidance.map((ats) => `• [${ats.area.toUpperCase()}] ${ats.title}: ${ats.recommendation}`),
      `\n--- DISCLAIMER ---`,
      `CareerPilot AI does not alter your uploaded documents or guarantee hiring outcomes. All metrics must be verified by the student.`,
    ];

    navigator.clipboard.writeText(sections.join("\n"));
    setCopiedAll(true);
    setTimeout(() => setCopiedAll(false), 2500);
  };

  return (
    <div className="space-y-6">
      {/* 1. Selection & Active Resume Inspection Bar */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Opportunity Selector */}
        <Card className="lg:col-span-7 border-border shadow-sm">
          <CardHeader className="pb-3">
            <CardTitle className="text-lg font-semibold text-[#14261C] flex items-center justify-between">
              <span className="flex items-center gap-2">
                <Target className="w-5 h-5 text-[#1B5E3B]" />
                1. Select Published Opportunity
              </span>
              <Badge variant="outline" className="text-xs border-[#1B5E3B]/30 text-[#1B5E3B]">
                {opportunities.length} Published
              </Badge>
            </CardTitle>
            <CardDescription className="text-xs text-[#5A7362]">
              Pick an active job posting to tailor your resume specifically for its qualifications and tech stack.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Search filter input */}
            <div className="relative">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-[#5A7362]" />
              <Input
                type="text"
                placeholder="Filter by title, company, or domain..."
                value={searchFilter}
                onChange={(e) => setSearchFilter(e.target.value)}
                className="pl-9 text-sm"
              />
            </div>

            {loadingOpportunities ? (
              <div className="flex items-center justify-center py-8 text-sm text-[#5A7362] gap-2">
                <Loader2 className="w-4 h-4 animate-spin text-[#1B5E3B]" />
                Loading published opportunities...
              </div>
            ) : filteredOpportunities.length === 0 ? (
              <div className="text-center py-6 border border-dashed rounded-lg text-sm text-[#5A7362]">
                No published opportunities match &quot;{searchFilter}&quot;.
              </div>
            ) : (
              <div className="max-h-56 overflow-y-auto space-y-2 pr-1">
                {filteredOpportunities.map((opp) => {
                  const isSelected = opp.id === selectedOpportunityId;
                  return (
                    <button
                      key={opp.id}
                      type="button"
                      onClick={() => {
                        setSelectedOpportunityId(opp.id);
                        setAnalysisResult(null);
                      }}
                      className={`w-full text-left p-3 rounded-lg border transition-all flex items-start justify-between gap-3 ${
                        isSelected
                          ? "bg-[#1B5E3B]/10 border-[#1B5E3B] shadow-xs"
                          : "bg-white border-border hover:border-[#1B5E3B]/40 hover:bg-black/[0.02]"
                      }`}
                    >
                      <div className="min-w-0 flex-1">
                        <div className="font-medium text-sm text-[#14261C] truncate">{opp.title}</div>
                        <div className="text-xs text-[#5A7362] flex items-center gap-2 mt-0.5">
                          <span className="font-semibold text-gray-700">{opp.company_name}</span>
                          {opp.locations && opp.locations.length > 0 && (
                            <span className="flex items-center gap-0.5">
                              • <MapPin className="w-3 h-3 inline" /> {opp.locations[0]}
                            </span>
                          )}
                        </div>
                      </div>
                      <div className="flex flex-col items-end gap-1">
                        <Badge variant="outline" className="text-[10px] uppercase font-semibold">
                          {opp.opportunity_type}
                        </Badge>
                        <span className="text-[10px] text-gray-500">{opp.work_model}</span>
                      </div>
                    </button>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Right: Active Resume Inspection Card */}
        <Card className="lg:col-span-5 border-border shadow-sm flex flex-col justify-between">
          <CardHeader className="pb-3">
            <CardTitle className="text-lg font-semibold text-[#14261C] flex items-center gap-2">
              <FileCheck className="w-5 h-5 text-[#1B5E3B]" />
              2. Active Resume Verified
            </CardTitle>
            <CardDescription className="text-xs text-[#5A7362]">
              Your designated active resume will be safely compared without modifying your saved file.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 flex-1 flex flex-col justify-between">
            {loadingContext ? (
              <div className="flex items-center justify-center py-6 text-sm text-[#5A7362] gap-2">
                <Loader2 className="w-4 h-4 animate-spin text-[#1B5E3B]" />
                Verifying active resume...
              </div>
            ) : contextData?.active_resume ? (
              <div className="space-y-3">
                <div className="p-3.5 rounded-lg border border-[#1B5E3B]/20 bg-[#1B5E3B]/5 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-[#1B5E3B] uppercase tracking-wider flex items-center gap-1.5">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      Active Resume Ready
                    </span>
                    {contextData.active_resume.completeness_score !== null &&
                      contextData.active_resume.completeness_score !== undefined && (
                        <Badge className="bg-[#1B5E3B] text-white text-xs">
                          {contextData.active_resume.completeness_score}% Score
                        </Badge>
                      )}
                  </div>
                  <div className="font-semibold text-sm text-[#14261C] truncate">
                    {contextData.active_resume.original_filename}
                  </div>
                  <div className="text-xs text-[#5A7362] flex items-center justify-between">
                    <span>
                      Size: {(contextData.active_resume.file_size / (1024 * 1024)).toFixed(2)} MB • {contextData.active_resume.file_type.split("/")[1]?.toUpperCase() || "PDF"}
                    </span>
                    <span>
                      {contextData.active_resume.score_label || "Parsed"}
                    </span>
                  </div>
                </div>

                {contextData.readiness_notes.length > 0 && (
                  <div className="space-y-1">
                    {contextData.readiness_notes.map((note, idx) => (
                      <div key={idx} className="text-xs text-amber-700 bg-amber-50 p-2 rounded border border-amber-200 flex items-start gap-1.5">
                        <AlertTriangle className="w-3.5 h-3.5 mt-0.5 shrink-0" />
                        <span>{note}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              <div className="p-4 rounded-lg border border-red-200 bg-red-50 text-red-800 text-xs space-y-2">
                <div className="font-semibold flex items-center gap-1.5">
                  <AlertCircle className="w-4 h-4" />
                  No Active Resume Found
                </div>
                <p>
                  You must have an uploaded and activated resume in your profile before analyzing against a job.
                </p>
                <Link href="/profile" className="inline-block mt-1">
                  <Button size="sm" variant="outline" className="border-red-300 text-red-800 hover:bg-red-100 text-xs">
                    Upload Resume in Profile &rarr;
                  </Button>
                </Link>
              </div>
            )}

            {/* Analysis triggers */}
            <div className="pt-2 border-t border-border space-y-3">
              <label className="flex items-center gap-2 cursor-pointer text-xs text-gray-700">
                <input
                  type="checkbox"
                  checked={includeBulletRewrites}
                  onChange={(e) => setIncludeBulletRewrites(e.target.checked)}
                  className="rounded text-[#1B5E3B] focus:ring-[#1B5E3B] h-4 w-4"
                />
                <span>Include AI-assisted / grounded bullet rewrites for vague lines</span>
              </label>

              <Button
                onClick={handleAnalyze}
                disabled={
                  analyzing ||
                  !selectedOpportunityId ||
                  !contextData?.active_resume ||
                  !contextData.is_ready_for_analysis
                }
                className="w-full bg-[#1B5E3B] hover:bg-[#2E7D4F] text-white font-semibold py-2.5 shadow-sm transition-all flex items-center justify-center gap-2"
              >
                {analyzing ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Analyzing Resume Against Job...
                  </>
                ) : (
                  <>
                    <Wand2 className="w-4 h-4" />
                    Analyze Resume Against Job
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Error notification banner */}
      {analysisError && (
        <div className="p-4 rounded-xl border border-red-200 bg-red-50/80 text-red-900 text-sm flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-600 mt-0.5 shrink-0" />
          <div className="space-y-1">
            <div className="font-semibold">Analysis Notice</div>
            <p className="text-xs text-red-800">{analysisError}</p>
          </div>
        </div>
      )}

      {/* 2. Analysis Results View */}
      {analysisResult && (
        <div className="space-y-6 pt-2">
          {/* Header Overview Banner */}
          <div className="rounded-xl border border-[#1B5E3B]/20 bg-gradient-to-r from-[#1B5E3B]/10 via-[#F6FAF7] to-[#1B5E3B]/5 p-5 sm:p-6 shadow-sm">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <div>
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-[#1B5E3B] text-white">
                    Job-Specific Recommendations
                  </span>
                  {analysisResult.provider === "gemini" ? (
                    <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 border border-emerald-300 flex items-center gap-1">
                      <Sparkles className="w-3 h-3" />
                      Gemini AI-Assisted ({analysisResult.provider_model || "Flash"})
                    </span>
                  ) : (
                    <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-slate-100 text-slate-800 border border-slate-300 flex items-center gap-1">
                      <ShieldCheck className="w-3 h-3" />
                      Deterministic Engine (Zero External Calls)
                    </span>
                  )}
                  <span className="text-xs text-[#5A7362]">
                    Analyzed on {new Date(analysisResult.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
                <h2 className="text-xl sm:text-2xl font-bold text-[#14261C] mt-1.5">
                  {analysisResult.opportunity_title}
                </h2>
                <div className="text-sm text-[#5A7362] flex items-center gap-2 mt-0.5">
                  <span className="font-semibold text-gray-800">{analysisResult.company_name}</span>
                  <span>•</span>
                  <span>Active Resume: <strong className="text-gray-700">{analysisResult.resume_filename}</strong></span>
                  {analysisResult.resume_completeness_score && (
                    <span className="text-[#1B5E3B] font-semibold">
                      ({analysisResult.resume_completeness_score}% completeness)
                    </span>
                  )}
                </div>
              </div>

              {/* Action buttons */}
              <div className="flex items-center gap-2 self-stretch sm:self-auto">
                <Button
                  onClick={handleCopyAll}
                  variant="outline"
                  className="flex-1 sm:flex-none border-[#1B5E3B]/40 text-[#1B5E3B] hover:bg-[#1B5E3B]/10 font-medium text-xs flex items-center gap-1.5"
                >
                  {copiedAll ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                  {copiedAll ? "Copied Report!" : "Copy Recommendations"}
                </Button>
                <Button
                  onClick={handleAnalyze}
                  variant="outline"
                  size="icon"
                  title="Re-run analysis"
                  disabled={analyzing}
                  className="border-gray-300 hover:bg-gray-100 text-gray-700"
                >
                  <RefreshCw className={`w-4 h-4 ${analyzing ? "animate-spin" : ""}`} />
                </Button>
              </div>
            </div>

            {/* Quick Metrics Bar */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-5 pt-4 border-t border-[#1B5E3B]/15">
              <div className="bg-white/80 p-3 rounded-lg border border-border/80">
                <div className="text-xs text-[#5A7362]">Relevant Strengths</div>
                <div className="text-xl font-bold text-[#1B5E3B]">{analysisResult.strengths.length} Found</div>
              </div>
              <div className="bg-white/80 p-3 rounded-lg border border-border/80">
                <div className="text-xs text-[#5A7362]">Requirement Gaps</div>
                <div className="text-xl font-bold text-amber-600">{analysisResult.gaps.length} Areas</div>
              </div>
              <div className="bg-white/80 p-3 rounded-lg border border-border/80">
                <div className="text-xs text-[#5A7362]">Actionable Edits</div>
                <div className="text-xl font-bold text-[#14261C]">{analysisResult.improvements.length} Rewrites</div>
              </div>
              <div className="bg-white/80 p-3 rounded-lg border border-border/80">
                <div className="text-xs text-[#5A7362]">ATS Structure</div>
                <div className="text-xl font-bold text-emerald-700">
                  {analysisResult.ats_guidance.some((a) => a.status === "improvement_needed")
                    ? "Action Needed"
                    : "Verified"}
                </div>
              </div>
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="flex items-center gap-2 border-b border-border pb-1 overflow-x-auto">
            <button
              onClick={() => setActiveTab("overview")}
              className={`px-4 py-2 text-sm font-semibold rounded-t-lg transition-colors whitespace-nowrap flex items-center gap-2 ${
                activeTab === "overview"
                  ? "bg-white border-t-2 border-[#1B5E3B] text-[#1B5E3B] shadow-xs"
                  : "text-[#5A7362] hover:text-[#14261C]"
              }`}
            >
              <FileText className="w-4 h-4" />
              Overview &amp; Summary
            </button>
            <button
              onClick={() => setActiveTab("strengths")}
              className={`px-4 py-2 text-sm font-semibold rounded-t-lg transition-colors whitespace-nowrap flex items-center gap-2 ${
                activeTab === "strengths"
                  ? "bg-white border-t-2 border-[#1B5E3B] text-[#1B5E3B] shadow-xs"
                  : "text-[#5A7362] hover:text-[#14261C]"
              }`}
            >
              <CheckCircle2 className="w-4 h-4 text-[#1B5E3B]" />
              Relevant Strengths ({analysisResult.strengths.length})
            </button>
            <button
              onClick={() => setActiveTab("gaps")}
              className={`px-4 py-2 text-sm font-semibold rounded-t-lg transition-colors whitespace-nowrap flex items-center gap-2 ${
                activeTab === "gaps"
                  ? "bg-white border-t-2 border-[#1B5E3B] text-[#1B5E3B] shadow-xs"
                  : "text-[#5A7362] hover:text-[#14261C]"
              }`}
            >
              <AlertCircle className="w-4 h-4 text-amber-600" />
              Requirement Gaps ({analysisResult.gaps.length})
            </button>
            <button
              onClick={() => setActiveTab("improvements")}
              className={`px-4 py-2 text-sm font-semibold rounded-t-lg transition-colors whitespace-nowrap flex items-center gap-2 ${
                activeTab === "improvements"
                  ? "bg-white border-t-2 border-[#1B5E3B] text-[#1B5E3B] shadow-xs"
                  : "text-[#5A7362] hover:text-[#14261C]"
              }`}
            >
              <Wand2 className="w-4 h-4 text-emerald-600" />
              Actionable Rewrites ({analysisResult.improvements.length})
            </button>
            <button
              onClick={() => setActiveTab("ats")}
              className={`px-4 py-2 text-sm font-semibold rounded-t-lg transition-colors whitespace-nowrap flex items-center gap-2 ${
                activeTab === "ats"
                  ? "bg-white border-t-2 border-[#1B5E3B] text-[#1B5E3B] shadow-xs"
                  : "text-[#5A7362] hover:text-[#14261C]"
              }`}
            >
              <ShieldCheck className="w-4 h-4 text-gray-700" />
              ATS &amp; Formatting ({analysisResult.ats_guidance.length})
            </button>
          </div>

          {/* TAB 1: OVERVIEW */}
          {activeTab === "overview" && (
            <div className="space-y-6">
              <Card className="border-border shadow-sm">
                <CardHeader>
                  <CardTitle className="text-base font-semibold text-[#14261C]">
                    Data Completeness &amp; Sufficiency
                  </CardTitle>
                  <CardDescription className="text-xs text-[#5A7362]">
                    Audit of data inputs utilized during this analysis to ensure grounded recommendations.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div className="p-3 rounded-lg border border-gray-200 bg-gray-50/50 space-y-1.5">
                      <div className="text-xs font-semibold text-gray-700 flex items-center gap-1.5">
                        <CheckCircle2 className="w-4 h-4 text-[#1B5E3B]" />
                        Active Resume Analysis Status
                      </div>
                      <p className="text-xs text-gray-600">
                        {analysisResult.data_sufficiency.has_resume_text
                          ? "Resume text parsed and analyzed successfully."
                          : "Resume text was empty or incomplete."}
                      </p>
                    </div>

                    <div className="p-3 rounded-lg border border-gray-200 bg-gray-50/50 space-y-1.5">
                      <div className="text-xs font-semibold text-gray-700 flex items-center gap-1.5">
                        <CheckCircle2 className="w-4 h-4 text-[#1B5E3B]" />
                        Opportunity Context Availability
                      </div>
                      <p className="text-xs text-gray-600">
                        {analysisResult.data_sufficiency.has_job_description
                          ? "Full job description and required qualifications analyzed."
                          : "Basic skill tags analyzed; full description was limited."}
                      </p>
                    </div>
                  </div>

                  {analysisResult.data_sufficiency.details.length > 0 && (
                    <div className="p-3 rounded-lg bg-amber-50/80 border border-amber-200 text-xs text-amber-900 space-y-1">
                      <div className="font-semibold flex items-center gap-1.5">
                        <Info className="w-3.5 h-3.5 text-amber-700" />
                        Analysis Notes:
                      </div>
                      <ul className="list-disc list-inside space-y-0.5 text-amber-800">
                        {analysisResult.data_sufficiency.details.map((d, i) => (
                          <li key={i}>{d}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Highlights Summary */}
                  <div className="p-4 rounded-xl border border-[#1B5E3B]/20 bg-[#F6FAF7] space-y-3">
                    <div className="font-semibold text-sm text-[#14261C] flex items-center gap-2">
                      <Sparkles className="w-4 h-4 text-[#1B5E3B]" />
                      Executive Recommendation Summary
                    </div>
                    <p className="text-xs text-[#5A7362] leading-relaxed">
                      You possess strong existing alignment with <strong>{analysisResult.strengths.filter(s => s.category === "skill").length} core skills</strong> requested by {analysisResult.company_name}.
                      We have identified <strong>{analysisResult.gaps.length} missing skill requirements</strong> to be aware of, and generated <strong>{analysisResult.improvements.length} concrete bullet improvements</strong> you can paste into your resume.
                    </p>
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        onClick={() => setActiveTab("improvements")}
                        className="bg-[#1B5E3B] hover:bg-[#2E7D4F] text-white text-xs font-semibold"
                      >
                        Explore Bullet Rewrites &rarr;
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => setActiveTab("gaps")}
                        className="border-[#1B5E3B]/30 text-[#1B5E3B] text-xs font-semibold"
                      >
                        Review Skill Gaps
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Safety Disclaimers */}
              <div className="p-4 rounded-xl border border-gray-200 bg-white text-xs text-gray-600 space-y-2">
                <div className="font-semibold text-gray-800 flex items-center gap-1.5">
                  <ShieldCheck className="w-4 h-4 text-[#1B5E3B]" />
                  CareerPilot AI Trust &amp; Integrity Standards
                </div>
                <ul className="space-y-1 list-disc list-inside text-gray-500">
                  {analysisResult.disclaimers.map((d, idx) => (
                    <li key={idx}>{d}</li>
                  ))}
                </ul>
              </div>
            </div>
          )}

          {/* TAB 2: RELEVANT STRENGTHS */}
          {activeTab === "strengths" && (
            <div className="space-y-4">
              <div className="text-xs text-[#5A7362]">
                These credentials from your active resume and candidate profile directly support your candidacy for <strong>{analysisResult.opportunity_title}</strong>.
              </div>

              {analysisResult.strengths.length === 0 ? (
                <div className="p-8 text-center border border-dashed rounded-xl bg-white text-sm text-[#5A7362]">
                  No direct overlap detected with this specific role. Review the &quot;Requirement Gaps&quot; tab to see missing areas.
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {analysisResult.strengths.map((item, idx) => {
                    const iconMap = {
                      skill: <Target className="w-4 h-4 text-[#1B5E3B]" />,
                      project: <FolderGit2 className="w-4 h-4 text-blue-600" />,
                      experience: <Briefcase className="w-4 h-4 text-purple-600" />,
                      education: <GraduationCap className="w-4 h-4 text-emerald-600" />,
                    };
                    const icon = iconMap[item.category as keyof typeof iconMap] || <CheckCircle2 className="w-4 h-4 text-[#1B5E3B]" />;

                    return (
                      <Card key={idx} className="border-border shadow-xs hover:border-[#1B5E3B]/30 transition-all">
                        <CardHeader className="pb-2">
                          <div className="flex items-center justify-between gap-2">
                            <span className="flex items-center gap-2 font-semibold text-sm text-[#14261C]">
                              {icon}
                              {item.title}
                            </span>
                            <Badge
                              variant="outline"
                              className={`text-[10px] uppercase font-semibold ${
                                item.source === "both"
                                  ? "bg-[#1B5E3B]/10 text-[#1B5E3B] border-[#1B5E3B]/30"
                                  : item.source === "profile"
                                  ? "bg-blue-50 text-blue-700 border-blue-200"
                                  : "bg-purple-50 text-purple-700 border-purple-200"
                              }`}
                            >
                              {item.source === "both" ? "Profile & Resume" : item.source === "profile" ? "Verified Profile" : "Resume Evidence"}
                            </Badge>
                          </div>
                        </CardHeader>
                        <CardContent className="space-y-2 text-xs">
                          <p className="text-gray-700 font-medium">{item.relevance_explanation}</p>
                          <div className="p-2.5 rounded bg-gray-50 border border-gray-100 text-gray-600 italic">
                            Evidence: {item.evidence}
                          </div>
                        </CardContent>
                      </Card>
                    );
                  })}
                </div>
              )}
            </div>
          )}

          {/* TAB 3: REQUIREMENT GAPS */}
          {activeTab === "gaps" && (
            <div className="space-y-4">
              <div className="p-3 rounded-lg border border-amber-200 bg-amber-50/70 text-xs text-amber-900 flex items-start gap-2">
                <Info className="w-4 h-4 text-amber-700 shrink-0 mt-0.5" />
                <div>
                  <strong>Honest Skill Assessment:</strong> Missing evidence does not mean you lack the competency.
                  If you have coursework, personal projects, or internships using these tools, add them to your profile and mention them on your resume. Never claim skills you cannot defend in an interview.
                </div>
              </div>

              {analysisResult.gaps.length === 0 ? (
                <div className="p-8 text-center border rounded-xl bg-white text-sm text-[#1B5E3B] font-semibold flex flex-col items-center gap-2">
                  <CheckCircle2 className="w-8 h-8 text-[#1B5E3B]" />
                  No Requirement Gaps Detected!
                  <span className="text-xs text-[#5A7362] font-normal">
                    Your active resume and verified profile skills evidenced all core requirements specified in this job posting.
                  </span>
                </div>
              ) : (
                <div className="space-y-3">
                  {analysisResult.gaps.map((gap, idx) => (
                    <Card key={idx} className="border-border shadow-xs">
                      <CardContent className="p-4 space-y-2 text-xs">
                        <div className="flex items-center justify-between">
                          <div className="font-semibold text-sm text-gray-900 flex items-center gap-2">
                            <AlertCircle className="w-4 h-4 text-amber-600" />
                            {gap.skill_name}
                          </div>
                          <Badge
                            variant="outline"
                            className={`text-[10px] font-semibold uppercase ${
                              gap.requirement_level === "required"
                                ? "bg-red-50 text-red-700 border-red-200"
                                : "bg-amber-50 text-amber-700 border-amber-200"
                            }`}
                          >
                            {gap.requirement_level === "required" ? "Required / Core" : "Preferred / Bonus"}
                          </Badge>
                        </div>
                        <p className="text-gray-700">{gap.explanation}</p>
                        <div className="p-3 rounded bg-blue-50/60 border border-blue-100 text-blue-900 flex items-start gap-2">
                          <ArrowRight className="w-3.5 h-3.5 text-blue-700 mt-0.5 shrink-0" />
                          <span>
                            <strong>Candidate Guidance:</strong> {gap.student_guidance}
                          </span>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* TAB 4: ACTIONABLE REWRITES */}
          {activeTab === "improvements" && (
            <div className="space-y-4">
              <div className="flex items-center justify-between text-xs text-[#5A7362]">
                <span>
                  Prioritized recommendations to strengthen wording, elevate key accomplishments, and align with {analysisResult.opportunity_title}.
                </span>
                <span className="font-semibold text-gray-700">
                  {analysisResult.improvements.length} Recommendations
                </span>
              </div>

              {analysisResult.improvements.length === 0 ? (
                <div className="p-8 text-center border rounded-xl bg-white text-sm text-[#5A7362]">
                  No specific bullet edits needed. Your active resume phrasing is already concise and metric-driven.
                </div>
              ) : (
                <div className="space-y-4">
                  {analysisResult.improvements.map((imp, idx) => {
                    const isBulletRewrite = imp.category === "bullet_rewrite";
                    return (
                      <Card key={idx} className="border-border shadow-sm">
                        <CardHeader className="pb-2">
                          <div className="flex items-center justify-between gap-2 flex-wrap">
                            <span className="font-semibold text-sm text-[#14261C] flex items-center gap-2">
                              {isBulletRewrite ? (
                                <Wand2 className="w-4 h-4 text-[#1B5E3B]" />
                              ) : (
                                <Sparkles className="w-4 h-4 text-emerald-600" />
                              )}
                              {imp.title}
                            </span>
                            <div className="flex items-center gap-2">
                              {imp.is_gemini_assisted && (
                                <Badge className="bg-emerald-100 text-emerald-800 border-emerald-300 text-[10px] flex items-center gap-1">
                                  <Sparkles className="w-2.5 h-2.5" />
                                  Gemini Assisted
                                </Badge>
                              )}
                              <Badge
                                variant="outline"
                                className={`text-[10px] uppercase font-semibold ${
                                  imp.priority === "high"
                                    ? "bg-red-50 text-red-700 border-red-200"
                                    : "bg-blue-50 text-blue-700 border-blue-200"
                                }`}
                              >
                                {imp.priority} Priority
                              </Badge>
                            </div>
                          </div>
                          <CardDescription className="text-xs text-[#5A7362]">
                            {imp.reason}
                          </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-3 text-xs">
                          {/* Original phrasing if applicable */}
                          {imp.original_content && (
                            <div className="space-y-1">
                              <span className="font-semibold text-gray-500 uppercase tracking-wider text-[10px]">
                                Original from your resume:
                              </span>
                              <div className="p-2.5 rounded bg-gray-50 border border-gray-200 text-gray-700 line-through decoration-red-400">
                                {imp.original_content}
                              </div>
                            </div>
                          )}

                          {/* Suggested rewrite if applicable */}
                          {imp.suggested_wording && (
                            <div className="space-y-1">
                              <div className="flex items-center justify-between">
                                <span className="font-semibold text-[#1B5E3B] uppercase tracking-wider text-[10px] flex items-center gap-1">
                                  <Check className="w-3 h-3" />
                                  Suggested High-Impact Phrasing:
                                </span>
                                <Button
                                  size="sm"
                                  variant="ghost"
                                  onClick={() => handleCopyText(imp.suggested_wording!, `imp-${idx}`)}
                                  className="h-6 text-[10px] text-[#1B5E3B] hover:bg-[#1B5E3B]/10 font-medium flex items-center gap-1"
                                >
                                  {copiedId === `imp-${idx}` ? (
                                    <>
                                      <Check className="w-3 h-3 text-[#1B5E3B]" />
                                      Copied!
                                    </>
                                  ) : (
                                    <>
                                      <Copy className="w-3 h-3" />
                                      Copy Phrasing
                                    </>
                                  )}
                                </Button>
                              </div>
                              <div className="p-3 rounded-lg bg-[#F6FAF7] border border-[#1B5E3B]/30 text-gray-900 font-medium">
                                {imp.suggested_wording}
                              </div>
                              <p className="text-[11px] text-gray-500 italic">
                                Note: Bracketed fields like <code>[insert metric]</code> require your verified numbers. Do not claim metrics you did not achieve.
                              </p>
                            </div>
                          )}

                          {imp.evidence_support && (
                            <div className="text-[11px] text-[#5A7362] flex items-center gap-1.5 pt-1">
                              <Info className="w-3.5 h-3.5" />
                              <span>{imp.evidence_support}</span>
                            </div>
                          )}
                        </CardContent>
                      </Card>
                    );
                  })}
                </div>
              )}
            </div>
          )}

          {/* TAB 5: ATS & FORMATTING */}
          {activeTab === "ats" && (
            <div className="space-y-4">
              <div className="p-3 rounded-lg border border-gray-200 bg-gray-50/80 text-xs text-gray-700 space-y-1">
                <div className="font-semibold text-gray-900 flex items-center gap-1.5">
                  <ShieldCheck className="w-4 h-4 text-[#1B5E3B]" />
                  What is ATS Optimization?
                </div>
                <p className="text-gray-600 leading-relaxed">
                  Applicant Tracking Systems (ATS) scan and index resume text into search fields for human recruiters.
                  Clear headings, conventional sections, and natural keyword proximity guarantee your credentials are indexed cleanly without parsing errors.
                </p>
              </div>

              <div className="space-y-3">
                {analysisResult.ats_guidance.map((item, idx) => (
                  <Card key={idx} className="border-border shadow-xs">
                    <CardHeader className="pb-2">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-sm text-[#14261C] flex items-center gap-2">
                          <CheckCircle2
                            className={`w-4 h-4 ${
                              item.status === "good"
                                ? "text-[#1B5E3B]"
                                : item.status === "improvement_needed"
                                ? "text-amber-600"
                                : "text-blue-600"
                            }`}
                          />
                          {item.title}
                        </span>
                        <Badge
                          variant="outline"
                          className={`text-[10px] font-semibold uppercase ${
                            item.status === "good"
                              ? "bg-emerald-50 text-emerald-800 border-emerald-200"
                              : item.status === "improvement_needed"
                              ? "bg-amber-50 text-amber-800 border-amber-200"
                              : "bg-blue-50 text-blue-800 border-blue-200"
                          }`}
                        >
                          {item.status.replace("_", " ")}
                        </Badge>
                      </div>
                    </CardHeader>
                    <CardContent className="space-y-2 text-xs">
                      <p className="text-gray-800 font-medium">{item.recommendation}</p>
                      <div className="p-2.5 rounded bg-gray-50 border border-gray-100 text-gray-600">
                        <strong>Why this matters:</strong> {item.rationale}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>

              {/* Disclaimer */}
              <div className="p-4 rounded-xl border border-amber-200 bg-amber-50/60 text-xs text-amber-900 space-y-1">
                <div className="font-semibold flex items-center gap-1.5">
                  <AlertTriangle className="w-4 h-4 text-amber-700" />
                  Score Integrity Notice
                </div>
                <p>
                  CareerPilot AI does not compute or claim a proprietary ATS pass probability, score guarantee, or interview prediction.
                  All suggestions target structural readability and keyword relevance for standard parsers.
                </p>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
