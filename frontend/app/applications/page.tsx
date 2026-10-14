import { Suspense } from "react";
import { Metadata } from "next";
import Link from "next/link";
import { ArrowLeft, RefreshCw, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ApplicationTracker } from "@/components/applications/application-tracker";

export const metadata: Metadata = {
  title: "Application Tracker | CareerPilot AI",
  description:
    "Track your job applications, status transitions, deadlines, personal reminders, and interview pipeline.",
};

export default function ApplicationsPage() {
  return (
    <div className="flex min-h-screen flex-col bg-[#F6FAF7] p-4 sm:p-8">
      <div className="mx-auto w-full max-w-6xl space-y-6">
        {/* Navigation Breadcrumb / Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link href="/dashboard" aria-label="Back to Dashboard">
              <Button
                variant="ghost"
                size="icon"
                className="rounded-full hover:bg-black/5"
              >
                <ArrowLeft className="h-5 w-5 text-[#14261C]" />
              </Button>
            </Link>
            <nav className="text-sm text-gray-500 font-medium">
              <Link href="/dashboard" className="hover:underline">
                Dashboard
              </Link>
              <span className="mx-2 text-gray-400">/</span>
              <span className="text-[#14261C] font-semibold">
                Application Tracker
              </span>
            </nav>
          </div>

          <div className="hidden sm:flex items-center gap-1.5 text-xs text-gray-500 font-medium bg-white px-3 py-1.5 rounded-full border border-gray-100 shadow-2xs">
            <ShieldCheck className="h-4 w-4 text-[#1B5E3B]" />
            <span>Candidate Data Private & Scoped</span>
          </div>
        </div>

        {/* Application Tracker Client Component */}
        <Suspense
          fallback={
            <div className="flex min-h-[300px] items-center justify-center bg-white rounded-2xl border border-gray-100">
              <RefreshCw className="h-6 w-6 animate-spin text-[#1B5E3B]" />
            </div>
          }
        >
          <ApplicationTracker />
        </Suspense>
      </div>
    </div>
  );
}
