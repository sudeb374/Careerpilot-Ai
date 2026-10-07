"use client";

import { useState, useEffect } from "react";
import { Bookmark } from "lucide-react";
import { Button } from "@/components/ui/button";
import { createClient } from "@/lib/supabase/client";

interface SaveButtonProps {
  opportunityId: string;
  onSavedChange?: (saved: boolean) => void;
  className?: string;
  variant?: "default" | "outline" | "ghost";
}

export function SaveButton({ opportunityId, onSavedChange, className, variant = "outline" }: SaveButtonProps) {
  const [saved, setSaved] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const supabase = createClient();
  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  useEffect(() => {
    async function checkSavedState() {
      try {
        const { data: { session } } = await supabase.auth.getSession();
        if (!session) {
          setLoading(false);
          return;
        }

        const res = await fetch(`${API_URL}/api/v1/opportunities/${opportunityId}/saved`, {
          headers: {
            Authorization: `Bearer ${session.access_token}`
          }
        });

        if (res.ok) {
          const data = await res.json();
          setSaved(data.saved);
        }
      } catch (err) {
        console.error("Failed to check saved state:", err);
      } finally {
        setLoading(false);
      }
    }

    checkSavedState();
  }, [opportunityId, supabase.auth, API_URL]);

  const toggleSave = async (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (loading) return;
    setError(null);
    setLoading(true);

    try {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) {
        setError("Please sign in to save opportunities.");
        setLoading(false);
        return;
      }

      if (saved) {
        const res = await fetch(`${API_URL}/api/v1/opportunities/${opportunityId}/save`, {
          method: "DELETE",
          headers: {
            Authorization: `Bearer ${session.access_token}`
          }
        });

        if (res.ok || res.status === 404) {
          setSaved(false);
          onSavedChange?.(false);
        } else {
          setError("Failed to unsave.");
        }
      } else {
        const res = await fetch(`${API_URL}/api/v1/opportunities/${opportunityId}/save`, {
          method: "POST",
          headers: {
            Authorization: `Bearer ${session.access_token}`
          }
        });

        if (res.ok || res.status === 409) {
          setSaved(true);
          onSavedChange?.(true);
        } else {
          setError("Failed to save.");
        }
      }
    } catch (err) {
      console.error("Error toggling save state:", err);
      setError("Network error occurred.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Button 
      variant={variant} 
      onClick={toggleSave} 
      disabled={loading}
      className={className}
      title={error || undefined}
    >
      <Bookmark className={`w-4 h-4 mr-2 ${saved ? "fill-[#F59E0B] text-[#F59E0B]" : ""}`} />
      {loading ? "..." : saved ? "Saved" : "Save"}
    </Button>
  );
}
