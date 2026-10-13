"use client";

import { useEffect, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import {
  AlertCircle,
  Briefcase,
  Check,
  CheckCircle2,
  Copy,
  Download,
  FileEdit,
  HelpCircle,
  Info,
  Lightbulb,
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
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { createClient } from "@/lib/supabase/client";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface OpportunityItem {
  id: string;
  title: string;
  company_name: string;
  opportunity_type: string;
  work_model: string;
  locations: string[];
  domain?: string;
  skills?: { id: string; name: string }[];
}

interface QuestionEvidenceSummary {
  matched_skills: string[];
  verified_skills: string[];
  resume_skills: string[];
  included_projects: string[];
  included_experiences: string[];
  included_education: string[];
  missing_information_notes: string[];
}

interface GeneratedAnswerData {
  question: string;
  opportunity_id?: string | null;
  opportunity_title?: string | null;
  company_name?: string | null;
  style: string;
  word_limit?: number | null;
  answer_text: string;
  provider: string;
  provider_model?: string | null;
  is_template_fallback: boolean;
  provider_note?: string | null;
  verified_evidence: QuestionEvidenceSummary;
  data_warnings: string[];
  disclaimer: string;
}

interface SuggestedQuestion {
  category: string;
  question: string;
  description: string;
}

export function ApplicationAssistant() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const preselectedOppId = searchParams.get("opportunity_id");

  // Selection & Form State
  const [opportunities, setOpportunities] = useState<OpportunityItem[]>([]);
  const [loadingOpportunities, setLoadingOpportunities] = useState(true);
  const [searchFilter, setSearchFilter] = useState("");
  const [selectedOpportunityId, setSelectedOpportunityId] = useState<string | null>(
    preselectedOppId || null
  );
  const [isGeneralMode, setIsGeneralMode] = useState<boolean>(!preselectedOppId);

  const [question, setQuestion] = useState("");
  const [style, setStyle] = useState<"professional" | "concise" | "detailed">("professional");
  const [wordLimit, setWordLimit] = useState<string>("");
  const [additionalContext, setAdditionalContext] = useState("");

  const [suggestedQuestions, setSuggestedQuestions] = useState<SuggestedQuestion[]>([]);

  // Execution State
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [generatedAnswer, setGeneratedAnswer] = useState<GeneratedAnswerData | null>(null);
  const [editableAnswer, setEditableAnswer] = useState("");
  const [copied, setCopied] = useState(false);

  // Fetch opportunities on mount
  useEffect(() => {
    async function loadOpportunities() {
      try {
        setLoadingOpportunities(true);
        const res = await fetch(`${API_URL}/api/v1/opportunities?limit=100`);
        if (!res.ok) throw new Error("Failed to load opportunities");
        const json = await res.json();
        const items: OpportunityItem[] = Array.isArray(json) ? json : json.items || [];
        setOpportunities(items);

        if (preselectedOppId && items.some((o) => o.id === preselectedOppId)) {
          setSelectedOpportunityId(preselectedOppId);
          setIsGeneralMode(false);
        }
      } catch (err) {
        console.error("Error loading opportunities:", err);
      } finally {
        setLoadingOpportunities(false);
      }
    }
    loadOpportunities();
  }, [preselectedOppId]);

  // Fetch suggested questions on mount
  useEffect(() => {
    async function loadSuggested() {
      try {
        const supabase = createClient();
        const {
          data: { session },
        } = await supabase.auth.getSession();
        if (!session) return;

        const res = await fetch(`${API_URL}/api/v1/copilot/application-assistant/suggested-questions`, {
          headers: {
            Authorization: `Bearer ${session.access_token}`,
          },
        });
        if (res.ok) {
          const json = await res.json();
          setSuggestedQuestions(json.suggested_questions || []);
        }
      } catch {
        // Fallback to static suggestions if API call fails
      }
    }
    loadSuggested();
  }, []);

  const selectedOpp = opportunities.find((o) => o.id === selectedOpportunityId);

  // Handle generation
  const handleGenerate = async () => {
    if (!question.trim()) {
      setError("Please enter an application question.");
      return;
    }

    try {
      setGenerating(true);
      setError(null);

      const supabase = createClient();
      const {
        data: { session },
      } = await supabase.auth.getSession();

      if (!session) {
        router.push("/auth/login");
        return;
      }

      const parsedLimit = wordLimit.trim() ? parseInt(wordLimit.trim(), 10) : null;

      const payload = {
        question: question.trim(),
        opportunity_id: isGeneralMode ? null : selectedOpportunityId,
        style,
        word_limit: parsedLimit && parsedLimit > 0 ? parsedLimit : null,
        additional_context: additionalContext.trim() ? additionalContext.trim() : null,
      };

      const res = await fetch(`${API_URL}/api/v1/copilot/application-assistant/generate`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${session.access_token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errJson = await res.json().catch(() => null);
        throw new Error(errJson?.detail || `Generation failed with status ${res.status}`);
      }

      const json: GeneratedAnswerData = await res.json();
      setGeneratedAnswer(json);
      setEditableAnswer(json.answer_text);
    } catch (err: unknown) {
      console.error(err);
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setGenerating(false);
    }
  };

  // Copy helper
  const handleCopy = async () => {
    if (!editableAnswer) return;
    try {
      await navigator.clipboard.writeText(editableAnswer);
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    } catch {
      // Clipboard fallback
    }
  };

  // Download helper
  const handleDownloadTxt = () => {
    if (!editableAnswer || !generatedAnswer) return;
    const content = `Question: ${generatedAnswer.question}\n\n${editableAnswer}`;
    const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    const oppSuffix = generatedAnswer.company_name
      ? `_${generatedAnswer.company_name.replace(/\s+/g, "_")}`
      : "";
    link.download = `Application_Answer${oppSuffix}.txt`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  // Filtered opportunities for selector
  const filteredOpps = opportunities.filter(
    (o) =>
      searchFilter.trim() === "" ||
      o.title.toLowerCase().includes(searchFilter.toLowerCase()) ||
      o.company_name.toLowerCase().includes(searchFilter.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* 2-Column Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Form & Context Controls (5 cols) */}
        <div className="lg:col-span-5 space-y-5">
          {/* 1. Target Opportunity / Context Selection */}
          <Card className="border-[#DAE3DC] bg-white shadow-xs">
            <CardHeader className="pb-3">
              <CardTitle className="text-base font-bold text-[#14261C] flex items-center gap-2">
                <Target className="w-4 h-4 text-[#1B5E3B]" />
                1. Target Context (Optional)
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => {
                    setIsGeneralMode(true);
                    setSelectedOpportunityId(null);
                  }}
                  className={`flex-1 py-1.5 px-3 rounded-lg text-xs font-semibold border transition-all ${
                    isGeneralMode
                      ? "border-[#1B5E3B] bg-[#E5EDE7] text-[#1B5E3B]"
                      : "border-[#DAE3DC] bg-white text-[#5A7362] hover:bg-[#F6FAF7]"
                  }`}
                >
                  General Application
                </button>
                <button
                  type="button"
                  onClick={() => setIsGeneralMode(false)}
                  className={`flex-1 py-1.5 px-3 rounded-lg text-xs font-semibold border transition-all ${
                    !isGeneralMode
                      ? "border-[#1B5E3B] bg-[#E5EDE7] text-[#1B5E3B]"
                      : "border-[#DAE3DC] bg-white text-[#5A7362] hover:bg-[#F6FAF7]"
                  }`}
                >
                  Specific Published Job
                </button>
              </div>

              {!isGeneralMode && (
                <>
                  <div className="relative mt-2">
                    <Search className="w-3.5 h-3.5 text-[#5A7362] absolute left-3 top-1/2 -translate-y-1/2" />
                    <Input
                      placeholder="Search published jobs..."
                      value={searchFilter}
                      onChange={(e) => setSearchFilter(e.target.value)}
                      className="pl-8 h-8 text-xs bg-[#F6FAF7] border-[#DAE3DC]"
                    />
                  </div>

                  {loadingOpportunities ? (
                    <div className="h-10 rounded-md bg-[#F0F5F1] animate-pulse" />
                  ) : (
                    <div className="max-h-40 overflow-y-auto space-y-1.5 border border-[#DAE3DC] rounded-lg p-1.5 bg-[#F6FAF7]">
                      {filteredOpps.length === 0 ? (
                        <p className="text-xs text-[#5A7362] p-2 text-center">
                          No matching opportunities found
                        </p>
                      ) : (
                        filteredOpps.map((opp) => {
                          const isSelected = selectedOpportunityId === opp.id;
                          return (
                            <button
                              key={opp.id}
                              type="button"
                              onClick={() => setSelectedOpportunityId(opp.id)}
                              className={`w-full text-left p-2 rounded-md text-xs transition-all flex items-start justify-between gap-2 ${
                                isSelected
                                  ? "bg-[#1B5E3B] text-white shadow-xs"
                                  : "hover:bg-white text-[#14261C]"
                              }`}
                            >
                              <div className="min-w-0">
                                <p className="font-semibold truncate">{opp.title}</p>
                                <p
                                  className={`text-[11px] truncate ${
                                    isSelected ? "text-white/80" : "text-[#5A7362]"
                                  }`}
                                >
                                  {opp.company_name} • {opp.work_model}
                                </p>
                              </div>
                              {isSelected && <Check className="w-3.5 h-3.5 shrink-0 mt-0.5" />}
                            </button>
                          );
                        })
                      )}
                    </div>
                  )}

                  {selectedOpp && (
                    <div className="bg-[#F6FAF7] border border-[#DAE3DC] rounded-lg p-2.5 text-xs space-y-1.5">
                      <div className="flex items-start justify-between">
                        <div>
                          <h4 className="font-bold text-[#14261C]">{selectedOpp.title}</h4>
                          <p className="text-[#5A7362]">{selectedOpp.company_name}</p>
                        </div>
                        <Badge variant="outline" className="text-[10px] bg-white border-[#DAE3DC]">
                          {selectedOpp.opportunity_type}
                        </Badge>
                      </div>
                      <div className="flex items-center gap-1.5 text-[11px] text-[#5A7362]">
                        <MapPin className="w-3 h-3" />
                        <span>{selectedOpp.locations?.join(", ") || selectedOpp.work_model}</span>
                      </div>
                    </div>
                  )}
                </>
              )}
            </CardContent>
          </Card>

          {/* 2. Application Question Input */}
          <Card className="border-[#DAE3DC] bg-white shadow-xs">
            <CardHeader className="pb-3">
              <CardTitle className="text-base font-bold text-[#14261C] flex items-center justify-between">
                <span className="flex items-center gap-2">
                  <HelpCircle className="w-4 h-4 text-[#1B5E3B]" />
                  2. Application Question
                </span>
                <span className="text-[11px] font-normal text-[#5A7362]">
                  {question.length}/1000
                </span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <Textarea
                placeholder="e.g., Why should we hire you? What is a technical challenge you solved? How do your skills match this role?"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                maxLength={1000}
                rows={3}
                className="text-xs border-[#DAE3DC] bg-[#F6FAF7] focus:bg-white resize-y"
              />

              {/* Quick Pick Chips */}
              {suggestedQuestions.length > 0 && (
                <div className="space-y-1.5 pt-1">
                  <div className="flex items-center gap-1.5 text-[11px] font-semibold text-[#5A7362]">
                    <Lightbulb className="w-3.5 h-3.5 text-[#F59E0B]" />
                    <span>Quick-Pick Common Questions:</span>
                  </div>
                  <div className="flex flex-wrap gap-1.5 max-h-32 overflow-y-auto">
                    {suggestedQuestions.map((sq, idx) => (
                      <button
                        key={idx}
                        type="button"
                        onClick={() => setQuestion(sq.question)}
                        className="text-[10px] text-left bg-[#F6FAF7] hover:bg-[#E5EDE7] hover:text-[#1B5E3B] text-[#14261C] border border-[#DAE3DC] px-2 py-1 rounded-md transition-all truncate max-w-full"
                        title={sq.description}
                      >
                        {sq.question}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* 3. Style & Constraints */}
          <Card className="border-[#DAE3DC] bg-white shadow-xs">
            <CardHeader className="pb-3">
              <CardTitle className="text-base font-bold text-[#14261C] flex items-center gap-2">
                <Wand2 className="w-4 h-4 text-[#1B5E3B]" />
                3. Style &amp; Length Options
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Style Selection */}
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-[#14261C]">Response Style</label>
                <div className="grid grid-cols-3 gap-2">
                  {(
                    [
                      { key: "professional", label: "Professional", desc: "~200 words" },
                      { key: "concise", label: "Concise", desc: "~120 words" },
                      { key: "detailed", label: "Detailed", desc: "~300 words" },
                    ] as const
                  ).map((s) => (
                    <button
                      key={s.key}
                      type="button"
                      onClick={() => setStyle(s.key)}
                      className={`p-2 rounded-lg text-left text-xs border transition-all ${
                        style === s.key
                          ? "border-[#1B5E3B] bg-[#E5EDE7]/50 text-[#14261C] font-semibold"
                          : "border-[#DAE3DC] bg-white text-[#5A7362] hover:bg-[#F6FAF7]"
                      }`}
                    >
                      <p className="font-semibold leading-tight">{s.label}</p>
                      <p className="text-[10px] text-[#5A7362] mt-0.5">{s.desc}</p>
                    </button>
                  ))}
                </div>
              </div>

              {/* Optional Word Limit & Focus Notes */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-[#14261C]">Word Limit (Optional)</label>
                  <Input
                    type="number"
                    min={30}
                    max={1000}
                    placeholder="e.g. 150"
                    value={wordLimit}
                    onChange={(e) => setWordLimit(e.target.value)}
                    className="h-8 text-xs bg-[#F6FAF7] border-[#DAE3DC]"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-semibold text-[#14261C]">Specific Angle (Optional)</label>
                  <Input
                    placeholder="e.g. Emphasize testing"
                    value={additionalContext}
                    onChange={(e) => setAdditionalContext(e.target.value)}
                    maxLength={500}
                    className="h-8 text-xs bg-[#F6FAF7] border-[#DAE3DC]"
                  />
                </div>
              </div>

              {/* Error Alert */}
              {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 p-3 rounded-lg text-xs flex items-start gap-2">
                  <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                  <div className="space-y-0.5">
                    <p className="font-semibold">Generation Error</p>
                    <p className="leading-relaxed">{error}</p>
                  </div>
                </div>
              )}

              {/* Generate Action Button */}
              <Button
                onClick={handleGenerate}
                disabled={generating || !question.trim()}
                className="w-full bg-[#1B5E3B] hover:bg-[#2E7D4F] text-white font-semibold h-10 gap-2 shadow-xs"
              >
                {generating ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    Generating Grounded Answer...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4" />
                    {generatedAnswer ? "Regenerate Answer" : "Generate Tailored Answer"}
                  </>
                )}
              </Button>

              <div className="flex items-center gap-2 text-[11px] text-[#5A7362] justify-center pt-1">
                <ShieldCheck className="w-3.5 h-3.5 text-[#1B5E3B]" />
                <span>Zero hallucinations: grounded strictly in your verified records.</span>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right Column: Answer Preview, Editor & Audit Trail (7 cols) */}
        <div className="lg:col-span-7 space-y-5">
          {!generatedAnswer && !generating && (
            <Card className="border-[#DAE3DC] bg-white shadow-xs p-12 text-center space-y-4">
              <div className="w-14 h-14 rounded-full bg-[#E5EDE7] text-[#1B5E3B] mx-auto flex items-center justify-center">
                <FileEdit className="w-7 h-7" />
              </div>
              <div className="space-y-1 max-w-md mx-auto">
                <h3 className="text-lg font-bold text-[#14261C]">Ready to Answer Your Questions</h3>
                <p className="text-xs sm:text-sm text-[#5A7362] leading-relaxed">
                  Enter an application question on the left (or select a common question chip) and click
                  &ldquo;Generate Tailored Answer&rdquo;. CareerPilot AI grounds every response strictly in
                  your verified projects, skills, and academic history.
                </p>
              </div>
              <div className="flex flex-wrap items-center justify-center gap-2 pt-2 text-xs text-[#5A7362]">
                <span className="flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5 text-[#1B5E3B]" /> Verified Facts Only
                </span>
                <span>•</span>
                <span className="flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5 text-[#1B5E3B]" /> Fully Editable Draft
                </span>
                <span>•</span>
                <span className="flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5 text-[#1B5E3B]" /> 1-Click Clipboard Copy
                </span>
              </div>
            </Card>
          )}

          {generating && (
            <Card className="border-[#DAE3DC] bg-white shadow-xs p-12 text-center space-y-4 animate-pulse">
              <div className="w-12 h-12 rounded-full bg-[#F0F5F1] mx-auto flex items-center justify-center">
                <RefreshCw className="w-6 h-6 text-[#1B5E3B] animate-spin" />
              </div>
              <div className="space-y-2">
                <h3 className="text-base font-bold text-[#14261C]">Synthesizing Your Verified Records...</h3>
                <p className="text-xs text-[#5A7362]">
                  Analyzing your projects, matching skills with {selectedOpp?.company_name || "the role"}, and structuring an authentic response.
                </p>
              </div>
            </Card>
          )}

          {generatedAnswer && (
            <div className="space-y-4">
              {/* Provider & Transparency Toolbar */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 bg-white border border-[#DAE3DC] rounded-xl px-4 py-3 shadow-xs">
                <div className="flex items-center gap-2">
                  {generatedAnswer.is_template_fallback ? (
                    <Badge variant="outline" className="bg-[#FFF8EB] border-[#F59E0B]/30 text-[#B45309] text-[10px]">
                      Deterministic Template Draft
                    </Badge>
                  ) : (
                    <Badge className="bg-[#1B5E3B] text-white text-[10px]">
                      AI Assisted ({generatedAnswer.provider_model || "Gemini"})
                    </Badge>
                  )}
                  <span className="text-xs text-[#5A7362]">
                    Style: <strong className="text-[#14261C] capitalize">{generatedAnswer.style}</strong>
                    {generatedAnswer.word_limit && (
                      <span> • Max: <strong className="text-[#14261C]">{generatedAnswer.word_limit}w</strong></span>
                    )}
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={handleCopy}
                    className="h-8 text-xs gap-1.5 border-[#DAE3DC] hover:bg-[#F6FAF7]"
                  >
                    {copied ? (
                      <>
                        <Check className="w-3.5 h-3.5 text-[#1B5E3B]" />
                        <span className="text-[#1B5E3B] font-semibold">Copied!</span>
                      </>
                    ) : (
                      <>
                        <Copy className="w-3.5 h-3.5" />
                        Copy Answer
                      </>
                    )}
                  </Button>

                  <Button
                    size="sm"
                    variant="outline"
                    onClick={handleDownloadTxt}
                    className="h-8 text-xs gap-1.5 border-[#DAE3DC] hover:bg-[#F6FAF7]"
                  >
                    <Download className="w-3.5 h-3.5" />
                    Download .txt
                  </Button>
                </div>
              </div>

              {/* Question Context Header */}
              <div className="bg-white border border-[#DAE3DC] rounded-xl p-3 shadow-xs">
                <span className="text-[10px] uppercase font-bold text-[#5A7362] block">Application Question:</span>
                <p className="text-xs font-semibold text-[#14261C] mt-0.5">{generatedAnswer.question}</p>
                {generatedAnswer.opportunity_title && (
                  <p className="text-[11px] text-[#5A7362] mt-1 flex items-center gap-1.5">
                    <Briefcase className="w-3 h-3 text-[#1B5E3B]" />
                    <span>
                      Target: <strong className="text-[#14261C]">{generatedAnswer.opportunity_title}</strong> at {generatedAnswer.company_name}
                    </span>
                  </p>
                )}
              </div>

              {/* Editable Answer Textarea Card */}
              <Card className="border-[#DAE3DC] bg-white shadow-xs overflow-hidden">
                <div className="p-3 bg-[#F6FAF7] border-b border-[#DAE3DC] flex items-center justify-between text-xs text-[#5A7362]">
                  <span className="font-semibold text-[#14261C]">Generated Draft (Editable)</span>
                  <span>
                    {editableAnswer.split(/\s+/).filter(Boolean).length} Words • {editableAnswer.length} Characters
                  </span>
                </div>
                <CardContent className="p-4 sm:p-5">
                  <Textarea
                    value={editableAnswer}
                    onChange={(e) => setEditableAnswer(e.target.value)}
                    rows={12}
                    className="w-full text-sm leading-relaxed text-[#14261C] border-[#DAE3DC] focus:ring-[#1B5E3B] font-sans resize-y bg-white"
                  />
                </CardContent>
              </Card>

              {/* Evidence Audit Trail Card */}
              <Card className="border-[#DAE3DC] bg-white shadow-xs">
                <CardHeader className="py-3 px-4 border-b border-[#DAE3DC]">
                  <CardTitle className="text-xs font-bold text-[#14261C] flex items-center gap-1.5">
                    <ShieldCheck className="w-4 h-4 text-[#1B5E3B]" />
                    Audit Trail: Grounded Evidence In Answer
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-4 space-y-2.5 text-xs">
                  {/* Matched skills */}
                  {generatedAnswer.verified_evidence.matched_skills.length > 0 && (
                    <div className="flex items-baseline gap-2">
                      <span className="text-[#5A7362] shrink-0 w-32 font-medium">Matched Skills:</span>
                      <div className="flex flex-wrap gap-1">
                        {generatedAnswer.verified_evidence.matched_skills.map((s) => (
                          <Badge key={s} variant="outline" className="text-[10px] bg-[#F6FAF7] border-[#DAE3DC]">
                            {s}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Profile Verified Skills */}
                  {generatedAnswer.verified_evidence.verified_skills.length > 0 && (
                    <div className="flex items-baseline gap-2">
                      <span className="text-[#5A7362] shrink-0 w-32 font-medium">Profile Skills:</span>
                      <div className="flex flex-wrap gap-1">
                        {generatedAnswer.verified_evidence.verified_skills.map((s) => (
                          <span key={s} className="text-[10px] bg-white border border-[#DAE3DC] px-1.5 py-0.5 rounded text-[#14261C]">
                            {s}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Resume-Extracted Skills */}
                  {generatedAnswer.verified_evidence.resume_skills.length > 0 && (
                    <div className="flex items-baseline gap-2">
                      <span className="text-[#5A7362] shrink-0 w-32 font-medium">Resume Evidence:</span>
                      <div className="flex flex-wrap gap-1">
                        {generatedAnswer.verified_evidence.resume_skills.map((s) => (
                          <Badge key={s} variant="outline" className="text-[10px] bg-[#E5EDE7]/40 text-[#1B5E3B] border-[#1B5E3B]/30">
                            {s} (Resume)
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Projects Cited */}
                  {generatedAnswer.verified_evidence.included_projects.length > 0 && (
                    <div className="flex items-baseline gap-2">
                      <span className="text-[#5A7362] shrink-0 w-32 font-medium">Projects Cited:</span>
                      <div className="flex flex-wrap gap-1">
                        {generatedAnswer.verified_evidence.included_projects.map((p) => (
                          <Badge key={p} variant="outline" className="text-[10px] bg-white border-[#DAE3DC]">
                            {p}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Experience Cited */}
                  {generatedAnswer.verified_evidence.included_experiences.length > 0 && (
                    <div className="flex items-baseline gap-2">
                      <span className="text-[#5A7362] shrink-0 w-32 font-medium">Experience Cited:</span>
                      <span className="text-[#14261C]">{generatedAnswer.verified_evidence.included_experiences.join("; ")}</span>
                    </div>
                  )}

                  {/* Education Cited */}
                  {generatedAnswer.verified_evidence.included_education.length > 0 && (
                    <div className="flex items-baseline gap-2">
                      <span className="text-[#5A7362] shrink-0 w-32 font-medium">Education Cited:</span>
                      <span className="text-[#14261C]">{generatedAnswer.verified_evidence.included_education.join("; ")}</span>
                    </div>
                  )}

                  {/* Missing notes */}
                  {generatedAnswer.verified_evidence.missing_information_notes.length > 0 && (
                    <div className="pt-2 border-t border-[#DAE3DC]/60 space-y-1">
                      <span className="text-[11px] font-semibold text-[#B45309]">Missing Information / Verification Notes:</span>
                      <ul className="list-disc list-inside text-[11px] text-[#5A7362] space-y-0.5">
                        {generatedAnswer.verified_evidence.missing_information_notes.map((n, i) => (
                          <li key={i}>{n}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {generatedAnswer.provider_note && (
                    <p className="text-[11px] text-[#5A7362] pt-2 border-t border-[#DAE3DC]/60 italic">
                      Note: {generatedAnswer.provider_note}
                    </p>
                  )}
                </CardContent>
              </Card>

              {/* Review & Safety Disclaimer */}
              <div className="bg-[#FFF8EB] border border-[#F59E0B]/30 rounded-xl p-4 flex items-start gap-3 text-xs text-[#92400E] shadow-xs">
                <Info className="w-4 h-4 text-[#D97706] shrink-0 mt-0.5" />
                <div className="space-y-1">
                  <p className="font-semibold text-[#78350F]">Review Before Submitting</p>
                  <p className="leading-relaxed">{generatedAnswer.disclaimer}</p>
                  <p className="text-[11px] text-[#92400E]/80">
                    CareerPilot AI does not automatically submit applications or contact recruiters. You remain in complete control of your application responses.
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
