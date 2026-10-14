"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { CheckCircle2, ChevronDown, Layers, Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { createClient } from "@/lib/supabase/client";

interface TrackApplicationButtonProps {
  opportunityId: string;
  className?: string;
}

export function TrackApplicationButton({
  opportunityId,
  className = "",
}: TrackApplicationButtonProps) {
  const supabase = createClient();
  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [isTracked, setIsTracked] = useState(false);
  const [status, setStatus] = useState<string | null>(null);
  const [showDropdown, setShowDropdown] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    async function checkState() {
      try {
        const {
          data: { session },
        } = await supabase.auth.getSession();
        if (!session) {
          setLoading(false);
          return;
        }

        const res = await fetch(
          `${API_URL}/api/v1/applications/opportunities/${opportunityId}/state`,
          {
            headers: { Authorization: `Bearer ${session.access_token}` },
          }
        );

        if (res.ok) {
          const data = await res.json();
          setIsTracked(data.is_tracked);
          setStatus(data.status);
        }
      } catch (err) {
        console.error("Failed to check application tracking state", err);
      } finally {
        setLoading(false);
      }
    }

    checkState();
  }, [opportunityId, API_URL, supabase.auth]);

  const handleTrack = async (targetStatus: "Saved" | "Applied") => {
    setSubmitting(true);
    setShowDropdown(false);
    setMessage(null);
    try {
      const {
        data: { session },
      } = await supabase.auth.getSession();
      if (!session) return;

      const payload = {
        opportunity_id: opportunityId,
        status: targetStatus,
        applied_at:
          targetStatus === "Applied" ? new Date().toISOString() : null,
        notes: `Tracked directly from opportunity page as ${targetStatus}.`,
      };

      const res = await fetch(`${API_URL}/api/v1/applications`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${session.access_token}`,
        },
        body: JSON.stringify(payload),
      });

      if (res.ok) {
        const app = await res.json();
        setIsTracked(true);
        setStatus(app.status);
        setMessage(`Added to tracker (${targetStatus})`);
        setTimeout(() => setMessage(null), 3000);
      }
    } catch (err) {
      console.error("Failed to track application", err);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <Button
        variant="outline"
        disabled
        className={`h-10 text-xs font-medium border-gray-200 ${className}`}
      >
        <Loader2 className="h-3.5 w-3.5 animate-spin mr-1" />
        Checking Tracker...
      </Button>
    );
  }

  if (isTracked && status) {
    return (
      <div className={`flex items-center gap-2 ${className}`}>
        <Link href="/applications" className="w-full">
          <Button
            variant="outline"
            className="w-full h-10 border-blue-200 bg-blue-50/60 hover:bg-blue-100 text-blue-800 text-xs font-semibold flex items-center justify-between px-3"
          >
            <div className="flex items-center gap-1.5">
              <CheckCircle2 className="h-3.5 w-3.5 text-blue-600" />
              <span>Tracked: {status}</span>
            </div>
            <span className="text-[10px] text-blue-600 underline">Manage</span>
          </Button>
        </Link>
      </div>
    );
  }

  return (
    <div className={`relative ${className}`}>
      {message ? (
        <div className="h-10 px-3 bg-emerald-50 text-emerald-800 rounded-lg border border-emerald-200 flex items-center justify-center text-xs font-semibold animate-in fade-in">
          <CheckCircle2 className="h-3.5 w-3.5 mr-1 text-emerald-600" />
          {message}
        </div>
      ) : (
        <div className="flex w-full">
          <Button
            variant="outline"
            disabled={submitting}
            onClick={() => handleTrack("Applied")}
            className="flex-1 h-10 border-[#1B5E3B]/40 text-[#1B5E3B] hover:bg-[#1B5E3B]/10 font-semibold text-xs rounded-r-none border-r-0 flex items-center justify-center gap-1"
          >
            {submitting ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <Layers className="h-3.5 w-3.5" />
            )}
            <span>Mark as Applied</span>
          </Button>

          <Button
            variant="outline"
            disabled={submitting}
            onClick={() => setShowDropdown(!showDropdown)}
            className="h-10 px-2 border-[#1B5E3B]/40 text-[#1B5E3B] hover:bg-[#1B5E3B]/10 rounded-l-none"
            aria-label="More tracking options"
          >
            <ChevronDown className="h-3.5 w-3.5" />
          </Button>
        </div>
      )}

      {showDropdown && (
        <div className="absolute right-0 top-12 z-20 w-48 bg-white rounded-xl shadow-lg border border-gray-100 p-1.5 animate-in fade-in space-y-1">
          <button
            type="button"
            onClick={() => handleTrack("Applied")}
            className="w-full text-left px-2.5 py-1.5 rounded-lg text-xs font-medium text-gray-700 hover:bg-gray-100 flex items-center gap-2"
          >
            <CheckCircle2 className="h-3.5 w-3.5 text-blue-600" />
            <span>Mark as Applied</span>
          </button>
          <button
            type="button"
            onClick={() => handleTrack("Saved")}
            className="w-full text-left px-2.5 py-1.5 rounded-lg text-xs font-medium text-gray-700 hover:bg-gray-100 flex items-center gap-2"
          >
            <Layers className="h-3.5 w-3.5 text-slate-500" />
            <span>Track as Saved</span>
          </button>
        </div>
      )}
    </div>
  );
}
