"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Loader2, Check, ChevronsUpDown, X, Plus } from "lucide-react";
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

export const COMMON_SOFT_SKILLS = [
  "Communication",
  "Leadership",
  "Teamwork",
  "Problem Solving",
  "Critical Thinking",
  "Adaptability",
  "Time Management",
  "Presentation",
] as const;

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
  const [skillSearchQuery, setSkillSearchQuery] = useState("");
  const [isAddingInlineSkill, setIsAddingInlineSkill] = useState(false);
  const [inlineSkillFeedback, setInlineSkillFeedback] = useState<string | null>(null);

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

  /**
   * Safely adds a missing technical or soft skill to the candidate's profile
   * and automatically attaches it to the current experience without discarding unsaved form data.
   */
  const handleAddMissingSkill = async (skillNameToAdd: string) => {
    const cleanName = skillNameToAdd.trim();
    if (!cleanName) return;

    // Check if already in profileSkills
    const existing = profileSkills.find(
      (ps) => ps.skill_name.toLowerCase() === cleanName.toLowerCase()
    );
    if (existing) {
      if (!selectedSkillIds.has(existing.id)) {
        setSelectedSkillIds((prev) => new Set([...prev, existing.id]));
      }
      setSkillSearchQuery("");
      return;
    }

    setIsAddingInlineSkill(true);
    setInlineSkillFeedback(null);

    try {
      const supabase = createClient();
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) {
        setInlineSkillFeedback("Session expired. Please log in again.");
        return;
      }

      const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${API_URL}/api/v1/profile/skills`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({
          skill_name: cleanName,
          proficiency: "Intermediate",
        }),
      });

      if (res.ok) {
        const newSkill: ProfileSkill = await res.json();
        setProfileSkills((prev) => [...prev, newSkill]);
        setSelectedSkillIds((prev) => new Set([...prev, newSkill.id]));
        setSkillSearchQuery("");
        setInlineSkillFeedback(`Added "${cleanName}" to profile skills and selected!`);
        setTimeout(() => setInlineSkillFeedback(null), 3000);
      } else {
        const errData = await res.json().catch(() => ({}));
        setInlineSkillFeedback(errData.detail || "Could not add skill to profile.");
      }
    } catch {
      setInlineSkillFeedback("Network error adding skill.");
    } finally {
      setIsAddingInlineSkill(false);
    }
  };

  /**
   * Quick handler for soft skills chips: toggles if already added, or creates & selects if not yet in profile.
   */
  const handleToggleOrAddSoftSkill = (softSkillName: string) => {
    const existing = profileSkills.find(
      (ps) => ps.skill_name.toLowerCase() === softSkillName.toLowerCase()
    );
    if (existing) {
      toggleSkill(existing.id);
    } else {
      handleAddMissingSkill(softSkillName);
    }
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
        <div className="flex items-center justify-between">
          <Label>Skills Used (Technical &amp; Soft Skills)</Label>
          <span className="text-xs text-muted-foreground">
            {selectedSkillIds.size} selected
          </span>
        </div>
        
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
                  {skill.proficiency && (
                    <span className="text-[10px] opacity-75">({skill.proficiency})</span>
                  )}
                  <button
                    type="button"
                    onClick={() => toggleSkill(skill.id)}
                    className="ml-1 hover:bg-primary/20 rounded-full p-0.5 focus:outline-none"
                    disabled={isSaving || isAddingInlineSkill}
                    aria-label={`Remove ${skill.skill_name}`}
                  >
                    <X className="h-3 w-3" />
                  </button>
                </Badge>
              ))}
              {getSelectedSkillObjects().length === 0 && (
                 <span className="text-sm text-muted-foreground italic">No skills selected yet</span>
              )}
            </div>

            <Popover open={openCombo} onOpenChange={setOpenCombo}>
              <PopoverTrigger
                aria-expanded={openCombo}
                className="flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 text-muted-foreground font-normal"
                disabled={isSaving || isAddingInlineSkill}
              >
                {profileSkills.length === 0
                  ? "Search or add skills (e.g., Python, Leadership)..."
                  : "Search your skills or add new..."}
                <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
              </PopoverTrigger>
              <PopoverContent className="w-[var(--radix-popover-trigger-width)] p-0" align="start">
                <Command>
                  <CommandInput
                    placeholder="Search your skills or type a new one..."
                    value={skillSearchQuery}
                    onValueChange={setSkillSearchQuery}
                  />
                  <CommandList>
                    <CommandEmpty>
                      <div className="p-3 text-center space-y-2">
                        <p className="text-xs text-muted-foreground">
                          {skillSearchQuery.trim()
                            ? `"${skillSearchQuery}" is not in your profile skills yet.`
                            : "No matching skills found."}
                        </p>
                        {skillSearchQuery.trim() && (
                          <Button
                            type="button"
                            size="sm"
                            disabled={isAddingInlineSkill}
                            onClick={() => handleAddMissingSkill(skillSearchQuery.trim())}
                            className="w-full text-xs bg-primary text-primary-foreground gap-1.5"
                          >
                            {isAddingInlineSkill ? (
                              <Loader2 className="size-3.5 animate-spin" />
                            ) : (
                              <Plus className="size-3.5" />
                            )}
                            Add &quot;{skillSearchQuery.trim()}&quot; to profile &amp; select
                          </Button>
                        )}
                      </div>
                    </CommandEmpty>
                    <CommandGroup heading="Your Saved Profile Skills">
                      {profileSkills.map((skill) => {
                        const isSelected = selectedSkillIds.has(skill.id);
                        return (
                          <CommandItem
                            key={skill.id}
                            value={skill.skill_name}
                            onSelect={() => {
                              toggleSkill(skill.id);
                            }}
                          >
                            <Check
                              className={cn(
                                "mr-2 h-4 w-4",
                                isSelected ? "opacity-100" : "opacity-0"
                              )}
                            />
                            <span className="flex-1">{skill.skill_name}</span>
                            {skill.proficiency && (
                              <span className="text-[10px] text-muted-foreground">
                                ({skill.proficiency})
                              </span>
                            )}
                          </CommandItem>
                        );
                      })}
                    </CommandGroup>

                    {/* Action to add typed skill as a new profile skill if not an exact duplicate */}
                    {skillSearchQuery.trim() &&
                      !profileSkills.some(
                        (ps) => ps.skill_name.toLowerCase() === skillSearchQuery.trim().toLowerCase()
                      ) && (
                        <div className="p-1 border-t border-border/50">
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            disabled={isAddingInlineSkill}
                            onClick={() => handleAddMissingSkill(skillSearchQuery.trim())}
                            className="w-full justify-start text-xs text-primary hover:text-primary gap-1.5 font-medium h-8"
                          >
                            {isAddingInlineSkill ? (
                              <Loader2 className="size-3.5 animate-spin" />
                            ) : (
                              <Plus className="size-3.5" />
                            )}
                            Add &quot;{skillSearchQuery.trim()}&quot; as new skill
                          </Button>
                        </div>
                      )}
                  </CommandList>
                </Command>
              </PopoverContent>
            </Popover>

            {/* Quick soft skill attachment chips */}
            <div className="space-y-1.5 pt-1">
              <span className="text-[11px] font-medium text-muted-foreground">
                Quick attach soft &amp; collaborative skills:
              </span>
              <div className="flex flex-wrap gap-1.5">
                {COMMON_SOFT_SKILLS.map((softSkill) => {
                  const existing = profileSkills.find(
                    (ps) => ps.skill_name.toLowerCase() === softSkill.toLowerCase()
                  );
                  const isSelected = existing && selectedSkillIds.has(existing.id);

                  return (
                    <button
                      key={softSkill}
                      type="button"
                      disabled={isSaving || isAddingInlineSkill}
                      onClick={() => handleToggleOrAddSoftSkill(softSkill)}
                      className={cn(
                        "inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-medium transition-colors border",
                        isSelected
                          ? "bg-primary text-primary-foreground border-primary shadow-2xs"
                          : "bg-[#EBF3ED] text-[#14261C] border-primary/20 hover:bg-primary/10 shadow-2xs"
                      )}
                    >
                      {isSelected ? (
                        <Check className="size-3" />
                      ) : (
                        <Plus className="size-3 text-primary" />
                      )}
                      {softSkill}
                    </button>
                  );
                })}
              </div>
            </div>

            {inlineSkillFeedback && (
              <p className="text-xs text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-md p-1.5 animate-in fade-in-50">
                {inlineSkillFeedback}
              </p>
            )}
          </>
        )}
      </div>

      <div className="flex justify-end space-x-3 pt-4 border-t border-border/50">
        <Button type="button" variant="outline" onClick={onCancel} disabled={isSaving || isAddingInlineSkill}>
          Cancel
        </Button>
        <Button type="submit" disabled={isSaving || isAddingInlineSkill} className="bg-saffron text-saffron-foreground hover:bg-saffron/90">
          {isSaving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          {isSaving ? "Saving..." : "Save"}
        </Button>
      </div>
    </form>
  );
}
