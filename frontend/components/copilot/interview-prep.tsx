"use client";

import { useCallback, useEffect, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import {
  AlertCircle,
  Award,
  BookOpen,
  Briefcase,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Clock,
  Eye,
  EyeOff,
  FileText,
  HelpCircle,
  Info,
  Lightbulb,
  RefreshCw,
  RotateCcw,
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

interface PublishedOpportunity {
  id: string;
  title: string;
  company_name: string;
  work_model: string;
  opportunity_type: string;
}

interface InterviewQuestionItem {
  id: string;
  identifier: string;
  question_text: string;
  category: string;
  difficulty: string;
  role_tags: string[];
  is_general: boolean;
  skill_tags: string[];
  expected_points: string[];
  rubric_criteria: string[];
  reference_answer: string | null;
}

interface InterviewSessionData {
  session_id: string;
  questions: InterviewQuestionItem[];
  total_questions: number;
  selected_role: string | null;
  opportunity_title: string | null;
  opportunity_company: string | null;
  category_filter: string | null;
  difficulty_filter: string | null;
  is_empty_bank: boolean;
  insufficient_coverage: boolean;
  notice: string | null;
}

interface LocalEvaluationData {
  question_id: string;
  addressed_points: string[];
  points_to_elaborate: string[];
  word_count: number;
  sentence_count: number;
  completeness_level: string;
  structure_feedback: string[];
  suggestions: string[];
  reference_answer_guidance: string | null;
  provider: string;
  disclaimer: string;
}

interface AIEvaluationData {
  question_id: string;
  feedback_markdown: string;
  strengths: string[];
  areas_for_improvement: string[];
  delivery_tips: string[];
  provider: string;
  provider_model: string | null;
  is_fallback: boolean;
  fallback_reason: string | null;
  disclaimer: string;
}

export function InterviewPrep() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const preselectedOppId = searchParams.get("opportunity_id");

  // Config and Filter States
  const [loadingConfig, setLoadingConfig] = useState(true);
  const [configError, setConfigError] = useState<string | null>(null);
  const [standardRoles, setStandardRoles] = useState<string[]>([
    "General / Any Role",
    "Data Analyst",
    "Data Scientist",
    "AI/ML Engineer",
    "Full-Stack Developer",
    "General Software Engineering",
  ]);
  const [categories, setCategories] = useState<string[]>([
    "All Categories",
    "Technical",
    "HR/Behavioural",
    "Project-Based",
  ]);
  const [difficulties, setDifficulties] = useState<string[]>([
    "All Levels",
    "Beginner",
    "Intermediate",
    "Advanced",
  ]);
  const [opportunities, setOpportunities] = useState<PublishedOpportunity[]>([]);

  // Selected Filter Values
  const [selectedRole, setSelectedRole] = useState<string>("General / Any Role");
  const [customRoleInput, setCustomRoleInput] = useState<string>("");
  const [isCustomRole, setIsCustomRole] = useState<boolean>(false);
  const [selectedOppId, setSelectedOppId] = useState<string>(preselectedOppId || "");
  const [selectedCategory, setSelectedCategory] = useState<string>("All Categories");
  const [selectedDifficulty, setSelectedDifficulty] = useState<string>("All Levels");
  const [questionCount, setQuestionCount] = useState<number>(5);

  // Practice Session State
  const [session, setSession] = useState<InterviewSessionData | null>(null);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState<number>(0);
  const [startingSession, setStartingSession] = useState<boolean>(false);
  const [sessionError, setSessionError] = useState<string | null>(null);

  // Student Answers (keyed by question ID)
  const [answers, setAnswers] = useState<Record<string, string>>({});

  // Evaluation States (keyed by question ID)
  const [evaluatingLocal, setEvaluatingLocal] = useState<boolean>(false);
  const [evaluatingAI, setEvaluatingAI] = useState<boolean>(false);
  const [localEvaluations, setLocalEvaluations] = useState<Record<string, LocalEvaluationData>>({});
  const [aiEvaluations, setAiEvaluations] = useState<Record<string, AIEvaluationData>>({});
  const [evalError, setEvalError] = useState<string | null>(null);

  // UI Accordions per question
  const [showGuidance, setShowGuidance] = useState<boolean>(false);
  const [showRubricPoints, setShowRubricPoints] = useState<boolean>(false);

  // Helper to fetch Supabase access token
  const getAccessToken = useCallback(async (): Promise<string | null> => {
    try {
      const supabase = createClient();
      const {
        data: { session },
      } = await supabase.auth.getSession();
      return session?.access_token || null;
    } catch {
      return null;
    }
  }, []);

  // Fetch configuration on mount
  useEffect(() => {
    async function loadConfig() {
      setLoadingConfig(true);
      setConfigError(null);
      try {
        const token = await getAccessToken();
        if (!token) {
          router.push("/auth/login?redirect=/interview-prep");
          return;
        }

        const res = await fetch(`${API_URL}/api/v1/copilot/interview-prep/config`, {
          headers: { Authorization: `Bearer ${token}` },
        });

        if (!res.ok) {
          throw new Error(`Failed to load interview config (Status ${res.status})`);
        }

        const data = await res.json();
        if (data.roles) setStandardRoles(data.roles);
        if (data.categories) setCategories(data.categories);
        if (data.difficulties) setDifficulties(data.difficulties);
        if (data.published_opportunities) setOpportunities(data.published_opportunities);

        // Preselect opportunity if URL parameter provided
        if (preselectedOppId && data.published_opportunities) {
          const match = data.published_opportunities.find((o: PublishedOpportunity) => o.id === preselectedOppId);
          if (match) {
            setSelectedOppId(match.id);
            setSelectedRole(match.title);
          }
        }
      } catch (err: unknown) {
        console.error("Config fetch error:", err);
        setConfigError(err instanceof Error ? err.message : "Unable to load interview preparation options.");
      } finally {
        setLoadingConfig(false);
      }
    }

    loadConfig();
  }, [getAccessToken, preselectedOppId, router]);

  // Start or restart practice session
  const handleStartSession = async () => {
    setStartingSession(true);
    setSessionError(null);
    setEvalError(null);

    try {
      const token = await getAccessToken();
      if (!token) {
        router.push("/auth/login?redirect=/interview-prep");
        return;
      }

      const activeRole = isCustomRole ? customRoleInput.trim() : selectedRole;

      const payload = {
        role: activeRole && activeRole !== "General / Any Role" ? activeRole : null,
        opportunity_id: selectedOppId || null,
        category: selectedCategory !== "All Categories" ? selectedCategory : null,
        difficulty: selectedDifficulty !== "All Levels" ? selectedDifficulty : null,
        question_count: questionCount,
      };

      const res = await fetch(`${API_URL}/api/v1/copilot/interview-prep/session`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to create session (${res.status})`);
      }

      const sessionData: InterviewSessionData = await res.json();
      setSession(sessionData);
      setCurrentQuestionIndex(0);
      setAnswers({});
      setLocalEvaluations({});
      setAiEvaluations({});
      setShowGuidance(false);
      setShowRubricPoints(false);
    } catch (err: unknown) {
      console.error("Session creation error:", err);
      setSessionError(err instanceof Error ? err.message : "Failed to start practice session.");
    } finally {
      setStartingSession(false);
    }
  };

  // Current Question
  const currentQuestion: InterviewQuestionItem | undefined =
    session && session.questions.length > 0 ? session.questions[currentQuestionIndex] : undefined;

  const currentAnswer = currentQuestion ? answers[currentQuestion.id] || "" : "";
  const currentLocalEval = currentQuestion ? localEvaluations[currentQuestion.id] : undefined;
  const currentAiEval = currentQuestion ? aiEvaluations[currentQuestion.id] : undefined;

  // Answer Text Change handler
  const handleAnswerChange = (val: string) => {
    if (!currentQuestion) return;
    setAnswers((prev) => ({
      ...prev,
      [currentQuestion.id]: val,
    }));
  };

  // Evaluate Answer Deterministically (Offline / Zero API)
  const handleEvaluateLocal = async () => {
    if (!currentQuestion || !currentAnswer.trim()) {
      setEvalError("Please type an answer before evaluating.");
      return;
    }

    setEvaluatingLocal(true);
    setEvalError(null);

    try {
      const token = await getAccessToken();
      if (!token) return;

      const res = await fetch(`${API_URL}/api/v1/copilot/interview-prep/evaluate-local`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          question_id: currentQuestion.id,
          answer_text: currentAnswer,
        }),
      });

      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.detail || `Local evaluation failed (${res.status})`);
      }

      const evalData: LocalEvaluationData = await res.json();
      setLocalEvaluations((prev) => ({
        ...prev,
        [currentQuestion.id]: evalData,
      }));
    } catch (err: unknown) {
      console.error("Local evaluation error:", err);
      setEvalError(err instanceof Error ? err.message : "Evaluation failed.");
    } finally {
      setEvaluatingLocal(false);
    }
  };

  // Optional AI Evaluation (Uses Gemini Quota)
  const handleEvaluateAI = async () => {
    if (!currentQuestion || !currentAnswer.trim()) {
      setEvalError("Please type an answer before requesting AI feedback.");
      return;
    }

    setEvaluatingAI(true);
    setEvalError(null);

    try {
      const token = await getAccessToken();
      if (!token) return;

      const res = await fetch(`${API_URL}/api/v1/copilot/interview-prep/evaluate-ai`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          question_id: currentQuestion.id,
          answer_text: currentAnswer,
        }),
      });

      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.detail || `AI evaluation failed (${res.status})`);
      }

      const aiData: AIEvaluationData = await res.json();
      setAiEvaluations((prev) => ({
        ...prev,
        [currentQuestion.id]: aiData,
      }));
    } catch (err: unknown) {
      console.error("AI evaluation error:", err);
      setEvalError(err instanceof Error ? err.message : "AI evaluation failed.");
    } finally {
      setEvaluatingAI(false);
    }
  };

  // Navigation between questions
  const goToNextQuestion = () => {
    if (!session) return;
    if (currentQuestionIndex < session.questions.length - 1) {
      setCurrentQuestionIndex((prev) => prev + 1);
      setShowGuidance(false);
      setShowRubricPoints(false);
      setEvalError(null);
    }
  };

  const goToPreviousQuestion = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex((prev) => prev - 1);
      setShowGuidance(false);
      setShowRubricPoints(false);
      setEvalError(null);
    }
  };

  // Word count and speaking time calculation
  const wordsCount = currentAnswer.trim() ? currentAnswer.trim().split(/\s+/).length : 0;
  const estimatedSpeakingTimeSec = Math.round((wordsCount / 130) * 60);

  return (
    <div className="space-y-6">
      {/* 1. SETUP / FILTER CARD */}
      <Card className="border-[#1B5E3B]/20 bg-white shadow-sm">
        <CardHeader className="pb-3 border-b border-gray-100">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <CardTitle className="text-lg font-bold text-[#14261C] flex items-center gap-2">
                <Target className="w-5 h-5 text-[#1B5E3B]" />
                Interview Practice Setup
              </CardTitle>
              <p className="text-xs text-[#5A7362] mt-0.5">
                Configure your practice session filters. Selecting and viewing questions uses zero external API calls.
              </p>
            </div>
            {session && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => setSession(null)}
                className="text-xs border-[#1B5E3B]/30 text-[#1B5E3B] hover:bg-[#E5EDE7]"
              >
                <RotateCcw className="w-3.5 h-3.5 mr-1.5" />
                Configure New Session
              </Button>
            )}
          </div>
        </CardHeader>

        {(!session || startingSession) && (
          <CardContent className="pt-4 space-y-4">
            {configError && (
              <div className="p-3 text-xs bg-red-50 text-red-700 rounded-lg border border-red-200 flex items-start gap-2">
                <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                <span>{configError}</span>
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* Target Role Selector */}
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-[#14261C]">Target Role</label>
                {!isCustomRole ? (
                  <select
                    value={selectedRole}
                    onChange={(e) => {
                      if (e.target.value === "__custom__") {
                        setIsCustomRole(true);
                      } else {
                        setSelectedRole(e.target.value);
                      }
                    }}
                    className="w-full h-9 px-3 text-xs rounded-md border border-gray-200 bg-white focus:outline-none focus:ring-1 focus:ring-[#1B5E3B]"
                  >
                    {standardRoles.map((role) => (
                      <option key={role} value={role}>
                        {role}
                      </option>
                    ))}
                    <option value="__custom__">+ Enter Custom Role...</option>
                  </select>
                ) : (
                  <div className="flex gap-1.5">
                    <Input
                      placeholder="e.g. DevOps Engineer"
                      value={customRoleInput}
                      onChange={(e) => setCustomRoleInput(e.target.value)}
                      className="h-9 text-xs"
                    />
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        setIsCustomRole(false);
                        setSelectedRole("General / Any Role");
                      }}
                      className="text-xs px-2 text-[#5A7362]"
                    >
                      Preset
                    </Button>
                  </div>
                )}
              </div>

              {/* Optional Opportunity Filter */}
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-[#14261C]">Target Opportunity (Optional)</label>
                <select
                  value={selectedOppId}
                  onChange={(e) => {
                    setSelectedOppId(e.target.value);
                    if (e.target.value) {
                      const opp = opportunities.find((o) => o.id === e.target.value);
                      if (opp) {
                        setSelectedRole(opp.title);
                        setIsCustomRole(false);
                      }
                    }
                  }}
                  className="w-full h-9 px-3 text-xs rounded-md border border-gray-200 bg-white focus:outline-none focus:ring-1 focus:ring-[#1B5E3B]"
                >
                  <option value="">None (General Role Practice)</option>
                  {opportunities.map((opp) => (
                    <option key={opp.id} value={opp.id}>
                      {opp.title} — {opp.company_name}
                    </option>
                  ))}
                </select>
              </div>

              {/* Category Filter */}
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-[#14261C]">Category</label>
                <select
                  value={selectedCategory}
                  onChange={(e) => setSelectedCategory(e.target.value)}
                  className="w-full h-9 px-3 text-xs rounded-md border border-gray-200 bg-white focus:outline-none focus:ring-1 focus:ring-[#1B5E3B]"
                >
                  {categories.map((cat) => (
                    <option key={cat} value={cat}>
                      {cat}
                    </option>
                  ))}
                </select>
              </div>

              {/* Difficulty & Count */}
              <div className="grid grid-cols-2 gap-2">
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-[#14261C]">Difficulty</label>
                  <select
                    value={selectedDifficulty}
                    onChange={(e) => setSelectedDifficulty(e.target.value)}
                    className="w-full h-9 px-3 text-xs rounded-md border border-gray-200 bg-white focus:outline-none focus:ring-1 focus:ring-[#1B5E3B]"
                  >
                    {difficulties.map((diff) => (
                      <option key={diff} value={diff}>
                        {diff}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-[#14261C]">Questions</label>
                  <select
                    value={questionCount}
                    onChange={(e) => setQuestionCount(Number(e.target.value))}
                    className="w-full h-9 px-3 text-xs rounded-md border border-gray-200 bg-white focus:outline-none focus:ring-1 focus:ring-[#1B5E3B]"
                  >
                    <option value={3}>3 Questions</option>
                    <option value={5}>5 Questions</option>
                    <option value={10}>10 Questions</option>
                  </select>
                </div>
              </div>
            </div>

            {sessionError && (
              <div className="p-3 text-xs bg-red-50 text-red-700 rounded-lg border border-red-200 flex items-start gap-2">
                <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                <span>{sessionError}</span>
              </div>
            )}

            <div className="pt-2 flex justify-end">
              <Button
                onClick={handleStartSession}
                disabled={startingSession || loadingConfig}
                className="bg-[#1B5E3B] text-white hover:bg-[#2E7D4F] font-semibold text-xs px-5 h-9 flex items-center gap-2"
              >
                {startingSession ? (
                  <>
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    Selecting Questions...
                  </>
                ) : (
                  <>
                    <BookOpen className="w-3.5 h-3.5" />
                    Start Practice Session
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        )}
      </Card>

      {/* 2. EMPTY STATE WHEN QUESTION BANK NOT SEEDED */}
      {session && session.is_empty_bank && (
        <Card className="border-amber-200 bg-amber-50/50">
          <CardContent className="py-8 text-center space-y-3">
            <HelpCircle className="w-10 h-10 text-amber-600 mx-auto" />
            <h3 className="text-base font-bold text-amber-900">Question Bank Not Seeded</h3>
            <p className="text-xs text-amber-800 max-w-md mx-auto">
              {session.notice ||
                "The interview question bank has not been seeded yet. Please run the seed command in the backend to load the initial curated questions."}
            </p>
            <div className="pt-2">
              <code className="text-xs bg-amber-100 text-amber-900 px-3 py-1.5 rounded-md font-mono">
                python -m app.seeds.seed_interview_questions
              </code>
            </div>
          </CardContent>
        </Card>
      )}

      {/* 3. ACTIVE PRACTICE SESSION VIEW */}
      {session && !session.is_empty_bank && currentQuestion && (
        <div className="space-y-6">
          {/* Session Header / Stepper */}
          <div className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm space-y-3">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <span className="text-xs font-semibold text-[#1B5E3B] uppercase tracking-wider">
                  Practice Session • Question {currentQuestionIndex + 1} of {session.total_questions}
                </span>
                <div className="flex items-center gap-2 mt-1">
                  <h2 className="text-base font-bold text-[#14261C]">
                    {session.selected_role ? `${session.selected_role} Preparation` : "General Interview Preparation"}
                  </h2>
                  {session.opportunity_company && (
                    <Badge variant="outline" className="text-[11px] text-[#5A7362] bg-gray-50">
                      <Briefcase className="w-3 h-3 mr-1 inline" />
                      {session.opportunity_company}
                    </Badge>
                  )}
                </div>
              </div>

              {/* Progress & Stepper */}
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={goToPreviousQuestion}
                  disabled={currentQuestionIndex === 0}
                  className="h-8 px-2.5 text-xs text-[#14261C]"
                >
                  <ChevronLeft className="w-4 h-4 mr-0.5" />
                  Prev
                </Button>
                <span className="text-xs font-medium text-[#5A7362] px-1">
                  {currentQuestionIndex + 1} / {session.total_questions}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={goToNextQuestion}
                  disabled={currentQuestionIndex === session.total_questions - 1}
                  className="h-8 px-2.5 text-xs text-[#14261C]"
                >
                  Next
                  <ChevronRight className="w-4 h-4 ml-0.5" />
                </Button>
              </div>
            </div>

            {/* Progress bar */}
            <div className="w-full bg-gray-100 rounded-full h-1.5 overflow-hidden">
              <div
                className="bg-[#1B5E3B] h-1.5 rounded-full transition-all duration-300"
                style={{
                  width: `${((currentQuestionIndex + 1) / session.total_questions) * 100}%`,
                }}
              />
            </div>

            {/* Informative notice banner if custom role was supplemented or coverage was limited */}
            {session.notice && (
              <div className="p-2.5 text-xs bg-[#E5EDE7]/60 text-[#14261C] rounded-lg border border-[#1B5E3B]/20 flex items-start gap-2">
                <Info className="w-4 h-4 text-[#1B5E3B] shrink-0 mt-0.5" />
                <span>{session.notice}</span>
              </div>
            )}
          </div>

          {/* Question Card */}
          <Card className="border-[#1B5E3B]/20 bg-white shadow-sm">
            <CardHeader className="pb-3 border-b border-gray-100">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge
                    variant="outline"
                    className={`text-xs font-semibold ${
                      currentQuestion.category === "Technical"
                        ? "bg-blue-50 text-blue-700 border-blue-200"
                        : currentQuestion.category === "HR/Behavioural"
                        ? "bg-purple-50 text-purple-700 border-purple-200"
                        : "bg-emerald-50 text-emerald-700 border-emerald-200"
                    }`}
                  >
                    {currentQuestion.category}
                  </Badge>
                  <Badge
                    variant="outline"
                    className={`text-xs ${
                      currentQuestion.difficulty === "Beginner"
                        ? "bg-green-50 text-green-700 border-green-200"
                        : currentQuestion.difficulty === "Intermediate"
                        ? "bg-yellow-50 text-yellow-700 border-yellow-200"
                        : "bg-red-50 text-red-700 border-red-200"
                    }`}
                  >
                    {currentQuestion.difficulty}
                  </Badge>
                  {currentQuestion.is_general && (
                    <Badge variant="outline" className="text-xs bg-gray-50 text-gray-600 border-gray-200">
                      General Coverage
                    </Badge>
                  )}
                </div>

                {/* Skill Tags */}
                <div className="flex flex-wrap items-center gap-1.5">
                  {currentQuestion.skill_tags.map((skill) => (
                    <span
                      key={skill}
                      className="text-[11px] px-2 py-0.5 rounded bg-gray-100 text-gray-700 border border-gray-200"
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              </div>
            </CardHeader>

            <CardContent className="pt-4 space-y-4">
              {/* Question Text */}
              <div className="text-base sm:text-lg font-bold text-[#14261C] leading-snug">
                {currentQuestion.question_text}
              </div>

              {/* Toggles for Rubric Points and Guidance */}
              <div className="flex flex-wrap gap-2 pt-1 border-t border-gray-100">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowRubricPoints(!showRubricPoints)}
                  className="text-xs text-[#1B5E3B] hover:bg-[#E5EDE7]/50 h-8 px-2.5 flex items-center gap-1.5"
                >
                  <Award className="w-3.5 h-3.5" />
                  {showRubricPoints ? "Hide Rubric Expectations" : "View Expected Rubric Points"}
                </Button>

                {currentQuestion.reference_answer && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setShowGuidance(!showGuidance)}
                    className="text-xs text-[#5A7362] hover:bg-gray-100 h-8 px-2.5 flex items-center gap-1.5"
                  >
                    {showGuidance ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                    {showGuidance ? "Hide Answer Guidance" : "View Answer Framework / Tips"}
                  </Button>
                )}
              </div>

              {/* Rubric Points Accordion */}
              {showRubricPoints && (
                <div className="p-3.5 bg-gray-50 rounded-lg border border-gray-200 text-xs space-y-2">
                  <div className="font-semibold text-[#14261C] flex items-center gap-1.5">
                    <CheckCircle2 className="w-4 h-4 text-[#1B5E3B]" />
                    Expected Evaluation Points:
                  </div>
                  <ul className="list-disc list-inside space-y-1 text-gray-700 pl-1">
                    {currentQuestion.expected_points.map((pt, idx) => (
                      <li key={idx} className="leading-relaxed">
                        {pt}
                      </li>
                    ))}
                  </ul>
                  {currentQuestion.rubric_criteria.length > 0 && (
                    <div className="pt-1.5 border-t border-gray-200 flex flex-wrap gap-1.5 items-center">
                      <span className="font-medium text-gray-500">Evaluation Criteria:</span>
                      {currentQuestion.rubric_criteria.map((c) => (
                        <span key={c} className="bg-white px-2 py-0.5 rounded border border-gray-200 text-gray-600">
                          {c}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Guidance Framework Accordion */}
              {showGuidance && currentQuestion.reference_answer && (
                <div className="p-3.5 bg-[#E5EDE7]/40 rounded-lg border border-[#1B5E3B]/20 text-xs space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-[#14261C] flex items-center gap-1.5">
                      <Lightbulb className="w-4 h-4 text-[#1B5E3B]" />
                      Answer Guidance & Framework
                    </span>
                    <Badge variant="outline" className="text-[10px] bg-white text-gray-500">
                      Guidance Only — Not Guaranteed Correct Answer
                    </Badge>
                  </div>
                  <p className="text-gray-700 leading-relaxed whitespace-pre-line">
                    {currentQuestion.reference_answer}
                  </p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Student Answer Section */}
          <Card className="border-[#1B5E3B]/20 bg-white shadow-sm">
            <CardHeader className="pb-2 border-b border-gray-100">
              <div className="flex items-center justify-between">
                <label htmlFor="answer-textarea" className="text-sm font-bold text-[#14261C] flex items-center gap-2">
                  <FileText className="w-4 h-4 text-[#1B5E3B]" />
                  Your Practice Response
                </label>
                <div className="flex items-center gap-3 text-xs text-gray-500 font-mono">
                  <span>{wordsCount} words</span>
                  <span className="text-gray-300">•</span>
                  <span className="flex items-center gap-1">
                    <Clock className="w-3.5 h-3.5 text-gray-400" />
                    ~{estimatedSpeakingTimeSec}s spoken
                  </span>
                </div>
              </div>
            </CardHeader>

            <CardContent className="pt-3 space-y-4">
              <Textarea
                id="answer-textarea"
                rows={7}
                placeholder="Type your spoken interview response here as if speaking directly to the hiring manager. Focus on concrete context, actions, trade-offs, and tangible results..."
                value={currentAnswer}
                onChange={(e) => handleAnswerChange(e.target.value)}
                className="w-full text-sm leading-relaxed border-gray-200 focus:border-[#1B5E3B] focus:ring-[#1B5E3B]"
              />

              {evalError && (
                <div className="p-3 text-xs bg-red-50 text-red-700 rounded-lg border border-red-200 flex items-start gap-2">
                  <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                  <span>{evalError}</span>
                </div>
              )}

              {/* Action Toolbar */}
              <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 pt-2">
                <div className="flex flex-wrap items-center gap-2">
                  {/* Default Local Rubric Button (Zero API) */}
                  <Button
                    onClick={handleEvaluateLocal}
                    disabled={evaluatingLocal || evaluatingAI || !currentAnswer.trim()}
                    className="bg-[#1B5E3B] text-white hover:bg-[#2E7D4F] font-semibold text-xs h-9 px-4 flex items-center gap-2 shadow-sm"
                  >
                    {evaluatingLocal ? (
                      <>
                        <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                        Evaluating Rubric...
                      </>
                    ) : (
                      <>
                        <ShieldCheck className="w-4 h-4" />
                        Evaluate with Rubric (Default / Offline)
                      </>
                    )}
                  </Button>

                  {/* Optional Gemini AI Feedback Button */}
                  <Button
                    variant="outline"
                    onClick={handleEvaluateAI}
                    disabled={evaluatingLocal || evaluatingAI || !currentAnswer.trim()}
                    className="border-purple-300 text-purple-800 hover:bg-purple-50 font-semibold text-xs h-9 px-4 flex items-center gap-2"
                  >
                    {evaluatingAI ? (
                      <>
                        <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                        Querying Gemini...
                      </>
                    ) : (
                      <>
                        <Sparkles className="w-4 h-4 text-purple-600" />
                        Get AI Feedback (uses Gemini quota)
                      </>
                    )}
                  </Button>
                </div>

                {/* Question Navigation */}
                <div className="flex items-center gap-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={goToPreviousQuestion}
                    disabled={currentQuestionIndex === 0}
                    className="text-xs h-9"
                  >
                    Previous
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={goToNextQuestion}
                    disabled={currentQuestionIndex === session.total_questions - 1}
                    className="text-xs h-9 text-[#1B5E3B] border-[#1B5E3B]/30 hover:bg-[#E5EDE7]"
                  >
                    Next Question
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* 4. EVALUATION RESULTS DISPLAY */}
          {(currentLocalEval || currentAiEval) && (
            <Card className="border-[#1B5E3B]/30 bg-white shadow-sm overflow-hidden">
              <CardHeader className="pb-3 border-b border-gray-100 bg-[#F6FAF7]">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <CardTitle className="text-base font-bold text-[#14261C] flex items-center gap-2">
                      <Wand2 className="w-4 h-4 text-[#1B5E3B]" />
                      Interview Performance Feedback
                    </CardTitle>
                    {/* Provider Badge */}
                    {currentAiEval ? (
                      <Badge
                        variant="outline"
                        className={`text-xs ${
                          currentAiEval.is_fallback
                            ? "bg-amber-50 text-amber-800 border-amber-300"
                            : "bg-purple-50 text-purple-800 border-purple-300"
                        }`}
                      >
                        <Sparkles className="w-3 h-3 mr-1 inline" />
                        {currentAiEval.is_fallback
                          ? "Local Rubric Fallback (Offline)"
                          : `Gemini AI Coach (${currentAiEval.provider_model || "Flash"})`}
                      </Badge>
                    ) : (
                      <Badge variant="outline" className="text-xs bg-emerald-50 text-[#1B5E3B] border-[#1B5E3B]/30">
                        <ShieldCheck className="w-3 h-3 mr-1 inline" />
                        Deterministic Rubric Engine (Offline / Zero API)
                      </Badge>
                    )}
                  </div>

                  {currentLocalEval && (
                    <Badge variant="outline" className="text-xs bg-white text-gray-700">
                      {currentLocalEval.completeness_level}
                    </Badge>
                  )}
                </div>
              </CardHeader>

              <CardContent className="pt-4 space-y-4 text-xs sm:text-sm">
                {/* Fallback Notice if Gemini failed */}
                {currentAiEval && currentAiEval.is_fallback && currentAiEval.fallback_reason && (
                  <div className="p-3 bg-amber-50 text-amber-800 rounded-lg border border-amber-200 flex items-start gap-2 text-xs">
                    <Info className="w-4 h-4 shrink-0 mt-0.5 text-amber-600" />
                    <span>{currentAiEval.fallback_reason}</span>
                  </div>
                )}

                {/* AI Markdown Evaluation (if Gemini succeeded) */}
                {currentAiEval && !currentAiEval.is_fallback ? (
                  <div className="space-y-4">
                    {/* Strengths */}
                    {currentAiEval.strengths.length > 0 && (
                      <div className="space-y-1.5">
                        <h4 className="font-bold text-emerald-800 flex items-center gap-1.5 text-xs sm:text-sm">
                          <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                          Key Strengths Observed:
                        </h4>
                        <ul className="list-disc list-inside space-y-1 text-gray-700 pl-1 text-xs">
                          {currentAiEval.strengths.map((str, idx) => (
                            <li key={idx} className="leading-relaxed">
                              {str}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Areas for Improvement */}
                    {currentAiEval.areas_for_improvement.length > 0 && (
                      <div className="space-y-1.5">
                        <h4 className="font-bold text-amber-800 flex items-center gap-1.5 text-xs sm:text-sm">
                          <Lightbulb className="w-4 h-4 text-amber-600" />
                          Opportunities to Elaborate & Strengthen:
                        </h4>
                        <ul className="list-disc list-inside space-y-1 text-gray-700 pl-1 text-xs">
                          {currentAiEval.areas_for_improvement.map((imp, idx) => (
                            <li key={idx} className="leading-relaxed">
                              {imp}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Delivery & Coaching Tips */}
                    {currentAiEval.delivery_tips.length > 0 && (
                      <div className="space-y-1.5">
                        <h4 className="font-bold text-purple-800 flex items-center gap-1.5 text-xs sm:text-sm">
                          <Clock className="w-4 h-4 text-purple-600" />
                          Live Interview Delivery Tips:
                        </h4>
                        <ul className="list-disc list-inside space-y-1 text-gray-700 pl-1 text-xs">
                          {currentAiEval.delivery_tips.map((tip, idx) => (
                            <li key={idx} className="leading-relaxed">
                              {tip}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                ) : (
                  /* Local Rubric Engine Breakdown */
                  currentLocalEval && (
                    <div className="space-y-4">
                      {/* Expected points coverage */}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {/* Points Addressed */}
                        <div className="p-3 bg-emerald-50/60 rounded-lg border border-emerald-200/60 space-y-2">
                          <div className="font-bold text-emerald-900 text-xs flex items-center gap-1.5">
                            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                            Rubric Points Addressed ({currentLocalEval.addressed_points.length}):
                          </div>
                          {currentLocalEval.addressed_points.length > 0 ? (
                            <ul className="space-y-1 text-xs text-emerald-950">
                              {currentLocalEval.addressed_points.map((pt, i) => (
                                <li key={i} className="flex items-start gap-1.5">
                                  <span className="text-emerald-600 font-bold">✓</span>
                                  <span>{pt}</span>
                                </li>
                              ))}
                            </ul>
                          ) : (
                            <p className="text-xs text-gray-500 italic">
                              None of the specific expected key points were clearly detected. Try expanding your response.
                            </p>
                          )}
                        </div>

                        {/* Points to Elaborate */}
                        <div className="p-3 bg-amber-50/60 rounded-lg border border-amber-200/60 space-y-2">
                          <div className="font-bold text-amber-900 text-xs flex items-center gap-1.5">
                            <Lightbulb className="w-4 h-4 text-amber-600" />
                            Points to Elaborate On ({currentLocalEval.points_to_elaborate.length}):
                          </div>
                          {currentLocalEval.points_to_elaborate.length > 0 ? (
                            <ul className="space-y-1 text-xs text-amber-950">
                              {currentLocalEval.points_to_elaborate.map((pt, i) => (
                                <li key={i} className="flex items-start gap-1.5">
                                  <span className="text-amber-600 font-bold">•</span>
                                  <span>{pt}</span>
                                </li>
                              ))}
                            </ul>
                          ) : (
                            <p className="text-xs text-emerald-700 font-medium">
                              Great job! All core rubric criteria appear touched upon.
                            </p>
                          )}
                        </div>
                      </div>

                      {/* Structural Feedback & Suggestions */}
                      {currentLocalEval.structure_feedback.length > 0 && (
                        <div className="p-3 bg-blue-50/60 rounded-lg border border-blue-200/60 space-y-1">
                          <span className="font-bold text-blue-900 text-xs">Answer Structure & Pacing:</span>
                          <ul className="list-disc list-inside text-xs text-blue-950 space-y-0.5">
                            {currentLocalEval.structure_feedback.map((fb, i) => (
                              <li key={i}>{fb}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {currentLocalEval.suggestions.length > 0 && (
                        <div className="p-3 bg-gray-50 rounded-lg border border-gray-200 space-y-1">
                          <span className="font-bold text-gray-800 text-xs">Practical Suggestions:</span>
                          <ul className="list-disc list-inside text-xs text-gray-700 space-y-0.5">
                            {currentLocalEval.suggestions.map((sug, i) => (
                              <li key={i}>{sug}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  )
                )}

                {/* Disclaimers & Limitations Disclosure */}
                <div className="pt-2 border-t border-gray-100 flex items-start gap-2 text-[11px] text-gray-500">
                  <ShieldCheck className="w-4 h-4 text-[#1B5E3B] shrink-0 mt-0.5" />
                  <span>
                    {currentAiEval ? currentAiEval.disclaimer : currentLocalEval?.disclaimer}
                  </span>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}
