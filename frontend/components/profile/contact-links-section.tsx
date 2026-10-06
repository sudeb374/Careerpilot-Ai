"use client";

import { useEffect, useState, useCallback } from "react";
import { createClient } from "@/lib/supabase/client";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Loader2, Edit2, Phone, Briefcase, GitBranch, Globe, ExternalLink } from "lucide-react";

interface ContactLinks {
  phone: string | null;
  linkedin_url: string | null;
  github_url: string | null;
  portfolio_url: string | null;
}

export function ContactLinksSection() {
  const [data, setData] = useState<ContactLinks>({
    phone: null,
    linkedin_url: null,
    github_url: null,
    portfolio_url: null,
  });
  const [isLoading, setIsLoading] = useState(true);
  
  const [isEditing, setIsEditing] = useState(false);
  const [editValues, setEditValues] = useState<ContactLinks>({
    phone: "",
    linkedin_url: "",
    github_url: "",
    portfolio_url: "",
  });
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
        const profile = await res.json();
        setData({
          phone: profile.phone || null,
          linkedin_url: profile.linkedin_url || null,
          github_url: profile.github_url || null,
          portfolio_url: profile.portfolio_url || null,
        });
      }
    } catch (err) {
      console.error("Failed to load contact links", err);
    } finally {
      setIsLoading(false);
    }
  }, [API_URL]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchProfile();
  }, [fetchProfile]);

  const handleEdit = () => {
    setEditValues({
      phone: data.phone || "",
      linkedin_url: data.linkedin_url || "",
      github_url: data.github_url || "",
      portfolio_url: data.portfolio_url || "",
    });
    setError(null);
    setSuccess(null);
    setIsEditing(true);
  };

  const handleCancel = () => {
    setIsEditing(false);
    setError(null);
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setEditValues((prev) => ({ ...prev, [name]: value }));
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
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

      const payload = {
        phone: (editValues.phone || "").trim() || null,
        linkedin_url: (editValues.linkedin_url || "").trim() || null,
        github_url: (editValues.github_url || "").trim() || null,
        portfolio_url: (editValues.portfolio_url || "").trim() || null,
      };

      const res = await fetch(`${API_URL}/api/v1/profile`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${session.access_token}`
        },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        setData(payload);
        setSuccess("Contact and links updated successfully.");
        setIsEditing(false);
      } else {
        const errData = await res.json().catch(() => ({}));
        setError(errData.detail || "Failed to update contact links.");
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
          <CardTitle>Contact & Professional Links</CardTitle>
          <CardDescription>Phone number and external profiles.</CardDescription>
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
          <form onSubmit={handleSave} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="phone">Phone Number</Label>
                <Input
                  id="phone"
                  name="phone"
                  placeholder="e.g. +91 98765 43210"
                  value={editValues.phone || ""}
                  onChange={handleChange}
                  disabled={isSaving}
                  maxLength={30}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="linkedin_url">LinkedIn URL</Label>
                <Input
                  id="linkedin_url"
                  name="linkedin_url"
                  placeholder="https://linkedin.com/in/username"
                  value={editValues.linkedin_url || ""}
                  onChange={handleChange}
                  disabled={isSaving}
                  maxLength={500}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="github_url">GitHub URL</Label>
                <Input
                  id="github_url"
                  name="github_url"
                  placeholder="https://github.com/username"
                  value={editValues.github_url || ""}
                  onChange={handleChange}
                  disabled={isSaving}
                  maxLength={500}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="portfolio_url">Portfolio URL</Label>
                <Input
                  id="portfolio_url"
                  name="portfolio_url"
                  placeholder="https://yourportfolio.com"
                  value={editValues.portfolio_url || ""}
                  onChange={handleChange}
                  disabled={isSaving}
                  maxLength={500}
                />
              </div>
            </div>

            <div className="flex justify-end space-x-2 pt-4">
              <Button type="button" variant="outline" onClick={handleCancel} disabled={isSaving}>
                Cancel
              </Button>
              <Button type="submit" disabled={isSaving} className="bg-primary text-primary-foreground">
                {isSaving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                {isSaving ? "Saving..." : "Save Changes"}
              </Button>
            </div>
          </form>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-muted rounded-md text-muted-foreground flex-shrink-0">
                <Phone className="h-5 w-5" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground font-medium uppercase tracking-wider">Phone</p>
                {data.phone ? (
                  <p className="text-sm font-medium text-foreground">
                    &#9742; {data.phone}
                  </p>
                ) : (
                  <p className="text-sm text-muted-foreground italic">Not added</p>
                )}
              </div>
            </div>

            <div className="flex items-center space-x-3">
              <div className="p-2 bg-[#0077b5]/10 rounded-md text-[#0077b5] flex-shrink-0">
                <Briefcase className="h-5 w-5" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground font-medium uppercase tracking-wider">LinkedIn</p>
                {data.linkedin_url ? (
                  <a href={data.linkedin_url} target="_blank" rel="noopener noreferrer" className="text-sm font-medium text-primary hover:underline inline-flex items-center">
                    LinkedIn <ExternalLink className="ml-1 h-3 w-3" />
                  </a>
                ) : (
                  <p className="text-sm text-muted-foreground italic">Not added</p>
                )}
              </div>
            </div>

            <div className="flex items-center space-x-3">
              <div className="p-2 bg-foreground/10 rounded-md text-foreground flex-shrink-0">
                <GitBranch className="h-5 w-5" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground font-medium uppercase tracking-wider">GitHub</p>
                {data.github_url ? (
                  <a href={data.github_url} target="_blank" rel="noopener noreferrer" className="text-sm font-medium text-primary hover:underline inline-flex items-center">
                    GitHub <ExternalLink className="ml-1 h-3 w-3" />
                  </a>
                ) : (
                  <p className="text-sm text-muted-foreground italic">Not added</p>
                )}
              </div>
            </div>

            <div className="flex items-center space-x-3">
              <div className="p-2 bg-saffron/10 rounded-md text-saffron-foreground flex-shrink-0">
                <Globe className="h-5 w-5" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground font-medium uppercase tracking-wider">Portfolio</p>
                {data.portfolio_url ? (
                  <a href={data.portfolio_url} target="_blank" rel="noopener noreferrer" className="text-sm font-medium text-primary hover:underline inline-flex items-center">
                    Portfolio <ExternalLink className="ml-1 h-3 w-3" />
                  </a>
                ) : (
                  <p className="text-sm text-muted-foreground italic">Not added</p>
                )}
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
