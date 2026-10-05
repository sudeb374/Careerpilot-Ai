"use client";

import { Calendar, FolderGit2, Link as LinkIcon, Pencil, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { Project } from "./project-form";
import Link from "next/link";

interface ProjectCardProps {
  project: Project;
  onEdit: () => void;
  onDelete: () => void;
  isDeleting: boolean;
}

export function ProjectCard({ project, onEdit, onDelete, isDeleting }: ProjectCardProps) {
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
              <FolderGit2 className="h-5 w-5 text-primary" />
              {project.name}
            </h4>
            
            {project.url && (
              <Link 
                href={project.url} 
                target="_blank" 
                rel="noopener noreferrer"
                className="text-primary hover:underline text-sm flex items-center gap-1 mt-1 w-max"
              >
                <LinkIcon className="h-3 w-3" />
                {project.url}
              </Link>
            )}
          </div>
          
          {project.description && (
            <p className="text-muted-foreground text-sm whitespace-pre-wrap">
              {project.description}
            </p>
          )}
          
          {(project.start_date || project.end_date) && (
            <div className="flex items-center gap-4 text-sm text-muted-foreground">
              <span className="flex items-center gap-1">
                <Calendar className="h-4 w-4" />
                {project.start_date ? formatDate(project.start_date) : "Unknown Start"} 
                {" - "} 
                {project.end_date ? formatDate(project.end_date) : "Present"}
              </span>
            </div>
          )}
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <Button 
            variant="ghost" 
            size="icon" 
            onClick={onEdit}
            disabled={isDeleting}
            aria-label="Edit project"
          >
            <Pencil className="h-4 w-4" />
          </Button>
          <Button 
            variant="ghost" 
            size="icon" 
            onClick={onDelete}
            disabled={isDeleting}
            className="text-destructive hover:text-destructive hover:bg-destructive/10"
            aria-label="Delete project"
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}
