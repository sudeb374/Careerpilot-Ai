"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import {
  Loader2,
  ChevronRight,
  ChevronLeft,
  ArrowRight,
  User,
  GraduationCap,
  Sparkles,
  Briefcase,
  Compass,
  FileText,
  CheckCircle2,
  AlertCircle,
  Edit3,
} from "lucide-react";

import { LocationAutocomplete } from "@/components/ui/location-autocomplete";
import { ProfilePicture } from "@/components/profile/profile-picture";
import { MultiSkillEditor, ProfileSkill } from "@/components/profile/multi-skill-editor";
import { EducationSection } from "@/components/profile/education-section";
import { ExperienceSection } from "@/components/profile/experience-section";
import { ProjectsSection } from "@/components/profile/projects-section";
import { CareerPreferencesSection } from "@/components/profile/career-preferences-section";
import { ContactLinksSection } from "@/components/profile/contact-links-section";
import { ResumeSection } from "@/components/profile/resume-section";

// Visual Sections matching exact requirement specifications
export interface WizardVisualGroup {
  letter: "A" | "B" | "C" | "D" | "E" | "F";
  title: string;
  stepNumbers: number[];
  icon: typeof User;
}

export const VISUAL_GROUPS: WizardVisualGroup[] = [
  { letter: "A", title: "Profile Identity", stepNumbers: [1, 2], icon: User },
  { letter: "B", title: "Education", stepNumbers: [3], icon: GraduationCap },
  { letter: "C", title: "Skills", stepNumbers: [4], icon: Sparkles },
  { letter: "D", title: "Experience & Portfolio", stepNumbers: [5, 6], icon: Briefcase },
  { letter: "E", title: "Career Direction", stepNumbers: [7], icon: Compass },
  { letter: "F", title: "Application Materials", stepNumbers: [8, 9], icon: FileText },
];

export interface WizardStepMeta {
  step: number;
  sectionLetter: "A" | "B" | "C" | "D" | "E" | "F" | "Review";
  sectionTitle: string;
  title: string;
  description: string;
}

export const WIZARD_STEPS: WizardStepMeta[] = [
  {
    step: 1,
    sectionLetter: "A",
    sectionTitle: "Profile Identity",
    title: "Basic Information",
    description: "Provide your candidate name, professional headline, location, and photo.",
  },
  {
    step: 2,
    sectionLetter: "A",
    sectionTitle: "Profile Identity",
    title: "About",
    description: "Write a brief summary of your background, technical interests, and goals.",
  },
  {
    step: 3,
    sectionLetter: "B",
    sectionTitle: "Education",
    title: "Education",
    description: "Add your degrees, institutions, GPA, and graduation milestones.",
  },
  {
    step: 4,
    sectionLetter: "C",
    sectionTitle: "Skills",
    title: "Skills",
    description: "Stage multiple technical skills with proficiency levels before saving.",
  },
  {
    step: 5,
    sectionLetter: "D",
    sectionTitle: "Experience & Portfolio",
    title: "Experience",
    description: "Add internships, part-time roles, or professional work history.",
  },
  {
    step: 6,
    sectionLetter: "D",
    sectionTitle: "Experience & Portfolio",
    title: "Projects",
    description: "Showcase academic, open-source, or personal projects with links.",
  },
  {
    step: 7,
    sectionLetter: "E",
    sectionTitle: "Career Direction",
    title: "Career Preferences and Locations",
    description: "Configure your target job roles, preferred cities, and work models.",
  },
  {
    step: 8,
    sectionLetter: "F",
    sectionTitle: "Application Materials",
    title: "Contact Links",
    description: "Add your LinkedIn profile, GitHub URL, portfolio site, and phone number.",
  },
  {
    step: 9,
    sectionLetter: "F",
    sectionTitle: "Application Materials",
    title: "Resume Upload",
    description: "Upload your latest resume for AI structure verification and insights.",
  },
  {
    step: 10,
    sectionLetter: "Review",
    sectionTitle: "Review & Finish",
    title: "Review & Finish",
    description: "Review all information before completing setup.",
  },
];

