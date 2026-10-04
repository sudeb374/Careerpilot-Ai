import { Button } from "@/components/ui/button";
import {
  Compass,
  FileText,
  BarChart3,
  Target,
  ArrowRight,
  Sparkles,
} from "lucide-react";

const features = [
  {
    icon: Compass,
    title: "Smart Discovery",
    description:
      "AI-powered matching finds internships and entry-level roles tailored to your skills, interests, and career goals.",
  },
  {
    icon: FileText,
    title: "Resume Analysis",
    description:
      "Get instant, actionable feedback on your resume with AI-driven scoring and skill gap identification.",
  },
  {
    icon: BarChart3,
    title: "Career Insights",
    description:
      "Understand industry trends, in-demand skills, and personalized career path recommendations.",
  },
  {
    icon: Target,
    title: "Application Tracking",
    description:
      "Keep track of every opportunity from discovery to offer with a clean, organized dashboard.",
  },
];

export default function Home() {
  return (
    <div className="flex flex-col min-h-screen bg-background">
      {/* Navigation */}
      <header className="sticky top-0 z-50 w-full border-b border-border bg-background/80 backdrop-blur-sm">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-2">
            <Sparkles className="size-6 text-primary" />
            <span className="text-lg font-semibold tracking-tight text-foreground">
              CareerPilot AI
            </span>
          </div>
          <nav className="hidden items-center gap-6 sm:flex">
            <a
              href="#features"
              className="text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
            >
              Features
            </a>
            <a
              href="#about"
              className="text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
            >
              About
            </a>
            <Button size="sm">Get Started</Button>
          </nav>
          {/* Mobile menu button */}
          <Button variant="ghost" size="icon" className="sm:hidden">
            <svg
              className="size-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 6h16M4 12h16M4 18h16"
              />
            </svg>
          </Button>
        </div>
      </header>

      {/* Hero Section */}
      <main className="flex-1">
        <section className="relative overflow-hidden">
          {/* Subtle gradient background accent */}
          <div className="pointer-events-none absolute inset-0 -z-10">
            <div className="absolute left-1/2 top-0 h-[480px] w-[800px] -translate-x-1/2 rounded-full bg-primary/5 blur-3xl" />
          </div>

          <div className="mx-auto max-w-6xl px-4 py-24 sm:px-6 sm:py-32 lg:px-8">
            <div className="mx-auto max-w-2xl text-center">
              <div className="mb-6 inline-flex items-center gap-1.5 rounded-full bg-accent px-3 py-1 text-xs font-medium text-accent-foreground">
                <Sparkles className="size-3" />
                AI-Powered Career Platform
              </div>
              <h1 className="text-4xl font-bold tracking-tight text-foreground sm:text-5xl">
                Discover Your{" "}
                <span className="text-primary">Perfect Career Path</span>
              </h1>
              <p className="mt-6 text-lg leading-8 text-muted-foreground">
                CareerPilot AI helps college students and freshers find relevant
                internships, improve their resumes, and make smarter career
                decisions — all powered by AI.
              </p>
              <div className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row">
                <Button size="lg" className="gap-2">
                  Start Exploring
                  <ArrowRight className="size-4" />
                </Button>
                <Button variant="outline" size="lg">
                  Learn More
                </Button>
              </div>
            </div>
          </div>
        </section>

        {/* Features Section */}
        <section id="features" className="border-t border-border bg-muted/30 py-20 sm:py-24">
          <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
            <div className="mx-auto max-w-2xl text-center">
              <h2 className="text-3xl font-semibold tracking-tight text-foreground">
                Everything You Need to Launch Your Career
              </h2>
              <p className="mt-4 text-base leading-7 text-muted-foreground">
                From opportunity discovery to application tracking, CareerPilot
                AI equips you with the tools to succeed.
              </p>
            </div>

            <div className="mx-auto mt-16 grid max-w-5xl gap-6 sm:grid-cols-2 lg:gap-8">
              {features.map((feature) => (
                <div
                  key={feature.title}
                  className="group rounded-xl border border-border bg-card p-6 shadow-sm transition-shadow hover:shadow-md"
                >
                  <div className="mb-4 flex size-10 items-center justify-center rounded-lg bg-primary/10">
                    <feature.icon className="size-5 text-primary" />
                  </div>
                  <h3 className="text-base font-semibold text-foreground">
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

        {/* About / CTA Section */}
        <section id="about" className="py-20 sm:py-24">
          <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
            <div className="mx-auto max-w-3xl rounded-2xl border border-border bg-card p-8 text-center shadow-sm sm:p-12">
              <h2 className="text-2xl font-semibold tracking-tight text-foreground sm:text-3xl">
                Built for Students, Powered by AI
              </h2>
              <p className="mt-4 text-base leading-7 text-muted-foreground">
                CareerPilot AI combines machine learning and real-time data to
                match you with opportunities that fit your unique profile.
                Whether you&apos;re looking for your first internship or
                planning your career path, we&apos;ve got you covered.
              </p>
              <div className="mt-8">
                <Button size="lg" className="gap-2">
                  Get Started — It&apos;s Free
                  <ArrowRight className="size-4" />
                </Button>
              </div>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-border bg-muted/20">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 px-4 py-8 text-sm text-muted-foreground sm:flex-row sm:px-6 lg:px-8">
          <div className="flex items-center gap-2">
            <Sparkles className="size-4 text-primary" />
            <span className="font-medium text-foreground">CareerPilot AI</span>
          </div>
          <p>&copy; {new Date().getFullYear()} CareerPilot AI. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}
