"use client";

import { useState, useEffect } from "react";
import { createClient } from "@/lib/supabase/client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Loader2, X, Search } from "lucide-react";

interface OpportunityFormDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  opportunityToEdit?: Record<string, any>; // eslint-disable-line @typescript-eslint/no-explicit-any
  onSuccess: () => void;
}

export function OpportunityFormDialog({ open, onOpenChange, opportunityToEdit, onSuccess }: OpportunityFormDialogProps) {
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [formData, setFormData] = useState({
    title: "",
    company_name: "",
    company_website: "",
    company_logo_url: "",
    domain: "",
    description: "",
    opportunity_type: "Full-Time",
    work_model: "Remote",
    locations: "",
    required_experience_min: "",
    required_experience_max: "",
    education_requirements: "",
    eligibility: "",
    currency: "USD",
    stipend_min: "",
    stipend_max: "",
    salary_min: "",
    salary_max: "",
    application_url: "",
    deadline: "",
    source_name: "Internal",
    source_url: "",
    external_id: "",
    status: "Draft",
  });

  const [selectedSkills, setSelectedSkills] = useState<{ id: string, name: string }[]>([]);
  const [skillSearch, setSkillSearch] = useState("");
  const [skillResults, setSkillResults] = useState<{ id: string, name: string }[]>([]);
  const [searchingSkills, setSearchingSkills] = useState(false);

  const isEditing = !!opportunityToEdit;
  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  useEffect(() => {
    if (open && opportunityToEdit) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setFormData({
        title: opportunityToEdit.title || "",
        company_name: opportunityToEdit.company_name || "",
        company_website: opportunityToEdit.company_website || "",
        company_logo_url: opportunityToEdit.company_logo_url || "",
        domain: opportunityToEdit.domain || "",
        description: opportunityToEdit.description || "",
        opportunity_type: opportunityToEdit.opportunity_type || "Full-Time",
        work_model: opportunityToEdit.work_model || "Remote",
        locations: opportunityToEdit.locations ? opportunityToEdit.locations.join(", ") : "",
        required_experience_min: opportunityToEdit.required_experience_min?.toString() || "",
        required_experience_max: opportunityToEdit.required_experience_max?.toString() || "",
        education_requirements: opportunityToEdit.education_requirements || "",
        eligibility: opportunityToEdit.eligibility || "",
        currency: opportunityToEdit.currency || "USD",
        stipend_min: opportunityToEdit.stipend_min?.toString() || "",
        stipend_max: opportunityToEdit.stipend_max?.toString() || "",
        salary_min: opportunityToEdit.salary_min?.toString() || "",
        salary_max: opportunityToEdit.salary_max?.toString() || "",
        application_url: opportunityToEdit.application_url || "",
        deadline: opportunityToEdit.deadline ? new Date(opportunityToEdit.deadline).toISOString().slice(0, 16) : "",
        source_name: opportunityToEdit.source_name || "Internal",
        source_url: opportunityToEdit.source_url || "",
        external_id: opportunityToEdit.external_id || "",
        status: opportunityToEdit.status || "Draft",
      });
      setSelectedSkills(opportunityToEdit.skills || []);
    } else if (open) {
      // Reset form on new open
      setFormData({
        title: "", company_name: "", company_website: "", company_logo_url: "", domain: "", description: "",
        opportunity_type: "Full-Time", work_model: "Remote", locations: "", required_experience_min: "",
        required_experience_max: "", education_requirements: "", eligibility: "", currency: "USD",
        stipend_min: "", stipend_max: "", salary_min: "", salary_max: "", application_url: "", deadline: "",
        source_name: "Internal", source_url: "", external_id: "", status: "Draft",
      });
      setSelectedSkills([]);
    }
  }, [open, opportunityToEdit]);

  useEffect(() => {
    const fetchSkills = async () => {
      if (!skillSearch.trim()) {
        setSkillResults([]);
        return;
      }
      setSearchingSkills(true);
      try {
        const supabase = createClient();
        const { data: { session } } = await supabase.auth.getSession();
        if (!session) return;
        const res = await fetch(`${API_URL}/api/v1/skills/search?q=${encodeURIComponent(skillSearch)}&limit=10`, {
          headers: { "Authorization": `Bearer ${session.access_token}` }
        });
        if (res.ok) {
          const data = await res.json();
          setSkillResults(data);
        }
      } catch (err) {
        console.error("Skill search failed", err);
      } finally {
        setSearchingSkills(false);
      }
    };

    const timer = setTimeout(fetchSkills, 300);
    return () => clearTimeout(timer);
  }, [skillSearch, API_URL]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSelectChange = (name: string, value: string) => {
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const addSkill = (skill: { id: string, name: string }) => {
    if (!selectedSkills.some(s => s.id === skill.id)) {
      setSelectedSkills(prev => [...prev, skill]);
    }
    setSkillSearch("");
  };

  const removeSkill = (id: string) => {
    setSelectedSkills(prev => prev.filter(s => s.id !== id));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSaving(true);

    try {
      const minExp = formData.required_experience_min !== "" ? Number(formData.required_experience_min) : 0;
      if (minExp < 0) {
        throw new Error("Experience minimum must be >= 0");
      }
      if (formData.required_experience_max && Number(formData.required_experience_max) < minExp) {
        throw new Error("Experience maximum cannot be less than minimum");
      }
      if (formData.salary_min && formData.salary_max && Number(formData.salary_max) < Number(formData.salary_min)) {
        throw new Error("Salary maximum cannot be less than minimum");
      }
      if (formData.stipend_min && formData.stipend_max && Number(formData.stipend_max) < Number(formData.stipend_min)) {
        throw new Error("Stipend maximum cannot be less than minimum");
      }
      
      const payload: Record<string, any> = { ...formData }; // eslint-disable-line @typescript-eslint/no-explicit-any
      
      // Transform numerical fields
      const numericFields = ["required_experience_min", "required_experience_max", "stipend_min", "stipend_max", "salary_min", "salary_max"];
      for (const field of numericFields) {
        if (payload[field] === "" || payload[field] === null || payload[field] === undefined) {
          payload[field] = field === "required_experience_min" ? 0 : null;
        } else {
          payload[field] = Number(payload[field]);
        }
      }
      
      payload.locations = payload.locations ? payload.locations.split(",").map((l: string) => l.trim()).filter(Boolean) : [];
      payload.deadline = payload.deadline ? new Date(payload.deadline).toISOString() : null;
      payload.required_skill_ids = selectedSkills.map(s => s.id);

      const supabase = createClient();
      const { data: { session } } = await supabase.auth.getSession();
      
      if (!session) throw new Error("Not authenticated");

      const url = isEditing 
        ? `${API_URL}/api/v1/admin/opportunities/${opportunityToEdit.id}`
        : `${API_URL}/api/v1/admin/opportunities`;
        
      const res = await fetch(url, {
        method: isEditing ? "PATCH" : "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${session.access_token}`
        },
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        if (res.status === 409) {
          throw new Error("An opportunity with this Source and External ID already exists.");
        }
        if (errData.detail) {
          throw new Error(typeof errData.detail === 'string' ? errData.detail : JSON.stringify(errData.detail));
        }
        throw new Error("Failed to save opportunity.");
      }

      onSuccess();
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
      setIsSaving(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{isEditing ? "Edit Opportunity" : "Create Opportunity"}</DialogTitle>
          <DialogDescription>
            {isEditing ? "Update the details of this opportunity." : "Add a new opportunity to the platform."}
          </DialogDescription>
        </DialogHeader>

        {error && (
          <div className="bg-destructive/15 text-destructive p-3 rounded-md text-sm mb-4">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            
            {/* Basic Information */}
            <div className="space-y-4 md:col-span-2">
              <h3 className="text-lg font-medium border-b pb-2">Basic Information</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="title">Title *</Label>
                  <Input id="title" name="title" value={formData.title} onChange={handleChange} required />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="company_name">Company Name *</Label>
                  <Input id="company_name" name="company_name" value={formData.company_name} onChange={handleChange} required />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="company_website">Company Website</Label>
                  <Input id="company_website" name="company_website" type="url" value={formData.company_website} onChange={handleChange} />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="company_logo_url">Company Logo URL</Label>
                  <Input id="company_logo_url" name="company_logo_url" type="url" value={formData.company_logo_url} onChange={handleChange} />
                </div>
                <div className="space-y-2 md:col-span-2">
                  <Label htmlFor="domain">Domain / Industry</Label>
                  <Input id="domain" name="domain" value={formData.domain} onChange={handleChange} placeholder="e.g. Technology, Finance, Healthcare..." />
                </div>
              </div>
            </div>

            {/* Opportunity Details */}
            <div className="space-y-4 md:col-span-2">
              <h3 className="text-lg font-medium border-b pb-2">Opportunity Details</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2 md:col-span-2">
                  <Label htmlFor="description">Description</Label>
                  <Textarea id="description" name="description" value={formData.description} onChange={handleChange} rows={4} />
                </div>
                <div className="space-y-2">
                  <Label>Opportunity Type *</Label>
                  <Select value={formData.opportunity_type} onValueChange={(val) => handleSelectChange("opportunity_type", val || "Full-Time")}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Internship">Internship</SelectItem>
                      <SelectItem value="Full-Time">Full-Time</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Work Model *</Label>
                  <Select value={formData.work_model} onValueChange={(val) => handleSelectChange("work_model", val || "Remote")}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Remote">Remote</SelectItem>
                      <SelectItem value="Hybrid">Hybrid</SelectItem>
                      <SelectItem value="On-site">On-site</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2 md:col-span-2">
                  <Label htmlFor="locations">Locations (comma separated)</Label>
                  <Input id="locations" name="locations" value={formData.locations} onChange={handleChange} placeholder="e.g. City, State, Country" />
                </div>
              </div>
            </div>

            {/* Requirements */}
            <div className="space-y-4 md:col-span-2">
              <h3 className="text-lg font-medium border-b pb-2">Requirements</h3>
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label>Required Skills</Label>
                  <div className="flex flex-wrap gap-2 mb-2">
                    {selectedSkills.map(skill => (
                      <Badge key={skill.id} variant="secondary" className="flex items-center gap-1 bg-green-50 text-green-800 hover:bg-green-100 border-green-200">
                        {skill.name}
                        <button type="button" onClick={() => removeSkill(skill.id)} className="text-muted-foreground hover:text-foreground">
                          <X className="h-3 w-3" />
                        </button>
                      </Badge>
                    ))}
                  </div>
                  <div className="relative">
                    <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                    <Input 
                      placeholder="Search and add skills..." 
                      className="pl-8" 
                      value={skillSearch}
                      onChange={(e) => setSkillSearch(e.target.value)}
                    />
                    {skillSearch && skillResults.length > 0 && (
                      <div className="absolute z-10 w-full mt-1 bg-popover border shadow-md rounded-md max-h-48 overflow-y-auto">
                        {skillResults.map(skill => (
                          <div 
                            key={skill.id} 
                            className="px-3 py-2 text-sm hover:bg-muted cursor-pointer flex items-center justify-between"
                            onClick={() => addSkill(skill)}
                          >
                            {skill.name}
                            {selectedSkills.some(s => s.id === skill.id) && <span className="text-xs text-muted-foreground">Added</span>}
                          </div>
                        ))}
                      </div>
                    )}
                    {skillSearch && skillResults.length === 0 && !searchingSkills && (
                      <div className="absolute z-10 w-full mt-1 bg-popover border shadow-md rounded-md p-3 text-sm text-muted-foreground text-center">
                        No skills found matching &quot;{skillSearch}&quot;
                      </div>
                    )}
                  </div>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="required_experience_min">Min Experience (Years)</Label>
                    <Input id="required_experience_min" name="required_experience_min" type="number" step="0.5" min="0" value={formData.required_experience_min} onChange={handleChange} />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="required_experience_max">Max Experience (Years)</Label>
                    <Input id="required_experience_max" name="required_experience_max" type="number" step="0.5" min="0" value={formData.required_experience_max} onChange={handleChange} />
                  </div>
                  <div className="space-y-2 md:col-span-2">
                    <Label htmlFor="education_requirements">Education Requirements</Label>
                    <Input id="education_requirements" name="education_requirements" value={formData.education_requirements} onChange={handleChange} placeholder="e.g. B.Tech, B.E., MCA, etc." />
                  </div>
                  <div className="space-y-2 md:col-span-2">
                    <Label htmlFor="eligibility">Eligibility Notes</Label>
                    <Input id="eligibility" name="eligibility" value={formData.eligibility} onChange={handleChange} />
                  </div>
                </div>
              </div>
            </div>

            {/* Compensation */}
            <div className="space-y-4 md:col-span-2">
              <h3 className="text-lg font-medium border-b pb-2">Compensation</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="currency">Currency</Label>
                  <Input id="currency" name="currency" value={formData.currency} onChange={handleChange} />
                </div>
                <div className="col-span-2"></div>
                <div className="space-y-2">
                  <Label htmlFor="stipend_min">Stipend Min</Label>
                  <Input id="stipend_min" name="stipend_min" type="number" min="0" value={formData.stipend_min} onChange={handleChange} />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="stipend_max">Stipend Max</Label>
                  <Input id="stipend_max" name="stipend_max" type="number" min="0" value={formData.stipend_max} onChange={handleChange} />
                </div>
                <div></div>
                <div className="space-y-2">
                  <Label htmlFor="salary_min">Salary Min</Label>
                  <Input id="salary_min" name="salary_min" type="number" min="0" value={formData.salary_min} onChange={handleChange} />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="salary_max">Salary Max</Label>
                  <Input id="salary_max" name="salary_max" type="number" min="0" value={formData.salary_max} onChange={handleChange} />
                </div>
              </div>
            </div>

            {/* Application & Source */}
            <div className="space-y-4 md:col-span-2">
              <h3 className="text-lg font-medium border-b pb-2">Application, Source & Status</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2 md:col-span-2">
                  <Label htmlFor="application_url">Application URL</Label>
                  <Input id="application_url" name="application_url" type="url" value={formData.application_url} onChange={handleChange} />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="deadline">Application Deadline</Label>
                  <Input id="deadline" name="deadline" type="datetime-local" value={formData.deadline} onChange={handleChange} />
                </div>
                <div className="space-y-2">
                  <Label>Status *</Label>
                  <Select value={formData.status} onValueChange={(val) => handleSelectChange("status", val || "Draft")}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Draft">Draft</SelectItem>
                      <SelectItem value="Published">Published</SelectItem>
                      <SelectItem value="Closed">Closed</SelectItem>
                      <SelectItem value="Expired">Expired</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="source_name">Source Name *</Label>
                  <Input id="source_name" name="source_name" value={formData.source_name} onChange={handleChange} required />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="external_id">External ID</Label>
                  <Input id="external_id" name="external_id" value={formData.external_id} onChange={handleChange} placeholder="Unique ID from source" />
                </div>
                <div className="space-y-2 md:col-span-2">
                  <Label htmlFor="source_url">Source URL</Label>
                  <Input id="source_url" name="source_url" type="url" value={formData.source_url} onChange={handleChange} />
                </div>
              </div>
            </div>
            
          </div>

          <DialogFooter className="mt-6">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)} disabled={isSaving}>
              Cancel
            </Button>
            <Button type="submit" disabled={isSaving} className="bg-[#1B5E3B] hover:bg-[#2E7D4F]">
              {isSaving ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Saving...</> : "Save Opportunity"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
