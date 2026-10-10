import Link from "next/link";
import { MapPin, Calendar, Building2, Briefcase } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { SaveButton } from "./save-button";

export type OpportunityCardProps = {
  opportunity: Record<string, any>; // eslint-disable-line @typescript-eslint/no-explicit-any
  match?: Record<string, any>; // eslint-disable-line @typescript-eslint/no-explicit-any
  onSavedChange?: (saved: boolean) => void;
};

export function OpportunityCard({ opportunity, match, onSavedChange }: OpportunityCardProps) {
  // Format deadline securely
  const formatDeadline = (dateString: string | null) => {
    if (!dateString) return "No deadline";
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString("en-US", {
        day: "numeric",
        month: "short",
        year: "numeric"
      });
    } catch {
      return dateString;
    }
  };

  return (
    <div className="flex flex-col md:flex-row bg-white rounded-xl shadow-sm border border-gray-100 p-6 gap-6 hover:shadow-md transition-shadow">
      {/* Logo Section */}
      <div className="flex-shrink-0">
        {opportunity.company_logo_url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img 
            src={opportunity.company_logo_url} 
            alt={`${opportunity.company_name} logo`}
            className="w-16 h-16 object-contain rounded-md border border-gray-100 p-1"
          />
        ) : (
          <div className="w-16 h-16 bg-[#F6FAF7] text-[#1B5E3B] flex items-center justify-center rounded-md border border-gray-100">
            <Building2 className="w-8 h-8 opacity-50" />
          </div>
        )}
      </div>

      {/* Main Content */}
      <div className="flex-grow flex flex-col justify-between">
        <div className="flex flex-col md:flex-row md:justify-between md:items-start gap-4">
          <div>
            <h3 className="text-xl font-bold text-[#14261C] mb-1 flex items-center gap-3">
              {opportunity.title}
              {match && match.score !== null && (
                <Badge className={`px-2 py-0.5 text-xs ${
                  match.score >= 80 ? "bg-green-100 text-green-800 hover:bg-green-100 border-green-200" :
                  match.score >= 60 ? "bg-yellow-100 text-yellow-800 hover:bg-yellow-100 border-yellow-200" :
                  "bg-orange-100 text-orange-800 hover:bg-orange-100 border-orange-200"
                }`}>
                  {Math.round(match.score)}% Match
                </Badge>
              )}
            </h3>
            <p className="text-muted-foreground font-medium mb-3">
              {opportunity.company_name}
            </p>
            
            <div className="flex flex-wrap gap-2 mb-4">
              <Badge variant="outline" className="bg-[#F6FAF7] text-[#1B5E3B] border-[#1B5E3B]/20">
                <Briefcase className="w-3 h-3 mr-1" />
                {opportunity.opportunity_type}
              </Badge>
              <Badge variant="outline" className="bg-gray-50 text-gray-700">
                {opportunity.work_model}
              </Badge>
              {opportunity.domain && (
                <Badge variant="outline" className="bg-[#FFF8EB] text-[#B45309] border-[#F59E0B]/20">
                  {opportunity.domain}
                </Badge>
              )}
              {match && match.data_coverage && (
                <Badge variant="outline" className="bg-gray-50 text-gray-600 border-gray-200">
                  Coverage: {match.data_coverage}
                </Badge>
              )}
            </div>

            <div className="flex flex-col gap-2 text-sm text-gray-600 mb-4">
              {opportunity.locations && opportunity.locations.length > 0 && (
                <div className="flex items-start gap-2">
                  <MapPin className="w-4 h-4 mt-0.5 flex-shrink-0 opacity-70" />
                  <span>{opportunity.locations.join(" / ")}</span>
                </div>
              )}
              {opportunity.deadline && (
                <div className="flex items-center gap-2">
                  <Calendar className="w-4 h-4 opacity-70" />
                  <span>Deadline: {formatDeadline(opportunity.deadline)}</span>
                </div>
              )}
              {opportunity.stipend_min !== null && opportunity.stipend_min !== undefined && (
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-gray-700">Stipend:</span>
                  <span>
                    {opportunity.stipend_min} 
                    {opportunity.stipend_max ? ` - ${opportunity.stipend_max}` : ""} 
                    {opportunity.currency ? ` ${opportunity.currency}` : ""}
                  </span>
                </div>
              )}
              {opportunity.salary_min !== null && opportunity.salary_min !== undefined && (
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-gray-700">Salary:</span>
                  <span>
                    {opportunity.salary_min} 
                    {opportunity.salary_max ? ` - ${opportunity.salary_max}` : ""} 
                    {opportunity.currency ? ` ${opportunity.currency}` : ""}
                  </span>
                </div>
              )}
            </div>
            
            {/* Skills */}
            {opportunity.skills && opportunity.skills.length > 0 && (
              <div className="flex flex-wrap gap-1.5 mt-2">
                {opportunity.skills.map((skill: Record<string, any>) => ( // eslint-disable-line @typescript-eslint/no-explicit-any
                  <span key={skill.id} className="px-2.5 py-1 text-xs bg-gray-100 text-gray-600 rounded-md">
                    {skill.name}
                  </span>
                ))}
              </div>
            )}

            {/* Match Explanation */}
            {match && match.explanation && (
              <div className="mt-4 pt-4 border-t border-gray-100">
                <p className="text-sm text-gray-700 mb-2"><strong>Match Summary:</strong> {match.explanation.summary}</p>
                {match.matched_skills && match.matched_skills.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 mt-2 items-center">
                    <span className="text-xs font-semibold text-green-700 mr-1">Matched Skills:</span>
                    {match.matched_skills.map((skill: string) => (
                      <span key={skill} className="px-2 py-0.5 text-[10px] bg-green-50 text-green-700 border border-green-200 rounded-md">
                        {skill}
                      </span>
                    ))}
                  </div>
                )}
                {match.missing_required_skills && match.missing_required_skills.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 mt-2 items-center">
                    <span className="text-xs font-semibold text-orange-700 mr-1">Missing Skills:</span>
                    {match.missing_required_skills.map((skill: string) => (
                      <span key={skill} className="px-2 py-0.5 text-[10px] bg-orange-50 text-orange-700 border border-orange-200 rounded-md">
                        {skill}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>

          <div className="mt-4 md:mt-0 flex flex-col md:flex-row gap-3 flex-shrink-0">
            <SaveButton opportunityId={opportunity.id} onSavedChange={onSavedChange} variant="outline" className="w-full md:w-auto" />
            <Link href={`/opportunities/${opportunity.id}`}>
              <Button className="w-full md:w-auto bg-[#1B5E3B] text-white hover:bg-[#2E7D4F]">
                View Opportunity
              </Button>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
