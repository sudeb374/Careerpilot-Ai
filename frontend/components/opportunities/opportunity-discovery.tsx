"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter, usePathname, useSearchParams } from "next/navigation";
import { FolderSearch, SearchX, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { createClient } from "@/lib/supabase/client";
import { OpportunityCard } from "./opportunity-card";
import { OpportunityFilters, FiltersState } from "./opportunity-filters";

export function OpportunityDiscovery() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const supabase = createClient();
  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [opportunities, setOpportunities] = useState<Record<string, any>[]>([]); // eslint-disable-line @typescript-eslint/no-explicit-any
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);

  // Initialize filters from URL
  const [filters, setFilters] = useState<FiltersState>({
    q: searchParams.get("q") || "",
    opportunity_type: searchParams.get("opportunity_type") || "",
    work_model: searchParams.get("work_model") || "",
    location: searchParams.get("location") || "",
    domain: searchParams.get("domain") || "",
    skill_id: searchParams.get("skill_id") || "",
    skill_name: searchParams.get("skill_name") || "",
  });

  const page = parseInt(searchParams.get("page") || "1", 10);
  const pageSize = 10;

  // Sync state to URL and fetch
  const updateUrl = useCallback((newFilters: FiltersState, newPage: number = 1) => {
    const params = new URLSearchParams();
    if (newFilters.q) params.set("q", newFilters.q);
    if (newFilters.opportunity_type) params.set("opportunity_type", newFilters.opportunity_type);
    if (newFilters.work_model) params.set("work_model", newFilters.work_model);
    if (newFilters.location) params.set("location", newFilters.location);
    if (newFilters.domain) params.set("domain", newFilters.domain);
    if (newFilters.skill_id) {
      params.set("skill_id", newFilters.skill_id);
      if (newFilters.skill_name) params.set("skill_name", newFilters.skill_name);
    }
    if (newPage > 1) params.set("page", newPage.toString());

    router.replace(`${pathname}?${params.toString()}`, { scroll: false });
  }, [pathname, router]);

  const loadOpportunities = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const { data: { session } } = await supabase.auth.getSession();
      
      if (!session) {
        router.push("/login");
        return;
      }
      
      const queryParams = new URLSearchParams({
        page: page.toString(),
        page_size: pageSize.toString(),
      });
      
      if (filters.q) queryParams.append("q", filters.q);
      if (filters.opportunity_type) queryParams.append("opportunity_type", filters.opportunity_type);
      if (filters.work_model) queryParams.append("work_model", filters.work_model);
      if (filters.location) queryParams.append("location", filters.location);
      if (filters.domain) queryParams.append("domain", filters.domain);
      if (filters.skill_id) queryParams.append("skill_id", filters.skill_id);

      const response = await fetch(`${API_URL}/api/v1/opportunities?${queryParams.toString()}`, {
        headers: session ? { Authorization: `Bearer ${session.access_token}` } : {},
      });

      if (!response.ok) {
        throw new Error("Failed to fetch opportunities");
      }

      const data = await response.json();
      setOpportunities(data.items || []);
      setTotal(data.total || 0);
      setTotalPages(data.total_pages || 1);
    } catch (err: unknown) {
      console.error(err);
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }, [API_URL, supabase.auth, page, filters, pageSize, router]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadOpportunities();
  }, [loadOpportunities]);

  const handleFilterChange = (newFilterChanges: Partial<FiltersState>) => {
    const newFilters = { ...filters, ...newFilterChanges };
    setFilters(newFilters);
    updateUrl(newFilters, 1);
  };

  const handleClearFilters = () => {
    const emptyFilters = {
      q: "",
      opportunity_type: "",
      work_model: "",
      location: "",
      domain: "",
      skill_id: "",
      skill_name: "",
    };
    setFilters(emptyFilters);
    updateUrl(emptyFilters, 1);
  };

  const hasAnyFilter = Object.values(filters).some(val => val !== "");

  return (
    <div className="space-y-6">
      <OpportunityFilters 
        filters={filters} 
        onFilterChange={handleFilterChange} 
        onClear={handleClearFilters} 
      />

      {error ? (
        <div className="flex flex-col items-center justify-center p-12 bg-white rounded-xl border border-red-100 text-center space-y-4 shadow-sm">
          <div className="w-12 h-12 rounded-full bg-red-100 flex items-center justify-center text-red-600">
            <AlertCircle className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Unable to load opportunities</h3>
            <p className="text-gray-500 mt-1">Please try again.</p>
          </div>
          <Button onClick={loadOpportunities} variant="outline">Retry</Button>
        </div>
      ) : loading ? (
        <div className="space-y-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="flex bg-white rounded-xl shadow-sm border border-gray-100 p-6 gap-6 h-48 animate-pulse">
              <div className="w-16 h-16 bg-gray-200 rounded-md"></div>
              <div className="flex-grow space-y-4">
                <div className="h-6 bg-gray-200 rounded w-1/3"></div>
                <div className="h-4 bg-gray-200 rounded w-1/4"></div>
                <div className="flex gap-2">
                  <div className="h-6 bg-gray-200 rounded w-20"></div>
                  <div className="h-6 bg-gray-200 rounded w-20"></div>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : opportunities.length === 0 ? (
        <div className="flex flex-col items-center justify-center p-16 bg-white rounded-xl border border-gray-100 text-center space-y-4 shadow-sm">
          {hasAnyFilter ? (
            <>
              <div className="w-16 h-16 rounded-full bg-orange-50 flex items-center justify-center text-orange-500 mb-2">
                <SearchX className="w-8 h-8" />
              </div>
              <div>
                <h3 className="text-xl font-bold text-gray-900">No opportunities found</h3>
                <p className="text-gray-500 mt-2">Try changing your search or filters.</p>
              </div>
              <Button onClick={handleClearFilters} className="mt-4 bg-[#1B5E3B] text-white hover:bg-[#2E7D4F]">
                Clear Filters
              </Button>
            </>
          ) : (
            <>
              <div className="w-16 h-16 rounded-full bg-green-50 flex items-center justify-center text-[#1B5E3B] mb-2">
                <FolderSearch className="w-8 h-8" />
              </div>
              <div>
                <h3 className="text-xl font-bold text-gray-900">No opportunities available yet</h3>
                <p className="text-gray-500 mt-2">New opportunities will appear here as they are published.</p>
              </div>
            </>
          )}
        </div>
      ) : (
        <div className="space-y-4">
          <div className="text-sm text-gray-500 mb-2">
            Showing {(page - 1) * pageSize + 1}–{Math.min(page * pageSize, total)} of {total} opportunities
          </div>
          
          <div className="grid grid-cols-1 gap-4">
            {opportunities.map((opp) => (
              <OpportunityCard key={opp.id} opportunity={opp} />
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2 mt-8 py-4">
              <Button 
                variant="outline" 
                onClick={() => updateUrl(filters, page - 1)}
                disabled={page <= 1}
              >
                Previous
              </Button>
              <div className="flex gap-1">
                {Array.from({ length: totalPages }, (_, i) => i + 1).map((p) => {
                  // Simple pagination: show current, first, last, and a few around current
                  if (p === 1 || p === totalPages || (p >= page - 1 && p <= page + 1)) {
                    return (
                      <Button
                        key={p}
                        variant={p === page ? "default" : "outline"}
                        onClick={() => updateUrl(filters, p)}
                        className={p === page ? "bg-[#1B5E3B] text-white hover:bg-[#2E7D4F]" : ""}
                      >
                        {p}
                      </Button>
                    );
                  }
                  if (p === 2 && page > 3) return <span key={p} className="px-2 self-end">...</span>;
                  if (p === totalPages - 1 && page < totalPages - 2) return <span key={p} className="px-2 self-end">...</span>;
                  return null;
                })}
              </div>
              <Button 
                variant="outline" 
                onClick={() => updateUrl(filters, page + 1)}
                disabled={page >= totalPages}
              >
                Next
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
