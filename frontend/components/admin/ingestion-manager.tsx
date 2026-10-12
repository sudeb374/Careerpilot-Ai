"use client";

import { useState } from "react";
import Link from "next/link";
import { createClient } from "@/lib/supabase/client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Search,
  Loader2,
  AlertTriangle,
  CheckCircle,
  ExternalLink,
  ShieldAlert,
  Building2,
  MapPin,
  Calendar,
  DollarSign,
  Briefcase,
  Info,
  CheckSquare,
  Square,
  ChevronDown,
  ChevronUp,
  ArrowRight,
  Database,
  Sparkles,
} from "lucide-react";

export interface MatchedSkill {
  id: string;
  name: string;
}

export interface JobPreview {
  job_id: string;
  title: string;
  company_name: string;
  company_website?: string | null;
  company_logo_url?: string | null;
  description?: string | null;
  opportunity_type: string;
  work_model: string;
  locations?: string[] | null;
  application_url?: string | null;
  publisher?: string | null;
  posted_at?: string | null;
  deadline?: string | null;
  salary_min?: number | null;
  salary_max?: number | null;
  stipend_min?: number | null;
  stipend_max?: number | null;
  currency?: string | null;
  matched_skills: MatchedSkill[];
  unmapped_skills: string[];
  is_duplicate: boolean;
  review_required: boolean;
  warnings: string[];
  errors: string[];
  classification_conflict: boolean;
  raw_employment_types: string[];
}

export interface PreviewSummary {
  total_returned: number;
  valid_count: number;
  duplicate_count: number;
  review_required_count: number;
}

export interface ImportDetail {
  job_id: string;
  title: string;
  status: string;
  reason?: string | null;
  opportunity_id?: string | null;
}

export interface ImportResponse {
  inserted_count: number;
  skipped_count: number;
  duplicate_count: number;
  review_required_count: number;
  details: ImportDetail[];
}

const POPULAR_SEARCHES = [
  "Software Engineer Intern",
  "Frontend Developer Intern",
  "Backend Python Intern",
  "Data Science Intern",
  "Full Stack Developer",
];

