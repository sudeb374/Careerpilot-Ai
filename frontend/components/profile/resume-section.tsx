"use client";

import { useEffect, useState, useRef } from "react";
import { createClient } from "@/lib/supabase/client";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Loader2, Upload, FileText, CheckCircle2, Trash2, Download, AlertCircle, FileIcon, BarChart, RefreshCw, Info, ShieldCheck, Sparkles, AlertTriangle, Copy } from "lucide-react";

interface Resume {
  id: string;
  original_filename: string;
  file_type: string;
  file_size: number;
  is_active: boolean;
  has_parsed_text: boolean;
  has_structured_data: boolean;
  has_analysis: boolean;
  created_at: string;
  updated_at: string;
}

interface StructuredDataResponse {
  id: string;
  status: string;
  structured_data?: {
    schema_version: number;
    contact: {
      emails: string[];
      phones: string[];
      linkedin_urls: string[];
      github_urls: string[];
      portfolio_urls: string[];
    };
    skills: Array<{
      name: string;
      evidence: string;
    }>;
    sections: Record<string, string>;
    warnings: string[];
  };
  message?: string;
}

interface ResumeFinding {
  identifier: string;
  category: string;
  severity: string;
  title: string;
  explanation: string;
  recommendation: string;
  evidence?: string;
}

interface ResumeAnalysisData {
  schema_version: number;
  analysis_generated_at: string;
  completeness_score: number;
  score_label: string;
  category_scores: {
    contact: number;
    summary: number;
    education: number;
    skills: number;
    experience_projects: number;
    organization: number;
  };
  findings: ResumeFinding[];
  strengths: ResumeFinding[];
  limitations: string[];
}

interface ResumeAnalysisResponse {
  id: string;
  status: string;
  analysis?: ResumeAnalysisData;
  message?: string;
}

const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5MB

function SafeUrl({ url }: { url: string }) {
  let isValid = false;
  let safeLink = url;
  try {
    const u = new URL(url.startsWith('http') ? url : `https://${url}`);
    if (u.protocol === 'http:' || u.protocol === 'https:') {
      isValid = true;
      safeLink = u.href;
    }
  } catch {
    // ignore
  }

  if (isValid) {
    return (
      <a href={safeLink} target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">
        {url}
      </a>
    );
  }
  return <span className="text-foreground">{url}</span>;
}

