"use client";

import { useState, useEffect, useCallback } from "react";
import { createClient } from "@/lib/supabase/client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Plus, Search, Loader2, Eye, Pencil, Trash2, X } from "lucide-react";
import { OpportunityFormDialog } from "./opportunity-form-dialog";
import { OpportunityDeleteDialog } from "./opportunity-delete-dialog";
import { OpportunityViewDialog } from "./opportunity-view-dialog";

export type OpportunityData = Record<string, any>; // eslint-disable-line @typescript-eslint/no-explicit-any

export function OpportunitiesManager() {
  const [opportunities, setOpportunities] = useState<OpportunityData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Pagination and filtering
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalItems, setTotalItems] = useState(0);
  
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [typeFilter, setTypeFilter] = useState<string>("all");
  const [workModelFilter, setWorkModelFilter] = useState<string>("all");

  // Dialogs state
  const [formOpen, setFormOpen] = useState(false);
  const [selectedOpp, setSelectedOpp] = useState<OpportunityData | null>(null); // For Edit
  
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [oppToDelete, setOppToDelete] = useState<OpportunityData | null>(null);

  const [viewOpen, setViewOpen] = useState(false);
  const [oppToView, setOppToView] = useState<OpportunityData | null>(null);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  // Debounce search
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(search);
      setPage(1); // Reset page on search
    }, 500);
    return () => clearTimeout(timer);
  }, [search]);

  const loadOpportunities = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const supabase = createClient();
      const { data: { session } } = await supabase.auth.getSession();
      
      if (!session) {
        setError("Not authenticated");
        setLoading(false);
        return;
      }

      const params = new URLSearchParams();
      params.append("page", page.toString());
      params.append("page_size", "20");
      
      if (debouncedSearch) params.append("q", debouncedSearch);
      if (statusFilter !== "all") params.append("status", statusFilter);
      if (typeFilter !== "all") params.append("opportunity_type", typeFilter);
      if (workModelFilter !== "all") params.append("work_model", workModelFilter);

      const res = await fetch(`${API_URL}/api/v1/admin/opportunities?${params.toString()}`, {
        headers: {
          "Authorization": `Bearer ${session.access_token}`
        }
      });

      if (!res.ok) {
        throw new Error(`Failed to load opportunities (${res.status})`);
      }

      const data = await res.json();
      setOpportunities(data.items || []);
      setTotalPages(data.total_pages || 1);
      setTotalItems(data.total || 0);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setLoading(false);
    }
  }, [API_URL, page, debouncedSearch, statusFilter, typeFilter, workModelFilter]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadOpportunities();
  }, [loadOpportunities]);

  const handleCreate = () => {
    setSelectedOpp(null);
    setFormOpen(true);
  };

  const handleEdit = (opp: OpportunityData) => {
    setSelectedOpp(opp);
    setFormOpen(true);
  };

  const handleDelete = (opp: OpportunityData) => {
    setOppToDelete(opp);
    setDeleteOpen(true);
  };

  const handleView = (opp: OpportunityData) => {
    setOppToView(opp);
    setViewOpen(true);
  };

  const onFormSuccess = () => {
    setFormOpen(false);
    loadOpportunities();
  };

  const onDeleteSuccess = () => {
    setDeleteOpen(false);
    loadOpportunities();
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "Published": return "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400";
      case "Draft": return "bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300";
      case "Closed": return "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400";
      case "Expired": return "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400";
      default: return "bg-gray-100 text-gray-800";
    }
  };

  return (
    <div className="space-y-4">
      {/* Filters and Actions */}
      <div className="flex flex-col md:flex-row gap-4 items-center justify-between bg-card p-4 rounded-lg border shadow-sm">
        <div className="flex flex-1 flex-wrap items-center gap-3 w-full">
          <div className="relative w-full max-w-xs">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search title, company..."
              className="pl-9"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
            {search && (
              <button 
                onClick={() => setSearch("")}
                className="absolute right-2.5 top-2.5 text-muted-foreground hover:text-foreground"
              >
                <X className="h-4 w-4" />
              </button>
            )}
          </div>
          
          <Select value={statusFilter} onValueChange={(v) => setStatusFilter(v || "all")}>
            <SelectTrigger className="w-[140px]">
              <SelectValue placeholder="Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Statuses</SelectItem>
              <SelectItem value="Draft">Draft</SelectItem>
              <SelectItem value="Published">Published</SelectItem>
              <SelectItem value="Closed">Closed</SelectItem>
              <SelectItem value="Expired">Expired</SelectItem>
            </SelectContent>
          </Select>

          <Select value={typeFilter} onValueChange={(v) => setTypeFilter(v || "all")}>
            <SelectTrigger className="w-[140px]">
              <SelectValue placeholder="Type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Types</SelectItem>
              <SelectItem value="Internship">Internship</SelectItem>
              <SelectItem value="Full-Time">Full-Time</SelectItem>
            </SelectContent>
          </Select>

          <Select value={workModelFilter} onValueChange={(v) => setWorkModelFilter(v || "all")}>
            <SelectTrigger className="w-[140px]">
              <SelectValue placeholder="Work Model" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Models</SelectItem>
              <SelectItem value="Remote">Remote</SelectItem>
              <SelectItem value="Hybrid">Hybrid</SelectItem>
              <SelectItem value="On-site">On-site</SelectItem>
            </SelectContent>
          </Select>
        </div>
        
        <Button onClick={handleCreate} className="w-full md:w-auto shrink-0 bg-[#1B5E3B] hover:bg-[#2E7D4F] text-white">
          <Plus className="mr-2 h-4 w-4" /> Add Opportunity
        </Button>
      </div>

      {error && (
        <div className="bg-destructive/15 text-destructive p-3 rounded-md text-sm">
          {error}
        </div>
      )}

      {/* Table */}
      <div className="bg-card rounded-lg border shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="text-xs text-muted-foreground uppercase bg-muted/50">
              <tr>
                <th className="px-4 py-3 font-medium">Title</th>
                <th className="px-4 py-3 font-medium">Company</th>
                <th className="px-4 py-3 font-medium">Type</th>
                <th className="px-4 py-3 font-medium">Model</th>
                <th className="px-4 py-3 font-medium">Status</th>
                <th className="px-4 py-3 font-medium">Created</th>
                <th className="px-4 py-3 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {loading ? (
                <tr>
                  <td colSpan={7} className="px-4 py-8 text-center text-muted-foreground">
                    <Loader2 className="h-6 w-6 animate-spin mx-auto mb-2" />
                    Loading opportunities...
                  </td>
                </tr>
              ) : opportunities.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-4 py-8 text-center text-muted-foreground">
                    No opportunities found.
                  </td>
                </tr>
              ) : (
                opportunities.map((opp) => (
                  <tr key={opp.id} className="hover:bg-muted/50 transition-colors">
                    <td className="px-4 py-3 font-medium text-foreground">{opp.title}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        {opp.company_logo_url && (
                          // eslint-disable-next-line @next/next/no-img-element
                          <img src={opp.company_logo_url} alt="" className="w-5 h-5 object-contain rounded-sm" />
                        )}
                        {opp.company_name}
                      </div>
                    </td>
                    <td className="px-4 py-3">{opp.opportunity_type}</td>
                    <td className="px-4 py-3">{opp.work_model}</td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(opp.status)}`}>
                        {opp.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-muted-foreground">
                      {new Date(opp.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => handleView(opp)}>
                          <Eye className="h-4 w-4" />
                          <span className="sr-only">View</span>
                        </Button>
                        <Button variant="ghost" size="icon" className="h-8 w-8 text-blue-600 hover:text-blue-700 hover:bg-blue-50" onClick={() => handleEdit(opp)}>
                          <Pencil className="h-4 w-4" />
                          <span className="sr-only">Edit</span>
                        </Button>
                        <Button variant="ghost" size="icon" className="h-8 w-8 text-red-600 hover:text-red-700 hover:bg-red-50" onClick={() => handleDelete(opp)}>
                          <Trash2 className="h-4 w-4" />
                          <span className="sr-only">Delete</span>
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        
        {/* Pagination */}
        {!loading && totalPages > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t bg-muted/20">
            <div className="text-sm text-muted-foreground">
              Showing <span className="font-medium">{(page - 1) * 20 + 1}</span> to{" "}
              <span className="font-medium">{Math.min(page * 20, totalItems)}</span> of{" "}
              <span className="font-medium">{totalItems}</span> results
            </div>
            <div className="flex gap-2">
              <Button 
                variant="outline" 
                size="sm" 
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
              >
                Previous
              </Button>
              <Button 
                variant="outline" 
                size="sm"
                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
              >
                Next
              </Button>
            </div>
          </div>
        )}
      </div>

      {formOpen && (
        <OpportunityFormDialog 
          open={formOpen} 
          onOpenChange={setFormOpen} 
          opportunityToEdit={selectedOpp || undefined}
          onSuccess={onFormSuccess}
        />
      )}

      {deleteOpen && oppToDelete && (
        <OpportunityDeleteDialog
          open={deleteOpen}
          onOpenChange={setDeleteOpen}
          opportunity={oppToDelete}
          onSuccess={onDeleteSuccess}
        />
      )}

      {viewOpen && oppToView && (
        <OpportunityViewDialog
          open={viewOpen}
          onOpenChange={setViewOpen}
          opportunityId={oppToView.id}
        />
      )}
    </div>
  );
}
