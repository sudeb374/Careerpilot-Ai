"use client";

import { useState, useEffect, useRef } from "react";
import { Search, X, Loader2 } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { createClient } from "@/lib/supabase/client";

export type FiltersState = {
  q: string;
  opportunity_type: string;
  work_model: string;
  location: string;
  domain: string;
  skill_id: string;
  skill_name?: string; // For display
};

interface OpportunityFiltersProps {
  filters: FiltersState;
  onFilterChange: (filters: Partial<FiltersState>) => void;
  onClear: () => void;
}

export function OpportunityFilters({ filters, onFilterChange, onClear }: OpportunityFiltersProps) {
  // Local state for debouncing
  const [searchValue, setSearchValue] = useState(filters.q);
  const [locationValue, setLocationValue] = useState(filters.location);
  const [domainValue, setDomainValue] = useState(filters.domain);

  // Skill search state
  const [skillSearch, setSkillSearch] = useState("");
  const [skillResults, setSkillResults] = useState<Record<string, any>[]>([]); // eslint-disable-line @typescript-eslint/no-explicit-any
  const [searchingSkills, setSearchingSkills] = useState(false);
  const [showSkillDropdown, setShowSkillDropdown] = useState(false);
  const skillDropdownRef = useRef<HTMLDivElement>(null);

  const supabase = createClient();
  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  // Debounce effect for general text inputs
  useEffect(() => {
    const timer = setTimeout(() => {
      if (searchValue !== filters.q) onFilterChange({ q: searchValue });
      if (locationValue !== filters.location) onFilterChange({ location: locationValue });
      if (domainValue !== filters.domain) onFilterChange({ domain: domainValue });
    }, 500);
    return () => clearTimeout(timer);
  }, [searchValue, locationValue, domainValue, filters, onFilterChange]);

  // Sync back from props if changed externally (like clearing)
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setSearchValue(filters.q);
    setLocationValue(filters.location);
    setDomainValue(filters.domain);
  }, [filters.q, filters.location, filters.domain]);

  // Handle skill search
  useEffect(() => {
    const searchSkills = async () => {
      if (!skillSearch || skillSearch.length < 2) {
        setSkillResults([]);
        return;
      }
      
      setSearchingSkills(true);
      try {
        const { data: { session } } = await supabase.auth.getSession();
        if (!session) return;
        
        const res = await fetch(`${API_URL}/api/v1/skills/search?q=${encodeURIComponent(skillSearch)}&limit=10`, {
          headers: { Authorization: `Bearer ${session.access_token}` },
        });
        
        if (res.ok) {
          const data = await res.json();
          setSkillResults(data);
        }
      } catch (err) {
        console.error("Failed to search skills", err);
      } finally {
        setSearchingSkills(false);
      }
    };

    const timer = setTimeout(searchSkills, 300);
    return () => clearTimeout(timer);
  }, [skillSearch, API_URL, supabase.auth]);

  // Click outside for skill dropdown
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (skillDropdownRef.current && !skillDropdownRef.current.contains(e.target as Node)) {
        setShowSkillDropdown(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const selectSkill = (skill: Record<string, any>) => { // eslint-disable-line @typescript-eslint/no-explicit-any
    onFilterChange({ skill_id: skill.id, skill_name: skill.name });
    setSkillSearch("");
    setShowSkillDropdown(false);
  };

  const removeSkill = () => {
    onFilterChange({ skill_id: "", skill_name: "" });
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5 space-y-5">
      <div className="flex justify-between items-center">
        <h2 className="font-semibold text-lg text-[#14261C]">Filters</h2>
        <Button variant="ghost" size="sm" onClick={onClear} className="text-muted-foreground hover:text-foreground">
          Clear Filters
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="relative">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input 
            placeholder="Search roles, companies, skills, or keywords..." 
            className="pl-9"
            value={searchValue}
            onChange={(e) => setSearchValue(e.target.value)}
          />
        </div>

        <Select value={filters.opportunity_type} onValueChange={(val) => onFilterChange({ opportunity_type: val === "all" || !val ? "" : val })}>
          <SelectTrigger>
            <SelectValue placeholder="Opportunity Type" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Types</SelectItem>
            <SelectItem value="Internship">Internship</SelectItem>
            <SelectItem value="Full-Time">Full-Time</SelectItem>
            <SelectItem value="Contract">Contract</SelectItem>
            <SelectItem value="Part-Time">Part-Time</SelectItem>
            <SelectItem value="Freelance">Freelance</SelectItem>
          </SelectContent>
        </Select>

        <Select value={filters.work_model} onValueChange={(val) => onFilterChange({ work_model: val === "all" || !val ? "" : val })}>
          <SelectTrigger>
            <SelectValue placeholder="Work Model" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Models</SelectItem>
            <SelectItem value="Remote">Remote</SelectItem>
            <SelectItem value="Hybrid">Hybrid</SelectItem>
            <SelectItem value="On-site">On-site</SelectItem>
          </SelectContent>
        </Select>

        <Input 
          placeholder="Location (e.g. City, State, Country)" 
          value={locationValue}
          onChange={(e) => setLocationValue(e.target.value)}
        />

        <Input 
          placeholder="Domain / Industry (e.g. Technology...)" 
          value={domainValue}
          onChange={(e) => setDomainValue(e.target.value)}
        />

        <div className="relative" ref={skillDropdownRef}>
          {filters.skill_id && filters.skill_name ? (
            <div className="flex h-10 items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background">
              <span className="truncate">{filters.skill_name}</span>
              <button 
                type="button" 
                onClick={removeSkill}
                className="text-muted-foreground hover:text-foreground focus:outline-none"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          ) : (
            <Input 
              placeholder="Search by Skill" 
              value={skillSearch}
              onChange={(e) => {
                setSkillSearch(e.target.value);
                setShowSkillDropdown(true);
              }}
              onFocus={() => setShowSkillDropdown(true)}
            />
          )}

          {showSkillDropdown && skillSearch && (
            <div className="absolute z-10 w-full mt-1 bg-white border shadow-md rounded-md max-h-60 overflow-y-auto">
              {searchingSkills && <div className="p-3 text-sm text-center text-muted-foreground flex justify-center"><Loader2 className="h-4 w-4 animate-spin" /></div>}
              {!searchingSkills && skillResults.map((s) => (
                <div 
                  key={s.id} 
                  className="px-3 py-2 text-sm hover:bg-gray-100 cursor-pointer"
                  onClick={() => selectSkill(s)}
                >
                  {s.name}
                </div>
              ))}
              {!searchingSkills && skillSearch.length >= 2 && skillResults.length === 0 && (
                <div className="p-3 text-sm text-center text-muted-foreground">No skills found matching &quot;{skillSearch}&quot;</div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
