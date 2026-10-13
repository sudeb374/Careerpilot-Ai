"use client";

import { useState, useEffect, useCallback } from "react";
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
  Rss,
  UploadCloud,
  FileText,
  RefreshCw,
  Clock,
  Download,
  HelpCircle,
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

const RSS_PRESETS = [
  {
    id: "weworkremotely-programming",
    name: "We Work Remotely — Programming",
    url: "https://weworkremotely.com/categories/remote-programming-jobs.rss",
    description: "Curated remote developer and software engineering listings.",
  },
  {
    id: "weworkremotely-devops",
    name: "We Work Remotely — DevOps & Sysadmin",
    url: "https://weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss",
    description: "Remote cloud, infrastructure, and systems administration listings.",
  },
  {
    id: "weworkremotely-fullstack",
    name: "We Work Remotely — Full-Stack Programming",
    url: "https://weworkremotely.com/categories/remote-full-stack-programming-jobs.rss",
    description: "Curated full-stack engineering and software development openings.",
  },
  {
    id: "custom",
    name: "Custom RSS / Atom Feed URL...",
    url: "",
    description: "Enter any authorized public RSS 2.0 or Atom job feed URL.",
  },
];

export function IngestionManager() {
  const [activeTab, setActiveTab] = useState<"jsearch" | "rss" | "bulk">("jsearch");

  // JSearch state
  const [query, setQuery] = useState("Software Engineer Intern");
  const [country, setCountry] = useState("in");
  const [datePosted, setDatePosted] = useState("all");
  const [remoteOnly, setRemoteOnly] = useState(false);

  // RSS state
  const [rssPreset, setRssPreset] = useState("weworkremotely-programming");
  const [rssCustomUrl, setRssCustomUrl] = useState("");
  const [rssMaxItems, setRssMaxItems] = useState(20);
  const [rssKeywords, setRssKeywords] = useState("");
  const [feedMeta, setFeedMeta] = useState<{ title?: string | null; link?: string | null; description?: string | null } | null>(null);

  // Bulk Upload state (Phase 6.4)
  const [bulkFile, setBulkFile] = useState<File | null>(null);
  const [bulkMeta, setBulkMeta] = useState<{
    filename?: string;
    total_rows?: number;
    valid_count?: number;
    invalid_count?: number;
    duplicate_count?: number;
  } | null>(null);

  // Scheduled Refresh & Expiration state (Phase 6.4)
  const [refreshStatus, setRefreshStatus] = useState<{
    enabled: boolean;
    interval_minutes: number;
    jsearch_enabled: boolean;
    jsearch_query: string;
    rss_enabled: boolean;
    auto_expire: boolean;
    last_summary?: {
      last_run_at?: string | null;
      status: string;
      is_running: boolean;
      total_inserted: number;
      total_updated: number;
      total_duplicates: number;
      total_expired: number;
      duration_seconds: number;
      errors?: string[];
    };
  } | null>(null);
  const [triggeringRefresh, setTriggeringRefresh] = useState(false);
  const [refreshMessage, setRefreshMessage] = useState<string | null>(null);
  const [showScheduleDetails, setShowScheduleDetails] = useState(false);
  const [showTemplateGuide, setShowTemplateGuide] = useState(false);
  const [refreshIncludeJsearch, setRefreshIncludeJsearch] = useState(false);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [errorType, setErrorType] = useState<"config" | "rate_limit" | "import" | "rss" | "generic" | null>(null);

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

  const handleRssPreview = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const feedUrl = rssPreset === "custom"
      ? rssCustomUrl.trim()
      : RSS_PRESETS.find((p) => p.id === rssPreset)?.url || "";

    if (!feedUrl) {
      setError("Please provide a valid RSS feed URL.");
      return;
    }

    setLoading(true);
    setError(null);
    setErrorType(null);
    setImportResult(null);

    try {
      const supabase = createClient();
      const { data: { session } } = await supabase.auth.getSession();

      if (!session) {
        throw new Error("You must be logged in as an administrator to preview RSS ingestion.");
      }

      const res = await fetch(`${API_URL}/api/v1/admin/ingestion/rss/preview`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({
          feed_url: feedUrl,
          max_items: Number(rssMaxItems),
          filter_keywords: rssKeywords.trim() || undefined,
        }),
      });

      if (!res.ok) {
        setErrorType("rss");
        const errJson = await res.json().catch(() => null);
        throw new Error(errJson?.detail || `Feed request failed with status ${res.status}`);
      }

      const data = await res.json();
      setJobs(data.jobs || []);
      setSummary(data.summary || null);
      setFeedMeta({
        title: data.feed_title,
        link: data.feed_link,
        description: data.feed_description,
      });

      const autoSelected = new Set<string>();
      (data.jobs || []).forEach((j: JobPreview) => {
        if (!j.is_duplicate && (!j.errors || j.errors.length === 0)) {
          autoSelected.add(j.job_id);
        }
      });
      setSelectedJobIds(autoSelected);
    } catch (err) {
      setErrorType("rss");
      setError(err instanceof Error ? err.message : "Failed to fetch and preview RSS feed.");
    } finally {
      setLoading(false);
    }
  };

  const loadRefreshStatus = useCallback(async () => {
    try {
      const supabase = createClient();
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) return;
      const res = await fetch(`${API_URL}/api/v1/admin/ingestion/refresh/status`, {
        headers: { Authorization: `Bearer ${session.access_token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setRefreshStatus(data);
      }
    } catch {
      // Ignore background load error
    }
  }, [API_URL]);

  useEffect(() => {
    let ignore = false;
    async function init() {
      try {
        const supabase = createClient();
        const { data: { session } } = await supabase.auth.getSession();
        if (!session || ignore) return;
        const res = await fetch(`${API_URL}/api/v1/admin/ingestion/refresh/status`, {
          headers: { Authorization: `Bearer ${session.access_token}` },
        });
        if (res.ok && !ignore) {
          const data = await res.json();
          setRefreshStatus(data);
        }
      } catch {
        // Ignore background load error
      }
    }
    init();
    return () => {
      ignore = true;
    };
  }, [API_URL]);

  const handleTriggerRefresh = async () => {
    setTriggeringRefresh(true);
    setRefreshMessage(null);
    try {
      const supabase = createClient();
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) throw new Error("Administrator session required.");

      const res = await fetch(
        `${API_URL}/api/v1/admin/ingestion/refresh/trigger?force=true&include_jsearch=${refreshIncludeJsearch}`,
        {
          method: "POST",
          headers: { Authorization: `Bearer ${session.access_token}` },
        }
      );
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Refresh failed");
      }
      setRefreshMessage(`Sync complete: ${data.summary?.total_inserted ?? 0} new, ${data.summary?.total_updated ?? 0} updated, ${data.summary?.total_expired ?? 0} expired.`);
      await loadRefreshStatus();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to trigger scheduled refresh.");
      setErrorType("generic");
    } finally {
      setTriggeringRefresh(false);
    }
  };

  const downloadCsvTemplate = () => {
    const headers = [
      "title",
      "company_name",
      "opportunity_type",
      "work_model",
      "locations",
      "application_url",
      "company_website",
      "description",
      "deadline",
      "stipend_min",
      "stipend_max",
      "currency",
      "skills",
      "domain",
      "eligibility",
    ];
    const sampleRows = [
      [
        "Software Engineer Intern",
        "Acme Innovations",
        "Internship",
        "Remote",
        "San Francisco, CA; Bengaluru, India",
        "https://example.com/careers/swe-intern-2026",
        "https://example.com",
        "Join our engineering team to build scalable modern web applications with Python and React.",
        "2026-12-31T23:59:59Z",
        "1500",
        "2500",
        "USD",
        "Python, React, PostgreSQL",
        "Software Engineering",
        "Currently pursuing Bachelor's or Master's in CS or related field",
      ],
      [
        "Frontend Developer Intern",
        "Nexus Cloud Labs",
        "Internship",
        "Hybrid",
        "New York, NY",
        "https://example.com/careers/frontend-intern",
        "https://example.com",
        "Develop interactive web interfaces using TypeScript, Next.js, and modern CSS techniques.",
        "2026-11-30T23:59:59Z",
        "1200",
        "2000",
        "USD",
        "React, JavaScript, TypeScript, CSS",
        "Frontend Development",
        "Graduating class of 2026 or 2027",
      ],
    ];

    const escapeCsv = (val: string) => {
      if (val.includes(",") || val.includes('"') || val.includes("\n")) {
        return `"${val.replace(/"/g, '""')}"`;
      }
      return val;
    };

    const csvContent = [
      headers.join(","),
      ...sampleRows.map((r) => r.map(escapeCsv).join(",")),
    ].join("\n");

    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", "careerpilot_bulk_template.csv");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const downloadJsonTemplate = () => {
    const sampleData = {
      jobs: [
        {
          title: "Software Engineer Intern",
          company_name: "Acme Innovations",
          opportunity_type: "Internship",
          work_model: "Remote",
          locations: ["San Francisco, CA", "Bengaluru, India"],
          application_url: "https://example.com/careers/swe-intern-2026",
          company_website: "https://example.com",
          description:
            "Join our engineering team to build scalable modern web applications with Python and React.",
          deadline: "2026-12-31T23:59:59Z",
          stipend_min: 1500,
          stipend_max: 2500,
          currency: "USD",
          skills: "Python, React, PostgreSQL",
          domain: "Software Engineering",
          eligibility:
            "Currently pursuing Bachelor's or Master's in CS or related field",
        },
        {
          title: "Frontend Developer Intern",
          company_name: "Nexus Cloud Labs",
          opportunity_type: "Internship",
          work_model: "Hybrid",
          locations: ["New York, NY"],
          application_url: "https://example.com/careers/frontend-intern",
          company_website: "https://example.com",
          description:
            "Develop interactive web interfaces using TypeScript, Next.js, and modern CSS techniques.",
          deadline: "2026-11-30T23:59:59Z",
          stipend_min: 1200,
          stipend_max: 2000,
          currency: "USD",
          skills: "React, JavaScript, TypeScript, CSS",
          domain: "Frontend Development",
          eligibility: "Graduating class of 2026 or 2027",
        },
      ],
    };

    const jsonContent = JSON.stringify(sampleData, null, 2);
    const blob = new Blob([jsonContent], { type: "application/json;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", "careerpilot_bulk_template.json");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const handleBulkPreview = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!bulkFile) return;

    setLoading(true);
    setError(null);
    setErrorType(null);
    setImportResult(null);

    try {
      const supabase = createClient();
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) throw new Error("You must be logged in as an administrator to preview bulk upload.");

      const formData = new FormData();
      formData.append("file", bulkFile);

      const res = await fetch(`${API_URL}/api/v1/admin/ingestion/bulk-upload/preview`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${session.access_token}`,
        },
        body: formData,
      });

      if (!res.ok) {
        const errJson = await res.json().catch(() => null);
        throw new Error(errJson?.detail || `Upload preview failed with status ${res.status}`);
      }

      const data = await res.json();
      setJobs(data.jobs || []);
      setSummary(data.summary || null);
      setBulkMeta({
        filename: data.filename,
        total_rows: data.total_rows,
        valid_count: data.valid_count,
        invalid_count: data.invalid_count,
        duplicate_count: data.duplicate_count,
      });

      const autoSelected = new Set<string>();
      (data.jobs || []).forEach((j: JobPreview) => {
        if (!j.is_duplicate && (!j.errors || j.errors.length === 0)) {
          autoSelected.add(j.job_id);
        }
      });
      setSelectedJobIds(autoSelected);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to preview uploaded file.");
      setErrorType("generic");
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

      const importEndpoint = activeTab === "bulk"
        ? `${API_URL}/api/v1/admin/ingestion/bulk-upload/import`
        : activeTab === "rss"
        ? `${API_URL}/api/v1/admin/ingestion/rss/import`
        : `${API_URL}/api/v1/admin/ingestion/jsearch/import`;

      let res: Response;
      try {
        res = await fetch(importEndpoint, {
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
      {/* Source Selection Tabs */}
      <div className="flex border-b border-border space-x-2">
        <button
          type="button"
          onClick={() => {
            setActiveTab("jsearch");
            setJobs([]);
            setSummary(null);
            setError(null);
            setFeedMeta(null);
            setBulkMeta(null);
          }}
          className={`flex items-center gap-2 pb-3 px-4 text-sm font-semibold border-b-2 transition-colors ${
            activeTab === "jsearch"
              ? "border-primary text-primary"
              : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          <Sparkles className="h-4 w-4" />
          RapidAPI JSearch
        </button>
        <button
          type="button"
          onClick={() => {
            setActiveTab("rss");
            setJobs([]);
            setSummary(null);
            setError(null);
            setFeedMeta(null);
            setBulkMeta(null);
          }}
          className={`flex items-center gap-2 pb-3 px-4 text-sm font-semibold border-b-2 transition-colors ${
            activeTab === "rss"
              ? "border-primary text-primary"
              : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          <Rss className="h-4 w-4" />
          Authorized RSS Feeds (Phase 6.3)
        </button>
        <button
          type="button"
          onClick={() => {
            setActiveTab("bulk");
            setJobs([]);
            setSummary(null);
            setError(null);
            setFeedMeta(null);
            setBulkMeta(null);
          }}
          className={`flex items-center gap-2 pb-3 px-4 text-sm font-semibold border-b-2 transition-colors ${
            activeTab === "bulk"
              ? "border-primary text-primary"
              : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          <UploadCloud className="h-4 w-4" />
          Fallback Bulk Upload (Phase 6.4)
        </button>
      </div>

      {/* Background Scheduled Refresh & Auto-Expiration Status Banner */}
      {refreshStatus && (
        <div className="rounded-xl border border-border/80 bg-muted/40 p-4 space-y-3">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="flex items-start gap-3">
              <div className="p-2 rounded-lg bg-primary/10 text-primary mt-0.5">
                <Clock className="h-5 w-5" />
              </div>
              <div>
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-semibold text-foreground text-sm">Automated Refresh &amp; Deadline Expiration (Phase 6.4)</span>
                  <Badge variant={refreshStatus.enabled ? "default" : "secondary"} className="text-xs">
                    {refreshStatus.enabled ? "Schedule: Active (External Runner)" : "Schedule: Standby (Manual / External CLI)"}
                  </Badge>
                  {refreshStatus.auto_expire && (
                    <Badge variant="outline" className="text-xs text-amber-600 dark:text-amber-400 border-amber-500/30">
                      Auto-Expire Active
                    </Badge>
                  )}
                  <button
                    type="button"
                    onClick={() => setShowScheduleDetails(!showScheduleDetails)}
                    className="inline-flex items-center gap-1 text-xs text-primary hover:underline ml-1 font-medium"
                  >
                    <HelpCircle className="h-3.5 w-3.5" />
                    {showScheduleDetails ? "Hide Architecture" : "Why Standby? Architecture & Cron Guide"}
                  </button>
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  {refreshStatus.last_summary?.last_run_at ? (
                    <>
                      Last sync: {new Date(refreshStatus.last_summary.last_run_at).toLocaleString()} ({refreshStatus.last_summary.status}) —{" "}
                      <strong>{refreshStatus.last_summary.total_inserted}</strong> new,{" "}
                      <strong>{refreshStatus.last_summary.total_updated}</strong> updated,{" "}
                      <strong>{refreshStatus.last_summary.total_expired}</strong> expired.
                    </>
                  ) : (
                    <>Periodic sync of authorized RSS feeds and JSearch with past-deadline auto-expiration of published opportunities.</>
                  )}
                </p>
                {refreshMessage && (
                  <p className="text-xs text-emerald-600 dark:text-emerald-400 mt-1 font-medium">{refreshMessage}</p>
                )}
              </div>
            </div>
            <div className="flex flex-col sm:items-end gap-1.5 shrink-0">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={handleTriggerRefresh}
                disabled={triggeringRefresh || loading}
                className="shrink-0"
              >
                {triggeringRefresh ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Synchronizing...
                  </>
                ) : (
                  <>
                    <RefreshCw className="mr-2 h-4 w-4" />
                    Run Refresh &amp; Expire
                  </>
                )}
              </Button>
              <label className="flex items-center gap-1.5 text-[11px] text-muted-foreground cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={refreshIncludeJsearch}
                  onChange={(e) => setRefreshIncludeJsearch(e.target.checked)}
                  className="rounded border-border text-primary h-3 w-3"
                />
                <span>Include JSearch API (quota guard)</span>
              </label>
            </div>
          </div>

          {/* Collapsible Architecture & Setup Guide */}
          {showScheduleDetails && (
            <div className="mt-3 p-3.5 rounded-lg bg-background/80 border border-border/70 text-xs text-muted-foreground space-y-2">
              <div className="font-semibold text-foreground flex items-center gap-1.5 text-xs">
                <Info className="h-4 w-4 text-primary" />
                Process &amp; Deployment Architecture Guide
              </div>
              <p>
                • <strong>Why Standby?</strong> In multi-worker FastAPI deployments (e.g. Uvicorn/Gunicorn), running an internal background timer in each worker process causes duplicate concurrent job executions and burns API quota. CareerPilot AI delegates background runs to the standalone CLI runner <code>python -m app.cli.scheduled_refresh</code>.
              </p>
              <p>
                • <strong>Configuring External Automation:</strong> To enable recurring execution on your deployment server, configure an external OS cron job (e.g. <code>0 */6 * * * python -m app.cli.scheduled_refresh</code>) or Cloud Scheduler job, and set <code>SCHEDULED_REFRESH_ENABLED=true</code> in <code>backend/.env</code>.
              </p>
              <p>
                • <strong>Safe Manual Sync:</strong> Clicking &quot;Run Refresh &amp; Expire&quot; above executes safe on-demand synchronization and past-deadline expiration immediately. By default, JSearch is excluded to preserve your monthly RapidAPI allowance unless the quota guard checkbox is checked.
              </p>
            </div>
          )}
        </div>
      )}

      {activeTab === "jsearch" ? (
        <>
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
        </>
      ) : (
        <>
          {/* RSS Feed Notice */}
          <div className="rounded-xl border border-border/80 bg-card p-4 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="flex items-start gap-3">
              <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 mt-0.5">
                <Rss className="h-5 w-5" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-foreground text-sm">Authorized RSS Feed Ingestion (Phase 6.3)</span>
                  <Badge variant="outline" className="text-xs font-medium border-emerald-500/30 text-emerald-600 dark:text-emerald-400">Structured XML</Badge>
                </div>
                <p className="text-xs text-muted-foreground mt-1 max-w-2xl">
                  Reads clean XML (RSS 2.0 &amp; Atom 1.0) with strict SSRF protection and cross-source duplicate detection. HTML website scraping is intentionally deferred to avoid brittle parsers and legal uncertainty.
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2 text-xs text-muted-foreground shrink-0">
              <Info className="h-4 w-4" />
              <span>No scraping overhead</span>
            </div>
          </div>

          {/* RSS Feed Controls */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-lg">RSS &amp; Atom Feed Ingestion</CardTitle>
              <CardDescription>
                Select an approved feed preset or supply an authorized feed URL to discover openings.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleRssPreview} className="space-y-4">
                <div className="flex flex-col md:flex-row gap-3">
                  <div className="w-full md:w-80">
                    <Select value={rssPreset} onValueChange={(val) => val && setRssPreset(val)} disabled={loading}>
                      <SelectTrigger className="w-full">
                        <SelectValue placeholder="Select Feed Preset" />
                      </SelectTrigger>
                      <SelectContent>
                        {RSS_PRESETS.map((preset) => (
                          <SelectItem key={preset.id} value={preset.id}>
                            {preset.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  {rssPreset === "custom" && (
                    <div className="relative flex-1">
                      <Input
                        value={rssCustomUrl}
                        onChange={(e) => setRssCustomUrl(e.target.value)}
                        placeholder="https://example.com/feed.xml"
                        className="w-full"
                        disabled={loading}
                      />
                    </div>
                  )}

                  <div className="relative flex-1">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                      value={rssKeywords}
                      onChange={(e) => setRssKeywords(e.target.value)}
                      placeholder="Filter keywords (e.g. Intern, Python, React)..."
                      className="pl-9"
                      disabled={loading}
                    />
                  </div>

                  <div className="w-full md:w-32">
                    <Select value={String(rssMaxItems)} onValueChange={(val) => val && setRssMaxItems(Number(val))} disabled={loading}>
                      <SelectTrigger className="w-full">
                        <SelectValue placeholder="Max Items" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="10">10 Items</SelectItem>
                        <SelectItem value="20">20 Items</SelectItem>
                        <SelectItem value="50">50 Items</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <Button type="submit" disabled={loading || (rssPreset === "custom" && !rssCustomUrl.trim())} className="md:w-36">
                    {loading ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Fetching...
                      </>
                    ) : (
                      <>
                        <Rss className="mr-2 h-4 w-4" />
                        Fetch Feed
                      </>
                    )}
                  </Button>
                </div>

                {/* Preset feed description */}
                {rssPreset !== "custom" && (
                  <p className="text-xs text-muted-foreground">
                    {RSS_PRESETS.find((p) => p.id === rssPreset)?.description}
                  </p>
                )}
              </form>
            </CardContent>
          </Card>

          {/* Feed Metadata Banner if present */}
          {feedMeta && feedMeta.title && (
            <div className="rounded-lg border border-border/70 bg-muted/40 p-3 text-xs flex items-center justify-between">
              <div>
                <span className="font-semibold text-foreground">{feedMeta.title}</span>
                {feedMeta.description && <span className="text-muted-foreground ml-2">— {feedMeta.description}</span>}
              </div>
              {feedMeta.link && (
                <a href={feedMeta.link} target="_blank" rel="noopener noreferrer" className="flex items-center text-primary hover:underline shrink-0">
                  Feed Website <ExternalLink className="ml-1 h-3 w-3" />
                </a>
              )}
            </div>
          )}
        </>
      )}

      {activeTab === "bulk" && (
        <>
          {/* Bulk Upload Info Notice */}
          <div className="rounded-xl border border-border/80 bg-card p-4 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="flex items-start gap-3">
              <div className="p-2 rounded-lg bg-blue-500/10 text-blue-600 dark:text-blue-400 mt-0.5">
                <UploadCloud className="h-5 w-5" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-foreground text-sm">Fallback Bulk Upload (CSV &amp; JSON)</span>
                  <Badge variant="outline" className="text-xs font-medium border-blue-500/30 text-blue-600 dark:text-blue-400">Phase 6.4</Badge>
                </div>
                <p className="text-xs text-muted-foreground mt-1 max-w-2xl">
                  Upload opportunity listings from partner organizations, campus drives, and verified spreadsheets without fragile HTML scrapers.
                  Validates file size (max 5 MB, up to 500 rows) and sanitizes markup. All imported opportunities are saved strictly as <strong>Draft</strong>.
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2 text-xs text-muted-foreground shrink-0">
              <FileText className="h-4 w-4" />
              <span>.csv or .json (UTF-8)</span>
            </div>
          </div>

          {/* 4-Step Ingestion Workflow Guide */}
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-2.5 text-xs">
            <div className="p-3 rounded-lg border border-border/70 bg-card shadow-xs flex items-center gap-2.5">
              <span className="font-bold text-primary bg-primary/10 rounded-full h-5 w-5 flex items-center justify-center shrink-0 text-xs">1</span>
              <div>
                <div className="font-medium text-foreground">Upload File</div>
                <div className="text-[11px] text-muted-foreground">CSV or JSON (max 5 MB)</div>
              </div>
            </div>
            <div className="p-3 rounded-lg border border-border/70 bg-card shadow-xs flex items-center gap-2.5">
              <span className="font-bold text-primary bg-primary/10 rounded-full h-5 w-5 flex items-center justify-center shrink-0 text-xs">2</span>
              <div>
                <div className="font-medium text-foreground">Validate &amp; Preview</div>
                <div className="text-[11px] text-muted-foreground">Sanitized &amp; deduped</div>
              </div>
            </div>
            <div className="p-3 rounded-lg border border-border/70 bg-card shadow-xs flex items-center gap-2.5">
              <span className="font-bold text-primary bg-primary/10 rounded-full h-5 w-5 flex items-center justify-center shrink-0 text-xs">3</span>
              <div>
                <div className="font-medium text-foreground">Select Valid Rows</div>
                <div className="text-[11px] text-muted-foreground">Resolve warnings/errors</div>
              </div>
            </div>
            <div className="p-3 rounded-lg border border-border/70 bg-card shadow-xs flex items-center gap-2.5">
              <span className="font-bold text-primary bg-primary/10 rounded-full h-5 w-5 flex items-center justify-center shrink-0 text-xs">4</span>
              <div>
                <div className="font-medium text-foreground">Import as Draft</div>
                <div className="text-[11px] text-muted-foreground">Admin review before publish</div>
              </div>
            </div>
          </div>

          {/* Downloadable Templates Card */}
          <Card>
            <CardHeader className="pb-3">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                  <CardTitle className="text-lg flex items-center gap-2">
                    <Download className="h-5 w-5 text-primary" />
                    Downloadable Templates &amp; Format Specifications
                  </CardTitle>
                  <CardDescription>
                    Download pre-formatted CSV and JSON templates containing required columns and sample rows.
                  </CardDescription>
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  <Button type="button" variant="outline" size="sm" onClick={downloadCsvTemplate} className="text-xs">
                    <Download className="mr-1.5 h-3.5 w-3.5 text-emerald-600 dark:text-emerald-400" />
                    Download CSV Template
                  </Button>
                  <Button type="button" variant="outline" size="sm" onClick={downloadJsonTemplate} className="text-xs">
                    <Download className="mr-1.5 h-3.5 w-3.5 text-blue-600 dark:text-blue-400" />
                    Download JSON Template
                  </Button>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={() => setShowTemplateGuide(!showTemplateGuide)}
                    className="text-xs text-muted-foreground"
                  >
                    <Info className="mr-1 h-3.5 w-3.5" />
                    {showTemplateGuide ? "Hide Format Guide" : "View Format Guide"}
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="p-3 rounded-lg border border-amber-500/30 bg-amber-500/10 text-xs text-amber-800 dark:text-amber-400 flex items-start gap-2.5">
                <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5 text-amber-600 dark:text-amber-400" />
                <div>
                  <strong>Template Sample Data Notice:</strong> The downloaded templates contain example demonstration records. Review and replace each entry with your authentic employer or drive data before importing. Imported opportunities are strictly saved as <strong>Draft</strong> and will not be published or visible to students until administrator review.
                </div>
              </div>

              {showTemplateGuide && (
                <div className="p-3.5 rounded-lg bg-muted/40 border border-border/70 text-xs space-y-2">
                  <div className="font-semibold text-foreground">Accepted Field Specifications (CSV headers or JSON keys):</div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-x-4 gap-y-1.5 text-muted-foreground">
                    <div>• <strong>title</strong> (Required): Role title, max 255 chars</div>
                    <div>• <strong>company_name</strong> (Required): Employer name, max 255 chars</div>
                    <div>• <strong>opportunity_type</strong>: &apos;Internship&apos; or &apos;Full-Time&apos;</div>
                    <div>• <strong>work_model</strong>: &apos;Remote&apos;, &apos;Hybrid&apos;, or &apos;On-site&apos;</div>
                    <div>• <strong>locations</strong>: Comma-separated list or JSON array</div>
                    <div>• <strong>application_url</strong>: Valid http:// or https:// URL (max 500 chars)</div>
                    <div>• <strong>company_website</strong>: Valid company URL (max 500 chars)</div>
                    <div>• <strong>deadline</strong>: ISO-8601 date (e.g. 2026-12-31T23:59:59Z)</div>
                    <div>• <strong>stipend_min / stipend_max</strong>: Monthly stipend integer</div>
                    <div>• <strong>salary_min / salary_max</strong>: Annual salary integer</div>
                    <div>• <strong>currency</strong>: Currency code (e.g. USD, INR)</div>
                    <div>• <strong>skills</strong>: Comma-separated canonical skills</div>
                    <div>• <strong>domain, eligibility, education_requirements</strong>: Sanitized text</div>
                  </div>
                  <p className="text-[11px] text-muted-foreground/80 pt-1">
                    Limits: Maximum 5 MB per file, maximum 500 rows per batch. HTML script blocks and markup tags are automatically stripped for security.
                  </p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Bulk Upload Form */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-lg">Select File for Ingestion</CardTitle>
              <CardDescription>
                Supported formats: CSV (with header row) or JSON (array of job objects). Required fields: <code>title</code> and <code>company_name</code>.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleBulkPreview} className="space-y-4">
                <div className="flex flex-col md:flex-row items-center gap-3">
                  <Input
                    type="file"
                    accept=".csv,.json,text/csv,application/json"
                    onChange={(e) => {
                      if (e.target.files && e.target.files[0]) {
                        setBulkFile(e.target.files[0]);
                      }
                    }}
                    disabled={loading}
                    className="flex-1 cursor-pointer"
                  />
                  <Button type="submit" disabled={loading || !bulkFile} className="w-full md:w-40">
                    {loading ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Validating...
                      </>
                    ) : (
                      <>
                        <UploadCloud className="mr-2 h-4 w-4" />
                        Preview File
                      </>
                    )}
                  </Button>
                </div>

                {/* File Metadata Banner */}
                {bulkMeta && (
                  <div className="rounded-lg border border-border/70 bg-muted/40 p-3 text-xs flex flex-col md:flex-row items-start md:items-center justify-between gap-2">
                    <div>
                      <span className="font-semibold text-foreground">{bulkMeta.filename}</span>
                      <span className="text-muted-foreground ml-2">
                        — {bulkMeta.total_rows} total rows ({bulkMeta.valid_count} valid, {bulkMeta.invalid_count} invalid, {bulkMeta.duplicate_count} duplicate)
                      </span>
                    </div>
                  </div>
                )}
              </form>
            </CardContent>
          </Card>
        </>
      )}

      {/* 3. Error Alerts */}
      {error && (
        <div
          className={`p-4 rounded-xl border flex items-start gap-3 ${
            errorType === "config" || errorType === "rss"
              ? "bg-amber-500/10 border-amber-500/30 text-amber-700 dark:text-amber-400"
              : errorType === "rate_limit"
              ? "bg-purple-500/10 border-purple-500/30 text-purple-600 dark:text-purple-400"
              : "bg-destructive/10 border-destructive/30 text-destructive"
          }`}
        >
          {errorType === "config" || errorType === "rss" ? (
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
                : errorType === "rss"
                ? "RSS Feed Provider Unavailable"
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
            {errorType === "rss" && (
              <p className="text-xs text-muted-foreground mt-2">
                Tip: Select a verified preset from the list (such as We Work Remotely) or check that the custom feed URL is publicly accessible and returns valid RSS/Atom XML.
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
