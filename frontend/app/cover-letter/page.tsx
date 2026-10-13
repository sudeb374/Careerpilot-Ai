import { Suspense } from "react";
import { Metadata } from "next";
import Link from "next/link";
import { ArrowLeft, FileEdit } from "lucide-react";

import { Button } from "@/components/ui/button";
import { CoverLetterGenerator } from "@/components/copilot/cover-letter-generator";

export const metadata: Metadata = {
  title: "Personalized Cover Letter Generator | CareerPilot AI",
  description:
    "Generate tailored, evidence-backed cover letters grounded strictly in your verified profile and active resume.",
};

export default function CoverLetterPage() {
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
                Career Copilot • Phase 7.2
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-[#14261C] mt-1 flex items-center gap-2.5">
              <FileEdit className="w-7 h-7 text-[#1B5E3B]" />
              Personalized Cover Letter Generator
            </h1>
            <p className="text-sm text-[#5A7362] mt-1">
              Tailored drafts aligned with job requirements, grounded strictly in your verified skills, education, and projects.
            </p>
          </div>
        </div>

        {/* Interactive generator component */}
        <Suspense
          fallback={
            <div className="flex h-48 items-center justify-center text-sm text-[#5A7362]">
              Loading Cover Letter Generator...
            </div>
          }
        >
          <CoverLetterGenerator />
        </Suspense>
      </div>
    </div>
  );
}
