import { Suspense } from "react";
import { Metadata } from "next";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { OpportunityDiscovery } from "@/components/opportunities/opportunity-discovery";

export const metadata: Metadata = {
  title: "Opportunities | CareerPilot AI",
  description: "Find your next opportunity",
};

export default function OpportunitiesPage() {
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
            <h1 className="text-3xl font-bold tracking-tight text-[#14261C]">
              Find your next opportunity
            </h1>
            <p className="text-muted-foreground mt-1">
              Search internships and jobs that match your goals.
            </p>
          </div>
        </div>

        {/* Discovery Component */}
        <Suspense fallback={<div className="flex h-32 items-center justify-center">Loading...</div>}>
          <OpportunityDiscovery />
        </Suspense>
      </div>
    </div>
  );
}
