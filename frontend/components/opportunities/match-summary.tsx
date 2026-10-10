"use client";

import { useState, useEffect } from "react";
import { CheckCircle2, XCircle, Info, ChevronDown, ChevronUp } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { createClient } from "@/lib/supabase/client";

interface MatchComponentScore {
  component: string;
  awarded_points: number;
  max_points: number;
  explanation: string;
}

interface MatchExplanation {
  summary: string;
  strengths: string[];
  limitations: string[];
}

interface MatchResponse {
  scoring_version: string;
  score: number | null;
  score_label: string | null;
  data_coverage: "High" | "Moderate" | "Limited" | "Unavailable";
  matched_skills: string[];
  missing_required_skills: string[];
  matched_factors: string[];
  mismatched_preferences: string[];
  component_scores: MatchComponentScore[];
  components_not_assessed: string[];
  explanation: MatchExplanation;
}

export function OpportunityMatchSummary({ opportunityId }: { opportunityId: string }) {
  const supabase = createClient();
  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [matchData, setMatchData] = useState<MatchResponse | null>(null);
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    const fetchMatch = async () => {
      try {
        const { data: { session } } = await supabase.auth.getSession();
        if (!session) return; // Will be handled by the parent page authentication

        const response = await fetch(`${API_URL}/api/v1/opportunities/${opportunityId}/match`, {
          headers: { Authorization: `Bearer ${session.access_token}` },
        });

        if (!response.ok) {
          if (response.status !== 404) {
            setError("Failed to load match analysis.");
          }
          return; // 404 means maybe not published, or match not applicable
        }

        const data = await response.json();
        setMatchData(data);
      } catch (err) {
        console.error("Match error:", err);
        setError("Unable to connect to matching service.");
      } finally {
        setLoading(false);
      }
    };

    fetchMatch();
  }, [opportunityId, API_URL, supabase.auth]);

  if (loading) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 animate-pulse">
        <div className="h-6 w-1/3 bg-gray-200 rounded mb-4"></div>
        <div className="h-20 bg-gray-200 rounded mb-4"></div>
        <div className="h-4 w-full bg-gray-200 rounded"></div>
      </div>
    );
  }

  // If there's an error but we don't want to break the page
  if (error || !matchData) {
    return null; // Or a gentle error message if desired
  }

  const { score, data_coverage, component_scores, explanation, matched_skills, missing_required_skills } = matchData;

  // Determine colors based on score
  let scoreColor = "text-gray-500";
  let scoreBg = "bg-gray-100";
  let scoreBorder = "border-gray-200";

  if (score !== null) {
    if (score >= 80) {
      scoreColor = "text-green-600";
      scoreBg = "bg-green-50";
      scoreBorder = "border-green-200";
    } else if (score >= 60) {
      scoreColor = "text-yellow-600";
      scoreBg = "bg-yellow-50";
      scoreBorder = "border-yellow-200";
    } else {
      scoreColor = "text-orange-600";
      scoreBg = "bg-orange-50";
      scoreBorder = "border-orange-200";
    }
  }

  return (
    <div className={`bg-white rounded-xl shadow-sm border ${scoreBorder} overflow-hidden`}>
      {/* Header / Summary */}
      <div className={`p-6 ${scoreBg} border-b ${scoreBorder} flex flex-col md:flex-row gap-6 items-start md:items-center justify-between`}>
        <div className="flex items-center gap-6">
          {/* Circular Score Indicator */}
          <div className={`relative flex items-center justify-center w-20 h-20 rounded-full bg-white border-4 ${scoreBorder} shadow-sm shrink-0`}>
            {score !== null ? (
              <div className="text-center">
                <span className={`text-2xl font-bold ${scoreColor}`}>{Math.round(score)}</span>
                <span className="text-xs text-gray-500 block -mt-1">/ 100</span>
              </div>
            ) : (
              <span className="text-xl font-semibold text-gray-400">N/A</span>
            )}
          </div>
          
          <div>
            <h3 className="text-lg font-bold text-gray-900">Your Match Profile</h3>
            <p className="text-sm text-gray-600 mt-1">{explanation.summary}</p>
            <div className="flex gap-2 mt-2">
              <Badge variant="outline" className="bg-white/60">
                Data Coverage: {data_coverage}
              </Badge>
            </div>
          </div>
        </div>

        <Button 
          variant="ghost" 
          size="sm" 
          onClick={() => setExpanded(!expanded)}
          className="shrink-0 text-[#1B5E3B] hover:text-[#2E7D4F] hover:bg-[#1B5E3B]/10"
        >
          {expanded ? (
            <><ChevronUp className="w-4 h-4 mr-2" /> Hide Details</>
          ) : (
            <><ChevronDown className="w-4 h-4 mr-2" /> View Breakdown</>
          )}
        </Button>
      </div>

      {/* Expanded Details */}
      {expanded && (
        <div className="p-6 space-y-6">
          {/* Factor Breakdown */}
          <div>
            <h4 className="text-sm font-semibold text-gray-900 uppercase tracking-wider mb-4">Factor Breakdown</h4>
            <div className="space-y-3">
              {component_scores.map((comp) => (
                <div key={comp.component} className="flex flex-col md:flex-row justify-between md:items-center gap-2 p-3 bg-gray-50 rounded-lg border border-gray-100">
                  <div className="flex-grow">
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-medium text-gray-800">{comp.component}</span>
                      <span className="text-sm font-semibold text-gray-600 text-right">
                        {comp.awarded_points} / {comp.max_points} pts
                      </span>
                    </div>
                    <p className="text-sm text-gray-500">{comp.explanation}</p>
                  </div>
                  {/* Progress Bar Mini */}
                  <div className="w-full md:w-32 h-2 bg-gray-200 rounded-full overflow-hidden shrink-0 mt-2 md:mt-0">
                    <div 
                      className={`h-full ${comp.awarded_points / comp.max_points >= 0.7 ? "bg-green-500" : comp.awarded_points / comp.max_points >= 0.4 ? "bg-yellow-500" : "bg-orange-500"}`}
                      style={{ width: `${comp.max_points > 0 ? Math.round((comp.awarded_points / comp.max_points) * 100) : 0}%` }}
                    ></div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Skills Breakdown */}
          <div className="grid md:grid-cols-2 gap-6">
            {matched_skills.length > 0 && (
              <div>
                <h4 className="text-sm font-semibold text-green-800 flex items-center gap-2 mb-3">
                  <CheckCircle2 className="w-4 h-4" /> Matched Skills
                </h4>
                <div className="flex flex-wrap gap-2">
                  {matched_skills.map((skill) => (
                    <Badge key={skill} variant="outline" className="bg-green-50 text-green-700 border-green-200">
                      {skill}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
            
            {missing_required_skills.length > 0 && (
              <div>
                <h4 className="text-sm font-semibold text-orange-800 flex items-center gap-2 mb-3">
                  <XCircle className="w-4 h-4" /> Missing Required Skills
                </h4>
                <div className="flex flex-wrap gap-2">
                  {missing_required_skills.map((skill) => (
                    <Badge key={skill} variant="outline" className="bg-orange-50 text-orange-700 border-orange-200">
                      {skill}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Qualitative Feedback */}
          {(explanation.strengths.length > 0 || explanation.limitations.length > 0) && (
            <div className="grid md:grid-cols-2 gap-6 pt-4 border-t border-gray-100">
              {explanation.strengths.length > 0 && (
                <div>
                  <h4 className="font-medium text-gray-900 mb-2">Strengths</h4>
                  <ul className="list-disc pl-5 space-y-1 text-sm text-gray-600 marker:text-green-500">
                    {explanation.strengths.map((str, idx) => (
                      <li key={idx}>{str}</li>
                    ))}
                  </ul>
                </div>
              )}
              {explanation.limitations.length > 0 && (
                <div>
                  <h4 className="font-medium text-gray-900 mb-2">Areas for Improvement</h4>
                  <ul className="list-disc pl-5 space-y-1 text-sm text-gray-600 marker:text-orange-500">
                    {explanation.limitations.map((lim, idx) => (
                      <li key={idx}>{lim}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Disclaimer */}
      <div className="bg-gray-50 p-4 border-t border-gray-100 flex gap-3 text-xs text-gray-500">
        <Info className="w-4 h-4 shrink-0 text-gray-400 mt-0.5" />
        <p>
          Your match score is an estimate of how closely this opportunity aligns with your profile and preferences. It is not a probability of selection or a guarantee of hiring.
        </p>
      </div>
    </div>
  );
}
