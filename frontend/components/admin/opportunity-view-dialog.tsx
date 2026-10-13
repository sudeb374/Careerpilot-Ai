"use client";

import { useState, useEffect } from "react";
import { createClient } from "@/lib/supabase/client";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { Loader2, ExternalLink, AlertTriangle } from "lucide-react";

interface OpportunityViewDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  opportunityId: string;
}

export function OpportunityViewDialog({ open, onOpenChange, opportunityId }: OpportunityViewDialogProps) {
  const [opportunity, setOpportunity] = useState<Record<string, any> | null>(null); // eslint-disable-line @typescript-eslint/no-explicit-any
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchOpportunity = async () => {
      if (!open || !opportunityId) return;
      
      setLoading(true);
      setError(null);
      
      try {
        const supabase = createClient();
        const { data: { session } } = await supabase.auth.getSession();
        
        if (!session) throw new Error("Not authenticated");

        const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        const res = await fetch(`${API_URL}/api/v1/admin/opportunities/${opportunityId}`, {
          headers: {
            "Authorization": `Bearer ${session.access_token}`
          }
        });

        if (!res.ok) {
          throw new Error("Failed to fetch opportunity details");
        }

        const data = await res.json();
        setOpportunity(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "An error occurred");
      } finally {
        setLoading(false);
      }
    };

    fetchOpportunity();
  }, [open, opportunityId]);

  const isValidExternalUrl = (url: string | null | undefined): boolean => {
    if (!url || typeof url !== "string") return false;
    const trimmed = url.trim();
    return trimmed.startsWith("http://") || trimmed.startsWith("https://");
  };

  const formatCurrency = (val: number | null, currency: string | null) => {
    if (val === null || val === undefined) return null;
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: currency || 'USD', maximumFractionDigits: 0 }).format(val);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "Published": return "bg-green-100 text-green-800";
      case "Draft": return "bg-gray-100 text-gray-800";
      case "Closed": return "bg-blue-100 text-blue-800";
      case "Expired": return "bg-red-100 text-red-800";
      default: return "bg-gray-100 text-gray-800";
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex justify-between items-start pr-6">
            <div>
              <DialogTitle className="text-2xl font-bold">{opportunity?.title}</DialogTitle>
              <DialogDescription className="text-lg mt-1 flex items-center gap-2">
                {opportunity?.company_logo_url && (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={opportunity?.company_logo_url} alt="" className="w-6 h-6 object-contain rounded" />
                )}
                {opportunity?.company_name}
              </DialogDescription>
            </div>
            {opportunity && (
              <Badge className={getStatusColor(opportunity.status)}>
                {opportunity.status}
              </Badge>
            )}
          </div>
        </DialogHeader>

        {loading ? (
          <div className="py-12 flex justify-center text-muted-foreground">
            <Loader2 className="h-8 w-8 animate-spin" />
          </div>
        ) : error ? (
          <div className="bg-destructive/15 text-destructive p-4 rounded-md text-sm">
            {error}
          </div>
        ) : opportunity ? (
          <div className="space-y-6 mt-4">
            
            {(() => {
              const warnings = [];
              if (opportunity.eligibility && (opportunity.eligibility.toLowerCase().includes("classification conflict") || opportunity.eligibility.toLowerCase().includes("employment-type conflict"))) {
                warnings.push("Employment-type conflict flagged: title indicates Intern but provider reported Full-Time. Review required.");
              }
              if (!opportunity.application_url) warnings.push("Missing application URL");
              if (!opportunity.description) warnings.push("Missing description");
              if (!opportunity.skills || opportunity.skills.length === 0) warnings.push("Missing required skills");
              if (!opportunity.deadline) warnings.push("Missing deadline");
              if (!opportunity.company_website && !opportunity.company_logo_url) warnings.push("Incomplete company information");

              if (warnings.length > 0) {
                return (
                  <div className="bg-amber-50 border border-amber-200 rounded-md p-3 dark:bg-amber-900/20 dark:border-amber-800">
                    <h4 className="text-sm font-semibold text-amber-800 dark:text-amber-500 mb-1 flex items-center gap-1">
                      <AlertTriangle className="h-4 w-4" /> Data Quality Warnings
                    </h4>
                    <ul className="list-disc pl-5 text-sm text-amber-700 dark:text-amber-400">
                      {warnings.map((w, i) => <li key={i}>{w}</li>)}
                    </ul>
                  </div>
                );
              }
              return null;
            })()}

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 bg-muted/30 p-4 rounded-lg">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Type</p>
                <p className="font-medium">{opportunity.opportunity_type}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground">Work Model</p>
                <p className="font-medium">{opportunity.work_model}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground">Domain</p>
                <p className="font-medium">{opportunity.domain || "—"}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground">Deadline</p>
                <p className="font-medium">
                  {opportunity.deadline 
                    ? new Date(opportunity.deadline).toLocaleDateString(undefined, {
                        year: 'numeric',
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit'
                      }) 
                    : "No deadline"}
                </p>
              </div>
            </div>

            {opportunity.locations && opportunity.locations.length > 0 && (
              <div>
                <h4 className="text-sm font-semibold mb-2">Locations</h4>
                <div className="flex flex-wrap gap-2">
                  {opportunity.locations.map((loc: string, i: number) => (
                    <Badge key={i} variant="outline">{loc}</Badge>
                  ))}
                </div>
              </div>
            )}

            {opportunity.skills && opportunity.skills.length > 0 && (
              <div>
                <h4 className="text-sm font-semibold mb-2">Required Skills</h4>
                <div className="flex flex-wrap gap-2">
                  {opportunity.skills.map((skill: Record<string, any>) => ( // eslint-disable-line @typescript-eslint/no-explicit-any
                    <Badge key={skill.id} variant="secondary" className="bg-[#1B5E3B]/10 text-[#1B5E3B] hover:bg-[#1B5E3B]/20">
                      {skill.name}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {opportunity.description && (
              <div>
                <h4 className="text-sm font-semibold mb-2">Description</h4>
                <div className="whitespace-pre-wrap text-sm text-foreground/90">
                  {opportunity.description}
                </div>
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <h4 className="text-sm font-semibold border-b pb-1">Requirements</h4>
                <ul className="space-y-2 text-sm">
                  <li>
                    <span className="text-muted-foreground">Experience: </span>
                    {(opportunity.required_experience_min !== null || opportunity.required_experience_max !== null) ? (
                      <span>
                        {opportunity.required_experience_min ?? 0} - {opportunity.required_experience_max ?? "Any"} years
                      </span>
                    ) : "Not specified"}
                  </li>
                  <li>
                    <span className="text-muted-foreground">Education: </span>
                    <span>{opportunity.education_requirements || "Not specified"}</span>
                  </li>
                  <li>
                    <span className="text-muted-foreground">Eligibility: </span>
                    <span>{opportunity.eligibility || "Not specified"}</span>
                  </li>
                </ul>
              </div>

              <div className="space-y-4">
                <h4 className="text-sm font-semibold border-b pb-1">Compensation</h4>
                <ul className="space-y-2 text-sm">
                  {(opportunity.stipend_min !== null || opportunity.stipend_max !== null) && (
                    <li>
                      <span className="text-muted-foreground">Stipend: </span>
                      <span className="font-medium">
                        {formatCurrency(opportunity.stipend_min, opportunity.currency)} 
                        {opportunity.stipend_max && opportunity.stipend_min !== opportunity.stipend_max ? ` - ${formatCurrency(opportunity.stipend_max, opportunity.currency)}` : ""}
                      </span>
                    </li>
                  )}
                  {(opportunity.salary_min !== null || opportunity.salary_max !== null) && (
                    <li>
                      <span className="text-muted-foreground">Salary: </span>
                      <span className="font-medium">
                        {formatCurrency(opportunity.salary_min, opportunity.currency)} 
                        {opportunity.salary_max && opportunity.salary_min !== opportunity.salary_max ? ` - ${formatCurrency(opportunity.salary_max, opportunity.currency)}` : ""}
                      </span>
                    </li>
                  )}
                  {opportunity.stipend_min === null && opportunity.stipend_max === null && opportunity.salary_min === null && opportunity.salary_max === null && (
                    <li>Not specified</li>
                  )}
                </ul>
              </div>
            </div>

            <div className="space-y-4 pt-4 border-t">
              <h4 className="text-sm font-semibold">Source & Links</h4>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-muted-foreground">Source: </span>
                  {opportunity.source_name} 
                  {opportunity.external_id && <span className="text-muted-foreground text-xs ml-2">(ID: {opportunity.external_id})</span>}
                </div>
                {isValidExternalUrl(opportunity.source_url) && (
                  <div>
                    <a href={opportunity.source_url} target="_blank" rel="noopener noreferrer" className="flex items-center text-blue-600 hover:underline">
                      Original Posting <ExternalLink className="ml-1 h-3 w-3" />
                    </a>
                  </div>
                )}
                {isValidExternalUrl(opportunity.company_website) && (
                  <div>
                    <a href={opportunity.company_website} target="_blank" rel="noopener noreferrer" className="flex items-center text-blue-600 hover:underline">
                      Company Website <ExternalLink className="ml-1 h-3 w-3" />
                    </a>
                  </div>
                )}
                {isValidExternalUrl(opportunity.application_url) && (
                  <div>
                    <a href={opportunity.application_url} target="_blank" rel="noopener noreferrer" className="flex items-center text-blue-600 hover:underline font-semibold">
                      Apply Link <ExternalLink className="ml-1 h-3 w-3" />
                    </a>
                  </div>
                )}
              </div>
            </div>

          </div>
        ) : null}

        <DialogFooter className="mt-6 border-t pt-4">
          <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
            Close
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
