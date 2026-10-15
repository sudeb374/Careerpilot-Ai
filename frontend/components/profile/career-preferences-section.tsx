"use client";

import { useEffect, useState } from "react";
import { createClient } from "@/lib/supabase/client";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2, X, ChevronsUpDown, Check } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from "@/components/ui/command";
import { LocationAutocomplete } from "@/components/ui/location-autocomplete";
import { cn } from "@/lib/utils";

type CareerPreferences = {
  desired_roles: string[];
  locations: string[];
  job_type: string[];
  work_model: string[];
  preferred_domains: string[];
  sponsorship_needed: boolean | null;
};

const JOB_TYPES = ["Internship", "Full-Time", "Part-Time", "Contract"];
const WORK_MODELS = ["Remote", "Hybrid", "On-site"];
const SUGGESTED_ROLES = [
  "Software Engineer", "Data Scientist", "Machine Learning Engineer", "AI Engineer", 
  "Data Analyst", "Backend Developer", "Frontend Developer", "Full Stack Developer", 
  "DevOps Engineer", "Cloud Engineer", "QA Engineer", "Cybersecurity Analyst", 
  "Product Analyst", "Business Analyst"
];
const SUGGESTED_DOMAINS = [
  "Artificial Intelligence", "Machine Learning", "Data Science", "Software Development", 
  "FinTech", "EdTech", "HealthTech", "Cybersecurity", "E-commerce", "Cloud Computing", 
  "Data Analytics", "SaaS"
];

function MultiSelectField({ 
  label, 
  values, 
  onChange, 
  suggestions, 
  placeholder,
  disabled
}: { 
  label: string, 
  values: string[], 
  onChange: (v: string[]) => void, 
  suggestions?: string[], 
  placeholder: string,
  disabled: boolean
}) {
  const [open, setOpen] = useState(false);
  const [inputValue, setInputValue] = useState("");

  const handleRemove = (valToRemove: string) => {
    onChange(values.filter(v => v !== valToRemove));
  };

  const handleAdd = (val: string) => {
    const clean = val.trim();
    if (clean && !values.some(v => v.toLowerCase() === clean.toLowerCase())) {
      onChange([...values, clean]);
    }
    setInputValue("");
    setOpen(false);
  };

  const availableSuggestions = (suggestions || []).filter(
    s => !values.some(v => v.toLowerCase() === s.toLowerCase())
  );

  return (
    <div className="space-y-3">
      <Label>{label}</Label>
      <div className="flex flex-wrap gap-2 mb-2">
        {values.map(val => (
          <Badge key={val} variant="secondary" className="px-2 py-1 flex items-center gap-1 text-sm rounded-md">
            {val}
            {!disabled && (
              <button
                type="button"
                onClick={() => handleRemove(val)}
                className="text-muted-foreground hover:text-foreground ml-1"
              >
                <X className="h-3 w-3" />
              </button>
            )}
          </Badge>
        ))}
      </div>
      
      {suggestions ? (
        <Popover open={open} onOpenChange={setOpen}>
          <PopoverTrigger
            className="flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 text-muted-foreground font-normal"
            disabled={disabled}
          >
            {placeholder}
            <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
          </PopoverTrigger>
          <PopoverContent className="w-[var(--radix-popover-trigger-width)] p-0" align="start">
            <Command>
              <CommandInput 
                placeholder="Search or add custom..." 
                value={inputValue}
                onValueChange={setInputValue}
              />
              <CommandList>
                <CommandEmpty>
                  {inputValue.trim() ? (
                    <div 
                      className="p-2 text-sm cursor-pointer hover:bg-muted"
                      onClick={() => handleAdd(inputValue)}
                    >
                      Add &quot;{inputValue.trim()}&quot;
                    </div>
                  ) : "No results found."}
                </CommandEmpty>
                <CommandGroup>
                  {availableSuggestions.map((suggestion) => (
                    <CommandItem
                      key={suggestion}
                      onSelect={() => handleAdd(suggestion)}
                    >
                      <Check className="mr-2 h-4 w-4 opacity-0" />
                      {suggestion}
                    </CommandItem>
                  ))}
                  {inputValue.trim() && !availableSuggestions.some(s => s.toLowerCase() === inputValue.trim().toLowerCase()) && (
                    <CommandItem onSelect={() => handleAdd(inputValue)}>
                      <Check className="mr-2 h-4 w-4 opacity-0" />
                      Add &quot;{inputValue.trim()}&quot;
                    </CommandItem>
                  )}
                </CommandGroup>
              </CommandList>
            </Command>
          </PopoverContent>
        </Popover>
      ) : (
        <div className="flex gap-2">
          <Input 
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                e.preventDefault();
                handleAdd(inputValue);
              }
            }}
            placeholder={placeholder}
            disabled={disabled}
          />
          <Button 
            type="button" 
            variant="outline" 
            onClick={() => handleAdd(inputValue)}
            disabled={disabled || !inputValue.trim()}
          >
            Add
          </Button>
        </div>
      )}
    </div>
  );
}

