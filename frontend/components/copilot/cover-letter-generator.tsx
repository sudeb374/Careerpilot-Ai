"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import {
  AlertCircle,
  Check,
  CheckCircle2,
  Copy,
  Download,
  FileEdit,
  Info,
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

interface OpportunityOption {
  id: string;
  title: string;
  company_name: string;
  opportunity_type: string;
  work_model: string;
  locations?: string[];
  skills?: { id: string; name: string }[];
}

interface VerifiedEvidence {
  matched_skills: string[];
  included_projects: string[];
  included_experiences: string[];
  included_education: string[];
  resume_evidence_snippets: string[];
}

interface GeneratedLetterData {
  opportunity_id: string;
  opportunity_title: string;
  company_name: string;
  recipient_name: string;
  tone: "professional" | "enthusiastic" | "confident";
  length: "concise" | "standard" | "detailed";
  subject_line: string;
  cover_letter_text: string;
  provider: string;
  provider_model?: string | null;
  is_template_fallback: boolean;
  provider_note?: string | null;
  verified_evidence: VerifiedEvidence;
  data_warnings: string[];
  disclaimer: string;
}

export function CoverLetterGenerator() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const supabase = createClient();
  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const preselectedId = searchParams.get("opportunity_id");

  // State
  const [opportunities, setOpportunities] = useState<OpportunityOption[]>([]);
  const [selectedOpportunityId, setSelectedOpportunityId] = useState<string>(preselectedId || "");
  const [loadingOpportunities, setLoadingOpportunities] = useState(true);
  const [tone, setTone] = useState<"professional" | "enthusiastic" | "confident">("professional");
  const [length, setLength] = useState<"concise" | "standard" | "detailed">("standard");
  const [additionalNotes, setAdditionalNotes] = useState("");

  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [generatedLetter, setGeneratedLetter] = useState<GeneratedLetterData | null>(null);
  const [editableText, setEditableText] = useState("");
  const [copied, setCopied] = useState(false);
  const [copiedSubject, setCopiedSubject] = useState(false);
  const [searchFilter, setSearchFilter] = useState("");

  // 1. Fetch Published Opportunities for the dropdown
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

  // Selected Opportunity Details
  const selectedOpp = opportunities.find((o) => o.id === selectedOpportunityId);

  // 2. Generate Cover Letter
  const handleGenerate = async () => {
    if (!selectedOpportunityId) {
      setError("Please select a published opportunity first.");
      return;
    }

    setGenerating(true);
    setError(null);
    setCopied(false);

    try {
      const {
        data: { session },
      } = await supabase.auth.getSession();

      if (!session) {
        router.push("/login");
        return;
      }

      const res = await fetch(`${API_URL}/api/v1/copilot/cover-letter/generate`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${session.access_token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          opportunity_id: selectedOpportunityId,
          tone,
          length,
          additional_notes: additionalNotes.trim() ? additionalNotes.trim() : null,
        }),
      });

      if (!res.ok) {
        const errJson = await res.json().catch(() => null);
        throw new Error(errJson?.detail || `Generation failed with status ${res.status}`);
      }

      const json: GeneratedLetterData = await res.json();
      setGeneratedLetter(json);
      setEditableText(json.cover_letter_text);
    } catch (err: unknown) {
      console.error(err);
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setGenerating(false);
    }
  };

  // Copy helpers
  const handleCopyBody = async () => {
    if (!editableText) return;
    try {
      await navigator.clipboard.writeText(editableText);
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    } catch {
      // Fallback
    }
  };

  const handleCopySubject = async () => {
    if (!generatedLetter?.subject_line) return;
    try {
      await navigator.clipboard.writeText(generatedLetter.subject_line);
      setCopiedSubject(true);
      setTimeout(() => setCopiedSubject(false), 2500);
    } catch {
      // Fallback
    }
  };

  // Download helper
  const handleDownloadTxt = () => {
    if (!editableText || !generatedLetter) return;
    const content = `Subject: ${generatedLetter.subject_line}\n\n${editableText}`;
    const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `Cover_Letter_${generatedLetter.company_name.replace(/\s+/g, "_")}_${generatedLetter.opportunity_title.replace(/\s+/g, "_")}.txt`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  // Filtered opportunities for selector
  const filteredOpps = opportunities.filter((o) =>
    searchFilter.trim() === "" ||
    o.title.toLowerCase().includes(searchFilter.toLowerCase()) ||
    o.company_name.toLowerCase().includes(searchFilter.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Grid: Left Column Controls, Right Column Preview */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Configuration & Job Picker (5 cols) */}
        <div className="lg:col-span-5 space-y-5">
          {/* 1. Job Selection Card */}
          <Card className="border-[#DAE3DC] bg-white shadow-xs">
            <CardHeader className="pb-3">
              <CardTitle className="text-base font-bold text-[#14261C] flex items-center gap-2">
                <Target className="w-4 h-4 text-[#1B5E3B]" />
                1. Select Target Opportunity
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {loadingOpportunities ? (
                <div className="h-10 rounded-md bg-[#F0F5F1] animate-pulse" />
              ) : (
                <>
                  <div className="relative">
                    <Search className="w-3.5 h-3.5 text-[#5A7362] absolute left-3 top-1/2 -translate-y-1/2" />
                    <Input
                      placeholder="Search published jobs..."
                      value={searchFilter}
                      onChange={(e) => setSearchFilter(e.target.value)}
                      className="pl-8 h-8 text-xs bg-[#F6FAF7] border-[#DAE3DC]"
                    />
                  </div>

                  <div className="max-h-48 overflow-y-auto space-y-1.5 border border-[#DAE3DC] rounded-lg p-1.5 bg-[#F6FAF7]">
                    {filteredOpps.length === 0 ? (
                      <p className="text-xs text-[#5A7362] p-2 text-center">No matching opportunities found</p>
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
                              <p className={`text-[11px] truncate ${isSelected ? "text-white/80" : "text-[#5A7362]"}`}>
                                {opp.company_name} • {opp.work_model}
                              </p>
                            </div>
                            {isSelected && <Check className="w-3.5 h-3.5 shrink-0 mt-0.5" />}
                          </button>
                        );
                      })
                    )}
                  </div>
                </>
              )}

              {/* Selected Opportunity Summary */}
              {selectedOpp && (
                <div className="bg-[#F6FAF7] border border-[#DAE3DC] rounded-lg p-3 text-xs space-y-2 mt-2">
                  <div className="flex items-start justify-between">
                    <div>
                      <h4 className="font-bold text-[#14261C]">{selectedOpp.title}</h4>
                      <p className="text-[#5A7362]">{selectedOpp.company_name}</p>
                    </div>
                    <Badge variant="outline" className="text-[10px] bg-white border-[#DAE3DC]">
                      {selectedOpp.opportunity_type}
                    </Badge>
                  </div>
                  <div className="flex items-center gap-2 text-[#5A7362]">
                    <MapPin className="w-3 h-3" />
                    <span>{selectedOpp.locations?.join(", ") || selectedOpp.work_model}</span>
                  </div>
                  {selectedOpp.skills && selectedOpp.skills.length > 0 && (
                    <div className="pt-1.5 border-t border-[#DAE3DC]/60 flex flex-wrap gap-1">
                      {selectedOpp.skills.map((s) => (
                        <span key={s.id} className="text-[10px] bg-white border border-[#DAE3DC] px-1.5 py-0.5 rounded text-[#14261C]">
                          {s.name}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>

          {/* 2. Generation Controls */}
          <Card className="border-[#DAE3DC] bg-white shadow-xs">
            <CardHeader className="pb-3">
              <CardTitle className="text-base font-bold text-[#14261C] flex items-center gap-2">
                <Wand2 className="w-4 h-4 text-[#1B5E3B]" />
                2. Style &amp; Emphasis Options
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Tone Selection */}
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-[#14261C]">Professional Tone</label>
                <div className="grid grid-cols-3 gap-2">
                  {(
                    [
                      { key: "professional", label: "Professional", desc: "Formal & courteous" },
                      { key: "enthusiastic", label: "Enthusiastic", desc: "Passionate & dynamic" },
                      { key: "confident", label: "Confident", desc: "Direct & value-focused" },
                    ] as const
                  ).map((t) => (
                    <button
                      key={t.key}
                      type="button"
                      onClick={() => setTone(t.key)}
                      className={`p-2 rounded-lg text-left text-xs border transition-all ${
                        tone === t.key
                          ? "border-[#1B5E3B] bg-[#E5EDE7]/40 text-[#14261C] font-semibold"
                          : "border-[#DAE3DC] bg-white text-[#5A7362] hover:bg-[#F6FAF7]"
                      }`}
                    >
                      <p className="font-semibold leading-tight">{t.label}</p>
                      <p className="text-[10px] text-[#5A7362] mt-0.5">{t.desc}</p>
                    </button>
                  ))}
                </div>
              </div>

              {/* Length Selection */}
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-[#14261C]">Length Target</label>
                <div className="grid grid-cols-3 gap-2">
                  {(
                    [
                      { key: "concise", label: "Concise", words: "~250 words" },
                      { key: "standard", label: "Standard", words: "~350 words" },
                      { key: "detailed", label: "Detailed", words: "~450 words" },
                    ] as const
                  ).map((l) => (
                    <button
                      key={l.key}
                      type="button"
                      onClick={() => setLength(l.key)}
                      className={`p-2 rounded-lg text-left text-xs border transition-all ${
                        length === l.key
                          ? "border-[#1B5E3B] bg-[#E5EDE7]/40 text-[#14261C] font-semibold"
                          : "border-[#DAE3DC] bg-white text-[#5A7362] hover:bg-[#F6FAF7]"
                      }`}
                    >
                      <p className="font-semibold leading-tight">{l.label}</p>
                      <p className="text-[10px] text-[#5A7362] mt-0.5">{l.words}</p>
                    </button>
                  ))}
                </div>
              </div>

              {/* Additional Focus Note */}
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-[#14261C] flex items-center justify-between">
                  <span>Specific Focus / Angle (Optional)</span>
                  <span className="text-[10px] text-[#5A7362]">Max 500 chars</span>
                </label>
                <Input
                  placeholder="e.g., Highlight my DistributedCache project or API testing skills"
                  value={additionalNotes}
                  onChange={(e) => setAdditionalNotes(e.target.value)}
                  maxLength={500}
                  className="h-8 text-xs bg-[#F6FAF7] border-[#DAE3DC]"
                />
              </div>

              {/* Error Message if generation failed */}
              {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 p-3 rounded-lg text-xs flex items-start gap-2">
                  <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                  <div className="space-y-1">
                    <p className="font-semibold">Generation Error</p>
                    <p className="leading-relaxed">{error}</p>
                  </div>
                </div>
              )}

              {/* Generate Action Button */}
              <Button
                onClick={handleGenerate}
                disabled={generating || !selectedOpportunityId}
                className="w-full bg-[#1B5E3B] hover:bg-[#2E7D4F] text-white font-semibold h-10 gap-2 shadow-xs"
              >
                {generating ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    Generating Grounded Cover Letter...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4" />
                    Generate Tailored Cover Letter
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

        {/* Right Column: Output Preview & Editor (7 cols) */}
        <div className="lg:col-span-7 space-y-5">
          {!generatedLetter && !generating && (
            <Card className="border-[#DAE3DC] bg-white shadow-xs p-12 text-center space-y-4">
              <div className="w-14 h-14 rounded-full bg-[#E5EDE7] text-[#1B5E3B] mx-auto flex items-center justify-center">
                <FileEdit className="w-7 h-7" />
              </div>
              <div className="space-y-1 max-w-md mx-auto">
                <h3 className="text-lg font-bold text-[#14261C]">Ready to Generate Your Draft</h3>
                <p className="text-xs sm:text-sm text-[#5A7362] leading-relaxed">
                  Select a published opportunity on the left and click &ldquo;Generate Tailored Cover Letter&rdquo;.
                  CareerPilot AI will analyze your verified profile, education, projects, and active resume to draft an authentic, honest pitch.
                </p>
              </div>
              <div className="flex flex-wrap items-center justify-center gap-2 pt-2 text-xs text-[#5A7362]">
                <span className="flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5 text-[#1B5E3B]" /> Truthful Facts Only
                </span>
                <span>•</span>
                <span className="flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5 text-[#1B5E3B]" /> Editable In-Browser
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
                <h3 className="text-base font-bold text-[#14261C]">Crafting Your Personalized Letter...</h3>
                <p className="text-xs text-[#5A7362]">
                  Extracting relevant projects, matching skills with {selectedOpp?.company_name || "the company"}, and structuring a professional draft.
                </p>
              </div>
            </Card>
          )}

          {generatedLetter && (
            <div className="space-y-4">
              {/* Provider & Transparency Notice */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 bg-white border border-[#DAE3DC] rounded-xl px-4 py-3 shadow-xs">
                <div className="flex items-center gap-2">
                  {generatedLetter.is_template_fallback ? (
                    <Badge variant="outline" className="bg-[#EBF3ED] border-primary/20 text-primary text-[10px]">
                      Structured Letter Draft
                    </Badge>
                  ) : (
                    <Badge className="bg-[#1B5E3B] text-white text-[10px]">
                      Tailored Letter Ready
                    </Badge>
                  )}
                  <span className="text-xs text-[#5A7362]">
                    Tone: <strong className="text-[#14261C] capitalize">{generatedLetter.tone}</strong> • Length: <strong className="text-[#14261C] capitalize">{generatedLetter.length}</strong>
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={handleCopyBody}
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
                        Copy Text
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

              {/* Subject Line Card */}
              <div className="bg-white border border-[#DAE3DC] rounded-xl p-3 flex items-center justify-between gap-3 shadow-xs">
                <div className="min-w-0">
                  <span className="text-[10px] uppercase font-bold text-[#5A7362] block">Recommended Subject Line:</span>
                  <p className="text-xs font-semibold text-[#14261C] truncate">{generatedLetter.subject_line}</p>
                </div>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={handleCopySubject}
                  className="h-7 text-xs text-[#1B5E3B] hover:bg-[#E5EDE7] shrink-0"
                >
                  {copiedSubject ? "Copied!" : "Copy Subject"}
                </Button>
              </div>

              {/* Editable Textarea Card */}
              <Card className="border-[#DAE3DC] bg-white shadow-xs overflow-hidden">
                <div className="p-3 bg-[#F6FAF7] border-b border-[#DAE3DC] flex items-center justify-between text-xs text-[#5A7362]">
                  <span className="font-semibold text-[#14261C]">Draft Preview (Editable)</span>
                  <span>{editableText.split(/\s+/).filter(Boolean).length} Words • {editableText.length} Characters</span>
                </div>
                <CardContent className="p-4 sm:p-5">
                  <Textarea
                    value={editableText}
                    onChange={(e) => setEditableText(e.target.value)}
                    rows={16}
                    className="w-full text-sm leading-relaxed text-[#14261C] border-[#DAE3DC] focus:ring-[#1B5E3B] font-sans resize-y bg-white"
                  />
                </CardContent>
              </Card>

              {/* Verified Evidence Breakdown */}
              <Card className="border-[#DAE3DC] bg-white shadow-xs">
                <CardHeader className="py-3 px-4 border-b border-[#DAE3DC]">
                  <CardTitle className="text-xs font-bold text-[#14261C] flex items-center gap-1.5">
                    <ShieldCheck className="w-4 h-4 text-[#1B5E3B]" />
                    Audit Trail: Grounded Candidate Evidence Used
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-4 space-y-2.5 text-xs">
                  {generatedLetter.verified_evidence.matched_skills.length > 0 && (
                    <div className="flex items-baseline gap-2">
                      <span className="text-[#5A7362] shrink-0 w-28 font-medium">Matched Skills:</span>
                      <div className="flex flex-wrap gap-1">
                        {generatedLetter.verified_evidence.matched_skills.map((s) => (
                          <Badge key={s} variant="outline" className="text-[10px] bg-[#F6FAF7] border-[#DAE3DC]">
                            {s}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  {generatedLetter.verified_evidence.included_projects.length > 0 && (
                    <div className="flex items-baseline gap-2">
                      <span className="text-[#5A7362] shrink-0 w-28 font-medium">Projects Cited:</span>
                      <div className="flex flex-wrap gap-1">
                        {generatedLetter.verified_evidence.included_projects.map((p) => (
                          <Badge key={p} variant="outline" className="text-[10px] bg-white border-[#DAE3DC]">
                            {p}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  {generatedLetter.verified_evidence.included_education.length > 0 && (
                    <div className="flex items-baseline gap-2">
                      <span className="text-[#5A7362] shrink-0 w-28 font-medium">Education Cited:</span>
                      <span className="text-[#14261C]">{generatedLetter.verified_evidence.included_education.join("; ")}</span>
                    </div>
                  )}

                  {generatedLetter.provider_note && (
                    <p className="text-[11px] text-[#5A7362] pt-2 border-t border-[#DAE3DC]/60 italic">
                      Note: {generatedLetter.provider_note}
                    </p>
                  )}
                </CardContent>
              </Card>

              {/* Review & Safety Disclaimer */}
              <div className="bg-[#FFF8EB] border border-[#F59E0B]/30 rounded-xl p-4 flex items-start gap-3 text-xs text-[#92400E] shadow-xs">
                <Info className="w-4 h-4 text-[#D97706] shrink-0 mt-0.5" />
                <div className="space-y-1">
                  <p className="font-semibold text-[#78350F]">Review Before Submitting</p>
                  <p className="leading-relaxed">
                    {generatedLetter.disclaimer}
                  </p>
                  <p className="text-[11px] text-[#92400E]/80">
                    CareerPilot AI does not automatically submit applications or transmit messages to employers. You remain in full control of your application materials.
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
