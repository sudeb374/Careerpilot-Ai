"use client";

import { useEffect, useState, useCallback } from "react";
import { createClient } from "@/lib/supabase/client";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Loader2, Edit2 } from "lucide-react";

export function AboutSection() {
  const [about, setAbout] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const fetchProfile = useCallback(async () => {
    try {
      const supabase = createClient();
      const { data: { session } } = await supabase.auth.getSession();
      
      if (!session) return;

      const res = await fetch(`${API_URL}/api/v1/profile`, {
        headers: { "Authorization": `Bearer ${session.access_token}` }
      });

      if (res.ok) {
        const data = await res.json();
        setAbout(data.about || null);
      }
    } catch (err) {
      console.error("Failed to load about section", err);
    } finally {
      setIsLoading(false);
    }
  }, [API_URL]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchProfile();
  }, [fetchProfile]);

  const handleEdit = () => {
    setEditValue(about || "");
    setError(null);
    setSuccess(null);
    setIsEditing(true);
  };

  const handleCancel = () => {
    setIsEditing(false);
    setError(null);
  };

  const handleSave = async () => {
    setError(null);
    setSuccess(null);
    setIsSaving(true);
    
    try {
      const supabase = createClient();
      const { data: { session } } = await supabase.auth.getSession();
      
      if (!session) {
        setError("Session expired. Please log in again.");
        setIsSaving(false);
        return;
      }

      const trimmedValue = editValue.trim() || null;

      const res = await fetch(`${API_URL}/api/v1/profile`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${session.access_token}`
        },
        body: JSON.stringify({ about: trimmedValue })
      });

      if (res.ok) {
        setAbout(trimmedValue);
        setSuccess("About section updated successfully.");
        setIsEditing(false);
      } else {
        const errData = await res.json().catch(() => ({}));
        setError(errData.detail || "Failed to update about section.");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "An unexpected error occurred.");
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <Card className="w-full h-48 flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </Card>
    );
  }

  return (
    <Card className="w-full border-border">
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle>About</CardTitle>
          <CardDescription>A professional summary of your background and goals.</CardDescription>
        </div>
        {!isEditing && (
          <Button variant="outline" size="sm" onClick={handleEdit}>
            <Edit2 className="mr-2 h-4 w-4" /> Edit
          </Button>
        )}
      </CardHeader>
      
      <CardContent>
        {error && (
          <div className="rounded-md bg-destructive/15 p-3 text-sm text-destructive mb-4">
            {error}
          </div>
        )}
        {success && !isEditing && (
          <div className="rounded-md bg-emerald-500/15 p-3 text-sm text-emerald-600 dark:text-emerald-400 mb-4">
            {success}
          </div>
        )}

        {isEditing ? (
          <div className="space-y-4">
            <Textarea
              value={editValue}
              onChange={(e) => setEditValue(e.target.value)}
              placeholder="e.g. I am a passionate software engineer..."
              className="min-h-[150px] resize-y"
              disabled={isSaving}
              maxLength={2000}
            />
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>{editValue.length} / 2000 characters</span>
            </div>
            <div className="flex justify-end space-x-2 pt-2">
              <Button variant="outline" onClick={handleCancel} disabled={isSaving}>
                Cancel
              </Button>
              <Button onClick={handleSave} disabled={isSaving} className="bg-primary text-primary-foreground">
                {isSaving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                {isSaving ? "Saving..." : "Save Changes"}
              </Button>
            </div>
          </div>
        ) : (
          <div>
            {!about ? (
              <div className="rounded-xl border border-dashed border-border p-8 text-center">
                <p className="text-muted-foreground mb-4">Add a professional summary to tell employers about yourself.</p>
                <Button variant="outline" onClick={handleEdit}>
                  Add About
                </Button>
              </div>
            ) : (
              <div className="whitespace-pre-wrap text-sm text-foreground">
                {about}
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
