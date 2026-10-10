"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter, usePathname, useSearchParams } from "next/navigation";
import { FolderSearch, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { createClient } from "@/lib/supabase/client";
import { OpportunityCard } from "./opportunity-card";
import Link from "next/link";

export function MatchesList() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const supabase = createClient();
  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [matches, setMatches] = useState<Record<string, any>[]>([]); // eslint-disable-line @typescript-eslint/no-explicit-any
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);

  const page = parseInt(searchParams.get("page") || "1", 10);
  const pageSize = 10;

  const updateUrl = useCallback((newPage: number = 1) => {
    const params = new URLSearchParams();
    if (newPage > 1) params.set("page", newPage.toString());
    router.replace(`${pathname}?${params.toString()}`, { scroll: false });
  }, [pathname, router]);

  const loadMatches = useCallback(async () => {
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

      const response = await fetch(`${API_URL}/api/v1/profile/opportunity-matches?${queryParams.toString()}`, {
        headers: { Authorization: `Bearer ${session.access_token}` },
      });

      if (!response.ok) {
        throw new Error("Failed to fetch matches");
      }

      const data = await response.json();
      setMatches(data.items || []);
      setTotal(data.total || 0);
      setTotalPages(data.total_pages || 1);
    } catch (err: unknown) {
      console.error(err);
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }, [API_URL, supabase.auth, page, pageSize, router]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadMatches();
  }, [loadMatches]);

  return (
    <div className="space-y-6">
      {error ? (
        <div className="flex flex-col items-center justify-center p-12 bg-white rounded-xl border border-red-100 text-center space-y-4 shadow-sm">
          <div className="w-12 h-12 rounded-full bg-red-100 flex items-center justify-center text-red-600">
            <AlertCircle className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Unable to load matches</h3>
            <p className="text-gray-500 mt-1">Please try again.</p>
          </div>
          <Button onClick={loadMatches} variant="outline">Retry</Button>
        </div>
      ) : loading ? (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
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
      ) : matches.length === 0 ? (
        <div className="flex flex-col items-center justify-center p-16 bg-white rounded-xl border border-gray-100 text-center space-y-4 shadow-sm">
          <div className="w-16 h-16 rounded-full bg-green-50 flex items-center justify-center text-[#1B5E3B] mb-2">
            <FolderSearch className="w-8 h-8" />
          </div>
          <div>
            <h3 className="text-xl font-bold text-gray-900">No matches found</h3>
            <p className="text-gray-500 mt-2 max-w-md mx-auto">
              We couldn&apos;t find any opportunities matching your current profile. You can improve your recommendations by completing your profile, adding more skills, and setting your career preferences.
            </p>
          </div>
          <Link href="/profile">
            <Button className="mt-4 bg-[#1B5E3B] text-white hover:bg-[#2E7D4F]">
              Update Profile
            </Button>
          </Link>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="text-sm text-gray-500 mb-2">
            Showing {(page - 1) * pageSize + 1}–{Math.min(page * pageSize, total)} of {total} matches
          </div>
          
          <div className="grid grid-cols-1 gap-4">
            {matches.map((item) => (
              <OpportunityCard 
                key={item.opportunity.id} 
                opportunity={item.opportunity} 
                match={item.match} 
              />
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2 mt-8 py-4">
              <Button 
                variant="outline" 
                onClick={() => updateUrl(page - 1)}
                disabled={page <= 1}
              >
                Previous
              </Button>
              <div className="flex gap-1">
                {Array.from({ length: totalPages }, (_, i) => i + 1).map((p) => {
                  if (p === 1 || p === totalPages || (p >= page - 1 && p <= page + 1)) {
                    return (
                      <Button
                        key={p}
                        variant={p === page ? "default" : "outline"}
                        onClick={() => updateUrl(p)}
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
                onClick={() => updateUrl(page + 1)}
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
