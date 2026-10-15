import { Suspense } from "react";
import { Metadata } from "next";
import Link from "next/link";
import { ArrowLeft, BookOpen } from "lucide-react";

import { Button } from "@/components/ui/button";
import { InterviewPrep } from "@/components/copilot/interview-prep";
import { StudentNav } from "@/components/navigation/student-nav";

export const metadata: Metadata = {
  title: "Interview Preparation Practice | CareerPilot AI",
  description:
    "Practice technical and behavioural interview questions with instant rubric evaluation and tailored coaching feedback.",
};

export default function InterviewPrepPage() {
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
                  Career Copilot • Practice Lab
                </span>
              </div>
              <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-[#14261C] mt-1 flex items-center gap-2.5">
                <BookOpen className="w-7 h-7 text-[#1B5E3B]" />
                Interview Preparation Practice
              </h1>
              <p className="text-sm text-[#5A7362] mt-1">
                Practice interview questions selected from our question bank. Evaluate your answers with instant rubric feedback or request comprehensive AI coaching on demand.
              </p>
            </div>
          </div>

          {/* Interactive interview preparation component */}
          <Suspense
            fallback={
              <div className="flex h-48 items-center justify-center text-sm text-[#5A7362]">
                Loading Interview Preparation...
              </div>
            }
          >
            <InterviewPrep />
          </Suspense>
        </div>
      </main>
    </div>
  );
}
