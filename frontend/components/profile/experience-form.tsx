"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Loader2, Check, ChevronsUpDown, X } from "lucide-react";
import { createClient } from "@/lib/supabase/client";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { ExperienceSkill } from "./experience-card";
import type { ProfileSkill } from "./skill-form";

export type Experience = {
  id: string;
  title: string;
  company: string;
  location?: string | null;
  description?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  is_current: boolean;
};

interface ExperienceFormProps {
  initialData?: Experience;
  onSave: (data: Partial<Experience>, skillsToAdd: string[], skillsToRemove: string[]) => Promise<void>;
  onCancel: () => void;
  isSaving: boolean;
  error: string | null;
}

export function ExperienceForm({ initialData, onSave, onCancel, isSaving, error }: ExperienceFormProps) {
  const [formData, setFormData] = useState({
    title: initialData?.title || "",
    company: initialData?.company || "",
    location: initialData?.location || "",
    description: initialData?.description || "",
    start_date: initialData?.start_date || "",
    end_date: initialData?.end_date || "",
    is_current: initialData?.is_current || false,
  });

  const [validationError, setValidationError] = useState<string | null>(null);

  // --- Skills State ---
  const [profileSkills, setProfileSkills] = useState<ProfileSkill[]>([]);
  const [initialExperienceSkills, setInitialExperienceSkills] = useState<ExperienceSkill[]>([]);
  
  // A set of profile_skill_ids that the user wants attached
  const [selectedSkillIds, setSelectedSkillIds] = useState<Set<string>>(new Set());
  
  const [openCombo, setOpenCombo] = useState(false);
  const [isLoadingSkills, setIsLoadingSkills] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      setIsLoadingSkills(true);
      try {
        const supabase = createClient();
        const { data: { session } } = await supabase.auth.getSession();
        if (!session) return;
        
        const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        
        // Fetch all profile skills
        const psRes = await fetch(`${API_URL}/api/v1/profile/skills`, {
          headers: { Authorization: `Bearer ${session.access_token}` }
        });
        let pSkills: ProfileSkill[] = [];
        if (psRes.ok) {
          pSkills = await psRes.json();
          setProfileSkills(pSkills);
        }

        // If editing, fetch existing experience skills
        if (initialData?.id) {
          const esRes = await fetch(`${API_URL}/api/v1/profile/experience/${initialData.id}/skills`, {
            headers: { Authorization: `Bearer ${session.access_token}` }
          });
          if (esRes.ok) {
            const eSkills: ExperienceSkill[] = await esRes.json();
            setInitialExperienceSkills(eSkills);
            setSelectedSkillIds(new Set(eSkills.map(es => es.profile_skill_id)));
          }
        }
      } catch (err) {
        console.error("Failed to load skills", err);
      } finally {
        setIsLoadingSkills(false);
      }
    };
    fetchData();
  }, [initialData?.id]);

  const toggleSkill = (profileSkillId: string) => {
    const newSelected = new Set(selectedSkillIds);
    if (newSelected.has(profileSkillId)) {
      newSelected.delete(profileSkillId);
    } else {
      newSelected.add(profileSkillId);
    }
    setSelectedSkillIds(newSelected);
  };
  
  const getSelectedSkillObjects = () => {
    return profileSkills.filter(ps => selectedSkillIds.has(ps.id));
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target;
    
    if (type === "checkbox") {
      const checked = (e.target as HTMLInputElement).checked;
      setFormData((prev) => ({
        ...prev,
        [name]: checked,
      }));
    } else {
      setFormData((prev) => ({
        ...prev,
        [name]: value,
      }));
    }
    
    setValidationError(null);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setValidationError(null);

    // Validate dates
    if (formData.start_date && formData.end_date && !formData.is_current) {
      if (new Date(formData.end_date) < new Date(formData.start_date)) {
        setValidationError("End date cannot be earlier than start date.");
        return;
      }
    }
    
    // Calculate skillsToAdd and skillsToRemove
    const initialIds = new Set(initialExperienceSkills.map(es => es.profile_skill_id));
    const finalIds = selectedSkillIds;
    
    const skillsToAdd = Array.from(finalIds).filter(id => !initialIds.has(id));
    const skillsToRemove = Array.from(initialIds).filter(id => !finalIds.has(id));

    onSave({
      title: formData.title,
      company: formData.company,
      location: formData.location || null,
      description: formData.description || null,
      start_date: formData.start_date || null,
      end_date: formData.is_current ? null : (formData.end_date || null),
      is_current: formData.is_current,
    }, skillsToAdd, skillsToRemove);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4 rounded-xl border border-border bg-card p-6 shadow-sm">
      <h3 className="text-lg font-medium">{initialData ? "Edit Experience" : "Add Experience"}</h3>
      
      {(error || validationError) && (
        <div className="rounded-md bg-destructive/15 p-3 text-sm text-destructive">
          {validationError || error}
        </div>
      )}

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <Label htmlFor="title">Job Title <span className="text-destructive">*</span></Label>
          <Input
            id="title"
            name="title"
            value={formData.title}
            onChange={handleChange}
            required
            disabled={isSaving}
            placeholder="e.g. Software Engineer"
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="company">Company <span className="text-destructive">*</span></Label>
          <Input
            id="company"
            name="company"
            value={formData.company}
            onChange={handleChange}
            required
            disabled={isSaving}
            placeholder="e.g. Tech Corp Inc."
          />
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="location">Location</Label>
        <Input
          id="location"
          name="location"
          value={formData.location}
          onChange={handleChange}
          disabled={isSaving}
          placeholder="e.g. New York, NY (or Remote)"
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
            disabled={isSaving || formData.is_current}
            required={!formData.is_current && !!formData.start_date}
          />
        </div>
      </div>

      <div className="flex items-center space-x-2">
        <input
          type="checkbox"
          id="is_current"
          name="is_current"
          checked={formData.is_current}
          onChange={handleChange}
          disabled={isSaving}
          className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
        />
        <Label htmlFor="is_current" className="font-normal cursor-pointer">
          I am currently working here
        </Label>
      </div>

      <div className="space-y-2">
        <Label htmlFor="description">Description</Label>
        <Textarea
          id="description"
          name="description"
          value={formData.description}
          onChange={handleChange}
          disabled={isSaving}
          placeholder="Describe your responsibilities and achievements..."
          className="min-h-[120px]"
        />
      </div>

      {/* Skills Used Section */}
      <div className="space-y-3 pt-2 border-t border-border/50">
        <Label>Skills Used</Label>
        
        {isLoadingSkills ? (
           <div className="flex items-center space-x-2 text-sm text-muted-foreground">
             <Loader2 className="h-4 w-4 animate-spin" />
             <span>Loading skills...</span>
           </div>
        ) : (
          <>
            <div className="flex flex-wrap gap-2 mb-2">
              {getSelectedSkillObjects().map((skill) => (
                <Badge key={skill.id} variant="secondary" className="bg-primary/10 text-primary hover:bg-primary/20 flex items-center gap-1 font-normal">
                  {skill.skill_name}
                  <button
                    type="button"
                    onClick={() => toggleSkill(skill.id)}
                    className="ml-1 hover:bg-primary/20 rounded-full p-0.5 focus:outline-none"
                    disabled={isSaving}
                  >
                    <X className="h-3 w-3" />
                  </button>
                </Badge>
              ))}
              {getSelectedSkillObjects().length === 0 && (
                 <span className="text-sm text-muted-foreground italic">No skills selected</span>
              )}
            </div>

            <Popover open={openCombo} onOpenChange={setOpenCombo}>
              <PopoverTrigger
                aria-expanded={openCombo}
                className="flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 text-muted-foreground font-normal"
                disabled={isSaving || profileSkills.length === 0}
              >
                {profileSkills.length === 0 
                  ? "Add skills to your profile first" 
                  : "Search your profile skills..."}
                <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
              </PopoverTrigger>
              <PopoverContent className="w-[var(--radix-popover-trigger-width)] p-0">
                <Command>
                  <CommandInput placeholder="Search your skills..." />
                  <CommandList>
                    <CommandEmpty>No matching skills found.</CommandEmpty>
                    <CommandGroup>
                      {profileSkills.map((skill) => {
                        const isSelected = selectedSkillIds.has(skill.id);
                        return (
                          <CommandItem
                            key={skill.id}
                            value={skill.skill_name}
                            onSelect={() => {
                              toggleSkill(skill.id);
                              // Keep it open for multi-select
                            }}
                          >
                            <Check
                              className={cn(
                                "mr-2 h-4 w-4",
                                isSelected ? "opacity-100" : "opacity-0"
                              )}
                            />
                            {skill.skill_name}
                          </CommandItem>
                        );
                      })}
                    </CommandGroup>
                  </CommandList>
                </Command>
              </PopoverContent>
            </Popover>
          </>
        )}
      </div>

      <div className="flex justify-end space-x-3 pt-4 border-t border-border/50">
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
