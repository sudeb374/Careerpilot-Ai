"use client";

import { useEffect, useState } from "react";
import { createClient } from "@/lib/supabase/client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2 } from "lucide-react";

export function ProfileForm() {
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [isNewProfile, setIsNewProfile] = useState(true);

  const [formData, setFormData] = useState({
    full_name: "",
    headline: "",
    location: "",
  });

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  useEffect(() => {
    async function loadProfile() {
      try {
        const supabase = createClient();
        const { data: { session } } = await supabase.auth.getSession();
        
        if (!session) {
          setError("You must be logged in to view your profile.");
          setIsLoading(false);
          return;
        }

        const res = await fetch(`${API_URL}/api/v1/profile`, {
          headers: {
            "Authorization": `Bearer ${session.access_token}`
          }
        });

        if (res.ok) {
          const profile = await res.json();
          setFormData({
            full_name: profile.full_name || "",
            headline: profile.headline || "",
            location: profile.location || "",
          });
          setIsNewProfile(false);
        } else if (res.status === 404) {
          setIsNewProfile(true);
        } else {
          setError("Failed to load profile data.");
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "An unexpected error occurred.");
      } finally {
        setIsLoading(false);
      }
    }

    loadProfile();
  }, [API_URL]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    if (!formData.full_name.trim()) {
      setError("Full Name is required.");
      return;
    }

    setIsSaving(true);

    try {
      const supabase = createClient();
      const { data: { session } } = await supabase.auth.getSession();
      
      if (!session) {
        setError("Your session has expired. Please log in again.");
        setIsSaving(false);
        return;
      }

      const method = isNewProfile ? "POST" : "PATCH";
      
      const res = await fetch(`${API_URL}/api/v1/profile`, {
        method,
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${session.access_token}`
        },
        body: JSON.stringify({
          full_name: formData.full_name,
          headline: formData.headline || null,
          location: formData.location || null,
        }),
      });

      if (res.ok) {
        setSuccess("Profile saved successfully!");
        setIsNewProfile(false);
      } else {
        const errData = await res.json().catch(() => ({}));
        setError(errData.detail || "Failed to save profile.");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "An unexpected error occurred while saving.");
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex h-48 items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>Basic Information</CardTitle>
        <CardDescription>
          Update your main profile details. This information will be visible to potential connections.
        </CardDescription>
      </CardHeader>
      <form onSubmit={handleSubmit}>
        <CardContent className="space-y-6">
          {error && (
            <div className="rounded-md bg-destructive/15 p-3 text-sm text-destructive">
              {error}
            </div>
          )}
          {success && (
            <div className="rounded-md bg-emerald-500/15 p-3 text-sm text-emerald-600 dark:text-emerald-400">
              {success}
            </div>
          )}

          <div className="space-y-2">
            <Label htmlFor="full_name">Full Name <span className="text-destructive">*</span></Label>
            <Input
              id="full_name"
              name="full_name"
              placeholder="e.g. Jane Doe"
              value={formData.full_name}
              onChange={handleChange}
              disabled={isSaving}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="headline">Headline</Label>
            <Input
              id="headline"
              name="headline"
              placeholder="e.g. Computer Science Student at XYZ University"
              value={formData.headline}
              onChange={handleChange}
              disabled={isSaving}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="location">Location</Label>
            <Input
              id="location"
              name="location"
              placeholder="e.g. San Francisco, CA"
              value={formData.location}
              onChange={handleChange}
              disabled={isSaving}
            />
          </div>
        </CardContent>
        <CardFooter className="flex justify-end">
          <Button type="submit" disabled={isSaving} className="bg-saffron text-saffron-foreground hover:bg-saffron/90">
            {isSaving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            {isSaving ? "Saving..." : "Save Profile"}
          </Button>
        </CardFooter>
      </form>
    </Card>
  );
}
