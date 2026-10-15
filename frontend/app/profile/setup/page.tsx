import { Metadata } from "next";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { StudentNav } from "@/components/navigation/student-nav";
import { ProfileSetupWizard } from "@/components/profile/wizard/profile-setup-wizard";

export const metadata: Metadata = {
  title: "Profile Setup Wizard | CareerPilot AI",
  description: "Complete your multi-step candidate profile setup",
};

export default function ProfileSetupPage() {
  return (
    <div className="flex min-h-screen flex-col bg-[#F6FAF7]">
      <StudentNav />
      <main className="flex-1 p-4 sm:p-8">
        <div className="mx-auto w-full max-w-4xl space-y-6">
          {/* Header navigation */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Link href="/profile" aria-label="Back to Profile">
                <Button variant="ghost" size="icon" className="rounded-full bg-white shadow-2xs">
                  <ArrowLeft className="h-5 w-5" />
                </Button>
              </Link>
              <div>
                <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-[#14261C]">
                  Profile Setup
                </h1>
                <p className="text-xs sm:text-sm text-muted-foreground">
                  Follow the 9 steps to build a complete candidate profile and unlock tailored opportunities.
                </p>
              </div>
            </div>

            <Link href="/profile">
              <Button variant="outline" size="sm" className="hidden sm:inline-flex bg-white">
                View Full Profile
              </Button>
            </Link>
          </div>

          {/* Setup Wizard */}
          <ProfileSetupWizard />
        </div>
      </main>
    </div>
  );
}
