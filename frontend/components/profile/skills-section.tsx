"use client";

import { useEffect, useState, useCallback } from "react";
import { createClient } from "@/lib/supabase/client";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2, Plus } from "lucide-react";
import { SkillForm, type ProfileSkill } from "./skill-form";
import { SkillCard } from "./skill-card";

export function SkillsSection() {
  const [skills, setSkills] = useState<ProfileSkill[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  
  const [showForm, setShowForm] = useState(false);
  const [editingSkill, setEditingSkill] = useState<ProfileSkill | undefined>(undefined);
  
  const [error, setError] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const fetchSkills = useCallback(async () => {
    try {
      const supabase = createClient();
      const { data: { session } } = await supabase.auth.getSession();
      
      if (!session) return;

      const res = await fetch(`${API_URL}/api/v1/profile/skills`, {
        headers: { "Authorization": `Bearer ${session.access_token}` }
      });

      if (res.ok) {
        const data = await res.json();
        setSkills(data);
      }
    } catch (err) {
      console.error("Failed to load skills", err);
    } finally {
      setIsLoading(false);
    }
  }, [API_URL]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchSkills();
  }, [fetchSkills]);

  const handleSave = async (data: Partial<ProfileSkill>) => {
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

      const method = editingSkill ? "PATCH" : "POST";
      const url = editingSkill 
        ? `${API_URL}/api/v1/profile/skills/${editingSkill.id}` 
        : `${API_URL}/api/v1/profile/skills`;

      const res = await fetch(url, {
        method,
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${session.access_token}`
        },
        body: JSON.stringify(data)
      });

      if (res.ok) {
        await fetchSkills();
        setShowForm(false);
        setEditingSkill(undefined);
      } else if (res.status === 409) {
        setFormError("You already have this skill in your profile.");
      } else {
        const errData = await res.json().catch(() => ({}));
        setFormError(errData.detail || "Failed to save skill.");
      }
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "An unexpected error occurred.");
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm("Are you sure you want to remove this skill?")) {
      return;
    }

    setDeletingId(id);
    setError(null);

    try {
      const supabase = createClient();
      const { data: { session } } = await supabase.auth.getSession();
      
      if (!session) return;

      const res = await fetch(`${API_URL}/api/v1/profile/skills/${id}`, {
        method: "DELETE",
        headers: { "Authorization": `Bearer ${session.access_token}` }
      });

      if (res.ok || res.status === 204) {
        await fetchSkills();
      } else {
        setError("Failed to delete skill.");
      }
    } catch {
      setError("An unexpected error occurred while deleting.");
    } finally {
      setDeletingId(null);
    }
  };

  const openAddForm = () => {
    setEditingSkill(undefined);
    setFormError(null);
    setShowForm(true);
  };

  const openEditForm = (skill: ProfileSkill) => {
    setEditingSkill(skill);
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
          <CardTitle>Skills</CardTitle>
          <CardDescription>Highlight your key abilities and tools.</CardDescription>
        </div>
        {!showForm && (
          <Button onClick={openAddForm} className="bg-primary text-primary-foreground">
            <Plus className="mr-2 h-4 w-4" /> Add Skill
          </Button>
        )}
      </CardHeader>
      
      <CardContent className="space-y-6">
        {error && (
          <div className="rounded-md bg-destructive/15 p-3 text-sm text-destructive">
            {error}
          </div>
        )}

        {showForm && (
          <SkillForm
            initialData={editingSkill}
            onSave={handleSave}
            onCancel={() => {
              setShowForm(false);
              setEditingSkill(undefined);
            }}
            isSaving={isSaving}
            error={formError}
          />
        )}

        <div className="space-y-4">
          {skills.length === 0 && !showForm ? (
            <div className="rounded-xl border border-dashed border-border p-8 text-center">
              <p className="text-muted-foreground">No skills added yet.</p>
              <Button variant="outline" onClick={openAddForm} className="mt-4">
                Add your first skill
              </Button>
            </div>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {skills.map((skill) => (
                <SkillCard
                  key={skill.id}
                  skill={skill}
                  onEdit={() => openEditForm(skill)}
                  onDelete={() => handleDelete(skill.id)}
                  isDeleting={deletingId === skill.id}
                />
              ))}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
