"use client";

import { useEffect, useState, useCallback } from "react";
import { createClient } from "@/lib/supabase/client";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2, Plus } from "lucide-react";
import { EducationForm, type Education } from "./education-form";
import { EducationCard } from "./education-card";

export function EducationSection() {
  const [educations, setEducations] = useState<Education[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  
  const [showForm, setShowForm] = useState(false);
  const [editingEducation, setEditingEducation] = useState<Education | undefined>(undefined);
  
  const [error, setError] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const fetchEducations = useCallback(async () => {
    try {
      const supabase = createClient();
      const { data: { session } } = await supabase.auth.getSession();
      
      if (!session) return;

      const res = await fetch(`${API_URL}/api/v1/profile/education`, {
        headers: { "Authorization": `Bearer ${session.access_token}` }
      });

      if (res.ok) {
        const data = await res.json();
        setEducations(data);
      }
    } catch (err) {
      console.error("Failed to load educations", err);
    } finally {
      setIsLoading(false);
    }
  }, [API_URL]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchEducations();
  }, [fetchEducations]);

  const handleSave = async (data: Partial<Education>) => {
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

      const method = editingEducation ? "PATCH" : "POST";
      const url = editingEducation 
        ? `${API_URL}/api/v1/profile/education/${editingEducation.id}` 
        : `${API_URL}/api/v1/profile/education`;

      const res = await fetch(url, {
        method,
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${session.access_token}`
        },
        body: JSON.stringify(data)
      });

      if (res.ok) {
        await fetchEducations();
        setShowForm(false);
        setEditingEducation(undefined);
      } else {
        const errData = await res.json().catch(() => ({}));
        setFormError(errData.detail || "Failed to save education record.");
      }
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "An unexpected error occurred.");
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm("Are you sure you want to delete this education record?")) {
      return;
    }

    setDeletingId(id);
    setError(null);

    try {
      const supabase = createClient();
      const { data: { session } } = await supabase.auth.getSession();
      
      if (!session) return;

      const res = await fetch(`${API_URL}/api/v1/profile/education/${id}`, {
        method: "DELETE",
        headers: { "Authorization": `Bearer ${session.access_token}` }
      });

      if (res.ok || res.status === 204) {
        await fetchEducations();
      } else {
        setError("Failed to delete education record.");
      }
    } catch {
      setError("An unexpected error occurred while deleting.");
    } finally {
      setDeletingId(null);
    }
  };

  const openAddForm = () => {
    setEditingEducation(undefined);
    setFormError(null);
    setShowForm(true);
  };

  const openEditForm = (education: Education) => {
    setEditingEducation(education);
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
          <CardTitle>Education</CardTitle>
          <CardDescription>Add your academic background and qualifications.</CardDescription>
        </div>
        {!showForm && (
          <Button onClick={openAddForm} className="bg-primary text-primary-foreground">
            <Plus className="mr-2 h-4 w-4" /> Add Education
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
          <EducationForm
            initialData={editingEducation}
            onSave={handleSave}
            onCancel={() => {
              setShowForm(false);
              setEditingEducation(undefined);
            }}
            isSaving={isSaving}
            error={formError}
          />
        ) : (
          <div className="space-y-4">
            {educations.length === 0 ? (
              <div className="rounded-xl border border-dashed border-border p-8 text-center">
                <p className="text-muted-foreground">No education history added yet.</p>
                <Button variant="outline" onClick={openAddForm} className="mt-4">
                  Add your first education
                </Button>
              </div>
            ) : (
              educations.map((edu) => (
                <EducationCard
                  key={edu.id}
                  education={edu}
                  onEdit={() => openEditForm(edu)}
                  onDelete={() => handleDelete(edu.id)}
                  isDeleting={deletingId === edu.id}
                />
              ))
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
