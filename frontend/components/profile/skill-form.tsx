"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Loader2, Check, ChevronsUpDown } from "lucide-react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
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
import { cn } from "@/lib/utils";

export type ProfileSkill = {
  id: string;
  skill_name: string;
  proficiency: string;
};

interface SkillFormProps {
  initialData?: ProfileSkill;
  onSave: (data: Partial<ProfileSkill>) => Promise<void>;
  onCancel: () => void;
  isSaving: boolean;
  error: string | null;
}

const COMMON_SKILLS = [
  "Python",
  "Java",
  "JavaScript",
  "TypeScript",
  "C",
  "C++",
  "SQL",
  "HTML",
  "CSS",
  "React",
  "Next.js",
  "Node.js",
  "FastAPI",
  "Django",
  "Flask",
  "PyTorch",
  "TensorFlow",
  "Scikit-learn",
  "Pandas",
  "NumPy",
  "Matplotlib",
  "Git",
  "GitHub",
  "Docker",
  "PostgreSQL",
  "MongoDB",
  "Machine Learning",
  "Deep Learning",
  "Data Science",
  "Artificial Intelligence",
  "NLP",
  "Computer Vision",
];

const PROFICIENCIES = ["Beginner", "Intermediate", "Advanced", "Expert"];

export function SkillForm({ initialData, onSave, onCancel, isSaving, error }: SkillFormProps) {
  const skillName = initialData?.skill_name || "";
  const [proficiency, setProficiency] = useState(initialData?.proficiency || "");
  const [openCombo, setOpenCombo] = useState(false);
  const [customSkill, setCustomSkill] = useState("");

  const isEditing = !!initialData;

  const isSkillStandard = skillName === "" || COMMON_SKILLS.includes(skillName);
  
  // Local state to keep track of what exactly is selected in combobox
  const [comboValue, setComboValue] = useState(isSkillStandard ? skillName : "Other");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    const finalSkillName = comboValue === "Other" ? customSkill : comboValue;
    
    onSave({
      skill_name: finalSkillName,
      proficiency,
    });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4 rounded-xl border border-border bg-card p-6 shadow-sm mb-6">
      <h3 className="text-lg font-medium">{isEditing ? "Edit Skill" : "Add Skill"}</h3>
      
      {error && (
        <div className="rounded-md bg-destructive/15 p-3 text-sm text-destructive">
          {error}
        </div>
      )}

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <Label htmlFor="skill_name">Skill <span className="text-destructive">*</span></Label>
          <Popover open={openCombo} onOpenChange={setOpenCombo}>
            <PopoverTrigger
                aria-expanded={openCombo}
                className="flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                disabled={isSaving || isEditing}
              >
                {comboValue
                  ? comboValue
                  : "Select or search skill..."}
                <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
            </PopoverTrigger>
            <PopoverContent className="w-[var(--radix-popover-trigger-width)] p-0">
              <Command>
                <CommandInput placeholder="Search skill..." />
                <CommandList>
                  <CommandEmpty>No skill found.</CommandEmpty>
                  <CommandGroup>
                    {COMMON_SKILLS.map((skill) => (
                      <CommandItem
                        key={skill}
                        value={skill}
                        onSelect={() => {
                          setComboValue(skill);
                          setOpenCombo(false);
                        }}
                      >
                        <Check
                          className={cn(
                            "mr-2 h-4 w-4",
                            comboValue === skill ? "opacity-100" : "opacity-0"
                          )}
                        />
                        {skill}
                      </CommandItem>
                    ))}
                    <CommandItem
                      value="Other"
                      onSelect={() => {
                        setComboValue("Other");
                        setOpenCombo(false);
                      }}
                    >
                      <Check
                        className={cn(
                          "mr-2 h-4 w-4",
                          comboValue === "Other" ? "opacity-100" : "opacity-0"
                        )}
                      />
                      Other (Custom Skill)
                    </CommandItem>
                  </CommandGroup>
                </CommandList>
              </Command>
            </PopoverContent>
          </Popover>

          {comboValue === "Other" && (
            <Input
              value={customSkill}
              onChange={(e) => setCustomSkill(e.target.value)}
              disabled={isSaving || isEditing}
              placeholder="Enter custom skill"
              className="mt-2"
              required
            />
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="proficiency">Proficiency <span className="text-destructive">*</span></Label>
          <Select 
            value={proficiency} 
            onValueChange={(val) => setProficiency(val || "")}
            disabled={isSaving}
            required
          >
            <SelectTrigger id="proficiency">
              <SelectValue placeholder="Select proficiency" />
            </SelectTrigger>
            <SelectContent>
              {PROFICIENCIES.map((lvl) => (
                <SelectItem key={lvl} value={lvl}>{lvl}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="flex justify-end space-x-3 pt-4">
        <Button type="button" variant="outline" onClick={onCancel} disabled={isSaving}>
          Cancel
        </Button>
        <Button type="submit" disabled={isSaving || (!comboValue && !isEditing) || !proficiency} className="bg-saffron text-saffron-foreground hover:bg-saffron/90">
          {isSaving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          {isSaving ? "Saving..." : "Save"}
        </Button>
      </div>
    </form>
  );
}