export function IngestionManager() {
  const [query, setQuery] = useState("Software Engineer Intern");
  const [country, setCountry] = useState("in");
  const [datePosted, setDatePosted] = useState("all");
  const [remoteOnly, setRemoteOnly] = useState(false);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [errorType, setErrorType] = useState<"config" | "rate_limit" | "import" | "generic" | null>(null);

  const [jobs, setJobs] = useState<JobPreview[]>([]);
  const [summary, setSummary] = useState<PreviewSummary | null>(null);
  const [selectedJobIds, setSelectedJobIds] = useState<Set<string>>(new Set());

  // Expandable description states
  const [expandedJobIds, setExpandedJobIds] = useState<Set<string>>(new Set());

  // Confirmation dialog state
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [importing, setImporting] = useState(false);
  const [importResult, setImportResult] = useState<ImportResponse | null>(null);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const handlePreview = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
    setErrorType(null);
    setImportResult(null);

    try {
      const supabase = createClient();
      const { data: { session } } = await supabase.auth.getSession();

      if (!session) {
        throw new Error("You must be logged in as an administrator to preview job ingestion.");
      }

      const res = await fetch(`${API_URL}/api/v1/admin/ingestion/jsearch/preview`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({
          query: query.trim(),
          country: country.trim().toLowerCase(),
          date_posted: datePosted,
          remote_jobs_only: remoteOnly,
          page: 1,
          num_pages: 1,
        }),
      });

      if (!res.ok) {
        const errJson = await res.json().catch(() => null);
        const detail = errJson?.detail || `API request failed with status ${res.status}`;

        if (res.status === 400 && detail.includes("JSEARCH_API_KEY")) {
          setErrorType("config");
        } else if (res.status === 429) {
          setErrorType("rate_limit");
        } else {
          setErrorType("generic");
        }
        throw new Error(detail);
      }

      const data = await res.json();
      setJobs(data.jobs || []);
      setSummary(data.summary || null);

      // Auto-select importable (non-duplicate, non-error) jobs
      const autoSelected = new Set<string>();
      (data.jobs || []).forEach((j: JobPreview) => {
        if (!j.is_duplicate && (!j.errors || j.errors.length === 0)) {
          autoSelected.add(j.job_id);
        }
      });
      setSelectedJobIds(autoSelected);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to preview job listings.");
    } finally {
      setLoading(false);
    }
  };

  const toggleSelectJob = (jobId: string) => {
    const next = new Set(selectedJobIds);
    if (next.has(jobId)) {
      next.delete(jobId);
    } else {
      next.add(jobId);
    }
    setSelectedJobIds(next);
  };

  const selectAllImportable = () => {
    const next = new Set<string>();
    jobs.forEach((j) => {
      if (!j.is_duplicate && (!j.errors || j.errors.length === 0)) {
        next.add(j.job_id);
      }
    });
    setSelectedJobIds(next);
  };

  const deselectAll = () => {
    setSelectedJobIds(new Set());
  };

  const toggleExpandDescription = (jobId: string) => {
    const next = new Set(expandedJobIds);
    if (next.has(jobId)) {
      next.delete(jobId);
    } else {
      next.add(jobId);
    }
    setExpandedJobIds(next);
  };

  const handleExecuteImport = async () => {
    if (selectedJobIds.size === 0) return;

    setImporting(true);
    setError(null);
    setErrorType(null);

    try {
      const supabase = createClient();
      const { data: { session } } = await supabase.auth.getSession();

      if (!session) {
        setErrorType("import");
        throw new Error("You must be logged in as an administrator.");
      }

      const selectedJobsList = jobs.filter((j) => selectedJobIds.has(j.job_id));

      let res: Response;
      try {
        res = await fetch(`${API_URL}/api/v1/admin/ingestion/jsearch/import`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${session.access_token}`,
          },
          body: JSON.stringify({
            selected_job_ids: Array.from(selectedJobIds),
            jobs: selectedJobsList,
          }),
        });
      } catch (networkErr: unknown) {
        setErrorType("import");
        const msg = networkErr instanceof Error && networkErr.message === "Failed to fetch"
          ? "Unable to connect to the backend server (Failed to fetch). Please verify that the backend API is online and CORS is permitted."
          : networkErr instanceof Error ? networkErr.message : "Network error during import request.";
        throw new Error(msg);
      }

      if (!res.ok) {
        setErrorType("import");
        const errJson = await res.json().catch(() => null);
        throw new Error(errJson?.detail || `Import failed with HTTP status ${res.status}.`);
      }

      const result: ImportResponse = await res.json();
      setImportResult(result);
      setConfirmOpen(false);

      // Mark imported jobs as duplicates in the preview list
      const importedIds = new Set(
        result.details.filter((d) => d.status === "imported").map((d) => d.job_id)
      );

      setJobs((prevJobs) =>
        prevJobs.map((j) => {
          if (importedIds.has(j.job_id)) {
            return {
              ...j,
              is_duplicate: true,
              warnings: [...j.warnings, "Successfully imported into CareerPilot catalog (Draft)."],
            };
          }
          return j;
        })
      );

      // Clear selection
      setSelectedJobIds(new Set());
    } catch (err) {
      setErrorType("import");
      setError(err instanceof Error ? err.message : "Job import failed.");
      setConfirmOpen(false);
    } finally {
      setImporting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* 1. Free-Tier Allowance & Provider Notice */}
      <div className="rounded-xl border border-border/80 bg-card p-4 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-start gap-3">
          <div className="p-2 rounded-lg bg-primary/10 text-primary mt-0.5">
            <Sparkles className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-semibold text-foreground text-sm">RapidAPI JSearch Integration</span>
              <Badge variant="outline" className="text-xs font-medium">Free Tier Guard</Badge>
            </div>
            <p className="text-xs text-muted-foreground mt-1 max-w-2xl">
              Basic plan allowance is 200 requests/month. Each search preview requests 1 bounded page. Multi-page auto-fetching is disabled to preserve quota.
              Imported opportunities are strictly saved as <strong>Draft</strong> for administrator review and attribution retention.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2 text-xs text-muted-foreground shrink-0">
          <Info className="h-4 w-4" />
          <span>Default: 1 result page</span>
        </div>
      </div>

      {/* 2. Search & Filter Controls */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-lg">Search Job Discovery</CardTitle>
          <CardDescription>
            Specify role title, skills, or target keywords to fetch real-time listings.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handlePreview} className="space-y-4">
            <div className="flex flex-col md:flex-row gap-3">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="e.g. Software Engineer Intern, Python Developer..."
                  className="pl-9"
                  disabled={loading}
                />
              </div>

              <div className="w-full md:w-44">
                <Select value={country} onValueChange={(val) => val && setCountry(val)} disabled={loading}>
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Country" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="in">India (IN)</SelectItem>
                    <SelectItem value="us">United States (US)</SelectItem>
                    <SelectItem value="gb">United Kingdom (GB)</SelectItem>
                    <SelectItem value="ca">Canada (CA)</SelectItem>
                    <SelectItem value="de">Germany (DE)</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="w-full md:w-44">
                <Select value={datePosted} onValueChange={(val) => val && setDatePosted(val)} disabled={loading}>
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Posting Time" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Dates</SelectItem>
                    <SelectItem value="today">Past 24 Hours</SelectItem>
                    <SelectItem value="3days">Past 3 Days</SelectItem>
                    <SelectItem value="week">Past Week</SelectItem>
                    <SelectItem value="month">Past Month</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <Button type="submit" disabled={loading || !query.trim()} className="md:w-36">
                {loading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Searching...
                  </>
                ) : (
                  <>
                    <Search className="mr-2 h-4 w-4" />
                    Preview Jobs
                  </>
                )}
              </Button>
            </div>

            {/* Quick search tags and remote toggle */}
            <div className="flex flex-wrap items-center justify-between gap-3 pt-1 text-xs">
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-muted-foreground">Quick queries:</span>
                {POPULAR_SEARCHES.map((term) => (
                  <button
                    key={term}
                    type="button"
                    onClick={() => {
                      setQuery(term);
                    }}
                    className="px-2.5 py-1 rounded-md bg-muted hover:bg-muted/80 text-foreground transition-colors"
                  >
                    {term}
                  </button>
                ))}
              </div>

              <label className="flex items-center gap-2 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={remoteOnly}
                  onChange={(e) => setRemoteOnly(e.target.checked)}
                  disabled={loading}
                  className="rounded border-input text-primary focus:ring-primary"
                />
                <span className="text-foreground font-medium">Remote only</span>
              </label>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* 3. Error Alerts */}
      {error && (
        <div
          className={`p-4 rounded-xl border flex items-start gap-3 ${
            errorType === "config"
              ? "bg-amber-500/10 border-amber-500/30 text-amber-600 dark:text-amber-400"
              : errorType === "rate_limit"
              ? "bg-purple-500/10 border-purple-500/30 text-purple-600 dark:text-purple-400"
              : "bg-destructive/10 border-destructive/30 text-destructive"
          }`}
        >
          {errorType === "config" ? (
            <ShieldAlert className="h-5 w-5 shrink-0 mt-0.5" />
          ) : (
            <AlertTriangle className="h-5 w-5 shrink-0 mt-0.5" />
          )}
          <div className="space-y-1 text-sm">
            <h4 className="font-semibold">
              {errorType === "config"
                ? "Provider Configuration Required"
                : errorType === "rate_limit"
                ? "Rate Limit or Allowance Exceeded"
                : errorType === "import"
                ? "Job Import Failed"
                : "Ingestion Query Error"}
            </h4>
            <p className="leading-relaxed">{error}</p>
            {errorType === "config" && (
              <p className="text-xs text-muted-foreground mt-2">
                Tip: Add <code>JSEARCH_API_KEY=&lt;your_key&gt;</code> to your <code>backend/.env</code> file and restart the backend server.
              </p>
            )}
          </div>
        </div>
      )}

      {/* 4. Import Result Banner */}
      {importResult && (
        <div className="p-5 rounded-xl border border-emerald-500/30 bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 font-semibold">
              <CheckCircle className="h-5 w-5" />
              <span>Import Completed Successfully!</span>
            </div>
            <Link href="/admin/opportunities">
              <Button size="sm" variant="outline" className="border-emerald-500/40 text-emerald-700 dark:text-emerald-300">
                View in Opportunities Manager
                <ArrowRight className="ml-1.5 h-3.5 w-3.5" />
              </Button>
            </Link>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
            <div className="bg-background/60 p-2.5 rounded-lg border border-border/50">
              <span className="text-muted-foreground block">Inserted (Draft):</span>
              <span className="text-lg font-bold text-foreground">{importResult.inserted_count}</span>
            </div>
            <div className="bg-background/60 p-2.5 rounded-lg border border-border/50">
              <span className="text-muted-foreground block">Duplicates Skipped:</span>
              <span className="text-lg font-bold text-foreground">{importResult.duplicate_count}</span>
            </div>
            <div className="bg-background/60 p-2.5 rounded-lg border border-border/50">
              <span className="text-muted-foreground block">Validation Skipped:</span>
              <span className="text-lg font-bold text-foreground">{importResult.skipped_count}</span>
            </div>
            <div className="bg-background/60 p-2.5 rounded-lg border border-border/50">
              <span className="text-muted-foreground block">Review Flagged:</span>
              <span className="text-lg font-bold text-foreground">{importResult.review_required_count}</span>
            </div>
          </div>
        </div>
      )}

      {/* 5. Summary & Action Bar */}
      {summary && jobs.length > 0 && (
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-4 rounded-xl bg-card border border-border shadow-sm">
          <div className="flex flex-wrap items-center gap-4 text-xs">
            <div>
              <span className="text-muted-foreground">Results: </span>
              <span className="font-semibold text-foreground">{summary.total_returned}</span>
            </div>
            <div>
              <span className="text-muted-foreground">Ready to Import: </span>
              <span className="font-semibold text-emerald-600 dark:text-emerald-400">{summary.valid_count}</span>
            </div>
            <div>
              <span className="text-muted-foreground">Needs Review: </span>
              <span className="font-semibold text-amber-600 dark:text-amber-400">{summary.review_required_count}</span>
            </div>
            <div>
              <span className="text-muted-foreground">Already in DB: </span>
              <span className="font-semibold text-muted-foreground">{summary.duplicate_count}</span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={selectedJobIds.size === summary.valid_count ? deselectAll : selectAllImportable}
            >
              {selectedJobIds.size === summary.valid_count ? (
                <>
                  <Square className="mr-1.5 h-3.5 w-3.5" />
                  Deselect All
                </>
              ) : (
                <>
                  <CheckSquare className="mr-1.5 h-3.5 w-3.5" />
                  Select All Importable
                </>
              )}
            </Button>

            <Button
              type="button"
              disabled={selectedJobIds.size === 0 || importing}
              onClick={() => setConfirmOpen(true)}
              size="sm"
            >
              <Database className="mr-1.5 h-4 w-4" />
              Import Selected ({selectedJobIds.size})
            </Button>
          </div>
        </div>
      )}

      {/* 6. Jobs List Cards */}
      {loading ? (
        <div className="py-16 text-center space-y-3">
          <Loader2 className="h-8 w-8 animate-spin mx-auto text-primary" />
          <p className="text-sm font-medium text-foreground">Querying RapidAPI JSearch...</p>
          <p className="text-xs text-muted-foreground">
            Retrieving real-time listings, matching canonical skills, and checking duplicate records.
          </p>
        </div>
      ) : jobs.length > 0 ? (
        <div className="space-y-4">
          {jobs.map((job) => {
            const isSelected = selectedJobIds.has(job.job_id);
            const isExpanded = expandedJobIds.has(job.job_id);
            const isImportable = !job.is_duplicate && (!job.errors || job.errors.length === 0);

            return (
              <div
                key={job.job_id}
                className={`rounded-xl border transition-all p-5 ${
                  job.is_duplicate
                    ? "bg-muted/40 border-border opacity-75"
                    : isSelected
                    ? "bg-card border-primary ring-1 ring-primary/20 shadow-sm"
                    : "bg-card border-border hover:border-border/80"
                }`}
              >
                <div className="flex items-start gap-4">
                  {/* Selection Checkbox */}
                  <div className="pt-1">
                    <input
                      type="checkbox"
                      checked={isSelected}
                      disabled={!isImportable}
                      onChange={() => toggleSelectJob(job.job_id)}
                      className="h-4 w-4 rounded border-input text-primary focus:ring-primary disabled:opacity-40 cursor-pointer"
                    />
                  </div>

                  {/* Main Job Info */}
                  <div className="flex-1 space-y-3">
                    <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-2">
                      <div>
                        <div className="flex flex-wrap items-center gap-2">
                          <h3 className="text-base font-semibold text-foreground tracking-tight">
                            {job.title}
                          </h3>

                          {/* Duplicate badge */}
                          {job.is_duplicate && (
                            <Badge variant="secondary" className="text-xs bg-muted text-muted-foreground">
                              Already in Catalog
                            </Badge>
                          )}

                          {/* Classification Conflict Alert Badge */}
                          {job.classification_conflict && (
                            <Badge variant="destructive" className="bg-amber-500/15 text-amber-700 dark:text-amber-400 border-amber-500/30 gap-1">
                              <AlertTriangle className="h-3 w-3" />
                              Conflict: Title says Intern, reported Full-Time
                            </Badge>
                          )}

                          {/* Opportunity Type */}
                          <Badge variant={job.opportunity_type === "Internship" ? "default" : "secondary"}>
                            {job.opportunity_type}
                          </Badge>

                          {/* Work Model */}
                          <Badge variant="outline">
                            {job.work_model}
                          </Badge>
                        </div>

                        {/* Employer & Metadata */}
                        <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-muted-foreground mt-1">
                          <span className="flex items-center gap-1 font-medium text-foreground">
                            <Building2 className="h-3.5 w-3.5 text-muted-foreground" />
                            {job.company_name}
                          </span>

                          {job.locations && job.locations.length > 0 && (
                            <span className="flex items-center gap-1">
                              <MapPin className="h-3.5 w-3.5" />
                              {job.locations.join("; ")}
                            </span>
                          )}

                          {job.publisher && (
                            <span className="flex items-center gap-1">
                              <Briefcase className="h-3.5 w-3.5" />
                              Via {job.publisher}
                            </span>
                          )}

                          {job.posted_at && (
                            <span className="flex items-center gap-1">
                              <Calendar className="h-3.5 w-3.5" />
                              Posted {new Date(job.posted_at).toLocaleDateString()}
                            </span>
                          )}
                        </div>
                      </div>

                      {/* Direct Apply Link */}
                      {job.application_url && (
                        <a
                          href={job.application_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 text-xs text-primary hover:underline shrink-0"
                        >
                          <span>Apply URL</span>
                          <ExternalLink className="h-3 w-3" />
                        </a>
                      )}
                    </div>

                    {/* Salary / Stipend */}
                    {(job.stipend_min !== null && job.stipend_min !== undefined) ||
                    (job.salary_min !== null && job.salary_min !== undefined) ? (
                      <div className="flex items-center gap-1.5 text-xs text-foreground font-medium">
                        <DollarSign className="h-3.5 w-3.5 text-muted-foreground" />
                        {job.opportunity_type === "Internship" && job.stipend_min !== null ? (
                          <span>
                            Stipend: {job.currency || "INR"} {job.stipend_min?.toLocaleString()}
                            {job.stipend_max ? ` - ${job.stipend_max?.toLocaleString()}` : ""} / month
                          </span>
                        ) : job.salary_min !== null ? (
                          <span>
                            Salary: {job.currency || "INR"} {job.salary_min?.toLocaleString()}
                            {job.salary_max ? ` - ${job.salary_max?.toLocaleString()}` : ""} / year
                          </span>
                        ) : null}
                      </div>
                    ) : null}

                    {/* Skill Badges */}
                    <div className="space-y-1.5">
                      {job.matched_skills.length > 0 && (
                        <div className="flex flex-wrap items-center gap-1.5 text-xs">
                          <span className="text-muted-foreground text-[11px]">Matched Skills:</span>
                          {job.matched_skills.map((skill) => (
                            <span
                              key={skill.id}
                              className="px-2 py-0.5 rounded-full bg-primary/10 text-primary text-[11px] font-medium"
                            >
                              {skill.name}
                            </span>
                          ))}
                        </div>
                      )}

                      {job.unmapped_skills.length > 0 && (
                        <div className="flex flex-wrap items-center gap-1.5 text-xs">
                          <span className="text-muted-foreground text-[11px]">Unmapped Suggestions:</span>
                          {job.unmapped_skills.map((s) => (
                            <span
                              key={s}
                              className="px-2 py-0.5 rounded-full bg-muted text-muted-foreground text-[11px]"
                            >
                              {s}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Warnings and Review Notes */}
                    {job.warnings.length > 0 && (
                      <div className="rounded-lg bg-amber-500/10 border border-amber-500/20 p-2.5 text-xs text-amber-700 dark:text-amber-400 space-y-1">
                        <span className="font-semibold block flex items-center gap-1">
                          <AlertTriangle className="h-3.5 w-3.5" />
                          Review Flags:
                        </span>
                        <ul className="list-disc list-inside space-y-0.5 pl-1">
                          {job.warnings.map((w, i) => (
                            <li key={i}>{w}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Description Toggle */}
                    {job.description && (
                      <div>
                        <button
                          type="button"
                          onClick={() => toggleExpandDescription(job.job_id)}
                          className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground font-medium"
                        >
                          {isExpanded ? (
                            <>
                              <ChevronUp className="h-3.5 w-3.5" />
                              Hide Description
                            </>
                          ) : (
                            <>
                              <ChevronDown className="h-3.5 w-3.5" />
                              Show Full Description
                            </>
                          )}
                        </button>
                        {isExpanded && (
                          <div className="mt-2 text-xs text-muted-foreground whitespace-pre-line bg-muted/30 p-3 rounded-lg border max-h-60 overflow-y-auto">
                            {job.description}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      ) : summary ? (
        <div className="py-16 text-center space-y-2 border rounded-xl bg-card">
          <p className="text-base font-semibold text-foreground">No listings found</p>
          <p className="text-xs text-muted-foreground max-w-sm mx-auto">
            Try adjusting your search keywords, broadening the date timeframe, or selecting another country.
          </p>
        </div>
      ) : null}

      {/* 7. Confirmation Modal Dialog */}
      <Dialog open={confirmOpen} onOpenChange={setConfirmOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Confirm Job Ingestion</DialogTitle>
            <DialogDescription className="pt-1 text-sm text-muted-foreground">
              You are about to import <strong>{selectedJobIds.size}</strong> selected {selectedJobIds.size === 1 ? "opportunity" : "opportunities"} into the CareerPilot catalog.
            </DialogDescription>
          </DialogHeader>

          <div className="rounded-lg bg-primary/10 border border-primary/20 p-3 text-xs text-foreground space-y-1.5 mt-2">
            <p className="font-semibold text-primary">Safety & Review Guarantee:</p>
            <ul className="list-disc list-inside space-y-1 text-muted-foreground">
              <li>Listings will be imported with status <strong>Draft</strong>.</li>
              <li>No listings will be published automatically to students.</li>
              <li>Only verified canonical skills are linked.</li>
              <li>You can review, edit details, and publish in Opportunities Manager.</li>
            </ul>
          </div>
          <DialogFooter className="mt-4">
            <Button
              type="button"
              variant="outline"
              onClick={() => setConfirmOpen(false)}
              disabled={importing}
            >
              Cancel
            </Button>
            <Button
              type="button"
              onClick={handleExecuteImport}
              disabled={importing}
            >
              {importing ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Importing to Draft...
                </>
              ) : (
                `Confirm Import (${selectedJobIds.size})`
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