export function ResumeSection() {
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);
  const [isExtracting, setIsExtracting] = useState<string | null>(null);
  const [viewExtractedTextId, setViewExtractedTextId] = useState<string | null>(null);
  const [extractedText, setExtractedText] = useState<{ id: string; text: string; charCount: number; status: string } | null>(null);
  const [dialogError, setDialogError] = useState<string | null>(null);
  
  const [isStructuring, setIsStructuring] = useState<string | null>(null);
  const [viewStructuredDataId, setViewStructuredDataId] = useState<string | null>(null);
  const [structuredData, setStructuredData] = useState<StructuredDataResponse | null>(null);
  
  const [isAnalyzing, setIsAnalyzing] = useState<string | null>(null);
  const [viewAnalysisId, setViewAnalysisId] = useState<string | null>(null);
  const [analysisData, setAnalysisData] = useState<ResumeAnalysisResponse | null>(null);
  
  const fileInputRef = useRef<HTMLInputElement>(null);
  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  useEffect(() => {
    async function loadResumes() {
      try {
        const supabase = createClient();
        const { data: { session } } = await supabase.auth.getSession();
        
        if (!session) {
          setError("You must be logged in to view your resumes.");
          setIsLoading(false);
          return;
        }

        const res = await fetch(`${API_URL}/api/v1/profile/resumes`, {
          headers: {
            "Authorization": `Bearer ${session.access_token}`
          }
        });

        if (res.ok) {
          const data = await res.json();
          setResumes(data);
        } else {
          // Do not swallow original HTTP status
          let errorDetail = `HTTP ${res.status} ${res.statusText}`;
          try {
            const errData = await res.json();
            if (errData.detail) errorDetail += `: ${errData.detail}`;
          } catch {
            // response was not JSON
          }
          console.error(`Backend error loading resumes: ${errorDetail}`);
          setError(`API endpoint failed (${res.status}): ${errorDetail}`);
        }
      } catch (err) {
        console.error("Network or CORS error fetching resumes:", err);
        setError(err instanceof Error ? err.message : "CORS or Network error occurred.");
      } finally {
        setIsLoading(false);
      }
    }
    
    loadResumes();
  }, [API_URL, refreshKey]);

  const clearMessages = () => {
    setError(null);
    setSuccess(null);
  };

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    clearMessages();

    if (file.size > MAX_FILE_SIZE) {
      setError("File size exceeds maximum limit of 5MB.");
      if (fileInputRef.current) fileInputRef.current.value = "";
      return;
    }

    const allowedTypes = [
      "application/pdf",
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ];
    if (!allowedTypes.includes(file.type)) {
      setError("Unsupported file type. Only PDF and DOCX are allowed.");
      if (fileInputRef.current) fileInputRef.current.value = "";
      return;
    }

    setIsUploading(true);
    try {
      const supabase = createClient();
      const { data: { session } } = await supabase.auth.getSession();
      
      if (!session) {
        setError("Your session has expired.");
        setIsUploading(false);
        return;
      }

      const formData = new FormData();
      formData.append("file", file);

      const res = await fetch(`${API_URL}/api/v1/profile/resumes`, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${session.access_token}`
        },
        body: formData
      });

      if (res.ok) {
        setSuccess("Resume uploaded successfully!");
        setRefreshKey(k => k + 1);
      } else {
        let errorDetail = `HTTP ${res.status} ${res.statusText}`;
        try {
          const errData = await res.json();
          if (errData.detail) errorDetail += `: ${errData.detail}`;
        } catch {
          // ignore
        }
        console.error(`Backend error uploading resume: ${errorDetail}`);
        setError(`Upload failed (${res.status}): ${errorDetail}`);
      }
    } catch (err) {
      console.error("Network or CORS error uploading resume:", err);
      setError(err instanceof Error ? err.message : "CORS or Network error occurred during upload.");
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const handleActivate = async (id: string) => {
    if (actionLoading || isUploading) return;
    clearMessages();
    setActionLoading(`activate-${id}`);

    try {
      const supabase = createClient();
      const { data: { session } } = await supabase.auth.getSession();
      
      if (!session) {
        setError("Your session has expired.");
        return;
      }

      const res = await fetch(`${API_URL}/api/v1/profile/resumes/${id}/activate`, {
        method: "PATCH",
        headers: {
          "Authorization": `Bearer ${session.access_token}`
        }
      });

      if (res.ok) {
        setSuccess("Resume activated successfully.");
        setRefreshKey(k => k + 1);
      } else {
        const errData = await res.json().catch(() => ({}));
        setError(errData.detail || "Failed to activate resume.");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "An unexpected error occurred.");
    } finally {
      setActionLoading(null);
    }
  };

  const handleDownload = async (id: string, filename: string) => {
    if (actionLoading || isUploading) return;
    clearMessages();
    setActionLoading(`download-${id}`);

    try {
      const supabase = createClient();
      const { data: { session } } = await supabase.auth.getSession();
      
      if (!session) {
        setError("Your session has expired.");
        return;
      }

      const res = await fetch(`${API_URL}/api/v1/profile/resumes/${id}/download`, {
        headers: {
          "Authorization": `Bearer ${session.access_token}`
        }
      });

      if (res.ok) {
        const data = await res.json();
        // Safe redirect to download the file directly in browser
        const link = document.createElement("a");
        link.href = data.signed_url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      } else {
        const errData = await res.json().catch(() => ({}));
        setError(errData.detail || "Failed to generate download link.");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "An unexpected error occurred.");
    } finally {
      setActionLoading(null);
    }
  };

  const handleDelete = async (id: string, isActive: boolean) => {
    if (actionLoading || isUploading) return;
    
    if (!window.confirm("Are you sure you want to delete this resume?")) {
      return;
    }
    
    clearMessages();
    setActionLoading(`delete-${id}`);

    try {
      const supabase = createClient();
      const { data: { session } } = await supabase.auth.getSession();
      
      if (!session) {
        setError("Your session has expired.");
        return;
      }

      const res = await fetch(`${API_URL}/api/v1/profile/resumes/${id}`, {
        method: "DELETE",
        headers: {
          "Authorization": `Bearer ${session.access_token}`
        }
      });

      if (res.ok || res.status === 204) {
        if (isActive) {
          setSuccess("Active resume deleted. You currently have no active resume.");
        } else {
          setSuccess("Resume deleted successfully.");
        }
        setRefreshKey(k => k + 1);
      } else {
        const errData = await res.json().catch(() => ({}));
        setError(errData.detail || "Failed to delete resume.");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "An unexpected error occurred.");
    } finally {
      setActionLoading(null);
    }
  };

  const handleExtractText = async (id: string, originalFilename: string) => {
    if (actionLoading || isUploading || isExtracting) return;
    clearMessages();
    setIsExtracting(id);

    try {
      const supabase = createClient();
      const { data: { session } } = await supabase.auth.getSession();
      
      if (!session) {
        setError("Your session has expired.");
        return;
      }

      const res = await fetch(`${API_URL}/api/v1/profile/resumes/${id}/parse`, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${session.access_token}`
        }
      });

      if (res.ok) {
        const data = await res.json();
        setSuccess(`Text extracted successfully from ${originalFilename}.`);
        setRefreshKey(k => k + 1);
        setExtractedText({
          id,
          text: data.extracted_text,
          charCount: data.character_count,
          status: data.status
        });
        setViewExtractedTextId(id);
      } else {
        let errorDetail = `HTTP ${res.status} ${res.statusText}`;
        try {
          const errData = await res.json();
          if (errData.detail) errorDetail = errData.detail;
        } catch { /* ignore */ }
        setError(`Failed to extract text: ${errorDetail}`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "An unexpected error occurred during extraction.");
    } finally {
      setIsExtracting(null);
    }
  };

  const handleViewExtractedText = async (id: string) => {
    if (actionLoading || isUploading || isExtracting) return;
    
    if (extractedText?.id === id) {
      setViewExtractedTextId(id);
      return;
    }

    clearMessages();
    setIsExtracting(id);
    setDialogError(null);

    try {
      const supabase = createClient();
      const { data: { session } } = await supabase.auth.getSession();
      
      if (!session) {
        setError("Your session has expired.");
        return;
      }

      const res = await fetch(`${API_URL}/api/v1/profile/resumes/${id}/parsed-text`, {
        method: "GET",
        headers: {
          "Authorization": `Bearer ${session.access_token}`
        }
      });

      if (res.ok) {
        const data = await res.json();
        setExtractedText({
          id,
          text: data.extracted_text,
          charCount: data.character_count,
          status: data.status
        });
        setViewExtractedTextId(id);
      } else {
        let errorDetail = `HTTP ${res.status} ${res.statusText}`;
        try {
          const errData = await res.json();
          if (errData.detail) errorDetail = errData.detail;
        } catch { /* ignore */ }
        setError(`Failed to retrieve extracted text: ${errorDetail}`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "An unexpected error occurred retrieving text.");
    } finally {
      setIsExtracting(null);
    }
  };

  const handleStructureResume = async (id: string, originalFilename: string, forceReextract: boolean = false) => {
    if (actionLoading || isUploading || isExtracting || isStructuring || isAnalyzing) return;

    if (forceReextract) {
      if (!window.confirm("Are you sure you want to re-extract details? This will refresh the structured result and may require a new analysis.")) {
        return;
      }
    }

    clearMessages();
    setIsStructuring(id);
    setDialogError(null);

    try {
      const supabase = createClient();
      const { data: { session } } = await supabase.auth.getSession();
      
      if (!session) {
        setError("Your session has expired.");
        return;
      }

      const res = await fetch(`${API_URL}/api/v1/profile/resumes/${id}/structure`, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${session.access_token}`
        }
      });

      if (res.ok) {
        const data = await res.json();
        setSuccess(`Structured data extracted successfully from ${originalFilename}.`);
        setRefreshKey(k => k + 1);
        setStructuredData(data);
        setViewStructuredDataId(id);
      } else {
        let errorDetail = `HTTP ${res.status} ${res.statusText}`;
        try {
          const errData = await res.json();
          if (errData.detail) errorDetail = errData.detail;
        } catch { /* ignore */ }
        setError(`Failed to extract structured data: ${errorDetail}`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "An unexpected error occurred during structured extraction.");
    } finally {
      setIsStructuring(null);
    }
  };

  const handleViewStructuredData = async (id: string) => {
    if (actionLoading || isUploading || isExtracting || isStructuring) return;
    
    // Use cached if matching
    if (viewStructuredDataId === id && structuredData) {
      setViewStructuredDataId(id);
      return;
    }

    clearMessages();
    setIsStructuring(id);
    setDialogError(null);

    try {
      const supabase = createClient();
      const { data: { session } } = await supabase.auth.getSession();
      
      if (!session) {
        setError("Your session has expired.");
        return;
      }

      const res = await fetch(`${API_URL}/api/v1/profile/resumes/${id}/structured-data`, {
        method: "GET",
        headers: {
          "Authorization": `Bearer ${session.access_token}`
        }
      });

      if (res.ok) {
        const data = await res.json();
        setStructuredData(data);
        setViewStructuredDataId(id);
      } else {
        let errorDetail = `HTTP ${res.status} ${res.statusText}`;
        try {
          const errData = await res.json();
          if (errData.detail) errorDetail = errData.detail;
        } catch { /* ignore */ }
        setError(`Failed to retrieve structured data: ${errorDetail}`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "An unexpected error occurred retrieving structured data.");
    } finally {
      setIsStructuring(null);
    }
  };

  const handleAnalyzeResume = async (id: string, originalFilename: string) => {
    if (actionLoading || isUploading || isExtracting || isStructuring || isAnalyzing) return;
    clearMessages();
    setIsAnalyzing(id);
    setDialogError(null);

    try {
      const supabase = createClient();
      const { data: { session } } = await supabase.auth.getSession();
      
      if (!session) {
        setError("Your session has expired.");
        return;
      }

      const res = await fetch(`${API_URL}/api/v1/profile/resumes/${id}/analyze`, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${session.access_token}`
        }
      });

      if (res.ok) {
        const data = await res.json();
        setSuccess(`Resume analysis completed successfully for ${originalFilename}.`);
        setRefreshKey(k => k + 1);
        setAnalysisData(data);
        setViewAnalysisId(id);
      } else {
        let errorDetail = `HTTP ${res.status} ${res.statusText}`;
        try {
          const errData = await res.json();
          if (errData.detail) errorDetail = errData.detail;
        } catch { /* ignore */ }
        setError(`Failed to analyze resume: ${errorDetail}`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "An unexpected error occurred during analysis.");
    } finally {
      setIsAnalyzing(null);
    }
  };

  const handleViewAnalysis = async (id: string) => {
    if (actionLoading || isUploading || isExtracting || isStructuring || isAnalyzing) return;
    
    // Use cached if matching
    if (viewAnalysisId === id && analysisData) {
      setViewAnalysisId(id);
      return;
    }

    clearMessages();
    setIsAnalyzing(id);
    setDialogError(null);

    try {
      const supabase = createClient();
      const { data: { session } } = await supabase.auth.getSession();
      
      if (!session) {
        setError("Your session has expired.");
        return;
      }

      const res = await fetch(`${API_URL}/api/v1/profile/resumes/${id}/analysis`, {
        method: "GET",
        headers: {
          "Authorization": `Bearer ${session.access_token}`
        }
      });

      if (res.ok) {
        const data = await res.json();
        setAnalysisData(data);
        setViewAnalysisId(id);
      } else {
        let errorDetail = `HTTP ${res.status} ${res.statusText}`;
        try {
          const errData = await res.json();
          if (errData.detail) errorDetail = errData.detail;
        } catch { /* ignore */ }
        setError(`Failed to retrieve analysis data: ${errorDetail}`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "An unexpected error occurred retrieving analysis data.");
    } finally {
      setIsAnalyzing(null);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  if (isLoading) {
    return (
      <div className="flex h-48 items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  const activeResume = resumes.find(r => r.is_active);
  const otherResumes = resumes.filter(r => !r.is_active);

  return (
    <Card className="w-full">
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle>Resume Intelligence</CardTitle>
          <CardDescription>
            Manage your resumes. Resume analysis and insights will be available in a future CareerPilot feature.
          </CardDescription>
        </div>
        <div>
          <input
            type="file"
            ref={fileInputRef}
            className="hidden"
            accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            onChange={handleFileSelect}
          />
          <Button 
            onClick={() => fileInputRef.current?.click()}
            disabled={isUploading || actionLoading !== null}
            className="bg-saffron text-saffron-foreground hover:bg-saffron/90"
          >
            {isUploading ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Upload className="mr-2 h-4 w-4" />
            )}
            Upload Resume
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {error && (
          <div className="flex items-center rounded-md bg-destructive/15 p-3 text-sm text-destructive">
            <AlertCircle className="mr-2 h-4 w-4" />
            {error}
          </div>
        )}
        {success && (
          <div className="flex items-center rounded-md bg-emerald-500/15 p-3 text-sm text-emerald-600 dark:text-emerald-400">
            <CheckCircle2 className="mr-2 h-4 w-4" />
            {success}
          </div>
        )}

        {resumes.length === 0 ? (
          <div className="flex flex-col items-center justify-center rounded-lg border border-dashed p-8 text-center animate-in fade-in-50">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/10 mb-4">
              <FileIcon className="h-6 w-6 text-primary" />
            </div>
            <h3 className="text-lg font-semibold mb-1">No resume uploaded yet</h3>
            <p className="text-sm text-muted-foreground mb-4 max-w-sm">
              Upload your resume to prepare it for future Resume Intelligence and opportunity matching. Supported formats: PDF, DOCX (Max 5MB).
            </p>
            <Button 
              variant="outline" 
              onClick={() => fileInputRef.current?.click()}
              disabled={isUploading}
            >
              {isUploading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Upload className="mr-2 h-4 w-4" />}
              Select File
            </Button>
          </div>
        ) : (
          <div className="space-y-6">
            {activeResume && (
              <div className="space-y-3">
                <h3 className="text-sm font-medium text-foreground">Active Resume</h3>
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between p-4 rounded-lg border-2 border-primary/20 bg-primary/5">
                  <div className="flex items-start sm:items-center space-x-4 mb-4 sm:mb-0">
                    <div className="p-2 rounded-full bg-primary/10">
                      <FileText className="h-6 w-6 text-primary" />
                    </div>
                    <div>
                      <div className="flex items-center space-x-2">
                        <p className="font-medium text-foreground">{activeResume.original_filename}</p>
                        <span className="inline-flex items-center rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400">
                          Active
                        </span>
                      </div>
                      <p className="text-sm text-muted-foreground mt-1" suppressHydrationWarning>
                        {formatFileSize(activeResume.file_size)} • Uploaded {new Date(activeResume.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                  <div className="flex flex-wrap items-center gap-2">
                    <Button 
                      variant="outline" 
                      size="sm" 
                      onClick={() => handleDownload(activeResume.id, activeResume.original_filename)}
                      disabled={actionLoading !== null || isUploading}
                    >
                      {actionLoading === `download-${activeResume.id}` ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <Download className="mr-2 h-4 w-4" />
                      )}
                      Download
                    </Button>
                    
                    {activeResume.has_structured_data ? (
                      <>
                        <Button 
                          variant="outline" 
                          size="sm" 
                          onClick={() => handleViewStructuredData(activeResume.id)}
                          disabled={actionLoading !== null || isUploading || isExtracting !== null || isStructuring !== null}
                        >
                          <FileText className="mr-2 h-4 w-4" />
                          View Extracted Details
                        </Button>
                        <Button 
                          variant="outline" 
                          size="sm" 
                          onClick={() => handleStructureResume(activeResume.id, activeResume.original_filename, true)}
                          disabled={actionLoading !== null || isUploading || isExtracting !== null || isStructuring !== null}
                        >
                          {isStructuring === activeResume.id ? (
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          ) : (
                            <RefreshCw className="mr-2 h-4 w-4" />
                          )}
                          Re-extract Details
                        </Button>
                      </>
                    ) : activeResume.has_parsed_text ? (
                      <Button 
                        variant="outline" 
                        size="sm" 
                        onClick={() => handleStructureResume(activeResume.id, activeResume.original_filename)}
                        disabled={actionLoading !== null || isUploading || isExtracting !== null || isStructuring !== null}
                      >
                        {isStructuring === activeResume.id ? (
                          <>
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            Structuring Resume...
                          </>
                        ) : (
                          <>
                            <FileText className="mr-2 h-4 w-4" />
                            Extract Structured Data
                          </>
                        )}
                      </Button>
                    ) : null}

                    {activeResume.has_parsed_text ? (
                      <Button 
                        variant="outline" 
                        size="sm" 
                        onClick={() => handleViewExtractedText(activeResume.id)}
                        disabled={actionLoading !== null || isUploading || isExtracting !== null || isStructuring !== null}
                      >
                        {isExtracting === activeResume.id ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <FileText className="mr-2 h-4 w-4" />
                        )}
                        View Extracted Text
                      </Button>
                    ) : (
                      <Button 
                        variant="outline" 
                        size="sm" 
                        onClick={() => handleExtractText(activeResume.id, activeResume.original_filename)}
                        disabled={actionLoading !== null || isUploading || isExtracting !== null || isStructuring !== null}
                      >
                        {isExtracting === activeResume.id ? (
                          <>
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            Extracting...
                          </>
                        ) : (
                          <>
                            <FileText className="mr-2 h-4 w-4" />
                            Extract Text
                          </>
                        )}
                      </Button>
                    )}

                    {activeResume.has_analysis ? (
                      <Button 
                        variant="default" 
                        size="sm" 
                        onClick={() => handleViewAnalysis(activeResume.id)}
                        disabled={actionLoading !== null || isUploading || isExtracting !== null || isStructuring !== null || isAnalyzing !== null}
                        className="bg-primary text-primary-foreground hover:bg-primary/90"
                      >
                        {isAnalyzing === activeResume.id ? (
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        ) : (
                          <Sparkles className="mr-2 h-4 w-4" />
                        )}
                        View Analysis
                      </Button>
                    ) : activeResume.has_structured_data ? (
                      <Button 
                        variant="default" 
                        size="sm" 
                        onClick={() => handleAnalyzeResume(activeResume.id, activeResume.original_filename)}
                        disabled={actionLoading !== null || isUploading || isExtracting !== null || isStructuring !== null || isAnalyzing !== null}
                      >
                        {isAnalyzing === activeResume.id ? (
                          <>
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            Analyzing...
                          </>
                        ) : (
                          <>
                            <Sparkles className="mr-2 h-4 w-4" />
                            Analyze Resume
                          </>
                        )}
                      </Button>
                    ) : null}

                    <Button 
                      variant="ghost" 
                      size="sm" 
                      onClick={() => handleDelete(activeResume.id, true)}
                      disabled={actionLoading !== null || isUploading}
                      className="text-destructive hover:bg-destructive/10 hover:text-destructive"
                    >
                      {actionLoading === `delete-${activeResume.id}` ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <Trash2 className="h-4 w-4" />
                      )}
                      <span className="sr-only">Delete</span>
                    </Button>
                  </div>
                </div>
              </div>
            )}

            {otherResumes.length > 0 && (
              <div className="space-y-3">
                <h3 className="text-sm font-medium text-foreground">Other Resumes</h3>
                <div className="space-y-3">
                  {otherResumes.map(resume => (
                    <div key={resume.id} className="flex flex-col sm:flex-row items-start sm:items-center justify-between p-4 rounded-lg border bg-card">
                      <div className="flex items-start sm:items-center space-x-4 mb-4 sm:mb-0">
                        <div className="p-2 rounded-full bg-muted">
                          <FileText className="h-6 w-6 text-muted-foreground" />
                        </div>
                        <div>
                          <p className="font-medium text-foreground">{resume.original_filename}</p>
                          <p className="text-sm text-muted-foreground mt-1" suppressHydrationWarning>
                            {formatFileSize(resume.file_size)} • Uploaded {new Date(resume.created_at).toLocaleDateString()}
                          </p>
                        </div>
                      </div>
                      <div className="flex flex-wrap items-center gap-2">
                        <Button 
                          variant="secondary" 
                          size="sm" 
                          onClick={() => handleActivate(resume.id)}
                          disabled={actionLoading !== null || isUploading}
                        >
                          {actionLoading === `activate-${resume.id}` ? (
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          ) : (
                            <CheckCircle2 className="mr-2 h-4 w-4" />
                          )}
                          Set as Active
                        </Button>
                        <Button 
                          variant="outline" 
                          size="sm" 
                          onClick={() => handleDownload(resume.id, resume.original_filename)}
                          disabled={actionLoading !== null || isUploading}
                        >
                          {actionLoading === `download-${resume.id}` ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : (
                            <Download className="mr-2 h-4 w-4" />
                          )}
                          <span className="sr-only sm:not-sr-only sm:ml-2">Download</span>
                        </Button>

                        {resume.has_structured_data ? (
                          <>
                            <Button 
                              variant="outline" 
                              size="sm" 
                              onClick={() => handleViewStructuredData(resume.id)}
                              disabled={actionLoading !== null || isUploading || isExtracting !== null || isStructuring !== null}
                            >
                              <FileText className="mr-2 h-4 w-4" />
                              View Extracted Details
                            </Button>
                            <Button 
                              variant="outline" 
                              size="sm" 
                              onClick={() => handleStructureResume(resume.id, resume.original_filename, true)}
                              disabled={actionLoading !== null || isUploading || isExtracting !== null || isStructuring !== null}
                            >
                              {isStructuring === resume.id ? (
                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                              ) : (
                                <RefreshCw className="mr-2 h-4 w-4" />
                              )}
                              Re-extract Details
                            </Button>
                          </>
                        ) : resume.has_parsed_text ? (
                          <Button 
                            variant="outline" 
                            size="sm" 
                            onClick={() => handleStructureResume(resume.id, resume.original_filename)}
                            disabled={actionLoading !== null || isUploading || isExtracting !== null || isStructuring !== null}
                          >
                            {isStructuring === resume.id ? (
                              <>
                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                Structuring...
                              </>
                            ) : (
                              <>
                                <FileText className="mr-2 h-4 w-4" />
                                Extract Structured Data
                              </>
                            )}
                          </Button>
                        ) : null}

                        {resume.has_parsed_text ? (
                          <Button 
                            variant="outline" 
                            size="sm" 
                            onClick={() => handleViewExtractedText(resume.id)}
                            disabled={actionLoading !== null || isUploading || isExtracting !== null || isStructuring !== null}
                          >
                            {isExtracting === resume.id ? (
                              <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                              <FileText className="mr-2 h-4 w-4" />
                            )}
                            View Extracted Text
                          </Button>
                        ) : (
                          <Button 
                            variant="outline" 
                            size="sm" 
                            onClick={() => handleExtractText(resume.id, resume.original_filename)}
                            disabled={actionLoading !== null || isUploading || isExtracting !== null || isStructuring !== null}
                          >
                            {isExtracting === resume.id ? (
                              <>
                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                Extracting...
                              </>
                            ) : (
                              <>
                                <FileText className="mr-2 h-4 w-4" />
                                Extract Text
                              </>
                            )}
                          </Button>
                        )}

                        {resume.has_analysis ? (
                          <Button 
                            variant="default" 
                            size="sm" 
                            onClick={() => handleViewAnalysis(resume.id)}
                            disabled={actionLoading !== null || isUploading || isExtracting !== null || isStructuring !== null || isAnalyzing !== null}
                            className="bg-primary text-primary-foreground hover:bg-primary/90"
                          >
                            {isAnalyzing === resume.id ? (
                              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            ) : (
                              <Sparkles className="mr-2 h-4 w-4" />
                            )}
                            View Analysis
                          </Button>
                        ) : resume.has_structured_data ? (
                          <Button 
                            variant="default" 
                            size="sm" 
                            onClick={() => handleAnalyzeResume(resume.id, resume.original_filename)}
                            disabled={actionLoading !== null || isUploading || isExtracting !== null || isStructuring !== null || isAnalyzing !== null}
                          >
                            {isAnalyzing === resume.id ? (
                              <>
                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                Analyzing...
                              </>
                            ) : (
                              <>
                                <Sparkles className="mr-2 h-4 w-4" />
                                Analyze Resume
                              </>
                            )}
                          </Button>
                        ) : null}

                        <Button 
                          variant="ghost" 
                          size="sm" 
                          onClick={() => handleDelete(resume.id, false)}
                          disabled={actionLoading !== null || isUploading}
                          className="text-destructive hover:bg-destructive/10 hover:text-destructive"
                        >
                          {actionLoading === `delete-${resume.id}` ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : (
                            <Trash2 className="h-4 w-4" />
                          )}
                          <span className="sr-only">Delete</span>
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </CardContent>

      <Dialog open={viewExtractedTextId !== null} onOpenChange={(open) => !open && setViewExtractedTextId(null)}>
        <DialogContent className="sm:max-w-[800px] max-h-[85vh] flex flex-col bg-muted/30">
          <DialogHeader>
            <DialogTitle>Extracted Resume Text</DialogTitle>
            <DialogDescription>
              Raw text extracted from your document.
            </DialogDescription>
          </DialogHeader>
          
          {dialogError ? (
            <div className="flex items-center rounded-md bg-destructive/15 p-3 text-sm text-destructive">
              <AlertCircle className="mr-2 h-4 w-4" />
              {dialogError}
            </div>
          ) : extractedText ? (
            <div className="flex flex-col flex-1 min-h-0">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <span className="inline-flex items-center rounded-md bg-primary/10 px-2.5 py-1 text-xs font-medium text-primary">
                    {resumes.find(r => r.id === viewExtractedTextId)?.original_filename || "Resume"}
                  </span>
                  <span className="inline-flex items-center rounded-md bg-muted px-2.5 py-1 text-xs font-medium text-muted-foreground">
                    {extractedText.charCount.toLocaleString()} characters
                  </span>
                </div>
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={() => {
                    navigator.clipboard.writeText(extractedText.text);
                    setSuccess("Copied extracted text to clipboard.");
                    setTimeout(() => setSuccess(null), 3000);
                  }}
                >
                  <Copy className="h-4 w-4 mr-2" />
                  Copy Text
                </Button>
              </div>
              <div className="flex-1 overflow-y-auto rounded-lg border bg-card p-6 md:p-10 shadow-sm mx-auto w-full max-w-3xl">
                <pre className="whitespace-pre-wrap font-sans text-sm leading-relaxed text-card-foreground">
                  {extractedText.text}
                </pre>
              </div>
            </div>
          ) : (
            <div className="flex h-32 items-center justify-center">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          )}
        </DialogContent>
      </Dialog>

      <Dialog open={viewStructuredDataId !== null} onOpenChange={(open) => !open && setViewStructuredDataId(null)}>
        <DialogContent className="sm:max-w-[800px] max-h-[85vh] flex flex-col overflow-hidden">
          <DialogHeader>
            <DialogTitle>Extracted Resume Details</DialogTitle>
            <DialogDescription>
              We identified information from your resume. Review it for accuracy.
            </DialogDescription>
          </DialogHeader>
          
          <div className="flex-1 overflow-y-auto pr-2 space-y-6">
            <div className="rounded-md bg-muted/50 p-4 border text-sm text-muted-foreground">
              <AlertCircle className="inline-block mr-2 h-4 w-4 mb-0.5 text-primary" />
              Automated extraction can miss details or misinterpret resume formatting. This extraction does not automatically update your Profile, Skills, Education, Experience or Projects.
            </div>

            {(structuredData?.structured_data?.warnings?.length || 0) > 0 && (
              <div className="rounded-md bg-amber-500/15 p-4 border border-amber-500/20">
                <h4 className="font-semibold text-amber-700 dark:text-amber-400 mb-2 flex items-center">
                  <AlertCircle className="mr-2 h-4 w-4" />
                  Warnings
                </h4>
                <ul className="list-disc pl-5 space-y-1 text-sm text-amber-600 dark:text-amber-500">
                  {structuredData?.structured_data?.warnings?.map((w: string, i: number) => (
                    <li key={i}>{w}</li>
                  ))}
                </ul>
              </div>
            )}

            {structuredData?.structured_data && (
              <>
                {/* Contact Information */}
                {Object.values(structuredData.structured_data.contact || {}).some((arr) => Array.isArray(arr) && arr.length > 0) && (
                  <section className="space-y-3">
                    <h3 className="text-lg font-semibold border-b pb-2">Contact Information</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {structuredData.structured_data.contact.emails?.length > 0 && (
                        <div>
                          <p className="text-sm font-medium text-muted-foreground">Emails</p>
                          <ul className="mt-1 space-y-1">
                            {structuredData.structured_data.contact.emails.map((e: string, i: number) => (
                              <li key={i} className="text-sm">{e}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                      <div>
                        <p className="text-sm font-medium text-muted-foreground">Phones</p>
                        {structuredData.structured_data.contact.phones?.length > 0 ? (
                          <ul className="mt-1 space-y-1">
                            {structuredData.structured_data.contact.phones.map((p: string, i: number) => (
                              <li key={i} className="text-sm">{p}</li>
                            ))}
                          </ul>
                        ) : (
                          <p className="text-sm text-muted-foreground mt-1">Not detected</p>
                        )}
                      </div>
                      {structuredData.structured_data.contact.linkedin_urls?.length > 0 && (
                        <div>
                          <p className="text-sm font-medium text-muted-foreground">LinkedIn</p>
                          <ul className="mt-1 space-y-1">
                            {structuredData.structured_data.contact.linkedin_urls.map((url: string, i: number) => (
                              <li key={i} className="text-sm truncate">
                                <SafeUrl url={url} />
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {structuredData.structured_data.contact.github_urls?.length > 0 && (
                        <div>
                          <p className="text-sm font-medium text-muted-foreground">GitHub</p>
                          <ul className="mt-1 space-y-1">
                            {structuredData.structured_data.contact.github_urls.map((url: string, i: number) => (
                              <li key={i} className="text-sm truncate">
                                <SafeUrl url={url} />
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {structuredData.structured_data.contact.portfolio_urls?.length > 0 && (
                        <div>
                          <p className="text-sm font-medium text-muted-foreground">Portfolio</p>
                          <ul className="mt-1 space-y-1">
                            {structuredData.structured_data.contact.portfolio_urls.map((url: string, i: number) => (
                              <li key={i} className="text-sm truncate">
                                <SafeUrl url={url} />
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </section>
                )}

                {/* Skills */}
                {structuredData.structured_data.skills?.length > 0 && (
                  <section className="space-y-3">
                    <h3 className="text-lg font-semibold border-b pb-2">Recognized Skills</h3>
                    <div className="flex flex-wrap gap-2">
                      {structuredData.structured_data.skills.map((s, i: number) => (
                        <div key={i} className="inline-flex flex-col bg-muted rounded-md p-2 text-sm border">
                          <span className="font-semibold">{s.name}</span>
                          {s.evidence && s.evidence.length > 0 && (
                            <span className="text-xs text-muted-foreground mt-1 block max-w-[200px] truncate" title={s.evidence}>
                              Found in: {s.evidence}
                            </span>
                          )}
                        </div>
                      ))}
                    </div>
                  </section>
                )}

                {/* Sections */}
                {structuredData.structured_data.sections && Object.entries(structuredData.structured_data.sections).some(([, v]) => v) && (
                  <section className="space-y-4">
                    <h3 className="text-lg font-semibold border-b pb-2">Resume Sections</h3>
                    
                    {['summary', 'skills', 'experience', 'education', 'projects', 'certifications', 'achievements', 'publications'].map((sectionKey) => {
                      const content = structuredData.structured_data!.sections[sectionKey];
                      if (!content) return null;
                      
                      return (
                        <div key={sectionKey} className="space-y-2">
                          <h4 className="text-sm font-medium text-muted-foreground capitalize">{sectionKey}</h4>
                          <div className="bg-card rounded-md border p-3">
                            <pre className="whitespace-pre-wrap font-sans text-sm text-foreground">
                              {content}
                            </pre>
                          </div>
                        </div>
                      );
                    })}
                  </section>
                )}
              </>
            )}
          </div>
        </DialogContent>
      </Dialog>
      <Dialog open={viewAnalysisId !== null} onOpenChange={(open) => !open && setViewAnalysisId(null)}>
        <DialogContent className="sm:max-w-[850px] max-h-[90vh] flex flex-col overflow-hidden bg-background">
          <DialogHeader className="border-b pb-4">
            <div className="flex items-center justify-between">
              <DialogTitle className="text-xl flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-primary" />
                Resume Intelligence
              </DialogTitle>
              {viewAnalysisId && (
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={() => {
                    const resume = resumes.find(r => r.id === viewAnalysisId);
                    if (resume) handleAnalyzeResume(viewAnalysisId, resume.original_filename);
                  }}
                  disabled={isAnalyzing !== null}
                >
                  <RefreshCw className={`h-4 w-4 mr-2 ${isAnalyzing === viewAnalysisId ? 'animate-spin' : ''}`} />
                  Reanalyze
                </Button>
              )}
            </div>
            <DialogDescription className="text-sm mt-2 text-muted-foreground">
              Resume Completeness Score measures detected content and section organization. 
              It is not a hiring prediction or a guaranteed ATS compatibility score.
            </DialogDescription>
          </DialogHeader>

          <div className="flex-1 overflow-y-auto py-4 space-y-8 pr-2">
            {analysisData?.analysis ? (
              <>
                {/* Score Section */}
                <div className="flex flex-col md:flex-row gap-6 items-start">
                  <div className="w-full md:w-1/3 bg-primary/5 rounded-xl p-6 border-2 border-primary/10 flex flex-col items-center justify-center text-center">
                    <span className="text-sm font-semibold uppercase tracking-wider text-muted-foreground mb-2">
                      Completeness Score
                    </span>
                    <div className="text-6xl font-bold text-primary mb-2">
                      {analysisData.analysis.completeness_score}
                    </div>
                    <span className="inline-flex items-center rounded-full bg-primary/10 px-3 py-1 text-sm font-medium text-primary">
                      {analysisData.analysis.score_label}
                    </span>
                  </div>

                  <div className="w-full md:w-2/3 space-y-4">
                    <h3 className="font-semibold text-foreground flex items-center">
                      <BarChart className="h-4 w-4 mr-2 text-muted-foreground" />
                      Score Breakdown
                    </h3>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-3">
                      {[
                        { label: "Contact Info", score: analysisData.analysis.category_scores.contact, max: 15 },
                        { label: "Summary", score: analysisData.analysis.category_scores.summary, max: 10 },
                        { label: "Education", score: analysisData.analysis.category_scores.education, max: 15 },
                        { label: "Skills", score: analysisData.analysis.category_scores.skills, max: 20 },
                        { label: "Experience & Projects", score: analysisData.analysis.category_scores.experience_projects, max: 25 },
                        { label: "Organization", score: analysisData.analysis.category_scores.organization, max: 15 },
                      ].map((cat, i) => (
                        <div key={i} className="space-y-1.5">
                          <div className="flex justify-between text-sm">
                            <span className="text-muted-foreground">{cat.label}</span>
                            <span className="font-medium text-foreground">{cat.score} / {cat.max}</span>
                          </div>
                          <div className="h-2 w-full bg-muted rounded-full overflow-hidden">
                            <div 
                              className="h-full bg-primary transition-all" 
                              style={{ width: `${(cat.score / cat.max) * 100}%` }}
                            />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Findings & Strengths */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Improvements */}
                  <div className="space-y-4">
                    <h3 className="font-semibold text-amber-700 dark:text-amber-400 flex items-center border-b border-amber-200 dark:border-amber-900 pb-2">
                      <AlertTriangle className="h-4 w-4 mr-2" />
                      Improvement Suggestions
                    </h3>
                    {analysisData.analysis.findings.length > 0 ? (
                      <div className="space-y-3">
                        {analysisData.analysis.findings.map((f, i) => (
                          <div key={i} className={`border rounded-lg p-3 text-sm ${
                            f.severity === 'critical' 
                              ? 'bg-destructive/10 border-destructive/20' 
                              : 'bg-amber-50/50 dark:bg-amber-950/20 border-amber-100 dark:border-amber-900/50'
                          }`}>
                            <div className={`font-medium mb-1 ${
                              f.severity === 'critical' ? 'text-destructive' : 'text-amber-900 dark:text-amber-200'
                            }`}>{f.title}</div>
                            <p className={`mb-2 ${
                              f.severity === 'critical' ? 'text-destructive/80' : 'text-amber-700 dark:text-amber-400/90'
                            }`}>{f.explanation}</p>
                            <div className={`rounded px-2 py-1.5 flex gap-2 ${
                              f.severity === 'critical' ? 'bg-destructive/20' : 'bg-amber-100/50 dark:bg-amber-900/30'
                            }`}>
                              <Info className={`h-4 w-4 shrink-0 mt-0.5 ${
                                f.severity === 'critical' ? 'text-destructive' : 'text-amber-600 dark:text-amber-500'
                              }`} />
                              <span className={`font-medium ${
                                f.severity === 'critical' ? 'text-destructive' : 'text-amber-800 dark:text-amber-300'
                              }`}>{f.recommendation}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-sm text-muted-foreground italic">No major issues found.</p>
                    )}
                  </div>

                  {/* Strengths */}
                  <div className="space-y-4">
                    <h3 className="font-semibold text-emerald-700 dark:text-emerald-400 flex items-center border-b border-emerald-200 dark:border-emerald-900 pb-2">
                      <CheckCircle2 className="h-4 w-4 mr-2" />
                      Detected Strengths
                    </h3>
                    {analysisData.analysis.strengths.length > 0 ? (
                      <div className="space-y-3">
                        {analysisData.analysis.strengths.map((s, i) => (
                          <div key={i} className="bg-emerald-50/50 dark:bg-emerald-950/20 border border-emerald-100 dark:border-emerald-900/50 rounded-lg p-3 text-sm">
                            <div className="font-medium text-emerald-900 dark:text-emerald-200 mb-1">{s.title}</div>
                            <p className="text-emerald-700 dark:text-emerald-400/90">{s.explanation}</p>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-sm text-muted-foreground italic">Add more content to build strengths.</p>
                    )}
                  </div>
                </div>

                {/* ATS-readiness checks */}
                <div className="space-y-4">
                  <h3 className="font-semibold text-foreground flex items-center border-b pb-2">
                    <ShieldCheck className="h-4 w-4 mr-2 text-muted-foreground" />
                    Basic ATS-Readiness Checks
                  </h3>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
                    <div className="flex items-center gap-2">
                      <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                      <span>PDF/DOCX text was readable</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                      <span>Document contains structured text</span>
                    </div>
                    <div className="flex items-center gap-2">
                      {analysisData.analysis.category_scores.organization > 0 ? (
                        <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                      ) : (
                        <AlertCircle className="h-4 w-4 text-amber-500" />
                      )}
                      <span>Standard resume sections detected</span>
                    </div>
                    <div className="flex items-center gap-2">
                      {analysisData.analysis.category_scores.contact > 0 ? (
                        <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                      ) : (
                        <AlertCircle className="h-4 w-4 text-amber-500" />
                      )}
                      <span>Contact information detected</span>
                    </div>
                    <div className="flex items-center gap-2">
                      {analysisData.analysis.category_scores.skills > 0 ? (
                        <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                      ) : (
                        <AlertCircle className="h-4 w-4 text-amber-500" />
                      )}
                      <span>Recognized catalog skills detected</span>
                    </div>
                  </div>
                  <p className="text-xs text-muted-foreground mt-2">
                    Note: These are basic rule-based checks. They do not assess visual formatting, table structures, or guarantee compatibility with all ATS platforms.
                  </p>
                </div>
              </>
            ) : (
              <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
                {isAnalyzing ? (
                  <>
                    <Loader2 className="h-8 w-8 animate-spin mb-4" />
                    <p>Analyzing resume content...</p>
                  </>
                ) : (
                  <p>No analysis data available.</p>
                )}
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </Card>
  );
}
