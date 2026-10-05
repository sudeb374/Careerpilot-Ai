"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Loader2, Pencil, Trash2 } from "lucide-react";
import type { ProfileSkill } from "./skill-form";
import { cn } from "@/lib/utils";

interface SkillCardProps {
  skill: ProfileSkill;
  onEdit: () => void;
  onDelete: () => void;
  isDeleting: boolean;
}

export function SkillCard({ skill, onEdit, onDelete, isDeleting }: SkillCardProps) {
  
  // Helper to color code proficiency badges
  const getProficiencyColor = (level: string) => {
    switch (level.toLowerCase()) {
      case "expert":
        return "bg-green-100 text-green-800 border-green-200 dark:bg-green-900/30 dark:text-green-400 dark:border-green-800";
      case "advanced":
        return "bg-blue-100 text-blue-800 border-blue-200 dark:bg-blue-900/30 dark:text-blue-400 dark:border-blue-800";
      case "intermediate":
        return "bg-amber-100 text-amber-800 border-amber-200 dark:bg-amber-900/30 dark:text-amber-400 dark:border-amber-800";
      case "beginner":
        return "bg-gray-100 text-gray-800 border-gray-200 dark:bg-gray-800/50 dark:text-gray-400 dark:border-gray-700";
      default:
        return "bg-gray-100 text-gray-800 border-gray-200 dark:bg-gray-800/50 dark:text-gray-400 dark:border-gray-700";
    }
  };

  return (
    <Card className="overflow-hidden border-border transition-all hover:border-primary/20 hover:shadow-sm">
      <CardContent className="p-4">
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0 flex-1">
            <h4 className="truncate font-semibold text-foreground" title={skill.skill_name}>
              {skill.skill_name}
            </h4>
            <div className="mt-1 flex items-center">
              <span 
                className={cn(
                  "inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium",
                  getProficiencyColor(skill.proficiency)
                )}
              >
                {skill.proficiency}
              </span>
            </div>
          </div>
          <div className="flex shrink-0 space-x-1">
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 rounded-full text-muted-foreground hover:text-foreground"
              onClick={onEdit}
              disabled={isDeleting}
              title="Edit Proficiency"
            >
              <Pencil className="h-4 w-4" />
              <span className="sr-only">Edit skill</span>
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 rounded-full text-muted-foreground hover:text-destructive"
              onClick={onDelete}
              disabled={isDeleting}
              title="Delete Skill"
            >
              {isDeleting ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Trash2 className="h-4 w-4" />
              )}
              <span className="sr-only">Delete skill</span>
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
