import { Suspense } from "react";
import { Metadata } from "next";
import Link from "next/link";
import { ArrowLeft, FileCheck } from "lucide-react";

import { Button } from "@/components/ui/button";
import { JobResumeRecommendations } from "@/components/copilot/job-resume-recommendations";

export const metadata: Metadata = {
  title: "Job-Specific Resume Recommendations | CareerPilot AI",
  description:
    "Tailor your active resume for a selected published job with evidence-grounded recommendations, bullet rewrites, and requirement gap insights.",
};

export default function ResumeRecommendationsPage() {
  return (
    <div className="flex min-h-screen flex-col bg-[#F6FAF7] p-4 sm:p-8">
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
                Career Copilot • Phase 7.5
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-[#14261C] mt-1 flex items-center gap-2.5">
              <FileCheck className="w-7 h-7 text-[#1B5E3B]" />
              Job-Specific Resume Recommendations
            </h1>
            <p className="text-sm text-[#5A7362] mt-1">
              Analyze your active resume against a target job to uncover strengths, identify requirement gaps, and upgrade bullet points with grounded evidence.
            </p>
          </div>
        </div>

        {/* Interactive recommendations component */}
        <Suspense
          fallback={
            <div className="flex h-48 items-center justify-center text-sm text-[#5A7362]">
              Loading Resume Recommendations...
            </div>
          }
        >
          <JobResumeRecommendations />
        </Suspense>
      </div>
    </div>
  );
}
