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

export type Education = {
  id: string;
  institution: string;
  degree: string;
  field_of_study?: string | null;
  start_date: string;
  end_date?: string | null;
  currently_studying: boolean;
  grade?: string | null;
};

interface EducationFormProps {
  initialData?: Education;
  onSave: (data: Partial<Education>) => Promise<void>;
  onCancel: () => void;
  isSaving: boolean;
  error: string | null;
}

const COMMON_DEGREES = [
  "B.Tech / B.E.",
  "BCA",
  "B.Sc.",
  "B.Com",
  "BBA",
  "BA",
  "MCA",
  "M.Sc.",
  "M.Com",
  "MBA",
  "MA",
  "M.Tech / M.E.",
  "PhD",
  "Diploma",
];

const COMMON_FIELDS = [
  "Computer Science",
  "Artificial Intelligence & Machine Learning",
  "Data Science",
  "Information Technology",
  "Electronics & Communication",
  "Electrical Engineering",
  "Mechanical Engineering",
  "Civil Engineering",
  "Mathematics",
  "Physics",
  "Chemistry",
  "Business Administration",
  "Finance",
  "Economics",
  "Commerce",
  "English",
];

export function EducationForm({ initialData, onSave, onCancel, isSaving, error }: EducationFormProps) {
  const initialDegree = initialData?.degree || "";
  const isDegreeStandard = initialDegree === "" || COMMON_DEGREES.includes(initialDegree);
  
  const initialField = initialData?.field_of_study || "";
  const isFieldStandard = initialField === "" || COMMON_FIELDS.includes(initialField);

  const [formData, setFormData] = useState({
    institution: initialData?.institution || "",
    degree: isDegreeStandard ? initialDegree : "Other",
    custom_degree: isDegreeStandard ? "" : initialDegree,
    field_of_study: isFieldStandard ? initialField : "Other",
    custom_field_of_study: isFieldStandard ? "" : initialField,
    start_date: initialData?.start_date || "",
    end_date: initialData?.end_date || "",
    currently_studying: initialData?.currently_studying || false,
    grade: initialData?.grade || "",
  });

  const [openFieldCombo, setOpenFieldCombo] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value,
    }));
  };

  const handleSelectChange = (name: string, value: string) => {
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    const finalDegree = formData.degree === "Other" ? formData.custom_degree : formData.degree;
    const finalField = formData.field_of_study === "Other" ? formData.custom_field_of_study : formData.field_of_study;
    
    onSave({
      ...formData,
      degree: finalDegree,
      field_of_study: finalField || null,
      end_date: formData.currently_studying ? null : (formData.end_date || null),
      grade: formData.grade || null,
    });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4 rounded-xl border border-border bg-card p-6 shadow-sm">
      <h3 className="text-lg font-medium">{initialData ? "Edit Education" : "Add Education"}</h3>
      
      {error && (
        <div className="rounded-md bg-destructive/15 p-3 text-sm text-destructive">
          {error}
        </div>
      )}

      <div className="space-y-2">
        <Label htmlFor="institution">Institution <span className="text-destructive">*</span></Label>
        <Input
          id="institution"
          name="institution"
          value={formData.institution}
          onChange={handleChange}
          required
          disabled={isSaving}
          placeholder="e.g. University of Example"
        />
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <Label htmlFor="degree">Degree <span className="text-destructive">*</span></Label>
          <Select 
            value={formData.degree} 
            onValueChange={(val) => handleSelectChange("degree", val || "")}
            disabled={isSaving}
            required
          >
            <SelectTrigger id="degree">
              <SelectValue placeholder="Select a degree" />
            </SelectTrigger>
            <SelectContent>
              {COMMON_DEGREES.map((deg) => (
                <SelectItem key={deg} value={deg}>{deg}</SelectItem>
              ))}
              <SelectItem value="Other">Other</SelectItem>
            </SelectContent>
          </Select>
          
          {formData.degree === "Other" && (
            <Input
              name="custom_degree"
              value={formData.custom_degree}
              onChange={handleChange}
              required
              disabled={isSaving}
              placeholder="Enter custom degree"
              className="mt-2"
            />
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="field_of_study">Field of Study</Label>
          <Popover open={openFieldCombo} onOpenChange={setOpenFieldCombo}>
            <PopoverTrigger
                aria-expanded={openFieldCombo}
                className="flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                disabled={isSaving}
              >
                {formData.field_of_study
                  ? formData.field_of_study
                  : "Select field of study..."}
                <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
            </PopoverTrigger>
            <PopoverContent className="w-[var(--radix-popover-trigger-width)] p-0">
              <Command>
                <CommandInput placeholder="Search field..." />
                <CommandList>
                  <CommandEmpty>No field found.</CommandEmpty>
                  <CommandGroup>
                    {COMMON_FIELDS.map((field) => (
                      <CommandItem
                        key={field}
                        value={field}
                        onSelect={() => {
                          handleSelectChange("field_of_study", field);
                          setOpenFieldCombo(false);
                        }}
                      >
                        <Check
                          className={cn(
                            "mr-2 h-4 w-4",
                            formData.field_of_study === field ? "opacity-100" : "opacity-0"
                          )}
                        />
                        {field}
                      </CommandItem>
                    ))}
                    <CommandItem
                      value="Other"
                      onSelect={() => {
                        handleSelectChange("field_of_study", "Other");
                        setOpenFieldCombo(false);
                      }}
                    >
                      <Check
                        className={cn(
                          "mr-2 h-4 w-4",
                          formData.field_of_study === "Other" ? "opacity-100" : "opacity-0"
                        )}
                      />
                      Other
                    </CommandItem>
                  </CommandGroup>
                </CommandList>
              </Command>
            </PopoverContent>
          </Popover>

          {formData.field_of_study === "Other" && (
            <Input
              name="custom_field_of_study"
              value={formData.custom_field_of_study}
              onChange={handleChange}
              disabled={isSaving}
              placeholder="Enter custom field of study"
              className="mt-2"
            />
          )}
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <Label htmlFor="start_date">Start Date <span className="text-destructive">*</span></Label>
          <Input
            id="start_date"
            name="start_date"
            type="date"
            value={formData.start_date}
            onChange={handleChange}
            required
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
            disabled={isSaving || formData.currently_studying}
            required={!formData.currently_studying}
          />
        </div>
      </div>

      <div className="flex items-center space-x-2">
        <input
          type="checkbox"
          id="currently_studying"
          name="currently_studying"
          checked={formData.currently_studying}
          onChange={handleChange}
          disabled={isSaving}
          className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
        />
        <Label htmlFor="currently_studying" className="font-normal">
          I am currently studying here
        </Label>
      </div>

      <div className="space-y-2">
        <Label htmlFor="grade">Grade (Optional)</Label>
        <Input
          id="grade"
          name="grade"
          value={formData.grade}
          onChange={handleChange}
          disabled={isSaving}
          placeholder="e.g. 3.8 GPA"
        />
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
