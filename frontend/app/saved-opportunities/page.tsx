"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Bookmark, AlertCircle, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { createClient } from "@/lib/supabase/client";
import { OpportunityCard } from "@/components/opportunities/opportunity-card";

export default function SavedOpportunitiesPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const supabase = createClient();
  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [opportunities, setOpportunities] = useState<Record<string, any>[]>([]); // eslint-disable-line @typescript-eslint/no-explicit-any
  const [pagination, setPagination] = useState({
    page: 1,
    pageSize: 20,
    total: 0,
    totalPages: 1
  });

  const currentPage = parseInt(searchParams.get("page") || "1", 10);

  const fetchSavedOpportunities = useCallback(async (page: number) => {
    setLoading(true);
    setError(null);
    try {
      const { data: { session } } = await supabase.auth.getSession();
      
      if (!session) {
        router.push("/auth/login");
        return;
      }

      const response = await fetch(`${API_URL}/api/v1/profile/saved-opportunities?page=${page}&page_size=20`, {
        headers: {
          Authorization: `Bearer ${session.access_token}`
        }
      });

      if (!response.ok) {
        throw new Error("Failed to fetch saved opportunities");
      }

      const data = await response.json();
      
      setOpportunities(data.items || []);
      setPagination({
        page: data.page,
        pageSize: data.page_size,
        total: data.total,
        totalPages: data.total_pages
      });
    } catch (err: any) { // eslint-disable-line @typescript-eslint/no-explicit-any
      console.error("Error fetching saved opportunities:", err);
      setError(err.message || "An unexpected error occurred");
    } finally {
      setLoading(false);
    }
  }, [supabase.auth, API_URL, router]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchSavedOpportunities(currentPage);
  }, [fetchSavedOpportunities, currentPage]);

  const handlePageChange = (newPage: number) => {
    if (newPage < 1 || newPage > pagination.totalPages) return;
    router.push(`/saved-opportunities?page=${newPage}`);
  };

  const handleSavedChange = (saved: boolean, id: string) => {
    if (!saved) {
      setOpportunities(prev => {
        const next = prev.filter(opp => opp.id !== id);
        // If we emptied the page and there's a previous page, navigate back
        if (next.length === 0 && pagination.page > 1) {
          handlePageChange(pagination.page - 1);
        }
        return next;
      });
      setPagination(prev => ({
        ...prev,
        total: Math.max(0, prev.total - 1)
      }));
    }
  };

  return (
    <div className="min-h-screen bg-[#F6FAF7] flex flex-col">
      <main className="flex-grow container max-w-6xl mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-[#14261C] flex items-center gap-2">
            <Bookmark className="w-8 h-8 text-[#1B5E3B] fill-current" />
            Saved Opportunities
          </h1>
          <p className="text-gray-600 mt-2">Opportunities you&apos;ve bookmarked for later.</p>
        </div>

        {error ? (
          <div className="bg-red-50 border border-red-200 text-red-700 p-6 rounded-lg text-center">
            <AlertCircle className="w-12 h-12 mx-auto text-red-400 mb-4" />
            <h3 className="text-lg font-semibold mb-2">Unable to load saved opportunities.</h3>
            <p className="mb-4 text-red-600">{error}</p>
            <Button onClick={() => fetchSavedOpportunities(currentPage)} variant="outline" className="bg-white border-red-200 text-red-700 hover:bg-red-50">
              <RefreshCw className="w-4 h-4 mr-2" />
              Retry
            </Button>
          </div>
        ) : loading ? (
          <div className="space-y-4">
            {[1, 2, 3].map(i => (
              <div key={i} className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 h-40 animate-pulse"></div>
            ))}
          </div>
        ) : opportunities.length === 0 ? (
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-12 text-center flex flex-col items-center justify-center">
            <div className="w-20 h-20 bg-gray-50 rounded-full flex items-center justify-center mb-6">
              <Bookmark className="w-10 h-10 text-gray-400" />
            </div>
            <h3 className="text-xl font-bold text-gray-800 mb-2">No saved opportunities yet</h3>
            <p className="text-gray-500 mb-8 max-w-md mx-auto">
              Save opportunities you are interested in and come back to them later.
            </p>
            <Button onClick={() => router.push("/opportunities")} className="bg-[#1B5E3B] hover:bg-[#2E7D4F] text-white px-8">
              Explore Opportunities
            </Button>
          </div>
        ) : (
          <div className="space-y-4">
            {opportunities.map(opportunity => (
              <OpportunityCard 
                key={opportunity.id} 
                opportunity={opportunity} 
                onSavedChange={(saved) => handleSavedChange(saved, opportunity.id)}
              />
            ))}
            
            {pagination.totalPages > 1 && (
              <div className="mt-8 flex items-center justify-between border-t border-gray-200 bg-white px-4 py-3 sm:px-6 rounded-lg shadow-sm">
                <div className="hidden sm:flex sm:flex-1 sm:items-center sm:justify-between">
                  <div>
                    <p className="text-sm text-gray-700">
                      Showing <span className="font-medium">{((pagination.page - 1) * pagination.pageSize) + 1}</span> to <span className="font-medium">{Math.min(pagination.page * pagination.pageSize, pagination.total)}</span> of <span className="font-medium">{pagination.total}</span> saved opportunities
                    </p>
                  </div>
                  <div>
                    <nav className="isolate inline-flex -space-x-px rounded-md shadow-sm" aria-label="Pagination">
                      <Button
                        variant="outline"
                        onClick={() => handlePageChange(pagination.page - 1)}
                        disabled={pagination.page <= 1}
                        className="rounded-l-md"
                      >
                        Previous
                      </Button>
                      
                      {[...Array(pagination.totalPages)].map((_, i) => (
                        <Button
                          key={i}
                          variant={pagination.page === i + 1 ? "default" : "outline"}
                          onClick={() => handlePageChange(i + 1)}
                          className={pagination.page === i + 1 ? "bg-[#1B5E3B] text-white" : ""}
                        >
                          {i + 1}
                        </Button>
                      ))}

                      <Button
                        variant="outline"
                        onClick={() => handlePageChange(pagination.page + 1)}
                        disabled={pagination.page >= pagination.totalPages}
                        className="rounded-r-md"
                      >
                        Next
                      </Button>
                    </nav>
                  </div>
                </div>
                {/* Mobile pagination */}
                <div className="flex flex-1 justify-between sm:hidden">
                  <Button
                    variant="outline"
                    onClick={() => handlePageChange(pagination.page - 1)}
                    disabled={pagination.page <= 1}
                  >
                    Previous
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => handlePageChange(pagination.page + 1)}
                    disabled={pagination.page >= pagination.totalPages}
                  >
                    Next
                  </Button>
                </div>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
