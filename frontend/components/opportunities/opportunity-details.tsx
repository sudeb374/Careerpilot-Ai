"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { 
  ArrowLeft, 
  Building2, 
  MapPin, 
  Calendar, 
  Briefcase, 
  ExternalLink,
  AlertCircle,
  BookOpen,
  FileEdit,
  Sparkles,
  Globe,
  Link as LinkIcon
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { SaveButton } from "./save-button";
import { createClient } from "@/lib/supabase/client";
import { OpportunityMatchSummary } from "./match-summary";

interface OpportunityDetailsProps {
  opportunityId: string;
}

export function OpportunityDetails({ opportunityId }: OpportunityDetailsProps) {
  const router = useRouter();
  const supabase = createClient();
  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<{ status: number; message: string } | null>(null);
  const [opportunity, setOpportunity] = useState<Record<string, any> | null>(null); // eslint-disable-line @typescript-eslint/no-explicit-any

  const loadOpportunity = async () => {
    setLoading(true);
    setError(null);
    try {
      const { data: { session } } = await supabase.auth.getSession();
      
      if (!session) {
        router.push("/login");
        return;
      }

      const response = await fetch(`${API_URL}/api/v1/opportunities/${opportunityId}`, {
        headers: { Authorization: `Bearer ${session.access_token}` },
      });

      if (!response.ok) {
        if (response.status === 404) {
          setError({ status: 404, message: "Opportunity not found" });
          return;
        }
        setError({ status: response.status, message: "Unable to load this opportunity." });
        return;
      }

      const data = await response.json();
      setOpportunity(data);
    } catch (err: unknown) {
      console.error("Failed to load opportunity:", err);
      setError({ status: 500, message: "Unable to connect to the server." });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadOpportunity();
  }, [opportunityId]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleBack = () => {
    if (window.history.length > 2) {
      router.back();
    } else {
      router.push("/opportunities");
    }
  };

  const formatDeadline = (dateString: string | null) => {
    if (!dateString) return "No deadline specified";
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString("en-US", {
        day: "numeric",
        month: "long",
        year: "numeric"
      });
    } catch {
      return dateString;
    }
  };

  const isValidExternalUrl = (url: string | null | undefined): boolean => {
    if (!url || typeof url !== "string") return false;
    const trimmed = url.trim();
    return trimmed.startsWith("http://") || trimmed.startsWith("https://");
  };

  const formatCompensation = (min: number | null, max: number | null, currency: string | null) => {
    if (min === null && max === null) return null;
    const curr = currency ? `${currency} ` : "";
    if (min !== null && max !== null) return `${curr}${min} - ${curr}${max}`;
    if (min !== null) return `${curr}${min} (Minimum)`;
    if (max !== null) return `Up to ${curr}${max}`;
    return null;
  };

  if (error) {
    if (error.status === 404) {
      return (
        <div className="flex flex-col items-center justify-center p-16 bg-white rounded-xl border border-gray-100 text-center space-y-4 shadow-sm">
          <div className="w-16 h-16 rounded-full bg-orange-50 flex items-center justify-center text-orange-500 mb-2">
            <AlertCircle className="w-8 h-8" />
          </div>
          <div>
            <h3 className="text-xl font-bold text-gray-900">Opportunity not found</h3>
            <p className="text-gray-500 mt-2">This opportunity may have been removed or is no longer available.</p>
          </div>
          <Button onClick={() => router.push("/opportunities")} className="mt-4 bg-[#1B5E3B] text-white hover:bg-[#2E7D4F]">
            Back to Opportunities
          </Button>
        </div>
      );
    }

    return (
      <div className="flex flex-col items-center justify-center p-16 bg-white rounded-xl border border-gray-100 text-center space-y-4 shadow-sm">
        <div className="w-16 h-16 rounded-full bg-red-50 flex items-center justify-center text-red-500 mb-2">
          <AlertCircle className="w-8 h-8" />
        </div>
        <div>
          <h3 className="text-xl font-bold text-gray-900">{error.message}</h3>
          <p className="text-gray-500 mt-2">Please try again later.</p>
        </div>
        <div className="flex gap-4 mt-4">
          <Button onClick={() => router.push("/opportunities")} variant="outline">
            Back to Opportunities
          </Button>
          <Button onClick={loadOpportunity} className="bg-[#1B5E3B] text-white hover:bg-[#2E7D4F]">
            Try Again
          </Button>
        </div>
      </div>
    );
  }

  if (loading || !opportunity) {
    return (
      <div className="space-y-6">
        <div className="flex items-center mb-6">
          <div className="w-8 h-8 bg-gray-200 rounded-full animate-pulse mr-4"></div>
          <div className="h-4 w-32 bg-gray-200 rounded animate-pulse"></div>
        </div>
        
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-8">
          <div className="flex items-start gap-6">
            <div className="w-20 h-20 bg-gray-200 rounded-lg animate-pulse flex-shrink-0"></div>
            <div className="space-y-4 flex-grow">
              <div className="h-8 bg-gray-200 rounded w-1/3 animate-pulse"></div>
              <div className="h-5 bg-gray-200 rounded w-1/4 animate-pulse"></div>
              <div className="flex gap-2">
                <div className="h-6 w-24 bg-gray-200 rounded animate-pulse"></div>
                <div className="h-6 w-24 bg-gray-200 rounded animate-pulse"></div>
                <div className="h-6 w-24 bg-gray-200 rounded animate-pulse"></div>
              </div>
            </div>
            <div className="w-32 h-10 bg-gray-200 rounded animate-pulse"></div>
          </div>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="md:col-span-2 space-y-6">
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-8 space-y-4">
              <div className="h-6 w-1/4 bg-gray-200 rounded animate-pulse"></div>
              <div className="space-y-2">
                <div className="h-4 bg-gray-200 rounded animate-pulse w-full"></div>
                <div className="h-4 bg-gray-200 rounded animate-pulse w-full"></div>
                <div className="h-4 bg-gray-200 rounded animate-pulse w-5/6"></div>
              </div>
            </div>
          </div>
          <div className="space-y-6">
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 space-y-4">
              <div className="h-6 w-1/2 bg-gray-200 rounded animate-pulse"></div>
              <div className="flex gap-2">
                <div className="h-6 w-16 bg-gray-200 rounded animate-pulse"></div>
                <div className="h-6 w-16 bg-gray-200 rounded animate-pulse"></div>
                <div className="h-6 w-16 bg-gray-200 rounded animate-pulse"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const stipend = formatCompensation(opportunity.stipend_min, opportunity.stipend_max, opportunity.currency);
  const salary = formatCompensation(opportunity.salary_min, opportunity.salary_max, opportunity.currency);

  return (
    <div className="space-y-6">
      <button 
        onClick={handleBack}
        className="flex items-center text-sm font-medium text-gray-500 hover:text-gray-900 transition-colors"
      >
        <ArrowLeft className="w-4 h-4 mr-2" />
        Back to Opportunities
      </button>

      {/* Hero Section */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 md:p-8 flex flex-col md:flex-row gap-6 md:gap-8">
        <div className="flex-shrink-0">
          {opportunity.company_logo_url ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img 
              src={opportunity.company_logo_url} 
              alt={`${opportunity.company_name} logo`}
              className="w-20 h-20 md:w-24 md:h-24 object-contain rounded-lg border border-gray-100 p-2"
            />
          ) : (
            <div className="w-20 h-20 md:w-24 md:h-24 bg-[#F6FAF7] text-[#1B5E3B] flex items-center justify-center rounded-lg border border-gray-100">
              <Building2 className="w-10 h-10 md:w-12 md:h-12 opacity-50" />
            </div>
          )}
        </div>

        <div className="flex-grow flex flex-col justify-between">
          <div className="flex flex-col md:flex-row md:justify-between md:items-start gap-6">
            <div>
              <h1 className="text-2xl md:text-3xl font-bold text-[#14261C] mb-2">
                {opportunity.title}
              </h1>
              <p className="text-lg text-muted-foreground font-medium mb-4">
                {opportunity.company_name}
              </p>
              
              <div className="flex flex-wrap gap-2 mb-4">
                <Badge variant="outline" className="bg-[#F6FAF7] text-[#1B5E3B] border-[#1B5E3B]/20 py-1 px-3 text-sm">
                  <Briefcase className="w-4 h-4 mr-1.5" />
                  {opportunity.opportunity_type}
                </Badge>
                <Badge variant="outline" className="bg-gray-50 text-gray-700 py-1 px-3 text-sm">
                  {opportunity.work_model}
                </Badge>
                {opportunity.domain && (
                  <Badge variant="outline" className="bg-[#FFF8EB] text-[#B45309] border-[#F59E0B]/20 py-1 px-3 text-sm">
                    {opportunity.domain}
                  </Badge>
                )}
              </div>

              <div className="flex items-center gap-2 text-gray-600 font-medium">
                <MapPin className="w-4 h-4 opacity-70" />
                <span>{opportunity.locations?.length > 0 ? opportunity.locations.join(" / ") : "Location not specified"}</span>
              </div>
            </div>

            <div className="flex-shrink-0 flex flex-col gap-3 min-w-[300px]">
              <div className="flex flex-col sm:flex-row gap-3 w-full">
                <SaveButton 
                  opportunityId={opportunity.id} 
                  className="flex-1 h-11 border-[#1B5E3B] text-[#1B5E3B] hover:bg-[#F6FAF7] bg-white font-semibold"
                />
                {isValidExternalUrl(opportunity.application_url) ? (
                  <a 
                    href={opportunity.application_url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="flex-1"
                  >
                    <Button size="lg" className="w-full bg-[#F59E0B] hover:bg-[#D97706] text-white font-bold shadow-sm">
                      Apply Now
                      <ExternalLink className="w-4 h-4 ml-2" />
                    </Button>
                  </a>
                ) : (
                  <Button size="lg" disabled className="flex-1 font-bold" aria-disabled="true">
                    Unavailable
                  </Button>
                )}
              </div>

              <Link href={`/cover-letter?opportunity_id=${opportunity.id}`} className="w-full">
                <Button variant="outline" className="w-full h-10 border-[#1B5E3B]/30 text-[#1B5E3B] hover:bg-[#E5EDE7] font-semibold flex items-center justify-center gap-2">
                  <FileEdit className="w-4 h-4" />
                  Draft Tailored Cover Letter
                </Button>
              </Link>

              <Link href={`/application-assistant?opportunity_id=${opportunity.id}`} className="w-full">
                <Button variant="outline" className="w-full h-10 border-[#1B5E3B]/30 text-[#1B5E3B] hover:bg-[#E5EDE7] font-semibold flex items-center justify-center gap-2">
                  <Sparkles className="w-4 h-4" />
                  Answer Application Questions
                </Button>
              </Link>

              <Link href={`/interview-prep?opportunity_id=${opportunity.id}`} className="w-full">
                <Button variant="outline" className="w-full h-10 border-[#1B5E3B]/30 text-[#1B5E3B] hover:bg-[#E5EDE7] font-semibold flex items-center justify-center gap-2">
                  <BookOpen className="w-4 h-4" />
                  Practice Interview Questions
                </Button>
              </Link>
              
              <div className="text-center text-sm text-gray-500 mt-1 bg-gray-50 py-2 px-3 rounded-md border border-gray-100 flex items-center justify-center gap-2">
                <Calendar className="w-4 h-4" />
                <span>Deadline: <span className="font-semibold text-gray-700">{formatDeadline(opportunity.deadline)}</span></span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <OpportunityMatchSummary opportunityId={opportunity.id} />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content Column */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* Description */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 md:p-8">
            <h2 className="text-xl font-bold text-[#14261C] mb-6">About This Opportunity</h2>
            <div className="prose max-w-none text-gray-700 whitespace-pre-wrap font-medium">
              {opportunity.description || "No description provided."}
            </div>
          </div>
          
          {/* Optional Requirements (Experience, Education, Eligibility) */}
          {(opportunity.required_experience_min !== null || opportunity.required_experience_max !== null || opportunity.education_requirements || opportunity.eligibility) && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 md:p-8">
              <h2 className="text-xl font-bold text-[#14261C] mb-6">Requirements</h2>
              <div className="space-y-6">
                {(opportunity.required_experience_min !== null || opportunity.required_experience_max !== null) && (
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-2">Experience</h3>
                    <p className="text-gray-700 bg-gray-50 p-3 rounded-lg border border-gray-100">
                      {opportunity.required_experience_min !== null ? `${opportunity.required_experience_min} ` : ""}
                      {opportunity.required_experience_max !== null ? `- ${opportunity.required_experience_max} ` : (opportunity.required_experience_min !== null ? "+ " : "")}
                      years
                    </p>
                  </div>
                )}
                
                {opportunity.education_requirements && (
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-2">Education Requirements</h3>
                    <div className="text-gray-700 whitespace-pre-wrap bg-gray-50 p-4 rounded-lg border border-gray-100">
                      {opportunity.education_requirements}
                    </div>
                  </div>
                )}
                
                {opportunity.eligibility && (
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-2">Eligibility Criteria</h3>
                    <div className="text-gray-700 whitespace-pre-wrap bg-gray-50 p-4 rounded-lg border border-gray-100">
                      {opportunity.eligibility}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

        </div>

        {/* Sidebar Column */}
        <div className="space-y-6">
          
          {/* Skills Section */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <h3 className="text-lg font-bold text-[#14261C] mb-4">Required Skills</h3>
            {opportunity.skills && opportunity.skills.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {opportunity.skills.map((skill: Record<string, any>) => ( // eslint-disable-line @typescript-eslint/no-explicit-any
                  <span key={skill.id} className="px-3 py-1.5 text-sm bg-[#1B5E3B]/10 text-[#1B5E3B] font-medium rounded-md border border-[#1B5E3B]/20">
                    {skill.name}
                  </span>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-sm">No specific skills listed.</p>
            )}
          </div>

          {/* Compensation Section */}
          {(stipend || salary) && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
              <h3 className="text-lg font-bold text-[#14261C] mb-4">Compensation</h3>
              <div className="space-y-4">
                {stipend && (
                  <div>
                    <span className="block text-sm font-medium text-gray-500 mb-1">Stipend</span>
                    <span className="block font-semibold text-gray-900 text-lg">{stipend}</span>
                  </div>
                )}
                {stipend && salary && <div className="border-t border-gray-100"></div>}
                {salary && (
                  <div>
                    <span className="block text-sm font-medium text-gray-500 mb-1">Salary</span>
                    <span className="block font-semibold text-gray-900 text-lg">{salary}</span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Company & Source Information */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <h3 className="text-lg font-bold text-[#14261C] mb-4">Company & Source</h3>
            <div className="space-y-4 text-sm">
              <div>
                <span className="block font-medium text-gray-500 mb-1">Company</span>
                <span className="block font-semibold text-gray-900">{opportunity.company_name}</span>
              </div>
              
              {isValidExternalUrl(opportunity.company_website) && (
                <div>
                  <a 
                    href={opportunity.company_website} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="inline-flex items-center text-[#1B5E3B] hover:text-[#2E7D4F] hover:underline font-medium"
                  >
                    <Globe className="w-4 h-4 mr-1.5" />
                    Visit Website
                  </a>
                </div>
              )}

              {(opportunity.source_name || opportunity.source_url) && <div className="border-t border-gray-100"></div>}
              
              {opportunity.source_name && (
                <div>
                  <span className="block font-medium text-gray-500 mb-1">Source</span>
                  <span className="block font-medium text-gray-800">{opportunity.source_name}</span>
                </div>
              )}

              {isValidExternalUrl(opportunity.source_url) && (
                <div>
                  <a 
                    href={opportunity.source_url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="inline-flex items-center text-blue-600 hover:text-blue-800 hover:underline font-medium"
                  >
                    <LinkIcon className="w-4 h-4 mr-1.5" />
                    View Original Listing
                  </a>
                </div>
              )}
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
