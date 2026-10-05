import { Metadata } from "next";
import { ProfileForm } from "@/components/profile/profile-form";
import { EducationSection } from "@/components/profile/education-section";
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
            <p className="text-muted-foreground mt-1">
              Manage your personal information, experience, and career preferences.
            </p>
          </div>
        </div>

        {/* Profile Content sections */}
        <div className="space-y-6">
          <ProfileForm />
          
          <EducationSection />

          {/* Placeholders for future sections */}
          <div className="rounded-xl border border-border border-dashed bg-card/50 p-8 text-center text-muted-foreground">
            <p>Experience and Skills sections coming soon.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
