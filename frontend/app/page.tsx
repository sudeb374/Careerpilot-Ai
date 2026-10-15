"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import {
  ArrowRight,
  BookOpen,
  BriefcaseBusiness,
  CheckCircle2,
  ClipboardCheck,
  Compass,
  FileSearch,
  GraduationCap,
  Leaf,
  MapPin,
  Menu,
  Sparkles,
  Target,
  TrendingUp,
  Users,
  X,
  Zap,
} from "lucide-react";

/* ------------------------------------------------------------------ */
/*  Static data                                                        */
/* ------------------------------------------------------------------ */

const features = [
  {
    icon: Target,
    title: "Intelligent Matching",
    description:
      "Our AI analyzes your profile against thousands of opportunities to surface the roles most relevant to your skills and goals.",
  },
  {
    icon: FileSearch,
    title: "Resume Intelligence",
    description:
      "Upload your resume and get instant scoring, skill gap analysis, and actionable suggestions to stand out to recruiters.",
  },
  {
    icon: Compass,
    title: "Career Copilot",
    description:
      "Get personalized career path recommendations, industry insights, and skill trend analysis tailored to your field.",
  },
  {
    icon: ClipboardCheck,
    title: "Application Tracker",
    description:
      "Track every opportunity from discovery to offer in one organized dashboard — no more lost spreadsheets.",
  },
];

const steps = [
  {
    number: "01",
    icon: GraduationCap,
    title: "Build Your Profile",
    description:
      "Add your education, skills, interests, and career goals. It takes under five minutes.",
  },
  {
    number: "02",
    icon: Sparkles,
    title: "Get AI-Matched",
    description:
      "Our engine matches your profile against relevant internships and entry-level positions in real time.",
  },
  {
    number: "03",
    icon: TrendingUp,
    title: "Apply & Grow",
    description:
      "Apply with confidence, track your progress, and improve your profile with AI-driven feedback.",
  },
];

const benefits = [
  { icon: BookOpen, text: "Works for any major or discipline" },
  { icon: Zap, text: "Real-time matching, not stale listings" },
  { icon: Users, text: "Built specifically for students and freshers" },
  { icon: MapPin, text: "Filter by location, remote, or hybrid" },
  { icon: BriefcaseBusiness, text: "Internships and entry-level roles" },
  { icon: CheckCircle2, text: "Free to use — no hidden fees" },
];

const mockOpportunities = [
  { company: "Stripe", role: "Software Engineering Intern", match: 94, location: "Remote" },
  { company: "Notion", role: "Product Design Intern", match: 89, location: "San Francisco" },
  { company: "Vercel", role: "Frontend Engineer Intern", match: 85, location: "Remote" },
  { company: "Linear", role: "Backend Engineering Intern", match: 81, location: "New York" },
];

/* ------------------------------------------------------------------ */
/*  Page                                                               */
/* ------------------------------------------------------------------ */