function ToggleGroup({ 
  label, 
  options, 
  values, 
  onChange,
  disabled
}: { 
  label: string, 
  options: string[], 
  values: string[], 
  onChange: (v: string[]) => void,
  disabled: boolean
}) {
  const toggle = (opt: string) => {
    if (values.includes(opt)) {
      onChange(values.filter(v => v !== opt));
    } else {
      onChange([...values, opt]);
    }
  };

  return (
    <div className="space-y-3">
      <Label>{label}</Label>
      <div className="flex flex-wrap gap-2">
        {options.map(opt => {
          const selected = values.includes(opt);
          return (
            <button
              key={opt}
              type="button"
              disabled={disabled}
              onClick={() => toggle(opt)}
              className={cn(
                "px-3 py-1.5 rounded-full border text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                selected 
                  ? "bg-primary text-primary-foreground border-primary" 
                  : "bg-background text-foreground border-input hover:bg-accent hover:text-accent-foreground",
                disabled && "opacity-50 cursor-not-allowed"
              )}
            >
              {opt}
            </button>
          );
        })}
      </div>
    </div>
  );
}

function TriStateToggle({
  label,
  value,
  onChange,
  disabled
}: {
  label: string,
  value: boolean | null,
  onChange: (v: boolean | null) => void,
  disabled: boolean
}) {
  const options = [
    { label: "Yes", val: true },
    { label: "No", val: false },
    { label: "Not specified", val: null }
  ];

  return (
    <div className="space-y-3">
      <Label>{label}</Label>
      <div className="flex flex-wrap gap-2">
        {options.map(opt => {
          const selected = value === opt.val;
          return (
            <button
              key={opt.label}
              type="button"
              disabled={disabled}
              onClick={() => onChange(opt.val)}
              className={cn(
                "px-3 py-1.5 rounded-full border text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                selected 
                  ? "bg-primary text-primary-foreground border-primary" 
                  : "bg-background text-foreground border-input hover:bg-accent hover:text-accent-foreground",
                disabled && "opacity-50 cursor-not-allowed"
              )}
            >
              {opt.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}

export function CareerPreferencesSection() {
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const [prefs, setPrefs] = useState<CareerPreferences>({
    desired_roles: [],
    locations: [],
    job_type: [],
    work_model: [],
    preferred_domains: [],
    sponsorship_needed: null,
  });

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const fetchPrefs = async () => {
    try {
      const supabase = createClient();
      const { data: { session } } = await supabase.auth.getSession();
      
      if (!session) {
        setError("You must be logged in to view your profile.");
        setIsLoading(false);
        return;
      }

      const res = await fetch(`${API_URL}/api/v1/profile/preferences`, {
        headers: {
          "Authorization": `Bearer ${session.access_token}`
        }
      });

      if (res.ok) {
        const data = await res.json();
        setPrefs({
          desired_roles: data.desired_roles || [],
          locations: data.locations || [],
          job_type: data.job_type || [],
          work_model: data.work_model || [],
          preferred_domains: data.preferred_domains || [],
          sponsorship_needed: data.sponsorship_needed,
        });
      } else if (res.status !== 404) {
        setError("Failed to load career preferences.");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "An unexpected error occurred.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchPrefs();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [API_URL]);

  const handleSave = async () => {
    setError(null);
    setSuccess(null);
    setIsSaving(true);

    try {
      const supabase = createClient();
      const { data: { session } } = await supabase.auth.getSession();
      
      if (!session) {
        setError("Your session has expired. Please log in again.");
        setIsSaving(false);
        return;
      }

      const res = await fetch(`${API_URL}/api/v1/profile/preferences`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${session.access_token}`
        },
        body: JSON.stringify(prefs),
      });

      if (res.ok) {
        setSuccess("Preferences saved successfully!");
        // Refresh to confirm backend state
        await fetchPrefs();
      } else {
        const errData = await res.json().catch(() => ({}));
        setError(errData.detail || "Failed to save preferences.");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "An unexpected error occurred while saving.");
    } finally {
      setIsSaving(false);
      // clear success message after 3 seconds
      setTimeout(() => setSuccess(null), 3000);
    }
  };

  if (isLoading) {
    return (
      <Card className="w-full mb-6 border-border shadow-sm">
        <CardContent className="flex h-48 items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full mb-6 border-border shadow-sm">
      <CardHeader>
        <CardTitle>Career Preferences</CardTitle>
        <CardDescription>
          Tell CareerPilot what kinds of opportunities you&apos;re looking for. These preferences will help personalize your internship and job recommendations.
        </CardDescription>
      </CardHeader>
      
      <CardContent className="space-y-8">
        {error && (
          <div className="rounded-md bg-destructive/15 p-3 text-sm text-destructive">
            {error}
          </div>
        )}
        {success && (
          <div className="rounded-md bg-emerald-500/15 p-3 text-sm text-emerald-600 dark:text-emerald-400 transition-all">
            {success}
          </div>
        )}

        <div className="grid gap-8 sm:grid-cols-2">
          <MultiSelectField
            label="Desired Roles"
            placeholder="Search or add roles..."
            suggestions={SUGGESTED_ROLES}
            values={prefs.desired_roles}
            onChange={(v) => setPrefs({ ...prefs, desired_roles: v })}
            disabled={isSaving}
          />

          <MultiSelectField
            label="Preferred Domains"
            placeholder="Search or add domains..."
            suggestions={SUGGESTED_DOMAINS}
            values={prefs.preferred_domains}
            onChange={(v) => setPrefs({ ...prefs, preferred_domains: v })}
            disabled={isSaving}
          />
        </div>

        <div className="grid gap-8 sm:grid-cols-2">
          <ToggleGroup
            label="Job Type"
            options={JOB_TYPES}
            values={prefs.job_type}
            onChange={(v) => setPrefs({ ...prefs, job_type: v })}
            disabled={isSaving}
          />

          <ToggleGroup
            label="Work Model"
            options={WORK_MODELS}
            values={prefs.work_model}
            onChange={(v) => setPrefs({ ...prefs, work_model: v })}
            disabled={isSaving}
          />
        </div>

        <div className="grid gap-8 sm:grid-cols-2">
          <LocationAutocomplete
            label="Preferred Locations"
            placeholder="Type a city or locality (e.g., Kolkata, Sector V, Pune, Hinjawadi)..."
            values={prefs.locations}
            onChange={(v) => setPrefs({ ...prefs, locations: v })}
            disabled={isSaving}
            description="Add target work locations. Suggestions include Indian cities, localities, and postal zones."
          />

          <TriStateToggle
            label="Sponsorship Needed?"
            value={prefs.sponsorship_needed}
            onChange={(v) => setPrefs({ ...prefs, sponsorship_needed: v })}
            disabled={isSaving}
          />
        </div>

      </CardContent>
      <CardFooter className="flex justify-end pt-2">
        <Button 
          onClick={handleSave} 
          disabled={isSaving} 
          className="bg-saffron text-saffron-foreground hover:bg-saffron/90 min-w-32"
        >
          {isSaving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
          {isSaving ? "Saving..." : "Save Preferences"}
        </Button>
      </CardFooter>
    </Card>
  );
}
