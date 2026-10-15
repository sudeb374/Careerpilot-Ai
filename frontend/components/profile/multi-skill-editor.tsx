"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { createClient } from "@/lib/supabase/client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Plus,
  Trash2,
  Undo2,
  Check,
  AlertCircle,
  Loader2,
  Sparkles,
  BookOpen,
} from "lucide-react";

export type ProfileSkill = {
  id: string;
  skill_name: string;
  proficiency: string;
};

export interface StagedSkill {
  id?: string;
  skill_name: string;
  proficiency: string;
  status: "saved" | "added" | "modified" | "removed";
  originalProficiency?: string;
}

export const PROFICIENCIES = ["Beginner", "Intermediate", "Advanced", "Expert"] as const;

export const POPULAR_SKILLS = [
  "Python", "JavaScript", "TypeScript", "React", "Next.js", "Node.js",
  "SQL", "PostgreSQL", "FastAPI", "Django", "Docker", "Git",
  "HTML", "CSS", "TailwindCSS", "AWS", "Machine Learning", "Data Analysis",
  "PyTorch", "TensorFlow", "Pandas", "Java", "C++", "REST APIs"
];

export const POPULAR_SOFT_SKILLS = [
  "Communication",
  "Leadership",
  "Teamwork",
  "Problem Solving",
  "Critical Thinking",
  "Adaptability",
  "Time Management",
  "Presentation",
] as const;

interface MultiSkillEditorProps {
  initialSkills?: ProfileSkill[];
  onSaved?: (skills: ProfileSkill[]) => void;
  className?: string;
}

