import { Suspense } from "react";
import { Metadata } from "next";
import Link from "next/link";
import { ArrowLeft, Info } from "lucide-react";
import { Button } from "@/components/ui/button";
import { MatchesList } from "@/components/opportunities/matches-list";
import { StudentNav } from "@/components/navigation/student-nav";

export const metadata: Metadata = {
  title: "Your Matches | CareerPilot AI",
  description: "View opportunities matched to your profile",
};

export default function MatchesPage() {
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
            <h1 className="text-3xl font-bold tracking-tight text-[#14261C]">
              Your Matches
            </h1>
            <p className="text-muted-foreground mt-1">
              Opportunities ranked by alignment with your profile, skills, and preferences.
            </p>
          </div>
        </div>

        {/* Disclaimer */}
        <div className="bg-white p-4 rounded-xl border border-gray-100 flex gap-3 text-sm text-gray-500 shadow-sm">
          <Info className="w-5 h-5 shrink-0 text-gray-400" />
          <p>
            Your match score estimates how closely an opportunity aligns with your profile and preferences. It is not a probability of selection or a guarantee of hiring.
          </p>
        </div>

        {/* Matches List Component */}
        <Suspense fallback={<div className="flex h-32 items-center justify-center">Loading...</div>}>
          <MatchesList />
        </Suspense>
      </div>
    </main>
  </div>
);
}
