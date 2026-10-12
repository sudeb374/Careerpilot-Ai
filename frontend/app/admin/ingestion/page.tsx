import { Metadata } from "next";
import { IngestionManager } from "@/components/admin/ingestion-manager";

export const metadata: Metadata = {
  title: "Admin | Job Ingestion | CareerPilot AI",
  description: "Preview and import external job opportunities from JSearch",
};

export default function AdminIngestionPage() {
  return (
    <div className="p-6 h-full max-w-7xl mx-auto">
      <div className="mb-6">
        <h1 className="text-3xl font-bold tracking-tight text-foreground">
          Job Ingestion & Discovery
        </h1>
        <p className="text-muted-foreground mt-2">
          Discover external internships and entry-level positions from RapidAPI JSearch, preview and validate data, and import listings as Draft opportunities.
        </p>
      </div>

      <IngestionManager />
    </div>
  );
}
