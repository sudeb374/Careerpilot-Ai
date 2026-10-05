"use client";

import { Building2, Calendar, GraduationCap, Pencil, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { Education } from "./education-form";

interface EducationCardProps {
  education: Education;
  onEdit: () => void;
  onDelete: () => void;
  isDeleting: boolean;
}

export function EducationCard({ education, onEdit, onDelete, isDeleting }: EducationCardProps) {
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'short'
    });
  };

  return (
    <div className="relative rounded-xl border border-border bg-card p-6 shadow-sm transition-all hover:shadow-md">
      <div className="flex justify-between items-start gap-4">
        <div className="space-y-3">
          <div>
            <h4 className="text-lg font-semibold text-foreground flex items-center gap-2">
              <Building2 className="h-5 w-5 text-primary" />
              {education.institution}
            </h4>
            <p className="text-muted-foreground flex items-center gap-2 mt-1">
              <GraduationCap className="h-4 w-4" />
              {education.degree}{education.field_of_study ? `, ${education.field_of_study}` : ""}
            </p>
          </div>
          
          <div className="flex items-center gap-4 text-sm text-muted-foreground">
            <span className="flex items-center gap-1">
              <Calendar className="h-4 w-4" />
              {formatDate(education.start_date)} - {education.currently_studying ? "Present" : (education.end_date ? formatDate(education.end_date) : "")}
            </span>
            {education.grade && (
              <span className="px-2 py-0.5 rounded-full bg-secondary text-secondary-foreground text-xs font-medium">
                Grade: {education.grade}
              </span>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button 
            variant="ghost" 
            size="icon" 
            onClick={onEdit}
            disabled={isDeleting}
            aria-label="Edit education"
          >
            <Pencil className="h-4 w-4" />
          </Button>
          <Button 
            variant="ghost" 
            size="icon" 
            onClick={onDelete}
            disabled={isDeleting}
            className="text-destructive hover:text-destructive hover:bg-destructive/10"
            aria-label="Delete education"
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}
