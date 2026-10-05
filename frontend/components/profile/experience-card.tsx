"use client";

import { useEffect, useState } from "react";
import { Briefcase, Calendar, MapPin, Pencil, Trash2, Building2, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { createClient } from "@/lib/supabase/client";
import type { Experience } from "./experience-form";

export type ExperienceSkill = {
  id: string;
  profile_skill_id: string;
  skill_id: string | null;
  skill_name: string;
  is_custom: boolean;
  proficiency: string | null;
  created_at: string;
};

interface ExperienceCardProps {
  experience: Experience;
  onEdit: () => void;
  onDelete: () => void;
  isDeleting: boolean;
}

export function ExperienceCard({ experience, onEdit, onDelete, isDeleting }: ExperienceCardProps) {
  const [skills, setSkills] = useState<ExperienceSkill[]>([]);
  const [isLoadingSkills, setIsLoadingSkills] = useState(false);

  useEffect(() => {
    const fetchSkills = async () => {
      setIsLoadingSkills(true);
      try {
        const supabase = createClient();
        const { data: { session } } = await supabase.auth.getSession();
        if (!session) return;
        
        const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        const res = await fetch(`${API_URL}/api/v1/profile/experience/${experience.id}/skills`, {
          headers: { Authorization: `Bearer ${session.access_token}` }
        });
        if (res.ok) {
          const data = await res.json();
          setSkills(data);
        }
      } catch (err) {
        console.error("Failed to load experience skills", err);
      } finally {
        setIsLoadingSkills(false);
      }
    };

    fetchSkills();
  }, [experience.id]);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'short'
    });
  };

  return (
    <div className="relative rounded-xl border border-border bg-card p-6 shadow-sm transition-all hover:shadow-md">
      <div className="flex justify-between items-start gap-4">
        <div className="space-y-3 flex-1">
          <div>
            <h4 className="text-lg font-semibold text-foreground flex items-center gap-2">
              <Briefcase className="h-5 w-5 text-primary" />
              {experience.title}
            </h4>
            
            <div className="flex flex-wrap items-center gap-4 text-muted-foreground text-sm mt-1">
              <span className="flex items-center gap-1 font-medium text-foreground/80">
                <Building2 className="h-4 w-4" />
                {experience.company}
              </span>
              
              {experience.location && (
                <span className="flex items-center gap-1">
                  <MapPin className="h-4 w-4" />
                  {experience.location}
                </span>
              )}
            </div>
          </div>
          
          {(experience.start_date || experience.end_date || experience.is_current) && (
            <div className="flex items-center gap-4 text-sm text-muted-foreground">
              <span className="flex items-center gap-1">
                <Calendar className="h-4 w-4" />
                {experience.start_date ? formatDate(experience.start_date) : "Unknown Start"} 
                {" - "} 
                {experience.is_current ? (
                  <span className="font-medium text-primary">Present</span>
                ) : (
                  experience.end_date ? formatDate(experience.end_date) : "Unknown End"
                )}
              </span>
            </div>
          )}

          {experience.description && (
            <p className="text-muted-foreground text-sm whitespace-pre-wrap mt-3 border-t border-border/50 pt-3">
              {experience.description}
            </p>
          )}

          {/* Skills Section */}
          <div className="mt-4 pt-3 border-t border-border/50">
            <h5 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">Skills Used</h5>
            {isLoadingSkills ? (
              <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
            ) : skills.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {skills.map((skill) => (
                  <Badge key={skill.id} variant="secondary" className="bg-primary/10 text-primary hover:bg-primary/20 font-normal">
                    {skill.skill_name}
                  </Badge>
                ))}
              </div>
            ) : (
              <p className="text-xs text-muted-foreground italic">No skills tagged</p>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <Button 
            variant="ghost" 
            size="icon" 
            onClick={onEdit}
            disabled={isDeleting}
            aria-label="Edit experience"
          >
            <Pencil className="h-4 w-4" />
          </Button>
          <Button 
            variant="ghost" 
            size="icon" 
            onClick={onDelete}
            disabled={isDeleting}
            className="text-destructive hover:text-destructive hover:bg-destructive/10"
            aria-label="Delete experience"
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}
