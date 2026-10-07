import { Metadata } from "next";
import { OpportunityDetails } from "@/components/opportunities/opportunity-details";

export const metadata: Metadata = {
  title: "Opportunity Details | CareerPilot AI",
  description: "View opportunity details",
};

export default function OpportunityDetailsPage({ params }: { params: { opportunity_id: string } }) {
  return (
    <div className="flex min-h-screen flex-col bg-[#F6FAF7] p-4 sm:p-8">
      <div className="mx-auto w-full max-w-5xl">
        <OpportunityDetails opportunityId={params.opportunity_id} />
      </div>
    </div>
  );
}
