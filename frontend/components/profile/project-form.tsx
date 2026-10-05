"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Loader2 } from "lucide-react";

export type Project = {
  id: string;
  name: string;
  description?: string | null;
  url?: string | null;
  start_date?: string | null;
  end_date?: string | null;
};

interface ProjectFormProps {
  initialData?: Project;
  onSave: (data: Partial<Project>) => Promise<void>;
  onCancel: () => void;
  isSaving: boolean;
  error: string | null;
}

export function ProjectForm({ initialData, onSave, onCancel, isSaving, error }: ProjectFormProps) {
  const [formData, setFormData] = useState({
    name: initialData?.name || "",
    description: initialData?.description || "",
    url: initialData?.url || "",
    start_date: initialData?.start_date || "",
    end_date: initialData?.end_date || "",
  });

  const [validationError, setValidationError] = useState<string | null>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
    setValidationError(null);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setValidationError(null);

    // Validate URL if present
    if (formData.url) {
      try {
        new URL(formData.url);
      } catch {
        setValidationError("Please enter a valid URL (e.g. https://example.com)");
        return;
      }
    }

    // Validate dates
    if (formData.start_date && formData.end_date) {
      if (new Date(formData.end_date) < new Date(formData.start_date)) {
        setValidationError("End date cannot be earlier than start date.");
        return;
      }
    }

    onSave({
      name: formData.name,
      description: formData.description || null,
      url: formData.url || null,
      start_date: formData.start_date || null,
      end_date: formData.end_date || null,
    });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4 rounded-xl border border-border bg-card p-6 shadow-sm">
      <h3 className="text-lg font-medium">{initialData ? "Edit Project" : "Add Project"}</h3>
      
      {(error || validationError) && (
        <div className="rounded-md bg-destructive/15 p-3 text-sm text-destructive">
          {validationError || error}
        </div>
      )}

      <div className="space-y-2">
        <Label htmlFor="name">Project Name <span className="text-destructive">*</span></Label>
        <Input
          id="name"
          name="name"
          value={formData.name}
          onChange={handleChange}
          required
          disabled={isSaving}
          placeholder="e.g. AI Portfolio Website"
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="url">Project URL</Label>
        <Input
          id="url"
          name="url"
          type="url"
          value={formData.url}
          onChange={handleChange}
          disabled={isSaving}
          placeholder="https://example.com"
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="description">Description</Label>
        <Textarea
          id="description"
          name="description"
          value={formData.description}
          onChange={handleChange}
          disabled={isSaving}
          placeholder="Describe your project, your role, and the technologies used."
          className="min-h-[100px]"
        />
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <Label htmlFor="start_date">Start Date</Label>
          <Input
            id="start_date"
            name="start_date"
            type="date"
            value={formData.start_date}
            onChange={handleChange}
            disabled={isSaving}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="end_date">End Date</Label>
          <Input
            id="end_date"
            name="end_date"
            type="date"
            value={formData.end_date}
            onChange={handleChange}
            disabled={isSaving}
          />
        </div>
      </div>

      <div className="flex justify-end space-x-3 pt-4">
        <Button type="button" variant="outline" onClick={onCancel} disabled={isSaving}>
          Cancel
        </Button>
        <Button type="submit" disabled={isSaving} className="bg-saffron text-saffron-foreground hover:bg-saffron/90">
          {isSaving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          {isSaving ? "Saving..." : "Save"}
        </Button>
      </div>
    </form>
  );
}
