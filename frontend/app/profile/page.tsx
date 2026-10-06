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
import { ArrowLeft } from "lucide-react";

export const metadata: Metadata = {
  title: "Profile | CareerPilot AI",
  description: "Manage your CareerPilot student profile",
};

export default function ProfilePage() {
  return (
    <div className="flex min-h-screen flex-col bg-background p-4 sm:p-8">
      <div className="mx-auto w-full max-w-3xl space-y-8">
        
        {/* Header navigation */}
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
          </div>
        </div>

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
    </div>
  );
}
