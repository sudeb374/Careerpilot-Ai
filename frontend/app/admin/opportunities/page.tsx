import { Metadata } from "next";
import { OpportunitiesManager } from "@/components/admin/opportunities-manager";

export const metadata: Metadata = {
  title: "Admin | Opportunities | CareerPilot AI",
  description: "Manage opportunities",
};

export default function AdminOpportunitiesPage() {
  return (
    <div className="p-6 h-full max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight text-foreground">
          Opportunities
        </h1>
        <p className="text-muted-foreground mt-2">
          Manage, create, and update opportunities available on the platform.
        </p>
      </div>
      
      <OpportunitiesManager />
    </div>
  );
}