interface ConsolidatedProfile {
  id?: string;
  full_name?: string | null;
  headline?: string | null;
  location?: string | null;
  about?: string | null;
  profile_picture_url?: string | null;
  phone?: string | null;
  linkedin_url?: string | null;
  github_url?: string | null;
  portfolio_url?: string | null;
}

export function ProfileSetupWizard() {
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState(1);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [stepError, setStepError] = useState<string | null>(null);

  // Profile data state
  const [profile, setProfile] = useState<ConsolidatedProfile>({});
  const [isNewProfile, setIsNewProfile] = useState(true);

  // Form states for Step 1 (Basic Info) & Step 2 (About)
  const [basicInfo, setBasicInfo] = useState({
    full_name: "",
    headline: "",
    location: "",
  });
  const [aboutText, setAboutText] = useState("");

  // Review Summary Data
  const [reviewSummary, setReviewSummary] = useState<{
    profile: ConsolidatedProfile;
    educations: Array<{ id: string; institution: string; degree: string; field_of_study: string }>;
    skills: ProfileSkill[];
    experiences: Array<{ id: string; company: string; role: string }>;
    projects: Array<{ id: string; title: string }>;
    preferences: { desired_roles?: string[]; locations?: string[]; work_model?: string[] } | null;
    resumes: Array<{ id: string; original_filename: string; is_active: boolean }>;
  } | null>(null);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  // Load existing profile on mount to preserve state safely
  const loadExistingProfile = useCallback(async () => {
    try {
      const supabase = createClient();
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) return;

      const res = await fetch(`${API_URL}/api/v1/profile`, {
        headers: { Authorization: `Bearer ${session.access_token}` },
      });

      if (res.ok) {
        const data = await res.json();
        setProfile(data);
        setIsNewProfile(false);
        setBasicInfo({
          full_name: data.full_name || "",
          headline: data.headline || "",
          location: data.location || "",
        });
        setAboutText(data.about || "");
      } else if (res.status === 404) {
        setIsNewProfile(true);
      }
    } catch (err) {
      console.error("Failed to load existing profile in wizard:", err);
    } finally {
      setIsLoading(false);
    }
  }, [API_URL]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadExistingProfile();
  }, [loadExistingProfile]);

  // Load consolidated review summary when reaching step 10
  const loadReviewSummary = useCallback(async () => {
    setIsLoading(true);
    try {
      const supabase = createClient();
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) return;

      const headers = { Authorization: `Bearer ${session.access_token}` };

      const [profileRes, eduRes, skillRes, expRes, projRes, prefRes, resumeRes] = await Promise.all([
        fetch(`${API_URL}/api/v1/profile`, { headers }).catch(() => null),
        fetch(`${API_URL}/api/v1/profile/education`, { headers }).catch(() => null),
        fetch(`${API_URL}/api/v1/profile/skills`, { headers }).catch(() => null),
        fetch(`${API_URL}/api/v1/profile/experience`, { headers }).catch(() => null),
        fetch(`${API_URL}/api/v1/profile/projects`, { headers }).catch(() => null),
        fetch(`${API_URL}/api/v1/profile/preferences`, { headers }).catch(() => null),
        fetch(`${API_URL}/api/v1/profile/resumes`, { headers }).catch(() => null),
      ]);

      const profData = profileRes && profileRes.ok ? await profileRes.json() : {};
      const eduData = eduRes && eduRes.ok ? await eduRes.json() : [];
      const skillData = skillRes && skillRes.ok ? await skillRes.json() : [];
      const expData = expRes && expRes.ok ? await expRes.json() : [];
      const projData = projRes && projRes.ok ? await projRes.json() : [];
      const prefData = prefRes && prefRes.ok ? await prefRes.json() : null;
      const resumeData = resumeRes && resumeRes.ok ? await resumeRes.json() : [];

      setReviewSummary({
        profile: profData,
        educations: eduData,
        skills: skillData,
        experiences: expData,
        projects: projData,
        preferences: prefData,
        resumes: resumeData,
      });
    } catch (err) {
      console.error("Failed to load review summary:", err);
    } finally {
      setIsLoading(false);
    }
  }, [API_URL]);

  useEffect(() => {
    if (currentStep === 10) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      loadReviewSummary();
    }
  }, [currentStep, loadReviewSummary]);

  // Save Step 1: Basic Information
  const saveStep1 = async (): Promise<boolean> => {
    if (!basicInfo.full_name.trim()) {
      setStepError("Full Name is required.");
      return false;
    }

    setIsSaving(true);
    setStepError(null);
    try {
      const supabase = createClient();
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) {
        setStepError("Session expired. Please log in again.");
        return false;
      }

      const method = isNewProfile ? "POST" : "PATCH";
      const res = await fetch(`${API_URL}/api/v1/profile`, {
        method,
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({
          full_name: basicInfo.full_name.trim(),
          headline: basicInfo.headline.trim() || null,
          location: basicInfo.location.trim() || null,
        }),
      });

      if (res.ok) {
        setIsNewProfile(false);
        setProfile((prev) => ({
          ...prev,
          full_name: basicInfo.full_name.trim(),
          headline: basicInfo.headline.trim() || null,
          location: basicInfo.location.trim() || null,
        }));
        return true;
      } else {
        const errData = await res.json().catch(() => ({}));
        setStepError(errData.detail || "Failed to save basic information.");
        return false;
      }
    } catch (err: unknown) {
      setStepError((err as Error)?.message || "A network error occurred.");
      return false;
    } finally {
      setIsSaving(false);
    }
  };

  // Save Step 2: About
  const saveStep2 = async (): Promise<boolean> => {
    setIsSaving(true);
    setStepError(null);
    try {
      const supabase = createClient();
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) {
        setStepError("Session expired. Please log in again.");
        return false;
      }

      const trimmed = aboutText.trim() || null;
      const res = await fetch(`${API_URL}/api/v1/profile`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({ about: trimmed }),
      });

      if (res.ok) {
        setProfile((prev) => ({ ...prev, about: trimmed || undefined }));
        return true;
      } else {
        const errData = await res.json().catch(() => ({}));
        setStepError(errData.detail || "Failed to update about section.");
        return false;
      }
    } catch (err: unknown) {
      setStepError((err as Error)?.message || "A network error occurred.");
      return false;
    } finally {
      setIsSaving(false);
    }
  };

  // Advance step handler
  // Restore saved step from URL or localStorage if returning midway
  useEffect(() => {
    if (typeof window !== "undefined") {
      const params = new URLSearchParams(window.location.search);
      const urlStep = parseInt(params.get("step") || "", 10);
      if (urlStep >= 1 && urlStep <= 10) {
        // eslint-disable-next-line react-hooks/set-state-in-effect
        setCurrentStep(urlStep);
        return;
      }
      const saved = localStorage.getItem("careerpilot_wizard_step");
      if (saved) {
        const stepNum = parseInt(saved, 10);
        if (stepNum >= 1 && stepNum <= 10) {
          setCurrentStep(stepNum);
        }
      }
    }
  }, []);

  const changeStep = (stepNumber: number) => {
    setCurrentStep(stepNumber);
    if (typeof window !== "undefined") {
      localStorage.setItem("careerpilot_wizard_step", String(stepNumber));
    }
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const handleNext = async () => {
    setStepError(null);

    if (currentStep === 1) {
      const ok = await saveStep1();
      if (!ok) return;
    } else if (currentStep === 2) {
      const ok = await saveStep2();
      if (!ok) return;
    }

    if (currentStep < 10) {
      changeStep(currentStep + 1);
    }
  };

  const handleBack = () => {
    setStepError(null);
    if (currentStep > 1) {
      changeStep(currentStep - 1);
    }
  };

  const handleJumpToStep = (stepNumber: number) => {
    setStepError(null);
    changeStep(stepNumber);
  };

  const handleFinishWizard = async () => {
    setIsSaving(true);
    try {
      const supabase = createClient();
      await supabase.auth.updateUser({
        data: { profile_setup_completed: true },
      });
      if (typeof window !== "undefined") {
        localStorage.removeItem("careerpilot_wizard_step");
      }
    } catch (err) {
      console.warn("Could not set profile_setup_completed metadata:", err);
    } finally {
      setIsSaving(false);
      router.push("/dashboard");
    }
  };

  const currentStepMeta = WIZARD_STEPS.find((s) => s.step === currentStep) || WIZARD_STEPS[0];
  const progressPercent = Math.min(100, Math.round(((currentStep - 1) / 9) * 100));

  if (isLoading && currentStep === 1) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Loader2 className="size-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="mx-auto w-full max-w-4xl space-y-6">
      {/* Visual Section Group Navigator */}
      <div className="rounded-2xl border border-border bg-card p-4 sm:p-5 shadow-xs">
        <div className="flex items-center justify-between gap-2 border-b border-border/60 pb-3 mb-4">
          <div>
            <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Profile Setup Wizard
            </span>
            <h2 className="text-lg font-bold text-foreground">
              9 Steps • 6 Visual Sections
            </h2>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-medium text-muted-foreground">
              {progressPercent}% Complete
            </span>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => router.push("/profile")}
              className="text-xs text-muted-foreground hover:text-foreground"
            >
              Exit to Profile
            </Button>
          </div>
        </div>

        {/* 6 Visual Group Badges */}
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-2">
          {VISUAL_GROUPS.map((group) => {
            const isGroupActive = group.stepNumbers.includes(currentStep);
            const isGroupCompleted = group.stepNumbers.every((n) => n < currentStep);
            const Icon = group.icon;

            return (
              <button
                key={group.letter}
                type="button"
                onClick={() => handleJumpToStep(group.stepNumbers[0])}
                className={`flex flex-col items-start p-2.5 rounded-xl border text-left transition-all ${
                  isGroupActive
                    ? "border-primary bg-primary/5 text-primary shadow-2xs ring-1 ring-primary/30"
                    : isGroupCompleted
                    ? "border-emerald-200 bg-emerald-50/50 text-emerald-800 hover:bg-emerald-50"
                    : "border-border/70 bg-background/60 text-muted-foreground hover:border-border"
                }`}
              >
                <div className="flex items-center justify-between w-full mb-1">
                  <span className="text-[10px] font-bold uppercase tracking-wider">
                    Sec {group.letter}
                  </span>
                  {isGroupCompleted ? (
                    <CheckCircle2 className="size-3.5 text-emerald-600" />
                  ) : (
                    <Icon className="size-3.5 opacity-70" />
                  )}
                </div>
                <span className="text-xs font-medium line-clamp-1">
                  {group.title}
                </span>
              </button>
            );
          })}
        </div>

        {/* Progress bar */}
        <div className="mt-4">
          <div className="h-1.5 w-full bg-muted rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-emerald-500 to-primary transition-all duration-300 rounded-full"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
        </div>
      </div>

      {/* Step Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 px-1">
        <div>
          <div className="inline-flex items-center gap-1.5 text-xs font-semibold text-primary mb-1">
            <span>Section {currentStepMeta.sectionLetter} — {currentStepMeta.sectionTitle}</span>
            <span>•</span>
            <span>Step {currentStep} of 9</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">
            {currentStepMeta.title}
          </h1>
          <p className="text-xs sm:text-sm text-muted-foreground mt-0.5">
            {currentStepMeta.description}
          </p>
        </div>
      </div>

      {/* Step Error Notice */}
      {stepError && (
        <div className="flex items-center gap-2 rounded-xl bg-destructive/15 border border-destructive/20 p-3.5 text-xs font-medium text-destructive">
          <AlertCircle className="size-4 shrink-0" />
          <span>{stepError}</span>
        </div>
      )}

      {/* Step Content Container */}
      <div className="rounded-2xl border border-border bg-card p-5 sm:p-7 shadow-xs">
        {/* STEP 1: Basic Information */}
        {currentStep === 1 && (
          <div className="space-y-6">
            <div className="flex flex-col sm:flex-row items-center gap-6 border-b border-border/60 pb-6">
              <ProfilePicture
                fullName={basicInfo.full_name || "Student"}
                initialPictureUrl={profile.profile_picture_url}
              />
              <div className="space-y-1 text-center sm:text-left">
                <h3 className="text-sm font-semibold text-foreground">Profile Picture</h3>
                <p className="text-xs text-muted-foreground">
                  Upload a clear portrait. Formats: PNG, JPEG, WEBP up to 5MB.
                </p>
              </div>
            </div>

            <div className="space-y-4">
              <div className="space-y-1.5">
                <Label htmlFor="full_name" className="text-xs font-semibold text-foreground">
                  Full Name <span className="text-destructive">*</span>
                </Label>
                <Input
                  id="full_name"
                  value={basicInfo.full_name}
                  onChange={(e) => setBasicInfo({ ...basicInfo, full_name: e.target.value })}
                  placeholder="e.g. Priyanshu Sharma"
                  disabled={isSaving}
                  className="bg-background"
                />
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="headline" className="text-xs font-semibold text-foreground">
                  Professional Headline
                </Label>
                <Input
                  id="headline"
                  value={basicInfo.headline}
                  onChange={(e) => setBasicInfo({ ...basicInfo, headline: e.target.value })}
                  placeholder="e.g. Computer Science Student | Aspiring Full Stack Engineer"
                  disabled={isSaving}
                  className="bg-background"
                />
                <p className="text-[11px] text-muted-foreground">
                  A concise 1-line summary that highlights your primary focus or career objective.
                </p>
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="location" className="text-xs font-semibold text-foreground">
                  Primary Location
                </Label>
                <LocationAutocomplete
                  placeholder="Search city or locality (e.g., Kolkata, Salt Lake, Pune)..."
                  singleSelect={true}
                  value={basicInfo.location}
                  onValueChange={(loc) => {
                    setBasicInfo({ ...basicInfo, location: loc });
                  }}
                  disabled={isSaving}
                />
                <p className="text-[11px] text-muted-foreground">
                  Type your city or locality for matching opportunities. Free Indian postal coverage supported.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* STEP 2: About */}
        {currentStep === 2 && (
          <div className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="about-text" className="text-xs font-semibold text-foreground">
                Personal Bio / Summary
              </Label>
              <Textarea
                id="about-text"
                rows={6}
                value={aboutText}
                onChange={(e) => setAboutText(e.target.value)}
                placeholder="Passionate undergraduate student specializing in distributed systems, modern web engineering, and machine learning. Looking for software engineering internship opportunities where I can contribute to impactful software..."
                disabled={isSaving}
                className="bg-background leading-relaxed"
              />
              <div className="flex justify-between items-center text-[11px] text-muted-foreground">
                <span>Recommended: 2–4 sentences describing your passions and goals.</span>
                <span>{aboutText.length} characters</span>
              </div>
            </div>
          </div>
        )}

        {/* STEP 3: Education */}
        {currentStep === 3 && (
          <div className="space-y-4">
            <EducationSection />
          </div>
        )}

        {/* STEP 4: Skills */}
        {currentStep === 4 && (
          <div className="space-y-4">
            <MultiSkillEditor />
          </div>
        )}

        {/* STEP 5: Experience */}
        {currentStep === 5 && (
          <div className="space-y-4">
            <ExperienceSection />
          </div>
        )}

        {/* STEP 6: Projects */}
        {currentStep === 6 && (
          <div className="space-y-4">
            <ProjectsSection />
          </div>
        )}

        {/* STEP 7: Career Direction */}
        {currentStep === 7 && (
          <div className="space-y-4">
            <CareerPreferencesSection />
          </div>
        )}

        {/* STEP 8: Contact Links */}
        {currentStep === 8 && (
          <div className="space-y-4">
            <ContactLinksSection />
          </div>
        )}

        {/* STEP 9: Resume Upload */}
        {currentStep === 9 && (
          <div className="space-y-4">
            <ResumeSection />
          </div>
        )}

        {/* STEP 10: Review & Finish */}
        {currentStep === 10 && (
          <div className="space-y-6">
            {isLoading ? (
              <div className="flex h-48 items-center justify-center">
                <Loader2 className="size-6 animate-spin text-primary" />
              </div>
            ) : reviewSummary ? (
              <div className="space-y-6">
                <div className="rounded-xl bg-emerald-50 border border-emerald-200 p-4 flex items-center gap-3">
                  <CheckCircle2 className="size-6 text-emerald-600 shrink-0" />
                  <div>
                    <h3 className="text-sm font-bold text-emerald-900">
                      Profile Setup Complete!
                    </h3>
                    <p className="text-xs text-emerald-800">
                      Here is a summary of the profile information you configured across all 6 sections.
                    </p>
                  </div>
                </div>

                {/* Section A: Profile Identity Summary */}
                <div className="rounded-xl border border-border p-4 space-y-2">
                  <div className="flex items-center justify-between border-b pb-2">
                    <span className="text-xs font-bold uppercase text-muted-foreground flex items-center gap-1.5">
                      <User className="size-3.5" /> Section A: Profile Identity
                    </span>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleJumpToStep(1)}
                      className="h-6 text-xs text-primary"
                    >
                      <Edit3 className="size-3 mr-1" /> Edit
                    </Button>
                  </div>
                  <div className="text-xs space-y-1">
                    <p><strong>Name:</strong> {reviewSummary.profile.full_name || "Not set"}</p>
                    <p><strong>Headline:</strong> {reviewSummary.profile.headline || "Not set"}</p>
                    <p><strong>Location:</strong> {reviewSummary.profile.location || "Not set"}</p>
                    <p className="line-clamp-2"><strong>About:</strong> {reviewSummary.profile.about || "Not set"}</p>
                  </div>
                </div>

                {/* Section B: Education Summary */}
                <div className="rounded-xl border border-border p-4 space-y-2">
                  <div className="flex items-center justify-between border-b pb-2">
                    <span className="text-xs font-bold uppercase text-muted-foreground flex items-center gap-1.5">
                      <GraduationCap className="size-3.5" /> Section B: Education ({reviewSummary.educations.length})
                    </span>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleJumpToStep(3)}
                      className="h-6 text-xs text-primary"
                    >
                      <Edit3 className="size-3 mr-1" /> Edit
                    </Button>
                  </div>
                  {reviewSummary.educations.length > 0 ? (
                    <div className="space-y-1 text-xs">
                      {reviewSummary.educations.map((edu) => (
                        <div key={edu.id} className="text-muted-foreground">
                          • <strong className="text-foreground">{edu.degree} in {edu.field_of_study}</strong> — {edu.institution}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-muted-foreground italic">No education records added yet.</p>
                  )}
                </div>

                {/* Section C: Skills Summary */}
                <div className="rounded-xl border border-border p-4 space-y-2">
                  <div className="flex items-center justify-between border-b pb-2">
                    <span className="text-xs font-bold uppercase text-muted-foreground flex items-center gap-1.5">
                      <Sparkles className="size-3.5" /> Section C: Skills ({reviewSummary.skills.length})
                    </span>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleJumpToStep(4)}
                      className="h-6 text-xs text-primary"
                    >
                      <Edit3 className="size-3 mr-1" /> Edit
                    </Button>
                  </div>
                  {reviewSummary.skills.length > 0 ? (
                    <div className="flex flex-wrap gap-1.5">
                      {reviewSummary.skills.map((s) => (
                        <Badge key={s.id} variant="secondary" className="text-xs gap-1">
                          <span>{s.skill_name}</span>
                          <span className="text-[10px] opacity-70">({s.proficiency})</span>
                        </Badge>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-muted-foreground italic">No skills added yet.</p>
                  )}
                </div>

                {/* Section D: Experience & Projects */}
                <div className="rounded-xl border border-border p-4 space-y-2">
                  <div className="flex items-center justify-between border-b pb-2">
                    <span className="text-xs font-bold uppercase text-muted-foreground flex items-center gap-1.5">
                      <Briefcase className="size-3.5" /> Section D: Experience & Projects
                    </span>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleJumpToStep(5)}
                      className="h-6 text-xs text-primary"
                    >
                      <Edit3 className="size-3 mr-1" /> Edit
                    </Button>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                    <div>
                      <span className="font-semibold text-foreground">Work History:</span>
                      <p className="text-muted-foreground mt-0.5">
                        {reviewSummary.experiences.length} role{reviewSummary.experiences.length === 1 ? "" : "s"} saved.
                      </p>
                    </div>
                    <div>
                      <span className="font-semibold text-foreground">Projects:</span>
                      <p className="text-muted-foreground mt-0.5">
                        {reviewSummary.projects.length} project{reviewSummary.projects.length === 1 ? "" : "s"} saved.
                      </p>
                    </div>
                  </div>
                </div>

                {/* Section E: Career Direction */}
                <div className="rounded-xl border border-border p-4 space-y-2">
                  <div className="flex items-center justify-between border-b pb-2">
                    <span className="text-xs font-bold uppercase text-muted-foreground flex items-center gap-1.5">
                      <Compass className="size-3.5" /> Section E: Career Direction & Preferences
                    </span>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleJumpToStep(7)}
                      className="h-6 text-xs text-primary"
                    >
                      <Edit3 className="size-3 mr-1" /> Edit
                    </Button>
                  </div>
                  <div className="text-xs space-y-1">
                    <p>
                      <strong>Desired Roles:</strong>{" "}
                      {reviewSummary.preferences?.desired_roles?.join(", ") || "Not configured"}
                    </p>
                    <p>
                      <strong>Preferred Locations:</strong>{" "}
                      {reviewSummary.preferences?.locations?.join(", ") || "Not configured"}
                    </p>
                    <p>
                      <strong>Work Models:</strong>{" "}
                      {reviewSummary.preferences?.work_model?.join(", ") || "Not configured"}
                    </p>
                  </div>
                </div>

                {/* Section F: Application Materials */}
                <div className="rounded-xl border border-border p-4 space-y-2">
                  <div className="flex items-center justify-between border-b pb-2">
                    <span className="text-xs font-bold uppercase text-muted-foreground flex items-center gap-1.5">
                      <FileText className="size-3.5" /> Section F: Application Materials
                    </span>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleJumpToStep(8)}
                      className="h-6 text-xs text-primary"
                    >
                      <Edit3 className="size-3 mr-1" /> Edit
                    </Button>
                  </div>
                  <div className="text-xs space-y-1">
                    <p><strong>Phone:</strong> {reviewSummary.profile.phone || "Not set"}</p>
                    <p><strong>LinkedIn:</strong> {reviewSummary.profile.linkedin_url || "Not set"}</p>
                    <p><strong>GitHub:</strong> {reviewSummary.profile.github_url || "Not set"}</p>
                    <p><strong>Portfolio:</strong> {reviewSummary.profile.portfolio_url || "Not set"}</p>
                    <p>
                      <strong>Resumes:</strong>{" "}
                      {reviewSummary.resumes.length > 0
                        ? `${reviewSummary.resumes.length} resume(s) uploaded (${reviewSummary.resumes.find((r) => r.is_active)?.original_filename || "None active"})`
                        : "No resume uploaded yet"}
                    </p>
                  </div>
                </div>
              </div>
            ) : (
              <p className="text-xs text-muted-foreground">Unable to load review summary.</p>
            )}
          </div>
        )}
      </div>

      {/* Navigation Controls Bar */}
      <div className="flex items-center justify-between gap-4 rounded-2xl border border-border bg-card p-4 shadow-xs">
        <Button
          variant="outline"
          onClick={handleBack}
          disabled={currentStep === 1 || isSaving}
          className="gap-1.5 text-xs sm:text-sm"
        >
          <ChevronLeft className="size-4" />
          Back
        </Button>

        <div className="flex items-center gap-2">
          {currentStep < 10 ? (
            <Button
              onClick={handleNext}
              disabled={isSaving}
              className="gap-1.5 bg-primary text-primary-foreground text-xs sm:text-sm font-semibold"
            >
              {isSaving ? (
                <>
                  <Loader2 className="size-4 animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  Save & Continue
                  <ChevronRight className="size-4" />
                </>
              )}
            </Button>
          ) : (
            <Button
              onClick={handleFinishWizard}
              disabled={isSaving}
              className="gap-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs sm:text-sm font-semibold"
            >
              {isSaving ? (
                <>
                  <Loader2 className="size-4 animate-spin" />
                  Completing Setup...
                </>
              ) : (
                <>
                  Complete Setup & Go to Dashboard
                  <ArrowRight className="size-4" />
                </>
              )}
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
