import { Suspense } from "react";
import { Metadata } from "next";
import Link from "next/link";
import { ArrowLeft, Compass } from "lucide-react";

import { Button } from "@/components/ui/button";
import { SkillGapRoadmap } from "@/components/copilot/skill-gap-roadmap";
import { StudentNav } from "@/components/navigation/student-nav";

export const metadata: Metadata = {
  title: "Personalized Skill-Gap Roadmap | CareerPilot AI",
  description:
    "Explore your personalized skill-gap roadmap, comparing your profile and resume with real job market requirements.",
};

export default function RoadmapPage() {
  return (
    <div className="flex min-h-screen flex-col bg-[#F6FAF7]">
      <StudentNav />
      <main className="flex-1 p-4 sm:p-8">
        <div className="mx-auto w-full max-w-6xl space-y-6">
          {/* Header navigation */}
          <div className="flex items-center gap-4">
            <Link href="/dashboard" aria-label="Back to Dashboard">
              <Button variant="ghost" size="icon" className="rounded-full hover:bg-black/5">
                <ArrowLeft className="h-5 w-5 text-[#14261C]" />
              </Button>
            </Link>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-[#E5EDE7] text-[#1B5E3B]">
                  Career Copilot • Smart Roadmap
                </span>
              </div>
              <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-[#14261C] mt-1 flex items-center gap-2.5">
                <Compass className="w-7 h-7 text-[#1B5E3B]" />
                Skill-Gap Roadmap
              </h1>
              <p className="text-sm text-[#5A7362] mt-1">
                Evidence-based skill gaps, employer demand prioritization, and structured learning sequence tailored to your target role.
              </p>
            </div>
          </div>

          {/* Roadmap interactive component */}
          <Suspense
            fallback={
              <div className="flex h-48 items-center justify-center text-sm text-[#5A7362]">
                Loading Skill-Gap Roadmap...
              </div>
            }
          >
            <SkillGapRoadmap />
          </Suspense>
        </div>
      </main>
    </div>
  );
}
