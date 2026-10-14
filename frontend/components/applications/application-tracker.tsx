"use client";

import { useCallback, useEffect, useId, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  AlertCircle,
  Bell,
  BellRing,
  BookOpen,
  Briefcase,
  Calendar,
  CheckCircle2,
  Clock,
  ExternalLink,
  FileCheck,
  FileEdit,
  History,
  Layers,
  MapPin,
  Pencil,
  Plus,
  RefreshCw,
  Search,
  Sparkles,
  Trash2,
  X,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { createClient } from "@/lib/supabase/client";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export type ApplicationStatus =
  | "Saved"
  | "Applied"
  | "Assessment"
  | "Interview"
  | "Offer"
  | "Rejected"
  | "Withdrawn";

export interface OpportunitySummary {
  id: string;
  title: string;
  company_name: string;
  company_logo_url?: string | null;
  opportunity_type: string;
  work_model: string;
  domain?: string | null;
  locations?: string[];
  application_url?: string | null;
  deadline?: string | null;
}

export interface StatusHistoryItem {
  id: string;
  application_id: string;
  from_status?: string | null;
  to_status: string;
  note?: string | null;
  created_at: string;
}

export interface TrackedApplication {
  id: string;
  profile_id: string;
  opportunity_id: string;
  status: ApplicationStatus;
  applied_at?: string | null;
  status_updated_at: string;
  deadline?: string | null;
  reminder_at?: string | null;
  reminder_note?: string | null;
  notes?: string | null;
  created_at: string;
  updated_at: string;
  opportunity: OpportunitySummary;
  history?: StatusHistoryItem[];
}

export interface ApplicationAnalytics {
  total_tracked: number;
  total_submitted: number;
  by_status: Record<string, number>;
  active_in_progress: number;
  response_rate_percent: number;
  interview_rate_percent: number;
  sample_size_note: string;
  upcoming_reminders_count: number;
  due_reminders_count: number;
  upcoming_deadlines_count: number;
}

export interface RemindersSummary {
  due_reminders: TrackedApplication[];
  upcoming_reminders: TrackedApplication[];
  total_due: number;
  total_upcoming: number;
}

const STATUS_CONFIG: Record<
  ApplicationStatus,
  { label: string; badgeClass: string; dotClass: string }
> = {
  Saved: {
    label: "Saved / Bookmarked",
    badgeClass: "bg-slate-100 text-slate-700 border-slate-200",
    dotClass: "bg-slate-400",
  },
  Applied: {
    label: "Applied",
    badgeClass: "bg-blue-50 text-blue-700 border-blue-200",
    dotClass: "bg-blue-500",
  },
  Assessment: {
    label: "Assessment / Test",
    badgeClass: "bg-indigo-50 text-indigo-700 border-indigo-200",
    dotClass: "bg-indigo-500",
  },
  Interview: {
    label: "Interviewing",
    badgeClass: "bg-amber-50 text-amber-800 border-amber-200",
    dotClass: "bg-amber-500",
  },
  Offer: {
    label: "Offer Received",
    badgeClass: "bg-emerald-50 text-emerald-800 border-emerald-200",
    dotClass: "bg-emerald-500",
  },
  Rejected: {
    label: "Not Selected",
    badgeClass: "bg-rose-50 text-rose-700 border-rose-200",
    dotClass: "bg-rose-400",
  },
  Withdrawn: {
    label: "Withdrawn",
    badgeClass: "bg-gray-100 text-gray-600 border-gray-200",
    dotClass: "bg-gray-400",
  },
};

export function ApplicationTracker() {
  const router = useRouter();
  const supabase = createClient();

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Application data
  const [applications, setApplications] = useState<TrackedApplication[]>([]);
  const [analytics, setAnalytics] = useState<ApplicationAnalytics | null>(null);
  const [reminders, setReminders] = useState<RemindersSummary | null>(null);

  // Filters & Search
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState("");
  const [sortBy, setSortBy] = useState<string>("updated_desc");

  // Edit / Detail Modal state
  const [selectedApp, setSelectedApp] = useState<TrackedApplication | null>(null);
  const [editStatus, setEditStatus] = useState<ApplicationStatus>("Applied");
  const [editStatusNote, setEditStatusNote] = useState("");
  const [editAppliedAt, setEditAppliedAt] = useState("");
  const [editDeadline, setEditDeadline] = useState("");
  const [editReminderAt, setEditReminderAt] = useState("");
  const [editReminderNote, setEditReminderNote] = useState("");
  const [editNotes, setEditNotes] = useState("");
  const [modalSaving, setModalSaving] = useState(false);

  // New Application Modal state
  const [showAddModal, setShowAddModal] = useState(false);
  const [savedOpportunities, setSavedOpportunities] = useState<OpportunitySummary[]>([]);
  const [loadingSaved, setLoadingSaved] = useState(false);
  const [newOpportunityId, setNewOpportunityId] = useState("");
  const [newStatus, setNewStatus] = useState<ApplicationStatus>("Applied");
  const [newAppliedAt, setNewAppliedAt] = useState("");
  const [newDeadline, setNewDeadline] = useState("");
  const [newReminderAt, setNewReminderAt] = useState("");
  const [newReminderNote, setNewReminderNote] = useState("");
  const [newNotes, setNewNotes] = useState("");
  const [addSaving, setAddSaving] = useState(false);

  // Delete confirmation
  const [deleteConfirmAppId, setDeleteConfirmAppId] = useState<string | null>(null);

  const searchInputId = useId();

  // Load tracker data
  const loadData = useCallback(async () => {
    try {
      const {
        data: { session },
      } = await supabase.auth.getSession();
      if (!session) {
        router.push("/login");
        return;
      }

      setError(null);

      const headers = { Authorization: `Bearer ${session.access_token}` };

      // Fetch applications list, analytics, and reminders in parallel
      const [appsRes, analyticsRes, remindersRes] = await Promise.all([
        fetch(`${API_URL}/api/v1/applications?page=1&page_size=100`, { headers }),
        fetch(`${API_URL}/api/v1/applications/analytics`, { headers }),
        fetch(`${API_URL}/api/v1/applications/reminders`, { headers }),
      ]);

      if (!appsRes.ok) throw new Error("Failed to load tracked applications.");
      if (!analyticsRes.ok) throw new Error("Failed to load application analytics.");
      if (!remindersRes.ok) throw new Error("Failed to load application reminders.");

      const appsData = await appsRes.json();
      const analyticsData = await analyticsRes.json();
      const remindersData = await remindersRes.json();

      setApplications(appsData.items || []);
      setAnalytics(analyticsData);
      setReminders(remindersData);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to load application tracker.";
      setError(msg);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [router, supabase.auth]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadData();
  }, [loadData]);

  // Load saved opportunities for Add modal
  const loadSavedOpportunities = async () => {
    setLoadingSaved(true);
    try {
      const {
        data: { session },
      } = await supabase.auth.getSession();
      if (!session) return;

      const res = await fetch(`${API_URL}/api/v1/profile/saved-opportunities?page=1&page_size=50`, {
        headers: { Authorization: `Bearer ${session.access_token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setSavedOpportunities(data.items || []);
      }
    } catch (e) {
      console.error("Failed to load saved opportunities", e);
    } finally {
      setLoadingSaved(false);
    }
  };

  const handleOpenAddModal = () => {
    setShowAddModal(true);
    setNewOpportunityId("");
    setNewStatus("Applied");
    setNewAppliedAt(new Date().toISOString().slice(0, 10));
    setNewDeadline("");
    setNewReminderAt("");
    setNewReminderNote("");
    setNewNotes("");
    loadSavedOpportunities();
  };

  const handleSelectAppForDetail = async (app: TrackedApplication) => {
    try {
      const {
        data: { session },
      } = await supabase.auth.getSession();
      if (!session) return;

      // Fetch fresh details with history
      const res = await fetch(`${API_URL}/api/v1/applications/${app.id}`, {
        headers: { Authorization: `Bearer ${session.access_token}` },
      });
      if (res.ok) {
        const fullApp = await res.json();
        setSelectedApp(fullApp);
        setEditStatus(fullApp.status);
        setEditStatusNote("");
        setEditAppliedAt(
          fullApp.applied_at ? fullApp.applied_at.slice(0, 10) : ""
        );
        setEditDeadline(fullApp.deadline ? fullApp.deadline.slice(0, 10) : "");
        setEditReminderAt(
          fullApp.reminder_at ? fullApp.reminder_at.slice(0, 16) : ""
        );
        setEditReminderNote(fullApp.reminder_note || "");
        setEditNotes(fullApp.notes || "");
        return;
      }
    } catch {
      // Fallback to currently loaded data
    }
    setSelectedApp(app);
    setEditStatus(app.status);
    setEditStatusNote("");
    setEditAppliedAt(app.applied_at ? app.applied_at.slice(0, 10) : "");
    setEditDeadline(app.deadline ? app.deadline.slice(0, 10) : "");
    setEditReminderAt(app.reminder_at ? app.reminder_at.slice(0, 16) : "");
    setEditReminderNote(app.reminder_note || "");
    setEditNotes(app.notes || "");
  };

  const handleCreateApplication = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newOpportunityId) {
      setError("Please select an opportunity to track.");
      return;
    }

    setAddSaving(true);
    setError(null);
    try {
      const {
        data: { session },
      } = await supabase.auth.getSession();
      if (!session) return;

      const payload = {
        opportunity_id: newOpportunityId,
        status: newStatus,
        applied_at: newAppliedAt ? new Date(newAppliedAt).toISOString() : null,
        deadline: newDeadline ? new Date(newDeadline).toISOString() : null,
        reminder_at: newReminderAt ? new Date(newReminderAt).toISOString() : null,
        reminder_note: newReminderNote.trim() || null,
        notes: newNotes.trim() || null,
      };

      const res = await fetch(`${API_URL}/api/v1/applications`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${session.access_token}`,
        },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.detail || "Failed to create application record.");
      }

      setShowAddModal(false);
      setSuccessMessage(
        newStatus === "Saved"
          ? "Opportunity added to tracker as Saved."
          : `Application marked as ${newStatus} successfully.`
      );
      setTimeout(() => setSuccessMessage(null), 4000);
      await loadData();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to create application.";
      setError(msg);
    } finally {
      setAddSaving(false);
    }
  };

  const handleUpdateApplication = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedApp) return;

    setModalSaving(true);
    setError(null);
    try {
      const {
        data: { session },
      } = await supabase.auth.getSession();
      if (!session) return;

      const payload: Record<string, unknown> = {
        status: editStatus,
        status_change_note: editStatusNote.trim() || undefined,
        applied_at: editAppliedAt ? new Date(editAppliedAt).toISOString() : null,
        deadline: editDeadline ? new Date(editDeadline).toISOString() : null,
        reminder_at: editReminderAt ? new Date(editReminderAt).toISOString() : null,
        reminder_note: editReminderNote.trim() || null,
        notes: editNotes.trim() || null,
      };

      const res = await fetch(`${API_URL}/api/v1/applications/${selectedApp.id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${session.access_token}`,
        },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.detail || "Failed to update application.");
      }

      const updated = await res.json();
      setSelectedApp(updated);
      setSuccessMessage(`Application updated to ${editStatus} successfully.`);
      setTimeout(() => setSuccessMessage(null), 4000);
      await loadData();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to update application.";
      setError(msg);
    } finally {
      setModalSaving(false);
    }
  };

  const handleDeleteApplication = async (appId: string) => {
    setError(null);
    try {
      const {
        data: { session },
      } = await supabase.auth.getSession();
      if (!session) return;

      const res = await fetch(`${API_URL}/api/v1/applications/${appId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${session.access_token}` },
      });

      if (!res.ok) throw new Error("Failed to delete application.");

      setDeleteConfirmAppId(null);
      if (selectedApp && selectedApp.id === appId) {
        setSelectedApp(null);
      }
      setSuccessMessage("Application removed from tracker.");
      setTimeout(() => setSuccessMessage(null), 4000);
      await loadData();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to delete application.";
      setError(msg);
    }
  };

  const handleDismissReminder = async (app: TrackedApplication) => {
    try {
      const {
        data: { session },
      } = await supabase.auth.getSession();
      if (!session) return;

      const res = await fetch(`${API_URL}/api/v1/applications/${app.id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({
          reminder_at: null,
          reminder_note: null,
          status_change_note: "Reminder cleared / dismissed.",
        }),
      });

      if (res.ok) {
        setSuccessMessage("Reminder dismissed.");
        setTimeout(() => setSuccessMessage(null), 3000);
        await loadData();
      }
    } catch (e) {
      console.error("Failed to dismiss reminder", e);
    }
  };

  // Filtered & sorted application list
  const filteredApplications = applications
    .filter((app) => {
      if (statusFilter !== "ALL" && app.status !== statusFilter) {
        return false;
      }
      if (searchQuery.trim()) {
        const query = searchQuery.toLowerCase();
        const titleMatch = app.opportunity?.title?.toLowerCase().includes(query);
        const compMatch = app.opportunity?.company_name?.toLowerCase().includes(query);
        const notesMatch = app.notes?.toLowerCase().includes(query);
        return titleMatch || compMatch || notesMatch;
      }
      return true;
    })
    .sort((a, b) => {
      if (sortBy === "updated_desc") {
        return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime();
      }
      if (sortBy === "applied_desc") {
        const timeA = a.applied_at ? new Date(a.applied_at).getTime() : 0;
        const timeB = b.applied_at ? new Date(b.applied_at).getTime() : 0;
        return timeB - timeA;
      }
      if (sortBy === "deadline_asc") {
        const timeA = a.deadline ? new Date(a.deadline).getTime() : Infinity;
        const timeB = b.deadline ? new Date(b.deadline).getTime() : Infinity;
        return timeA - timeB;
      }
      if (sortBy === "company_asc") {
        return (a.opportunity?.company_name || "").localeCompare(
          b.opportunity?.company_name || ""
        );
      }
      return 0;
    });

  // Helpers for formatting
  const formatDate = (isoString?: string | null) => {
    if (!isoString) return null;
    try {
      const d = new Date(isoString);
      return d.toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
      });
    } catch {
      return isoString;
    }
  };

  const formatDateTime = (isoString?: string | null) => {
    if (!isoString) return null;
    try {
      const d = new Date(isoString);
      return d.toLocaleString("en-US", {
        month: "short",
        day: "numeric",
        hour: "numeric",
        minute: "2-digit",
      });
    } catch {
      return isoString;
    }
  };

  const getDaysDiff = (isoString: string) => {
    const target = new Date(isoString).getTime();
    const now = new Date().getTime();
    const diffDays = Math.ceil((target - now) / (1000 * 60 * 60 * 24));
    return diffDays;
  };

  if (loading) {
    return (
      <div className="flex min-h-[400px] flex-col items-center justify-center p-8 space-y-4">
        <RefreshCw className="h-8 w-8 animate-spin text-[#1B5E3B]" />
        <p className="text-gray-500 font-medium">Loading your Application Tracker...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Banner & Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white p-6 rounded-2xl border border-gray-100 shadow-sm">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl md:text-3xl font-bold text-[#14261C]">
              Application Tracker
            </h1>
            <Badge
              variant="outline"
              className="bg-[#F6FAF7] text-[#1B5E3B] border-[#1B5E3B]/20 font-semibold"
            >
              Phase 8
            </Badge>
          </div>
          <p className="text-muted-foreground mt-1 text-sm">
            Manage your job search pipeline, active submissions, deadlines, personal reminders, and interview milestones.
          </p>
        </div>

        <div className="flex items-center gap-3 flex-shrink-0">
          <Button
            id="tracker-refresh-btn"
            variant="outline"
            size="sm"
            onClick={() => {
              setRefreshing(true);
              loadData();
            }}
            disabled={refreshing}
            className="border-gray-200 text-gray-700 hover:bg-gray-50 flex items-center gap-1.5"
          >
            <RefreshCw className={`h-4 w-4 ${refreshing ? "animate-spin" : ""}`} />
            <span>Refresh</span>
          </Button>

          <Button
            id="tracker-add-app-btn"
            onClick={handleOpenAddModal}
            className="bg-[#1B5E3B] hover:bg-[#2E7D4F] text-white font-semibold flex items-center gap-1.5 shadow-sm"
          >
            <Plus className="h-4 w-4" />
            <span>Track Application</span>
          </Button>
        </div>
      </div>

      {/* Success Banner */}
      {successMessage && (
        <div className="bg-emerald-50 border border-emerald-200 text-emerald-800 px-4 py-3 rounded-xl flex items-center gap-2.5 shadow-sm animate-in fade-in">
          <CheckCircle2 className="h-5 w-5 text-emerald-600 flex-shrink-0" />
          <span className="text-sm font-medium">{successMessage}</span>
        </div>
      )}

      {/* Error Banner */}
      {error && (
        <div className="bg-rose-50 border border-rose-200 text-rose-800 px-4 py-3 rounded-xl flex items-center justify-between gap-2.5 shadow-sm">
          <div className="flex items-center gap-2.5">
            <AlertCircle className="h-5 w-5 text-rose-600 flex-shrink-0" />
            <span className="text-sm font-medium">{error}</span>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setError(null)}
            className="text-rose-700 hover:bg-rose-100 h-8 px-2"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>
      )}

      {/* Reminder Alerts Banner (if due or upcoming reminders exist) */}
      {reminders && (reminders.total_due > 0 || reminders.total_upcoming > 0) && (
        <div className="bg-amber-50/70 border border-amber-200/80 rounded-2xl p-5 shadow-sm">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2 text-amber-900 font-semibold">
              <BellRing className="h-5 w-5 text-amber-600 animate-pulse" />
              <span>Personal Reminders & Action Items</span>
            </div>
            <div className="flex items-center gap-2">
              {reminders.total_due > 0 && (
                <Badge className="bg-rose-100 text-rose-800 border-rose-200">
                  {reminders.total_due} Due / Overdue
                </Badge>
              )}
              {reminders.total_upcoming > 0 && (
                <Badge className="bg-amber-100 text-amber-800 border-amber-200">
                  {reminders.total_upcoming} Upcoming (Next 7 Days)
                </Badge>
              )}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-3">
            {reminders.due_reminders.map((dueApp) => (
              <div
                key={`due-${dueApp.id}`}
                className="bg-white p-3.5 rounded-xl border border-rose-200 flex items-start justify-between gap-3 shadow-xs"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-rose-600 uppercase tracking-wider">
                      Overdue / Due
                    </span>
                    <span className="text-xs text-gray-400">•</span>
                    <span className="text-xs text-gray-600 font-medium">
                      {formatDateTime(dueApp.reminder_at)}
                    </span>
                  </div>
                  <h4 className="font-semibold text-gray-900 text-sm">
                    {dueApp.opportunity?.title} at {dueApp.opportunity?.company_name}
                  </h4>
                  {dueApp.reminder_note && (
                    <p className="text-xs text-gray-600 bg-gray-50 px-2 py-1 rounded border border-gray-100">
                      &ldquo;{dueApp.reminder_note}&rdquo;
                    </p>
                  )}
                </div>
                <div className="flex flex-col gap-1.5 flex-shrink-0">
                  <Button
                    size="sm"
                    variant="outline"
                    className="h-7 text-xs border-gray-200 hover:bg-gray-50"
                    onClick={() => handleSelectAppForDetail(dueApp)}
                  >
                    View
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    className="h-7 text-xs text-gray-500 hover:text-gray-900"
                    onClick={() => handleDismissReminder(dueApp)}
                  >
                    Dismiss
                  </Button>
                </div>
              </div>
            ))}

            {reminders.upcoming_reminders.map((upApp) => (
              <div
                key={`up-${upApp.id}`}
                className="bg-white p-3.5 rounded-xl border border-amber-100 flex items-start justify-between gap-3 shadow-xs"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-amber-700 uppercase tracking-wider">
                      Upcoming
                    </span>
                    <span className="text-xs text-gray-400">•</span>
                    <span className="text-xs text-gray-600 font-medium">
                      {formatDateTime(upApp.reminder_at)}
                    </span>
                  </div>
                  <h4 className="font-semibold text-gray-900 text-sm">
                    {upApp.opportunity?.title} at {upApp.opportunity?.company_name}
                  </h4>
                  {upApp.reminder_note && (
                    <p className="text-xs text-gray-600 bg-gray-50 px-2 py-1 rounded border border-gray-100">
                      &ldquo;{upApp.reminder_note}&rdquo;
                    </p>
                  )}
                </div>
                <div className="flex flex-col gap-1.5 flex-shrink-0">
                  <Button
                    size="sm"
                    variant="outline"
                    className="h-7 text-xs border-gray-200 hover:bg-gray-50"
                    onClick={() => handleSelectAppForDetail(upApp)}
                  >
                    View
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    className="h-7 text-xs text-gray-500 hover:text-gray-900"
                    onClick={() => handleDismissReminder(upApp)}
                  >
                    Dismiss
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Analytics Summary Cards */}
      {analytics && (
        <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
          <Card className="border-gray-100 shadow-sm bg-white">
            <CardHeader className="p-4 pb-2">
              <CardTitle className="text-xs font-semibold text-gray-500 uppercase tracking-wider flex items-center justify-between">
                <span>Total Tracked</span>
                <Layers className="h-4 w-4 text-gray-400" />
              </CardTitle>
            </CardHeader>
            <CardContent className="p-4 pt-0">
              <div className="text-2xl font-bold text-gray-900">
                {analytics.total_tracked}
              </div>
              <p className="text-xs text-muted-foreground mt-0.5">
                Saved & submitted
              </p>
            </CardContent>
          </Card>

          <Card className="border-gray-100 shadow-sm bg-white">
            <CardHeader className="p-4 pb-2">
              <CardTitle className="text-xs font-semibold text-blue-600 uppercase tracking-wider flex items-center justify-between">
                <span>Submitted</span>
                <CheckCircle2 className="h-4 w-4 text-blue-500" />
              </CardTitle>
            </CardHeader>
            <CardContent className="p-4 pt-0">
              <div className="text-2xl font-bold text-blue-700">
                {analytics.total_submitted}
              </div>
              <p className="text-xs text-muted-foreground mt-0.5">
                Applied to employers
              </p>
            </CardContent>
          </Card>

          <Card className="border-gray-100 shadow-sm bg-white">
            <CardHeader className="p-4 pb-2">
              <CardTitle className="text-xs font-semibold text-amber-700 uppercase tracking-wider flex items-center justify-between">
                <span>In Progress</span>
                <Clock className="h-4 w-4 text-amber-500" />
              </CardTitle>
            </CardHeader>
            <CardContent className="p-4 pt-0">
              <div className="text-2xl font-bold text-amber-800">
                {analytics.active_in_progress}
              </div>
              <p className="text-xs text-muted-foreground mt-0.5">
                Assessments & interviews
              </p>
            </CardContent>
          </Card>

          <Card className="border-gray-100 shadow-sm bg-white">
            <CardHeader className="p-4 pb-2">
              <CardTitle className="text-xs font-semibold text-emerald-700 uppercase tracking-wider flex items-center justify-between">
                <span>Offers</span>
                <Sparkles className="h-4 w-4 text-emerald-600" />
              </CardTitle>
            </CardHeader>
            <CardContent className="p-4 pt-0">
              <div className="text-2xl font-bold text-emerald-800">
                {analytics.by_status?.Offer || 0}
              </div>
              <p className="text-xs text-muted-foreground mt-0.5">
                Received job offers
              </p>
            </CardContent>
          </Card>

          <Card className="border-gray-100 shadow-sm bg-white col-span-2 lg:col-span-1">
            <CardHeader className="p-4 pb-2">
              <CardTitle className="text-xs font-semibold text-purple-700 uppercase tracking-wider flex items-center justify-between">
                <span>Conversion</span>
                <BarChart3Icon className="h-4 w-4 text-purple-500" />
              </CardTitle>
            </CardHeader>
            <CardContent className="p-4 pt-0">
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-bold text-purple-800">
                  {analytics.interview_rate_percent}%
                </span>
                <span className="text-xs text-gray-500">interview rate</span>
              </div>
              <p
                className="text-[11px] text-gray-500 mt-1 line-clamp-2"
                title={analytics.sample_size_note}
              >
                {analytics.sample_size_note}
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Filter and Search Controls */}
      <div className="bg-white p-4 rounded-2xl border border-gray-100 shadow-sm space-y-3">
        <div className="flex flex-col md:flex-row gap-3 items-stretch md:items-center justify-between">
          {/* Search Box */}
          <div className="relative flex-1">
            <Search className="absolute left-3.5 top-3 h-4 w-4 text-gray-400" />
            <Input
              id={searchInputId}
              type="text"
              placeholder="Search by job title, company name, or personal notes..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9 bg-[#F6FAF7]/50 border-gray-200 focus-visible:ring-[#1B5E3B]"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery("")}
                className="absolute right-3 top-3 text-gray-400 hover:text-gray-600"
                aria-label="Clear search"
              >
                <X className="h-4 w-4" />
              </button>
            )}
          </div>

          {/* Sort selector */}
          <div className="flex items-center gap-2">
            <span className="text-xs font-medium text-gray-500 whitespace-nowrap">
              Sort by:
            </span>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="text-xs font-medium bg-gray-50 border border-gray-200 rounded-lg px-2.5 py-2 text-gray-700 focus:outline-none focus:ring-1 focus:ring-[#1B5E3B]"
            >
              <option value="updated_desc">Recently Updated</option>
              <option value="applied_desc">Applied Date (Newest)</option>
              <option value="deadline_asc">Deadline (Soonest)</option>
              <option value="company_asc">Company (A-Z)</option>
            </select>
          </div>
        </div>

        {/* Status Filter Tabs */}
        <div className="flex flex-wrap items-center gap-1.5 pt-1 border-t border-gray-50">
          <button
            onClick={() => setStatusFilter("ALL")}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              statusFilter === "ALL"
                ? "bg-[#1B5E3B] text-white shadow-xs"
                : "bg-gray-100 text-gray-600 hover:bg-gray-200/80"
            }`}
          >
            All ({applications.length})
          </button>

          {(
            [
              "Saved",
              "Applied",
              "Assessment",
              "Interview",
              "Offer",
              "Rejected",
              "Withdrawn",
            ] as ApplicationStatus[]
          ).map((st) => {
            const count = analytics?.by_status?.[st] || 0;
            const isSelected = statusFilter === st;
            return (
              <button
                key={st}
                onClick={() => setStatusFilter(st)}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all ${
                  isSelected
                    ? "bg-[#14261C] text-white shadow-xs"
                    : "bg-gray-100 text-gray-600 hover:bg-gray-200/80"
                }`}
              >
                <span
                  className={`w-2 h-2 rounded-full ${STATUS_CONFIG[st].dotClass}`}
                />
                <span>{st}</span>
                <span className="text-[10px] opacity-75 font-normal">
                  ({count})
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Applications List */}
      {filteredApplications.length === 0 ? (
        <div className="bg-white rounded-2xl border border-gray-100 p-12 text-center shadow-sm space-y-4">
          <div className="w-16 h-16 rounded-full bg-[#F6FAF7] text-[#1B5E3B] mx-auto flex items-center justify-center">
            <Briefcase className="h-8 w-8 opacity-60" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-gray-900">
              {applications.length === 0
                ? "No applications tracked yet"
                : "No applications match your filter"}
            </h3>
            <p className="text-sm text-gray-500 max-w-md mx-auto mt-1">
              {applications.length === 0
                ? "Start by tracking active jobs or saving opportunities to follow up on later. Tracking allows you to manage deadlines, reminders, and interview progress."
                : `No tracked records found for status "${statusFilter}"${
                    searchQuery ? ` and query "${searchQuery}"` : ""
                  }.`}
            </p>
          </div>

          <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
            {applications.length === 0 ? (
              <>
                <Button
                  onClick={handleOpenAddModal}
                  className="bg-[#1B5E3B] hover:bg-[#2E7D4F] text-white font-semibold"
                >
                  <Plus className="h-4 w-4 mr-1.5" />
                  Track First Application
                </Button>
                <Link href="/opportunities">
                  <Button variant="outline" className="border-gray-200 text-gray-700">
                    Discover Opportunities
                  </Button>
                </Link>
                <Link href="/saved-opportunities">
                  <Button variant="outline" className="border-gray-200 text-gray-700">
                    View Saved Jobs
                  </Button>
                </Link>
              </>
            ) : (
              <Button
                variant="outline"
                onClick={() => {
                  setStatusFilter("ALL");
                  setSearchQuery("");
                }}
                className="border-gray-200"
              >
                Clear Filters
              </Button>
            )}
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {filteredApplications.map((app) => {
            const opp = app.opportunity;
            const statusMeta = STATUS_CONFIG[app.status] || STATUS_CONFIG.Applied;
            const deadlineDays = app.deadline ? getDaysDiff(app.deadline) : null;
            const reminderDays = app.reminder_at ? getDaysDiff(app.reminder_at) : null;

            return (
              <div
                key={app.id}
                className="bg-white rounded-2xl border border-gray-100 p-5 md:p-6 shadow-xs hover:shadow-md transition-shadow flex flex-col md:flex-row gap-5 justify-between items-start"
              >
                {/* Left Section: Company Logo & Details */}
                <div className="flex gap-4 items-start flex-1 min-w-0">
                  <div className="flex-shrink-0">
                    {opp?.company_logo_url ? (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img
                        src={opp.company_logo_url}
                        alt={`${opp.company_name} logo`}
                        className="w-12 h-12 object-contain rounded-xl border border-gray-100 p-1 bg-white"
                      />
                    ) : (
                      <div className="w-12 h-12 bg-[#F6FAF7] text-[#1B5E3B] flex items-center justify-center rounded-xl border border-gray-100 font-bold text-sm">
                        {opp?.company_name ? opp.company_name.charAt(0) : "J"}
                      </div>
                    )}
                  </div>

                  <div className="space-y-2 flex-1 min-w-0">
                    <div>
                      <div className="flex flex-wrap items-center gap-2 mb-1">
                        <Link
                          href={`/opportunities/${opp?.id}`}
                          className="text-lg font-bold text-gray-900 hover:text-[#1B5E3B] transition-colors truncate"
                        >
                          {opp?.title || "Opportunity Details"}
                        </Link>

                        <Badge
                          variant="outline"
                          className={`${statusMeta.badgeClass} font-semibold text-xs py-0.5 px-2`}
                        >
                          <span
                            className={`w-1.5 h-1.5 rounded-full ${statusMeta.dotClass} mr-1.5`}
                          />
                          {app.status}
                        </Badge>

                        {app.status === "Saved" && (
                          <span className="text-[11px] text-gray-500 italic">
                            (Not yet applied)
                          </span>
                        )}
                      </div>

                      <div className="flex flex-wrap items-center gap-3 text-xs text-gray-500 font-medium">
                        <span className="font-semibold text-gray-700">
                          {opp?.company_name}
                        </span>
                        {opp?.work_model && (
                          <>
                            <span>•</span>
                            <span>{opp.work_model}</span>
                          </>
                        )}
                        {opp?.opportunity_type && (
                          <>
                            <span>•</span>
                            <span>{opp.opportunity_type}</span>
                          </>
                        )}
                        {opp?.locations && opp.locations.length > 0 && (
                          <>
                            <span>•</span>
                            <span className="flex items-center gap-1">
                              <MapPin className="h-3 w-3 opacity-60" />
                              {opp.locations.join(", ")}
                            </span>
                          </>
                        )}
                      </div>
                    </div>

                    {/* Metadata chips: Applied date, Deadline, Reminders */}
                    <div className="flex flex-wrap items-center gap-2 pt-1 text-xs">
                      {app.applied_at && (
                        <div className="flex items-center gap-1 bg-blue-50/70 text-blue-700 px-2 py-1 rounded-md border border-blue-100/70">
                          <CheckCircle2 className="h-3.5 w-3.5" />
                          <span>Submitted: {formatDate(app.applied_at)}</span>
                        </div>
                      )}

                      {app.deadline && (
                        <div
                          className={`flex items-center gap-1 px-2 py-1 rounded-md border ${
                            deadlineDays !== null && deadlineDays < 0
                              ? "bg-gray-100 text-gray-600 border-gray-200"
                              : deadlineDays !== null && deadlineDays <= 3
                              ? "bg-rose-50 text-rose-700 border-rose-200 font-semibold"
                              : "bg-gray-50 text-gray-700 border-gray-200"
                          }`}
                        >
                          <Calendar className="h-3.5 w-3.5 opacity-70" />
                          <span>
                            Deadline: {formatDate(app.deadline)}
                            {deadlineDays !== null && (
                              <span className="ml-1 opacity-80">
                                {deadlineDays < 0
                                  ? "(Passed)"
                                  : deadlineDays === 0
                                  ? "(Today)"
                                  : `(${deadlineDays}d left)`}
                              </span>
                            )}
                          </span>
                        </div>
                      )}

                      {app.reminder_at && (
                        <div
                          className={`flex items-center gap-1 px-2 py-1 rounded-md border ${
                            reminderDays !== null && reminderDays <= 0
                              ? "bg-amber-100 text-amber-900 border-amber-300 font-semibold"
                              : "bg-amber-50 text-amber-800 border-amber-200"
                          }`}
                        >
                          <Bell className="h-3.5 w-3.5 text-amber-600" />
                          <span>
                            Reminder: {formatDateTime(app.reminder_at)}
                            {app.reminder_note && `: "${app.reminder_note}"`}
                          </span>
                        </div>
                      )}
                    </div>

                    {/* Personal Notes preview */}
                    {app.notes && (
                      <div className="text-xs text-gray-600 bg-[#F6FAF7]/80 p-2.5 rounded-xl border border-gray-100/80 mt-2 max-w-2xl">
                        <span className="font-semibold text-gray-700 mr-1.5">
                          Notes:
                        </span>
                        <span className="line-clamp-2">{app.notes}</span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Right Section: Action Controls */}
                <div className="flex flex-col sm:flex-row md:flex-col gap-2 w-full md:w-auto flex-shrink-0 md:items-end">
                  <div className="flex items-center gap-2 w-full sm:w-auto">
                    <Button
                      size="sm"
                      onClick={() => handleSelectAppForDetail(app)}
                      className="flex-1 sm:flex-initial bg-[#1B5E3B] hover:bg-[#2E7D4F] text-white font-semibold text-xs h-8 px-3"
                    >
                      <Pencil className="h-3.5 w-3.5 mr-1" />
                      Manage & History
                    </Button>

                    {opp?.application_url && (
                      <a
                        href={opp.application_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex-1 sm:flex-initial"
                      >
                        <Button
                          size="sm"
                          variant="outline"
                          className="w-full text-xs h-8 px-3 border-gray-200 hover:bg-gray-50 flex items-center gap-1"
                        >
                          <span>Job Link</span>
                          <ExternalLink className="h-3 w-3" />
                        </Button>
                      </a>
                    )}
                  </div>

                  {/* Career Copilot Shortcuts */}
                  <div className="flex flex-wrap items-center gap-1.5 pt-1">
                    <Link
                      href={`/resume-recommendations?opportunity_id=${opp?.id}`}
                      className="text-[11px] font-medium text-[#1B5E3B] bg-[#1B5E3B]/10 hover:bg-[#1B5E3B]/20 px-2 py-0.5 rounded flex items-center gap-1"
                    >
                      <FileCheck className="h-3 w-3" />
                      Tailor Resume
                    </Link>
                    <Link
                      href={`/interview-prep?opportunity_id=${opp?.id}`}
                      className="text-[11px] font-medium text-amber-800 bg-amber-50 hover:bg-amber-100 px-2 py-0.5 rounded flex items-center gap-1"
                    >
                      <BookOpen className="h-3 w-3" />
                      Interview Prep
                    </Link>
                    <Link
                      href={`/cover-letter?opportunity_id=${opp?.id}`}
                      className="text-[11px] font-medium text-blue-700 bg-blue-50 hover:bg-blue-100 px-2 py-0.5 rounded flex items-center gap-1"
                    >
                      <FileEdit className="h-3 w-3" />
                      Cover Letter
                    </Link>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Modal: Application Detail & Edit Flow */}
      {selectedApp && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-xs animate-in fade-in">
          <div
            className="bg-white rounded-2xl shadow-xl border border-gray-100 max-w-2xl w-full max-h-[90vh] flex flex-col overflow-hidden"
            role="dialog"
            aria-modal="true"
            aria-labelledby="manage-app-title"
          >
            {/* Modal Header */}
            <div className="p-6 border-b border-gray-100 flex items-start justify-between bg-[#F6FAF7]/50">
              <div>
                <h3 id="manage-app-title" className="text-xl font-bold text-gray-900">
                  Manage Application
                </h3>
                <p className="text-xs text-gray-500 mt-0.5">
                  {selectedApp.opportunity?.title} • {selectedApp.opportunity?.company_name}
                </p>
              </div>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setSelectedApp(null)}
                className="rounded-full text-gray-400 hover:text-gray-700"
              >
                <X className="h-5 w-5" />
              </Button>
            </div>

            {/* Modal Body */}
            <form
              onSubmit={handleUpdateApplication}
              className="p-6 space-y-5 overflow-y-auto flex-1"
            >
              {/* Status Section */}
              <div className="space-y-2">
                <label className="text-xs font-bold text-gray-700 uppercase tracking-wider block">
                  Application Status
                </label>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                  {(
                    [
                      "Saved",
                      "Applied",
                      "Assessment",
                      "Interview",
                      "Offer",
                      "Rejected",
                      "Withdrawn",
                    ] as ApplicationStatus[]
                  ).map((st) => (
                    <button
                      type="button"
                      key={st}
                      onClick={() => setEditStatus(st)}
                      className={`px-3 py-2 rounded-xl text-xs font-semibold border text-center transition-all ${
                        editStatus === st
                          ? "bg-[#1B5E3B] text-white border-[#1B5E3B] shadow-xs"
                          : "bg-white text-gray-700 border-gray-200 hover:bg-gray-50"
                      }`}
                    >
                      {st}
                    </button>
                  ))}
                </div>
              </div>

              {/* Status change note (Audit Trail) */}
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-gray-700 flex items-center justify-between">
                  <span>Status Update Note / Milestone (Optional)</span>
                  <span className="text-[11px] text-gray-400">
                    Logged to activity history
                  </span>
                </label>
                <Input
                  placeholder="e.g. Received recruiter email, completed screening, invited for final round..."
                  value={editStatusNote}
                  onChange={(e) => setEditStatusNote(e.target.value)}
                  className="text-xs"
                />
              </div>

              {/* Dates Row: Applied Date & Deadline */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-gray-700 flex items-center gap-1.5">
                    <CheckCircle2 className="h-3.5 w-3.5 text-blue-600" />
                    <span>Submission Date</span>
                  </label>
                  <Input
                    type="date"
                    value={editAppliedAt}
                    onChange={(e) => setEditAppliedAt(e.target.value)}
                    className="text-xs"
                  />
                  <p className="text-[11px] text-gray-400">
                    When you submitted your application.
                  </p>
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-gray-700 flex items-center gap-1.5">
                    <Calendar className="h-3.5 w-3.5 text-gray-600" />
                    <span>Application Deadline</span>
                  </label>
                  <Input
                    type="date"
                    value={editDeadline}
                    onChange={(e) => setEditDeadline(e.target.value)}
                    className="text-xs"
                  />
                  <p className="text-[11px] text-gray-400">
                    Official job deadline or offer expiry.
                  </p>
                </div>
              </div>

              {/* Reminder Section */}
              <div className="p-4 bg-amber-50/50 rounded-xl border border-amber-200/60 space-y-3">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-bold text-amber-900 uppercase tracking-wider flex items-center gap-1.5">
                    <Bell className="h-3.5 w-3.5 text-amber-600" />
                    <span>Personal In-App Reminder</span>
                  </label>
                  {editReminderAt && (
                    <button
                      type="button"
                      onClick={() => {
                        setEditReminderAt("");
                        setEditReminderNote("");
                      }}
                      className="text-[11px] text-rose-600 hover:underline"
                    >
                      Clear Reminder
                    </button>
                  )}
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="text-[11px] font-medium text-gray-600 block mb-1">
                      Reminder Date & Time
                    </label>
                    <Input
                      type="datetime-local"
                      value={editReminderAt}
                      onChange={(e) => setEditReminderAt(e.target.value)}
                      className="text-xs bg-white"
                    />
                  </div>
                  <div>
                    <label className="text-[11px] font-medium text-gray-600 block mb-1">
                      Reminder Note
                    </label>
                    <Input
                      placeholder="e.g. Follow up with HR, review portfolio..."
                      value={editReminderNote}
                      onChange={(e) => setEditReminderNote(e.target.value)}
                      className="text-xs bg-white"
                    />
                  </div>
                </div>
              </div>

              {/* Personal Notes */}
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-gray-700 flex items-center justify-between">
                  <span>Personal Notes & Next Steps</span>
                  <span className="text-[11px] text-gray-400">Private to you</span>
                </label>
                <Textarea
                  rows={3}
                  placeholder="Record interview thoughts, recruiter names, questions to ask, salary discussions..."
                  value={editNotes}
                  onChange={(e) => setEditNotes(e.target.value)}
                  className="text-xs resize-none"
                />
              </div>

              {/* Application History / Audit Log */}
              {selectedApp.history && selectedApp.history.length > 0 && (
                <div className="space-y-2 pt-2 border-t border-gray-100">
                  <label className="text-xs font-bold text-gray-700 uppercase tracking-wider flex items-center gap-1.5">
                    <History className="h-3.5 w-3.5 text-gray-500" />
                    <span>Activity History & Milestones</span>
                  </label>
                  <div className="space-y-2 max-h-40 overflow-y-auto pr-1">
                    {selectedApp.history.map((hist) => (
                      <div
                        key={hist.id}
                        className="p-2.5 rounded-lg bg-gray-50 border border-gray-100 text-xs flex items-start justify-between gap-3"
                      >
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-semibold text-gray-900">
                              {hist.from_status
                                ? `${hist.from_status} → ${hist.to_status}`
                                : `Tracked as ${hist.to_status}`}
                            </span>
                            <span className="text-gray-400">•</span>
                            <span className="text-gray-500 text-[11px]">
                              {formatDateTime(hist.created_at)}
                            </span>
                          </div>
                          {hist.note && (
                            <p className="text-gray-600 mt-1 italic">
                              &ldquo;{hist.note}&rdquo;
                            </p>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Actions Footer */}
              <div className="pt-4 border-t border-gray-100 flex items-center justify-between gap-3">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setDeleteConfirmAppId(selectedApp.id)}
                  className="border-rose-200 text-rose-700 hover:bg-rose-50 flex items-center gap-1.5 text-xs"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                  <span>Remove Application</span>
                </Button>

                <div className="flex items-center gap-2">
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => setSelectedApp(null)}
                    className="text-xs"
                  >
                    Cancel
                  </Button>
                  <Button
                    type="submit"
                    size="sm"
                    disabled={modalSaving}
                    className="bg-[#1B5E3B] hover:bg-[#2E7D4F] text-white font-semibold text-xs"
                  >
                    {modalSaving ? "Saving..." : "Save Changes"}
                  </Button>
                </div>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Track New Application */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-xs animate-in fade-in">
          <div
            className="bg-white rounded-2xl shadow-xl border border-gray-100 max-w-xl w-full max-h-[90vh] flex flex-col overflow-hidden"
            role="dialog"
            aria-modal="true"
            aria-labelledby="track-new-app-title"
          >
            <div className="p-6 border-b border-gray-100 flex items-start justify-between bg-[#F6FAF7]/50">
              <div>
                <h3 id="track-new-app-title" className="text-xl font-bold text-gray-900">
                  Track an Opportunity
                </h3>
                <p className="text-xs text-gray-500 mt-0.5">
                  Link an opportunity to your tracking pipeline. Saving keeps it on your radar; marking as Applied tracks submitted applications.
                </p>
              </div>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setShowAddModal(false)}
                className="rounded-full text-gray-400 hover:text-gray-700"
              >
                <X className="h-5 w-5" />
              </Button>
            </div>

            <form
              onSubmit={handleCreateApplication}
              className="p-6 space-y-4 overflow-y-auto flex-1"
            >
              {/* Opportunity Selector */}
              <div className="space-y-1.5">
                <label className="text-xs font-bold text-gray-700 uppercase tracking-wider block">
                  Select Opportunity
                </label>
                {loadingSaved ? (
                  <p className="text-xs text-gray-500">Loading your saved opportunities...</p>
                ) : savedOpportunities.length > 0 ? (
                  <select
                    value={newOpportunityId}
                    onChange={(e) => {
                      const id = e.target.value;
                      setNewOpportunityId(id);
                      const chosen = savedOpportunities.find((o) => o.id === id);
                      if (chosen?.deadline) {
                        setNewDeadline(chosen.deadline.slice(0, 10));
                      }
                    }}
                    className="w-full text-xs bg-white border border-gray-200 rounded-xl p-2.5 text-gray-800 focus:outline-none focus:ring-1 focus:ring-[#1B5E3B]"
                    required
                  >
                    <option value="">-- Choose from your saved opportunities --</option>
                    {savedOpportunities.map((opp) => (
                      <option key={opp.id} value={opp.id}>
                        {opp.title} ({opp.company_name})
                      </option>
                    ))}
                  </select>
                ) : (
                  <div className="p-3 bg-amber-50 rounded-xl border border-amber-200 text-xs text-amber-800 space-y-2">
                    <p>
                      You don&apos;t have any saved opportunities yet. You can discover opportunities or paste an Opportunity ID below.
                    </p>
                    <Link href="/opportunities">
                      <Button
                        type="button"
                        size="sm"
                        variant="outline"
                        className="text-xs bg-white border-amber-300 text-amber-900"
                      >
                        Browse Published Opportunities
                      </Button>
                    </Link>
                  </div>
                )}

                {/* Direct ID input if needed */}
                <div className="pt-1">
                  <Input
                    placeholder="Or enter Opportunity UUID directly..."
                    value={newOpportunityId}
                    onChange={(e) => setNewOpportunityId(e.target.value.trim())}
                    className="text-xs"
                  />
                </div>
              </div>

              {/* Initial Status */}
              <div className="space-y-1.5">
                <label className="text-xs font-bold text-gray-700 uppercase tracking-wider block">
                  Initial Pipeline Status
                </label>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => {
                      setNewStatus("Applied");
                      if (!newAppliedAt) {
                        setNewAppliedAt(new Date().toISOString().slice(0, 10));
                      }
                    }}
                    className={`p-3 rounded-xl border text-left transition-all ${
                      newStatus === "Applied"
                        ? "bg-blue-50 border-blue-400 text-blue-900 ring-1 ring-blue-400"
                        : "bg-white border-gray-200 text-gray-700 hover:bg-gray-50"
                    }`}
                  >
                    <div className="font-bold text-xs flex items-center gap-1.5">
                      <CheckCircle2 className="h-4 w-4 text-blue-600" />
                      <span>Already Applied</span>
                    </div>
                    <p className="text-[11px] text-gray-500 mt-1">
                      You submitted an application on the company site.
                    </p>
                  </button>

                  <button
                    type="button"
                    onClick={() => {
                      setNewStatus("Saved");
                      setNewAppliedAt("");
                    }}
                    className={`p-3 rounded-xl border text-left transition-all ${
                      newStatus === "Saved"
                        ? "bg-slate-50 border-slate-400 text-slate-900 ring-1 ring-slate-400"
                        : "bg-white border-gray-200 text-gray-700 hover:bg-gray-50"
                    }`}
                  >
                    <div className="font-bold text-xs flex items-center gap-1.5">
                      <Briefcase className="h-4 w-4 text-slate-600" />
                      <span>Track as Saved</span>
                    </div>
                    <p className="text-[11px] text-gray-500 mt-1">
                      Keep in tracker to prepare & apply later.
                    </p>
                  </button>
                </div>
              </div>

              {/* Dates */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {newStatus !== "Saved" && (
                  <div className="space-y-1">
                    <label className="text-xs font-semibold text-gray-700">
                      Applied Date
                    </label>
                    <Input
                      type="date"
                      value={newAppliedAt}
                      onChange={(e) => setNewAppliedAt(e.target.value)}
                      className="text-xs"
                    />
                  </div>
                )}
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-gray-700">
                    Application Deadline
                  </label>
                  <Input
                    type="date"
                    value={newDeadline}
                    onChange={(e) => setNewDeadline(e.target.value)}
                    className="text-xs"
                  />
                </div>
              </div>

              {/* Reminder */}
              <div className="p-3 bg-amber-50/50 rounded-xl border border-amber-200/60 space-y-2">
                <label className="text-xs font-bold text-amber-900 uppercase tracking-wider flex items-center gap-1.5">
                  <Bell className="h-3.5 w-3.5 text-amber-600" />
                  <span>Set Follow-up Reminder (Optional)</span>
                </label>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  <Input
                    type="datetime-local"
                    value={newReminderAt}
                    onChange={(e) => setNewReminderAt(e.target.value)}
                    className="text-xs bg-white"
                  />
                  <Input
                    placeholder="e.g. Check recruiter reply..."
                    value={newReminderNote}
                    onChange={(e) => setNewReminderNote(e.target.value)}
                    className="text-xs bg-white"
                  />
                </div>
              </div>

              {/* Notes */}
              <div className="space-y-1">
                <label className="text-xs font-semibold text-gray-700">
                  Initial Notes
                </label>
                <Textarea
                  rows={2}
                  placeholder="Personal notes or reminders..."
                  value={newNotes}
                  onChange={(e) => setNewNotes(e.target.value)}
                  className="text-xs resize-none"
                />
              </div>

              {/* Submit Buttons */}
              <div className="pt-3 border-t border-gray-100 flex items-center justify-end gap-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setShowAddModal(false)}
                  className="text-xs"
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  size="sm"
                  disabled={addSaving || !newOpportunityId}
                  className="bg-[#1B5E3B] hover:bg-[#2E7D4F] text-white font-semibold text-xs"
                >
                  {addSaving ? "Adding..." : "Add to Tracker"}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Confirmation Dialog */}
      {deleteConfirmAppId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-xs animate-in fade-in">
          <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-6 max-w-sm w-full space-y-4">
            <div className="w-12 h-12 rounded-full bg-rose-50 text-rose-600 flex items-center justify-center mx-auto">
              <Trash2 className="h-6 w-6" />
            </div>
            <div className="text-center space-y-1">
              <h4 className="text-lg font-bold text-gray-900">
                Remove from Tracker?
              </h4>
              <p className="text-xs text-gray-500">
                This will delete your tracking record and its milestone history. The original opportunity will not be deleted.
              </p>
            </div>
            <div className="flex items-center gap-2 pt-2">
              <Button
                variant="outline"
                className="flex-1 text-xs"
                onClick={() => setDeleteConfirmAppId(null)}
              >
                Cancel
              </Button>
              <Button
                className="flex-1 text-xs bg-rose-600 hover:bg-rose-700 text-white font-semibold"
                onClick={() => handleDeleteApplication(deleteConfirmAppId)}
              >
                Yes, Remove
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function BarChart3Icon(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M3 3v18h18" />
      <path d="M18 17V9" />
      <path d="M13 17V5" />
      <path d="M8 17v-3" />
    </svg>
  );
}
