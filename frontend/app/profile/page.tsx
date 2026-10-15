import { Metadata } from "next";
import { ProfileForm } from "@/components/profile/profile-form";
import { AboutSection } from "@/components/profile/about-section";
import { ResumeSection } from "@/components/profile/resume-section";
import { EducationSection } from "@/components/profile/education-section";
import { SkillsSection } from "@/components/profile/skills-section";
import { ProjectsSection } from "@/components/profile/projects-section";
import { ExperienceSection } from "@/components/profile/experience-section";
import { CareerPreferencesSection } from "@/components/profile/career-preferences-section";
import { ContactLinksSection } from "@/components/profile/contact-links-section";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { ArrowLeft, Sparkles, ArrowRight } from "lucide-react";
import { StudentNav } from "@/components/navigation/student-nav";
import { createClient } from "@/lib/supabase/server";
import { getProfileStatus } from "@/lib/profile/profile-status";

export const metadata: Metadata = {
  title: "Profile | CareerPilot AI",
  description: "Manage your CareerPilot student profile",
};

export default async function ProfilePage() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  const {
    data: { session },
  } = await supabase.auth.getSession();

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  const profileStatus = await getProfileStatus(user, session?.access_token || null, API_URL);

  return (
    <div className="flex min-h-screen flex-col bg-background">
      <StudentNav />
      <main className="flex-1 p-4 sm:p-8">
        <div className="mx-auto w-full max-w-3xl space-y-8">
          {/* Header navigation */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <Link href="/dashboard" aria-label="Back to Dashboard">
                <Button variant="ghost" size="icon" className="rounded-full">
                  <ArrowLeft className="h-5 w-5" />
                </Button>
              </Link>
              <div>
                <h1 className="text-3xl font-bold tracking-tight text-foreground">
                  Your Profile
                </h1>
                <p className="text-xs sm:text-sm text-muted-foreground mt-0.5">
                  Edit your profile, education, skills, and resume sections independently below.
                </p>
              </div>
            </div>

            {/* For configured returning users, keep an unobtrusive link to reopen wizard if needed */}
            <Link href="/profile/setup">
              <Button
                variant="ghost"
                size="sm"
                className="text-xs text-muted-foreground hover:text-foreground"
              >
                Revisit setup wizard
              </Button>
            </Link>
          </div>

          {/* Modest in-progress notice ONLY when onboarding is genuinely incomplete */}
          {!profileStatus.isConfigured && profileStatus.role !== "admin" && (
            <div className="rounded-xl border border-primary/20 bg-primary/5 p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-2xs">
              <div className="flex items-center gap-3">
                <Sparkles className="size-5 text-primary shrink-0" />
                <div>
                  <p className="text-sm font-semibold text-[#14261C]">
                    Profile setup is in progress
                  </p>
                  <p className="text-xs text-muted-foreground">
                    Complete the remaining guided wizard steps to unlock personalized opportunity matches and AI assistance.
                  </p>
                </div>
              </div>
              <Link href="/profile/setup">
                <Button
                  size="sm"
                  className="bg-primary text-primary-foreground font-semibold gap-1.5 shrink-0"
                >
                  Continue Setup Wizard
                  <ArrowRight className="size-3.5" />
                </Button>
              </Link>
            </div>
          )}

          {/* Profile Content sections */}
          <div className="space-y-6">
            <ProfileForm />
            <AboutSection />
            <EducationSection />
            <SkillsSection />
            <ProjectsSection />
            <ExperienceSection />
            <CareerPreferencesSection />
            <ContactLinksSection />
            <ResumeSection />
          </div>
        </div>
      </main>
    </div>
  );
}
