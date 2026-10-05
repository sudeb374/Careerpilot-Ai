"use client";

import { useEffect, useState, useCallback } from "react";
import { createClient } from "@/lib/supabase/client";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2, Plus } from "lucide-react";
import { ExperienceForm, type Experience } from "./experience-form";
import { ExperienceCard } from "./experience-card";

export function ExperienceSection() {
  const [experiences, setExperiences] = useState<Experience[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  
  const [showForm, setShowForm] = useState(false);
  const [editingExperience, setEditingExperience] = useState<Experience | undefined>(undefined);
  
  const [error, setError] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const fetchExperiences = useCallback(async () => {
    try {
      const supabase = createClient();
      const { data: { session } } = await supabase.auth.getSession();
      
      if (!session) return;

      const res = await fetch(`${API_URL}/api/v1/profile/experience`, {
        headers: { "Authorization": `Bearer ${session.access_token}` }
      });

      if (res.ok) {
        const data = await res.json();
        setExperiences(data);
      }
    } catch (err) {
      console.error("Failed to load experiences", err);
    } finally {
      setIsLoading(false);
    }
  }, [API_URL]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchExperiences();
  }, [fetchExperiences]);

  const handleSave = async (data: Partial<Experience>, skillsToAdd: string[], skillsToRemove: string[]) => {
    setFormError(null);
    setIsSaving(true);
    
    try {
      const supabase = createClient();
      const { data: { session } } = await supabase.auth.getSession();
      
      if (!session) {
        setFormError("Session expired. Please log in again.");
        setIsSaving(false);
        return;
      }

      const method = editingExperience ? "PATCH" : "POST";
      const url = editingExperience 
        ? `${API_URL}/api/v1/profile/experience/${editingExperience.id}` 
        : `${API_URL}/api/v1/profile/experience`;

      const res = await fetch(url, {
        method,
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${session.access_token}`
        },
        body: JSON.stringify(data)
      });

      if (res.ok) {
        const savedExp = await res.json();
        
        const headers = {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${session.access_token}`
        };

        // Add skills
        for (const skillId of skillsToAdd) {
          await fetch(`${API_URL}/api/v1/profile/experience/${savedExp.id}/skills`, {
            method: "POST",
            headers,
            body: JSON.stringify({ profile_skill_id: skillId })
          }).catch(console.error); // Catch individually to not break loop
        }

        // Remove skills
        for (const skillId of skillsToRemove) {
          await fetch(`${API_URL}/api/v1/profile/experience/${savedExp.id}/skills/${skillId}`, {
            method: "DELETE",
            headers
          }).catch(console.error);
        }

        await fetchExperiences();
        setShowForm(false);
        setEditingExperience(undefined);
      } else {
        const errData = await res.json().catch(() => ({}));
        setFormError(errData.detail || "Failed to save experience.");
      }
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "An unexpected error occurred.");
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm("Are you sure you want to delete this experience record?")) {
      return;
    }

    setDeletingId(id);
    setError(null);

    try {
      const supabase = createClient();
      const { data: { session } } = await supabase.auth.getSession();
      
      if (!session) return;

      const res = await fetch(`${API_URL}/api/v1/profile/experience/${id}`, {
        method: "DELETE",
        headers: { "Authorization": `Bearer ${session.access_token}` }
      });

      if (res.ok || res.status === 204) {
        await fetchExperiences();
      } else {
        setError("Failed to delete experience.");
      }
    } catch {
      setError("An unexpected error occurred while deleting.");
    } finally {
      setDeletingId(null);
    }
  };

  const openAddForm = () => {
    setEditingExperience(undefined);
    setFormError(null);
    setShowForm(true);
  };

  const openEditForm = (experience: Experience) => {
    setEditingExperience(experience);
    setFormError(null);
    setShowForm(true);
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
          <CardTitle>Experience</CardTitle>
          <CardDescription>Detail your professional work history.</CardDescription>
        </div>
        {!showForm && (
          <Button onClick={openAddForm} className="bg-primary text-primary-foreground">
            <Plus className="mr-2 h-4 w-4" /> Add Experience
          </Button>
        )}
      </CardHeader>
      
      <CardContent className="space-y-6">
        {error && (
          <div className="rounded-md bg-destructive/15 p-3 text-sm text-destructive">
            {error}
          </div>
        )}

        {showForm ? (
          <ExperienceForm
            initialData={editingExperience}
            onSave={handleSave}
            onCancel={() => {
              setShowForm(false);
              setEditingExperience(undefined);
            }}
            isSaving={isSaving}
            error={formError}
          />
        ) : (
          <div className="space-y-4">
            {experiences.length === 0 ? (
              <div className="rounded-xl border border-dashed border-border p-8 text-center">
                <p className="text-muted-foreground">No experience history added yet.</p>
                <Button variant="outline" onClick={openAddForm} className="mt-4">
                  Add your first experience
                </Button>
              </div>
            ) : (
              experiences.map((exp) => (
                <ExperienceCard
                  key={exp.id}
                  experience={exp}
                  onEdit={() => openEditForm(exp)}
                  onDelete={() => handleDelete(exp.id)}
                  isDeleting={deletingId === exp.id}
                />
              ))
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
