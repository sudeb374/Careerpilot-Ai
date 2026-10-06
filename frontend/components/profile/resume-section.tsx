"use client";

import { useEffect, useState, useRef } from "react";
import { createClient } from "@/lib/supabase/client";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2, Upload, FileText, CheckCircle2, Trash2, Download, AlertCircle, FileIcon } from "lucide-react";

interface Resume {
  id: string;
  original_filename: string;
  file_type: string;
  file_size: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5MB

export function ResumeSection() {
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);
  
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
          } catch (_e) {
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
        } catch (_e) {
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
                      <p className="text-sm text-muted-foreground mt-1">
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
                          <p className="text-sm text-muted-foreground mt-1">
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
    </Card>
  );
}