export function MultiSkillEditor({
  initialSkills,
  onSaved,
  className = "",
}: MultiSkillEditorProps) {
  const [skills, setSkills] = useState<StagedSkill[]>([]);
  const [isLoading, setIsLoading] = useState(initialSkills === undefined);
  const [isSaving, setIsSaving] = useState(false);
  const [saveProgress, setSaveProgress] = useState<string | null>(null);

  // New skill input state
  const [skillInput, setSkillInput] = useState("");
  const [proficiencyInput, setProficiencyInput] = useState<string>("Intermediate");
  const [inputError, setInputError] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<{ type: "success" | "error"; message: string } | null>(null);

  // Autocomplete suggestions
  const [catalogSuggestions, setCatalogSuggestions] = useState<string[]>([]);
  const [isSearchingCatalog, setIsSearchingCatalog] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);

  const inputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  // Fetch initial skills if not provided
  const fetchSkills = useCallback(async () => {
    setIsLoading(true);
    try {
      const supabase = createClient();
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) return;

      const res = await fetch(`${API_URL}/api/v1/profile/skills`, {
        headers: { Authorization: `Bearer ${session.access_token}` },
      });
      if (res.ok) {
        const data: ProfileSkill[] = await res.json();
        setSkills(
          data.map((s) => ({
            id: s.id,
            skill_name: s.skill_name,
            proficiency: s.proficiency || "Intermediate",
            status: "saved",
            originalProficiency: s.proficiency || "Intermediate",
          }))
        );
      }
    } catch {
      setFeedback({ type: "error", message: "Failed to load skills from server." });
    } finally {
      setIsLoading(false);
    }
  }, [API_URL]);

  useEffect(() => {
    if (initialSkills) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setSkills(
        initialSkills.map((s) => ({
          id: s.id,
          skill_name: s.skill_name,
          proficiency: s.proficiency || "Intermediate",
          status: "saved",
          originalProficiency: s.proficiency || "Intermediate",
        }))
      );
      setIsLoading(false);
    } else {
      fetchSkills();
    }
  }, [initialSkills, fetchSkills]);

  // Click outside to close suggestion dropdown
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setShowSuggestions(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Debounced search for skills in global catalog
  useEffect(() => {
    const q = skillInput.trim();
    if (q.length < 1) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setCatalogSuggestions([]);
      return;
    }

    const timer = setTimeout(async () => {
      setIsSearchingCatalog(true);
      try {
        const supabase = createClient();
        const { data: { session } } = await supabase.auth.getSession();
        if (session) {
          const res = await fetch(`${API_URL}/api/v1/skills/search?q=${encodeURIComponent(q)}`, {
            headers: { Authorization: `Bearer ${session.access_token}` },
          });
          if (res.ok) {
            const results = await res.json();
            const names = (results as { name: string }[]).map((r) => r.name);
            setCatalogSuggestions(names);
          }
        }
      } catch {
        // Fallback to local filtering across technical and soft skills
        const allKnown = [...POPULAR_SKILLS, ...POPULAR_SOFT_SKILLS];
        const local = allKnown.filter((s) => s.toLowerCase().includes(q.toLowerCase()));
        setCatalogSuggestions(local);
      } finally {
        setIsSearchingCatalog(false);
      }
    }, 250);

    return () => clearTimeout(timer);
  }, [skillInput, API_URL]);

  // Add a skill to the staged list
  const handleAddSkill = (skillNameToAdd?: string) => {
    const name = (skillNameToAdd || skillInput).trim();
    setInputError(null);
    setFeedback(null);

    if (!name) {
      setInputError("Please enter a skill name.");
      inputRef.current?.focus();
      return;
    }

    // Duplicate check among non-removed skills
    const existing = skills.find(
      (s) => s.status !== "removed" && s.skill_name.toLowerCase() === name.toLowerCase()
    );
    if (existing) {
      setInputError(`"${name}" is already in your skills list.`);
      inputRef.current?.focus();
      return;
    }

    // Check if previously marked as removed -> restore it with new proficiency
    const wasRemoved = skills.find(
      (s) => s.status === "removed" && s.skill_name.toLowerCase() === name.toLowerCase()
    );

    if (wasRemoved) {
      setSkills((prev) =>
        prev.map((s) =>
          s === wasRemoved
            ? {
                ...s,
                proficiency: proficiencyInput,
                status: s.originalProficiency === proficiencyInput ? "saved" : "modified",
              }
            : s
        )
      );
    } else {
      // Add new staged skill
      setSkills((prev) => [
        ...prev,
        {
          skill_name: name,
          proficiency: proficiencyInput,
          status: "added",
        },
      ]);
    }

    setSkillInput("");
    setShowSuggestions(false);
    inputRef.current?.focus();
  };

  // Change proficiency of a staged skill
  const handleProficiencyChange = (index: number, newProficiency: string) => {
    setSkills((prev) =>
      prev.map((s, i) => {
        if (i !== index) return s;
        if (s.status === "added") {
          return { ...s, proficiency: newProficiency };
        }
        if (s.status === "saved" || s.status === "modified") {
          const isBackToOriginal = s.originalProficiency === newProficiency;
          return {
            ...s,
            proficiency: newProficiency,
            status: isBackToOriginal ? "saved" : "modified",
          };
        }
        return s;
      })
    );
  };

  // Remove or mark as removed
  const handleRemoveSkill = (index: number) => {
    setSkills((prev) => {
      const target = prev[index];
      if (!target) return prev;

      // If it was just added in this session, remove completely from state
      if (target.status === "added") {
        return prev.filter((_, i) => i !== index);
      }

      // If it exists in the database, mark for deletion
      return prev.map((s, i) => (i === index ? { ...s, status: "removed" } : s));
    });
  };

  // Undo remove
  const handleUndoRemove = (index: number) => {
    setSkills((prev) =>
      prev.map((s, i) => {
        if (i !== index) return s;
        const isModified = s.proficiency !== s.originalProficiency;
        return { ...s, status: isModified ? "modified" : "saved" };
      })
    );
  };

  // Discard all changes
  const handleDiscardChanges = () => {
    fetchSkills();
    setFeedback(null);
    setInputError(null);
  };

  // Count changes
  const addedCount = skills.filter((s) => s.status === "added").length;
  const modifiedCount = skills.filter((s) => s.status === "modified").length;
  const removedCount = skills.filter((s) => s.status === "removed").length;
  const hasChanges = addedCount > 0 || modifiedCount > 0 || removedCount > 0;
  const activeSkillsCount = skills.filter((s) => s.status !== "removed").length;

  // Single Save Action: commits all staged additions, edits, and removals
  const handleSaveAll = async () => {
    setIsSaving(true);
    setSaveProgress("Preparing to save skills...");
    setFeedback(null);
    setInputError(null);

    try {
      const supabase = createClient();
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) {
        setFeedback({ type: "error", message: "Session expired. Please sign in again." });
        setIsSaving(false);
        return;
      }

      const headers = {
        "Content-Type": "application/json",
        Authorization: `Bearer ${session.access_token}`,
      };

      // 1. Process Removals
      const toRemove = skills.filter((s) => s.status === "removed" && s.id);
      for (let i = 0; i < toRemove.length; i++) {
        const item = toRemove[i];
        setSaveProgress(`Removing ${item.skill_name}...`);
        await fetch(`${API_URL}/api/v1/profile/skills/${item.id}`, {
          method: "DELETE",
          headers,
        });
      }

      // 2. Process Modifications
      const toModify = skills.filter((s) => s.status === "modified" && s.id);
      for (let i = 0; i < toModify.length; i++) {
        const item = toModify[i];
        setSaveProgress(`Updating ${item.skill_name}...`);
        await fetch(`${API_URL}/api/v1/profile/skills/${item.id}`, {
          method: "PATCH",
          headers,
          body: JSON.stringify({ proficiency: item.proficiency }),
        });
      }

      // 3. Process Additions
      const toAdd = skills.filter((s) => s.status === "added");
      for (let i = 0; i < toAdd.length; i++) {
        const item = toAdd[i];
        setSaveProgress(`Adding ${item.skill_name}...`);
        await fetch(`${API_URL}/api/v1/profile/skills`, {
          method: "POST",
          headers,
          body: JSON.stringify({
            skill_name: item.skill_name,
            proficiency: item.proficiency,
          }),
        });
      }

      setSaveProgress("Finalizing skills...");
      // Re-fetch clean state
      const res = await fetch(`${API_URL}/api/v1/profile/skills`, { headers });
      if (res.ok) {
        const fresh: ProfileSkill[] = await res.json();
        setSkills(
          fresh.map((s) => ({
            id: s.id,
            skill_name: s.skill_name,
            proficiency: s.proficiency || "Intermediate",
            status: "saved",
            originalProficiency: s.proficiency || "Intermediate",
          }))
        );
        onSaved?.(fresh);
      }

      setFeedback({
        type: "success",
        message: `Saved ${activeSkillsCount} skill${activeSkillsCount === 1 ? "" : "s"} successfully.`,
      });
    } catch (err: unknown) {
      setFeedback({
        type: "error",
        message: (err as Error)?.message || "Failed to save skills. Please try again.",
      });
    } finally {
      setIsSaving(false);
      setSaveProgress(null);
    }
  };

  if (isLoading) {
    return (
      <div className="flex h-36 items-center justify-center">
        <Loader2 className="size-6 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className}`} ref={containerRef}>
      {/* Feedback Alert */}
      {feedback && (
        <div
          className={`flex items-center gap-2 rounded-xl p-3 text-xs font-medium border ${
            feedback.type === "success"
              ? "bg-emerald-50 text-emerald-800 border-emerald-200"
              : "bg-destructive/15 text-destructive border-destructive/20"
          }`}
        >
          {feedback.type === "success" ? (
            <Check className="size-4 shrink-0 text-emerald-600" />
          ) : (
            <AlertCircle className="size-4 shrink-0" />
          )}
          <span>{feedback.message}</span>
        </div>
      )}

      {/* Multiple Skills Input Bar */}
      <div className="rounded-xl border border-border bg-card p-4 shadow-2xs space-y-3">
        <div className="flex flex-col sm:flex-row items-stretch sm:items-end gap-3">
          {/* Skill Name Input & Autocomplete */}
          <div className="flex-1 space-y-1.5 relative">
            <Label htmlFor="skill-input" className="text-xs font-semibold text-foreground">
              Skill Name <span className="text-destructive">*</span>
            </Label>
            <div className="relative">
              <Input
                id="skill-input"
                ref={inputRef}
                type="text"
                placeholder="e.g. Python, React, SQL..."
                value={skillInput}
                onChange={(e) => {
                  setSkillInput(e.target.value);
                  setInputError(null);
                  setShowSuggestions(true);
                }}
                onFocus={() => {
                  if (skillInput.trim().length > 0) setShowSuggestions(true);
                }}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    handleAddSkill();
                  }
                }}
                disabled={isSaving}
                className="bg-background"
              />
              {isSearchingCatalog && (
                <div className="absolute right-3 top-2.5">
                  <Loader2 className="size-4 animate-spin text-primary opacity-60" />
                </div>
              )}
            </div>

            {/* Catalog autocomplete dropdown */}
            {showSuggestions && catalogSuggestions.length > 0 && (
              <div className="absolute z-50 mt-1 w-full rounded-xl border border-border bg-popover p-1 shadow-md text-popover-foreground max-h-48 overflow-y-auto">
                <div className="px-2 py-1 text-[10px] font-semibold text-muted-foreground uppercase tracking-wider flex items-center gap-1">
                  <BookOpen className="size-3" />
                  Standard Skill Catalog
                </div>
                {catalogSuggestions.map((suggestion) => (
                  <button
                    key={suggestion}
                    type="button"
                    onClick={() => {
                      handleAddSkill(suggestion);
                    }}
                    className="w-full text-left px-3 py-1.5 rounded-lg text-xs hover:bg-muted text-foreground flex items-center justify-between"
                  >
                    <span>{suggestion}</span>
                    <Plus className="size-3 text-muted-foreground" />
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Proficiency Select */}
          <div className="w-full sm:w-44 space-y-1.5">
            <Label htmlFor="proficiency-select" className="text-xs font-semibold text-foreground">
              Proficiency
            </Label>
            <Select
              value={proficiencyInput}
              onValueChange={(val) => {
                if (val) setProficiencyInput(val);
              }}
              disabled={isSaving}
            >
              <SelectTrigger id="proficiency-select" className="bg-background">
                <SelectValue placeholder="Proficiency" />
              </SelectTrigger>
              <SelectContent>
                {PROFICIENCIES.map((lvl) => (
                  <SelectItem key={lvl} value={lvl}>
                    {lvl}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Add Skill Button */}
          <Button
            type="button"
            onClick={() => handleAddSkill()}
            disabled={isSaving || !skillInput.trim()}
            className="bg-[#1B5E3B] hover:bg-[#203a2b] text-white shrink-0 gap-1.5"
          >
            <Plus className="size-4" />
            Add Skill
          </Button>
        </div>

        {inputError && (
          <p className="text-xs text-destructive flex items-center gap-1">
            <AlertCircle className="size-3.5" />
            {inputError}
          </p>
        )}

        {/* Quick popular suggestion chips */}
        <div className="pt-1 space-y-2">
          <div>
            <p className="text-[11px] font-medium text-muted-foreground mb-1.5">
              Quick additions — Technical skills:
            </p>
            <div className="flex flex-wrap gap-1.5">
              {POPULAR_SKILLS.slice(0, 10).map((skill) => {
                const alreadyAdded = skills.some(
                  (s) => s.status !== "removed" && s.skill_name.toLowerCase() === skill.toLowerCase()
                );
                if (alreadyAdded) return null;
                return (
                  <button
                    key={skill}
                    type="button"
                    onClick={() => handleAddSkill(skill)}
                    disabled={isSaving}
                    className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-medium bg-muted text-muted-foreground hover:bg-primary/10 hover:text-primary transition-colors border border-border/60"
                  >
                    <Plus className="size-2.5" />
                    {skill}
                  </button>
                );
              })}
            </div>
          </div>

          <div>
            <p className="text-[11px] font-medium text-muted-foreground mb-1.5">
              Quick additions — Soft & Collaborative skills:
            </p>
            <div className="flex flex-wrap gap-1.5">
              {POPULAR_SOFT_SKILLS.map((skill) => {
                const alreadyAdded = skills.some(
                  (s) => s.status !== "removed" && s.skill_name.toLowerCase() === skill.toLowerCase()
                );
                if (alreadyAdded) return null;
                return (
                  <button
                    key={skill}
                    type="button"
                    onClick={() => handleAddSkill(skill)}
                    disabled={isSaving}
                    className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-medium bg-emerald-50 text-emerald-800 hover:bg-emerald-100 hover:text-emerald-900 transition-colors border border-emerald-200 shadow-2xs"
                  >
                    <Plus className="size-2.5 text-emerald-600" />
                    {skill}
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      </div>

      {/* Review List of Skills */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h4 className="text-sm font-semibold text-foreground flex items-center gap-2">
            <Sparkles className="size-4 text-primary" />
            Review Your Skills ({activeSkillsCount})
          </h4>
          {hasChanges && (
            <span className="text-xs font-semibold text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/40 px-2 py-0.5 rounded-full border border-amber-200">
              Unsaved changes pending
            </span>
          )}
        </div>

        {skills.length === 0 ? (
          <div className="rounded-xl border border-dashed border-border p-8 text-center text-sm text-muted-foreground">
            No skills added yet. Type a skill above, choose a proficiency level, and click &quot;Add Skill&quot;.
          </div>
        ) : (
          <div className="grid gap-2.5 sm:grid-cols-2 lg:grid-cols-3">
            {skills.map((skill, index) => {
              const isRemoved = skill.status === "removed";
              const isAdded = skill.status === "added";
              const isModified = skill.status === "modified";

              return (
                <div
                  key={`${skill.skill_name}-${index}`}
                  className={`flex items-center justify-between gap-2 p-3 rounded-xl border transition-all text-xs ${
                    isRemoved
                      ? "bg-destructive/5 border-destructive/30 opacity-70 line-through"
                      : isAdded
                      ? "bg-emerald-50/60 border-emerald-300 shadow-2xs"
                      : isModified
                      ? "bg-amber-50/60 border-amber-300 shadow-2xs"
                      : "bg-card border-border shadow-2xs"
                  }`}
                >
                  <div className="flex-1 min-w-0 pr-1">
                    <div className="flex items-center gap-1.5 flex-wrap">
                      <span className="font-semibold text-foreground text-sm truncate">
                        {skill.skill_name}
                      </span>
                      {isAdded && (
                        <span className="text-[10px] font-bold px-1.5 py-0.2 rounded-full bg-emerald-100 text-emerald-800 border border-emerald-300">
                          New
                        </span>
                      )}
                      {isModified && (
                        <span className="text-[10px] font-bold px-1.5 py-0.2 rounded-full bg-amber-100 text-amber-800 border border-amber-300">
                          Edited
                        </span>
                      )}
                      {isRemoved && (
                        <span className="text-[10px] font-bold px-1.5 py-0.2 rounded-full bg-destructive/15 text-destructive border border-destructive/20 no-underline">
                          To Remove
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Proficiency Selector inline */}
                  {!isRemoved ? (
                    <div className="flex items-center gap-2">
                      <Select
                        value={skill.proficiency}
                        onValueChange={(val) => {
                          if (val) handleProficiencyChange(index, val);
                        }}
                        disabled={isSaving}
                      >
                        <SelectTrigger className="h-7 w-28 text-xs bg-background py-0">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {PROFICIENCIES.map((lvl) => (
                            <SelectItem key={lvl} value={lvl} className="text-xs">
                              {lvl}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>

                      <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        onClick={() => handleRemoveSkill(index)}
                        disabled={isSaving}
                        className="size-7 text-muted-foreground hover:text-destructive hover:bg-destructive/10 rounded-lg"
                        title="Remove skill"
                      >
                        <Trash2 className="size-3.5" />
                      </Button>
                    </div>
                  ) : (
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => handleUndoRemove(index)}
                      disabled={isSaving}
                      className="h-7 text-xs gap-1 border-muted-foreground/30"
                    >
                      <Undo2 className="size-3" />
                      Undo
                    </Button>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Save Action Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 pt-3 border-t border-border">
        <div className="text-xs text-muted-foreground">
          {hasChanges ? (
            <span>
              Pending updates:{" "}
              {addedCount > 0 && <strong className="text-emerald-700">{addedCount} to add</strong>}
              {addedCount > 0 && (modifiedCount > 0 || removedCount > 0) && ", "}
              {modifiedCount > 0 && <strong className="text-amber-700">{modifiedCount} modified</strong>}
              {modifiedCount > 0 && removedCount > 0 && ", "}
              {removedCount > 0 && <strong className="text-destructive">{removedCount} to remove</strong>}
            </span>
          ) : (
            <span>All skills are synchronized with your profile.</span>
          )}
        </div>

        <div className="flex items-center gap-2">
          {hasChanges && (
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={handleDiscardChanges}
              disabled={isSaving}
              className="text-xs"
            >
              Discard Changes
            </Button>
          )}

          <Button
            type="button"
            onClick={handleSaveAll}
            disabled={isSaving || !hasChanges}
            className="bg-[#1B5E3B] hover:bg-[#203a2b] text-white text-xs gap-2 min-w-32"
          >
            {isSaving ? (
              <>
                <Loader2 className="size-3.5 animate-spin" />
                {saveProgress || "Saving..."}
              </>
            ) : (
              <>
                <Check className="size-3.5" />
                Save Skills ({activeSkillsCount})
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}
