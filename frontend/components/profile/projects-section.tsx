"use client";

import { useEffect, useState, useCallback } from "react";
import { createClient } from "@/lib/supabase/client";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2, Plus } from "lucide-react";
import { ProjectForm, type Project } from "./project-form";
import { ProjectCard } from "./project-card";

export function ProjectsSection() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  
  const [showForm, setShowForm] = useState(false);
  const [editingProject, setEditingProject] = useState<Project | undefined>(undefined);
  
  const [error, setError] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const fetchProjects = useCallback(async () => {
    try {
      const supabase = createClient();
      const { data: { session } } = await supabase.auth.getSession();
      
      if (!session) return;

      const res = await fetch(`${API_URL}/api/v1/profile/projects`, {
        headers: { "Authorization": `Bearer ${session.access_token}` }
      });

      if (res.ok) {
        const data = await res.json();
        setProjects(data);
      }
    } catch (err) {
      console.error("Failed to load projects", err);
    } finally {
      setIsLoading(false);
    }
  }, [API_URL]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchProjects();
  }, [fetchProjects]);

  const handleSave = async (data: Partial<Project>) => {
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

      const method = editingProject ? "PATCH" : "POST";
      const url = editingProject 
        ? `${API_URL}/api/v1/profile/projects/${editingProject.id}` 
        : `${API_URL}/api/v1/profile/projects`;

      const res = await fetch(url, {
        method,
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${session.access_token}`
        },
        body: JSON.stringify(data)
      });

      if (res.ok) {
        await fetchProjects();
        setShowForm(false);
        setEditingProject(undefined);
      } else {
        const errData = await res.json().catch(() => ({}));
        setFormError(errData.detail || "Failed to save project.");
      }
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "An unexpected error occurred.");
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm("Are you sure you want to delete this project?")) {
      return;
    }

    setDeletingId(id);
    setError(null);

    try {
      const supabase = createClient();
      const { data: { session } } = await supabase.auth.getSession();
      
      if (!session) return;

      const res = await fetch(`${API_URL}/api/v1/profile/projects/${id}`, {
        method: "DELETE",
        headers: { "Authorization": `Bearer ${session.access_token}` }
      });

      if (res.ok || res.status === 204) {
        await fetchProjects();
      } else {
        setError("Failed to delete project.");
      }
    } catch {
      setError("An unexpected error occurred while deleting.");
    } finally {
      setDeletingId(null);
    }
  };

  const openAddForm = () => {
    setEditingProject(undefined);
    setFormError(null);
    setShowForm(true);
  };

  const openEditForm = (project: Project) => {
    setEditingProject(project);
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
          <CardTitle>Projects</CardTitle>
          <CardDescription>Showcase your portfolio and significant projects.</CardDescription>
        </div>
        {!showForm && (
          <Button onClick={openAddForm} className="bg-primary text-primary-foreground">
            <Plus className="mr-2 h-4 w-4" /> Add Project
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
          <ProjectForm
            initialData={editingProject}
            onSave={handleSave}
            onCancel={() => {
              setShowForm(false);
              setEditingProject(undefined);
            }}
            isSaving={isSaving}
            error={formError}
          />
        ) : (
          <div className="space-y-4">
            {projects.length === 0 ? (
              <div className="rounded-xl border border-dashed border-border p-8 text-center">
                <p className="text-muted-foreground">No projects added yet.</p>
                <Button variant="outline" onClick={openAddForm} className="mt-4">
                  Add your first project
                </Button>
              </div>
            ) : (
              projects.map((project) => (
                <ProjectCard
                  key={project.id}
                  project={project}
                  onEdit={() => openEditForm(project)}
                  onDelete={() => handleDelete(project.id)}
                  isDeleting={deletingId === project.id}
                />
              ))
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
