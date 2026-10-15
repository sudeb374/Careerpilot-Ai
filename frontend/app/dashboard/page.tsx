import { createClient } from "@/lib/supabase/server";
import Link from "next/link";
import { redirect } from "next/navigation";
import { getProfileStatus } from "@/lib/profile/profile-status";
import {
  Sparkles,
  ClipboardCheck,
  Compass,
  FileEdit,
  FileCheck,
  BookOpen,
  User,
  Bookmark,
  ShieldAlert,
  ArrowRight,
  ShieldCheck,
  Layers,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { StudentNav } from "@/components/navigation/student-nav";

export default async function DashboardPage(props: {
  searchParams?: Promise<{ error?: string }>;
}) {
  const searchParams = props.searchParams ? await props.searchParams : undefined;
  const isUnauthorized = searchParams?.error === "unauthorized";

  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  const {
    data: { session },
  } = await supabase.auth.getSession();

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  const profileStatus = await getProfileStatus(user, session?.access_token || null, API_URL);

  // If new or genuinely incomplete student account, automatically guide directly into the guided setup wizard
  if (!profileStatus.isConfigured && profileStatus.role !== "admin") {
    redirect("/profile/setup");
  }

  const displayName = profileStatus.displayName;
  const isAdmin = profileStatus.role === "admin";

  return (
    <div className="flex min-h-screen flex-col bg-[#F6FAF7]">
      <StudentNav />

      <main className="flex-1 mx-auto w-full max-w-7xl px-4 py-8 sm:px-6 lg:px-8 space-y-8">
        {/* Unauthorized Alert */}
        {isUnauthorized && (
          <div
            role="alert"
            className="flex items-center gap-3 rounded-xl border border-amber-300 bg-amber-50 p-4 text-left text-sm text-amber-900 shadow-xs"
          >
            <ShieldAlert className="h-5 w-5 shrink-0 text-amber-600" />
            <div>
              <p className="font-semibold text-amber-950">Administrative Access Denied</p>
              <p className="text-xs text-amber-800 mt-0.5">
                Your account does not possess administrator privileges. You have been safely returned to your candidate workspace.
              </p>
            </div>
          </div>
        )}

        {/* Welcome Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border/60 pb-6">
          <div>
            <div className="inline-flex items-center gap-1.5 rounded-full border border-primary/20 bg-primary/5 px-3 py-1 text-xs font-semibold text-primary mb-2">
              <Sparkles className="size-3" />
              CareerPilot Workspace
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-[#14261C]">
              Welcome back, {displayName}
            </h1>
            <p className="text-sm text-muted-foreground mt-1">
              Your personalized hub for opportunity matching, application tracking, and AI career guidance.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Link href="/profile">
              <Button size="sm" className="gap-2 bg-primary text-primary-foreground font-semibold">
                <User className="size-4" />
                Manage Profile & Resume
              </Button>
            </Link>
          </div>
        </div>

        {/* Admin Quick Banner (if admin) */}
        {isAdmin && (
          <div className="rounded-xl border border-primary/20 bg-primary/5 p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="flex size-10 items-center justify-center rounded-lg bg-primary text-white">
                <ShieldCheck className="size-5" />
              </div>
              <div>
                <p className="text-sm font-bold text-[#14261C]">Administrator Privilege Active</p>
                <p className="text-xs text-muted-foreground">
                  You have access to the Admin Portal for opportunity curation and automated job ingestion.
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Link href="/admin/opportunities">
                <Button size="sm" className="bg-[#1B5E3B] text-white hover:bg-[#2E7D4F]">
                  Open Admin Portal
                  <ArrowRight className="size-3.5 ml-1.5" />
                </Button>
              </Link>
            </div>
          </div>
        )}

        {/* Primary Sections Grid */}
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {/* Card 1: Your Matches */}
          <div className="rounded-2xl border border-border bg-card p-6 shadow-xs flex flex-col justify-between hover:shadow-md transition-shadow">
            <div>
              <div className="flex items-center justify-between mb-4">
                <div className="flex size-10 items-center justify-center rounded-xl bg-primary/10 text-primary">
                  <Sparkles className="size-5" />
                </div>
                <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-primary/10 text-primary">
                  AI Ranked
                </span>
              </div>
              <h2 className="text-lg font-bold text-foreground">Your Opportunity Matches</h2>
              <p className="mt-2 text-sm text-muted-foreground leading-relaxed">
                Roles ranked by real-time alignment with your verified skills, education, and career preferences.
              </p>
            </div>
            <div className="mt-6 pt-4 border-t border-border flex items-center justify-between">
              <Link href="/matches" className="w-full">
                <Button className="w-full bg-[#1B5E3B] text-white hover:bg-[#2E7D4F] gap-2">
                  View Matching Roles
                  <ArrowRight className="size-4" />
                </Button>
              </Link>
            </div>
          </div>

          {/* Card 2: Application Tracker */}
          <div className="rounded-2xl border border-border bg-card p-6 shadow-xs flex flex-col justify-between hover:shadow-md transition-shadow">
            <div>
              <div className="flex items-center justify-between mb-4">
                <div className="flex size-10 items-center justify-center rounded-xl bg-[#14261C]/10 text-[#14261C]">
                  <ClipboardCheck className="size-5" />
                </div>
                <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-[#14261C]/10 text-[#14261C]">
                  Pipeline
                </span>
              </div>
              <h2 className="text-lg font-bold text-foreground">Application Tracker</h2>
              <p className="mt-2 text-sm text-muted-foreground leading-relaxed">
                Organize every application from discovery to offer with status milestones, interview dates, and reminders.
              </p>
            </div>
            <div className="mt-6 pt-4 border-t border-border flex items-center justify-between">
              <Link href="/applications" className="w-full">
                <Button className="w-full bg-[#14261C] text-white hover:bg-[#203a2b] gap-2">
                  Open Application Tracker
                  <ArrowRight className="size-4" />
                </Button>
              </Link>
            </div>
          </div>

          {/* Card 3: Discover Opportunities */}
          <div className="rounded-2xl border border-border bg-card p-6 shadow-xs flex flex-col justify-between hover:shadow-md transition-shadow">
            <div>
              <div className="flex items-center justify-between mb-4">
                <div className="flex size-10 items-center justify-center rounded-xl bg-saffron/15 text-saffron">
                  <Compass className="size-5" />
                </div>
                <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-saffron/15 text-saffron">
                  Search & Filters
                </span>
              </div>
              <h2 className="text-lg font-bold text-foreground">Discover Opportunities</h2>
              <p className="mt-2 text-sm text-muted-foreground leading-relaxed">
                Filter and browse hundreds of active internships and entry-level positions across work models and disciplines.
              </p>
            </div>
            <div className="mt-6 pt-4 border-t border-border flex items-center justify-between gap-2">
              <Link href="/opportunities" className="flex-1">
                <Button variant="outline" className="w-full hover:bg-muted">
                  Explore Roles
                </Button>
              </Link>
              <Link href="/saved-opportunities">
                <Button variant="outline" size="icon" title="Saved Opportunities">
                  <Bookmark className="size-4 text-primary" />
                </Button>
              </Link>
            </div>
          </div>
        </div>

        {/* Career Copilot Suite Section */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold text-[#14261C] flex items-center gap-2">
                <Layers className="size-5 text-primary" />
                Career Copilot Suite
              </h2>
              <p className="text-sm text-muted-foreground mt-0.5">
                AI-driven preparation tools strictly grounded in your active profile and target job requirements.
              </p>
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {/* Tool 1: Skill-Gap Roadmap */}
            <Link
              href="/roadmap"
              className="group block rounded-xl border border-border bg-card p-5 hover:border-primary/40 hover:shadow-sm transition-all"
            >
              <div className="flex items-center gap-3">
                <div className="flex size-9 items-center justify-center rounded-lg bg-primary/10 text-primary group-hover:bg-primary group-hover:text-white transition-colors">
                  <Compass className="size-4" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-foreground group-hover:text-primary transition-colors">
                    Skill-Gap Roadmap
                  </h3>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    Prioritized learning sequence and demand gaps
                  </p>
                </div>
              </div>
            </Link>

            {/* Tool 2: Cover Letter Generator */}
            <Link
              href="/cover-letter"
              className="group block rounded-xl border border-border bg-card p-5 hover:border-primary/40 hover:shadow-sm transition-all"
            >
              <div className="flex items-center gap-3">
                <div className="flex size-9 items-center justify-center rounded-lg bg-primary/10 text-primary group-hover:bg-primary group-hover:text-white transition-colors">
                  <FileEdit className="size-4" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-foreground group-hover:text-primary transition-colors">
                    Cover Letter Generator
                  </h3>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    Targeted letters grounded in verified experience
                  </p>
                </div>
              </div>
            </Link>

            {/* Tool 3: Question Assistant */}
            <Link
              href="/application-assistant"
              className="group block rounded-xl border border-border bg-card p-5 hover:border-primary/40 hover:shadow-sm transition-all"
            >
              <div className="flex items-center gap-3">
                <div className="flex size-9 items-center justify-center rounded-lg bg-primary/10 text-primary group-hover:bg-primary group-hover:text-white transition-colors">
                  <Sparkles className="size-4" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-foreground group-hover:text-primary transition-colors">
                    Application Question Assistant
                  </h3>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    Draft answers for recruiter screening prompts
                  </p>
                </div>
              </div>
            </Link>

            {/* Tool 4: Interview Prep */}
            <Link
              href="/interview-prep"
              className="group block rounded-xl border border-border bg-card p-5 hover:border-primary/40 hover:shadow-sm transition-all"
            >
              <div className="flex items-center gap-3">
                <div className="flex size-9 items-center justify-center rounded-lg bg-primary/10 text-primary group-hover:bg-primary group-hover:text-white transition-colors">
                  <BookOpen className="size-4" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-foreground group-hover:text-primary transition-colors">
                    Interview Preparation Lab
                  </h3>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    Database questions & instant rubric evaluation
                  </p>
                </div>
              </div>
            </Link>

            {/* Tool 5: Resume Recommendations */}
            <Link
              href="/resume-recommendations"
              className="group block rounded-xl border border-border bg-card p-5 hover:border-primary/40 hover:shadow-sm transition-all"
            >
              <div className="flex items-center gap-3">
                <div className="flex size-9 items-center justify-center rounded-lg bg-primary/10 text-primary group-hover:bg-primary group-hover:text-white transition-colors">
                  <FileCheck className="size-4" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-foreground group-hover:text-primary transition-colors">
                    Resume Recommendations
                  </h3>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    Job-specific bullet points & keyword tailoring
                  </p>
                </div>
              </div>
            </Link>

            {/* Tool 6: Profile & Resume Intelligence */}
            <Link
              href="/profile"
              className="group block rounded-xl border border-border bg-card p-5 hover:border-primary/40 hover:shadow-sm transition-all"
            >
              <div className="flex items-center gap-3">
                <div className="flex size-9 items-center justify-center rounded-lg bg-primary/10 text-primary group-hover:bg-primary group-hover:text-white transition-colors">
                  <User className="size-4" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-foreground group-hover:text-primary transition-colors">
                    Profile & Resume
                  </h3>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    Manage education, projects, skills & active resume
                  </p>
                </div>
              </div>
            </Link>
          </div>
        </div>
      </main>
    </div>
  );
}