export default function Home() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <div className="flex min-h-screen flex-col bg-background">
      {/* ── Navigation ─────────────────────────────────────────────── */}
      <header className="sticky top-0 z-50 w-full border-b border-border bg-card/90 backdrop-blur-md">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6 lg:px-8">
          <Link href="/" className="flex items-center gap-2">
            <Leaf className="size-6 text-primary" />
            <span className="text-lg font-bold tracking-tight text-foreground">
              CareerPilot<span className="text-primary"> AI</span>
            </span>
          </Link>

          <nav className="hidden items-center gap-6 md:flex">
            <a href="#features" className="text-sm font-medium text-muted-foreground transition-colors hover:text-foreground">
              Features
            </a>
            <a href="#how-it-works" className="text-sm font-medium text-muted-foreground transition-colors hover:text-foreground">
              How It Works
            </a>
            <a href="#benefits" className="text-sm font-medium text-muted-foreground transition-colors hover:text-foreground">
              About
            </a>
            <Link href="/login" className="text-sm font-medium text-foreground hover:text-primary transition-colors">
              Sign In
            </Link>
            <Link href="/register">
              <Button size="sm">Get Started</Button>
            </Link>
          </nav>

          <Button
            variant="ghost"
            size="icon"
            className="md:hidden"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            aria-label="Toggle menu"
          >
            {mobileMenuOpen ? <X className="size-5" /> : <Menu className="size-5" />}
          </Button>
        </div>

        {/* Mobile dropdown */}
        {mobileMenuOpen && (
          <div className="border-b border-border bg-card px-4 py-4 md:hidden space-y-3">
            <a
              href="#features"
              onClick={() => setMobileMenuOpen(false)}
              className="block text-sm font-medium text-muted-foreground hover:text-foreground"
            >
              Features
            </a>
            <a
              href="#how-it-works"
              onClick={() => setMobileMenuOpen(false)}
              className="block text-sm font-medium text-muted-foreground hover:text-foreground"
            >
              How It Works
            </a>
            <a
              href="#benefits"
              onClick={() => setMobileMenuOpen(false)}
              className="block text-sm font-medium text-muted-foreground hover:text-foreground"
            >
              About
            </a>
            <div className="pt-2 border-t border-border flex flex-col gap-2">
              <Link
                href="/login"
                onClick={() => setMobileMenuOpen(false)}
                className="text-sm font-medium text-foreground py-1 hover:text-primary"
              >
                Sign In
              </Link>
              <Link href="/register" onClick={() => setMobileMenuOpen(false)}>
                <Button size="sm" className="w-full">Get Started</Button>
              </Link>
            </div>
          </div>
        )}
      </header>

      <main className="flex-1">
        {/* ── Hero ───────────────────────────────────────────────────── */}
        <section className="relative overflow-hidden">
          <div className="pointer-events-none absolute inset-0 -z-10">
            <div className="absolute -top-32 left-1/4 h-[500px] w-[600px] rounded-full bg-primary/[0.04] blur-3xl" />
            <div className="absolute -top-20 right-1/4 h-[400px] w-[500px] rounded-full bg-saffron/[0.03] blur-3xl" />
          </div>

          <div className="mx-auto max-w-6xl px-4 py-16 sm:px-6 sm:py-24 lg:px-8 lg:py-28">
            <div className="grid items-center gap-12 lg:grid-cols-2 lg:gap-16">
              {/* Text column */}
              <div>
                <div className="mb-5 inline-flex items-center gap-1.5 rounded-full border border-primary/20 bg-primary/5 px-3 py-1 text-xs font-medium text-primary">
                  <Sparkles className="size-3" />
                  AI-Powered Career Discovery
                </div>
                <h1 className="text-3xl font-bold leading-tight tracking-tight text-foreground sm:text-4xl lg:text-[2.75rem] lg:leading-[1.15]">
                  Find Internships That{" "}
                  <span className="text-primary">Match Your Potential</span>
                </h1>
                <p className="mt-5 max-w-lg text-base leading-7 text-muted-foreground">
                  CareerPilot AI analyzes your skills, interests, and goals to
                  surface the opportunities that fit — so you spend less time
                  scrolling job boards and more time preparing.
                </p>
                <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:items-center">
                  <Link href="/register" className="w-full sm:w-auto">
                    <Button
                      size="lg"
                      className="w-full sm:w-auto gap-2 bg-saffron text-saffron-foreground hover:bg-saffron/90 focus-visible:ring-saffron/50"
                    >
                      Get Started — It&apos;s Free
                      <ArrowRight className="size-4" />
                    </Button>
                  </Link>
                  <a href="#how-it-works" className="w-full sm:w-auto">
                    <Button variant="outline" size="lg" className="w-full sm:w-auto">
                      See How It Works
                    </Button>
                  </a>
                </div>
                <p className="mt-4 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-muted-foreground">
                  <span className="flex items-center gap-1"><CheckCircle2 className="size-3 text-primary" /> Free for students</span>
                  <span className="flex items-center gap-1"><CheckCircle2 className="size-3 text-primary" /> No credit card required</span>
                </p>
              </div>

              {/* Dashboard preview column */}
              <div className="relative mx-auto w-full max-w-lg lg:mx-0 lg:max-w-none">
                <div className="rounded-xl border border-border bg-card shadow-lg shadow-primary/[0.04]">
                  {/* Window chrome */}
                  <div className="flex items-center gap-2 border-b border-border px-4 py-2.5">
                    <div className="flex gap-1.5">
                      <span className="size-2.5 rounded-full bg-red-400/70" />
                      <span className="size-2.5 rounded-full bg-yellow-400/70" />
                      <span className="size-2.5 rounded-full bg-green-400/70" />
                    </div>
                    <span className="ml-2 text-[11px] font-medium text-muted-foreground">
                      CareerPilot AI — Dashboard
                    </span>
                  </div>

                  <div className="space-y-4 p-4">
                    {/* Stats row */}
                    <div className="grid grid-cols-3 gap-3">
                      <div className="rounded-lg bg-primary/[0.06] p-3 text-center">
                        <p className="text-xl font-bold text-primary">12</p>
                        <p className="mt-0.5 text-[11px] text-muted-foreground">New Matches</p>
                      </div>
                      <div className="rounded-lg bg-saffron/[0.08] p-3 text-center">
                        <p className="text-xl font-bold text-saffron">87<span className="text-sm font-semibold">/100</span></p>
                        <p className="mt-0.5 text-[11px] text-muted-foreground">Resume Score</p>
                      </div>
                      <div className="rounded-lg bg-info/[0.08] p-3 text-center">
                        <p className="text-xl font-bold text-info">5</p>
                        <p className="mt-0.5 text-[11px] text-muted-foreground">Applied</p>
                      </div>
                    </div>

                    {/* Opportunity list */}
                    <div>
                      <p className="mb-2 text-xs font-semibold text-foreground">Top Matches</p>
                      <div className="space-y-2">
                        {mockOpportunities.map((opp) => (
                          <div
                            key={opp.company}
                            className="flex items-center justify-between rounded-lg border border-border bg-background px-3 py-2.5"
                          >
                            <div className="min-w-0">
                              <p className="truncate text-xs font-semibold text-foreground">
                                {opp.role}
                              </p>
                              <p className="mt-0.5 text-[11px] text-muted-foreground">
                                {opp.company} · {opp.location}
                              </p>
                            </div>
                            <div className="ml-3 flex flex-col items-end gap-1">
                              <span className="text-xs font-bold text-primary">{opp.match}%</span>
                              <div className="h-1 w-12 overflow-hidden rounded-full bg-primary/10">
                                <div
                                  className="h-full rounded-full bg-primary"
                                  style={{ width: `${opp.match}%` }}
                                />
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* ── Features ──────────────────────────────────────────────── */}
        <section id="features" className="border-t border-border bg-card py-20 sm:py-24">
          <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
            <div className="mx-auto max-w-2xl text-center">
              <h2 className="text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
                Everything You Need to Launch Your Career
              </h2>
              <p className="mt-3 text-base leading-7 text-muted-foreground">
                From opportunity discovery to application tracking, CareerPilot
                AI equips you with tools purpose-built for students.
              </p>
            </div>

            <div className="mx-auto mt-14 grid max-w-5xl gap-5 sm:grid-cols-2">
              {features.map((feature) => (
                <div
                  key={feature.title}
                  className="group rounded-xl border border-border bg-background p-6 transition-shadow hover:shadow-md"
                >
                  <div className="mb-4 flex size-10 items-center justify-center rounded-lg bg-primary/10 text-primary transition-colors group-hover:bg-primary group-hover:text-primary-foreground">
                    <feature.icon className="size-5" />
                  </div>
                  <h3 className="text-[0.95rem] font-semibold text-foreground">
                    {feature.title}
                  </h3>
                  <p className="mt-2 text-sm leading-6 text-muted-foreground">
                    {feature.description}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ── How It Works ──────────────────────────────────────────── */}
        <section id="how-it-works" className="border-t border-border py-20 sm:py-24">
          <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
            <div className="mx-auto max-w-2xl text-center">
              <h2 className="text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
                How CareerPilot AI Works
              </h2>
              <p className="mt-3 text-base leading-7 text-muted-foreground">
                Three simple steps to start discovering opportunities matched to
                your profile.
              </p>
            </div>

            <div className="mx-auto mt-14 grid max-w-4xl gap-8 md:grid-cols-3">
              {steps.map((step, index) => (
                <div key={step.number} className="relative text-center">
                  {/* Connector line (desktop only, skip last) */}
                  {index < steps.length - 1 && (
                    <div className="absolute right-0 top-8 hidden h-px w-8 translate-x-full bg-border md:block" />
                  )}
                  <div className="mx-auto mb-4 flex size-14 items-center justify-center rounded-full border-2 border-primary/20 bg-primary/5">
                    <step.icon className="size-6 text-primary" />
                  </div>
                  <span className="text-xs font-bold tracking-widest text-primary">
                    STEP {step.number}
                  </span>
                  <h3 className="mt-2 text-base font-semibold text-foreground">
                    {step.title}
                  </h3>
                  <p className="mt-2 text-sm leading-6 text-muted-foreground">
                    {step.description}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ── Benefits ──────────────────────────────────────────────── */}
        <section id="benefits" className="border-t border-border bg-card py-20 sm:py-24">
          <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
            <div className="grid items-center gap-12 lg:grid-cols-2">
              <div>
                <h2 className="text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
                  Built for Students Like You
                </h2>
                <p className="mt-3 max-w-md text-base leading-7 text-muted-foreground">
                  CareerPilot AI is designed around how students actually search
                  for opportunities — not how job boards think they should.
                </p>
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                {benefits.map((benefit) => (
                  <div
                    key={benefit.text}
                    className="flex items-start gap-3 rounded-lg border border-border bg-background p-4"
                  >
                    <benefit.icon className="mt-0.5 size-4 shrink-0 text-primary" />
                    <span className="text-sm font-medium text-foreground">
                      {benefit.text}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* ── CTA ───────────────────────────────────────────────────── */}
        <section className="border-t border-border py-20 sm:py-24">
          <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
            <div className="mx-auto max-w-3xl rounded-2xl border border-primary/15 bg-primary/[0.03] p-8 text-center sm:p-12">
              <h2 className="text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
                Ready to Discover Your Next Opportunity?
              </h2>
              <p className="mx-auto mt-3 max-w-lg text-base leading-7 text-muted-foreground">
                Join students who are using AI to find internships and
                entry-level roles that actually match their skills and goals.
              </p>
              <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
                <Link href="/register" className="w-full sm:w-auto">
                  <Button
                    size="lg"
                    className="w-full sm:w-auto gap-2 bg-saffron text-saffron-foreground hover:bg-saffron/90 focus-visible:ring-saffron/50"
                  >
                    Get Started — It&apos;s Free
                    <ArrowRight className="size-4" />
                  </Button>
                </Link>
                <a href="#features" className="w-full sm:w-auto">
                  <Button variant="outline" size="lg" className="w-full sm:w-auto">
                    Learn More
                  </Button>
                </a>
              </div>
            </div>
          </div>
        </section>
      </main>

      {/* ── Footer ────────────────────────────────────────────────── */}
      <footer className="border-t border-border bg-card">
        <div className="mx-auto max-w-6xl px-4 py-10 sm:px-6 lg:px-8">
          <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
            {/* Brand */}
            <div className="sm:col-span-2 lg:col-span-1">
              <div className="flex items-center gap-2">
                <Leaf className="size-5 text-primary" />
                <span className="text-base font-bold text-foreground">
                  CareerPilot<span className="text-primary"> AI</span>
                </span>
              </div>
              <p className="mt-3 max-w-xs text-sm leading-6 text-muted-foreground">
                AI-powered career discovery for college students and freshers.
              </p>
            </div>

            {/* Platform */}
            <div>
              <h4 className="text-xs font-semibold uppercase tracking-wider text-foreground">
                Platform
              </h4>
              <ul className="mt-3 space-y-2 text-sm text-muted-foreground">
                <li><a href="#features" className="transition-colors hover:text-foreground">Features</a></li>
                <li><a href="#how-it-works" className="transition-colors hover:text-foreground">How It Works</a></li>
                <li><a href="#benefits" className="transition-colors hover:text-foreground">For Students</a></li>
              </ul>
            </div>

            {/* Resources */}
            <div>
              <h4 className="text-xs font-semibold uppercase tracking-wider text-foreground">
                Resources
              </h4>
              <ul className="mt-3 space-y-2 text-sm text-muted-foreground">
                <li><a href="#" className="transition-colors hover:text-foreground">Documentation</a></li>
                <li><a href="#" className="transition-colors hover:text-foreground">API Reference</a></li>
                <li><a href="#" className="transition-colors hover:text-foreground">Support</a></li>
              </ul>
            </div>

            {/* Legal */}
            <div>
              <h4 className="text-xs font-semibold uppercase tracking-wider text-foreground">
                Legal
              </h4>
              <ul className="mt-3 space-y-2 text-sm text-muted-foreground">
                <li><a href="#" className="transition-colors hover:text-foreground">Privacy Policy</a></li>
                <li><a href="#" className="transition-colors hover:text-foreground">Terms of Service</a></li>
              </ul>
            </div>
          </div>

          <div className="mt-10 flex flex-col items-center justify-between gap-4 border-t border-border pt-6 text-xs text-muted-foreground sm:flex-row">
            <p>&copy; {new Date().getFullYear()} CareerPilot AI. All rights reserved.</p>
            <p>
              Built with{" "}
              <span className="font-medium text-foreground">Next.js</span>,{" "}
              <span className="font-medium text-foreground">FastAPI</span>, and{" "}
              <span className="font-medium text-foreground">AI</span>.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
