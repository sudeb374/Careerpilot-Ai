import re

with open('components/profile/resume-section.tsx', 'r') as f:
    content = f.read()

# 1. Add has_structured_data to Resume interface
content = content.replace(
    "  has_parsed_text: boolean;\n  created_at: string;",
    "  has_parsed_text: boolean;\n  has_structured_data: boolean;\n  created_at: string;"
)

# 2. Add state variables
state_vars = """
  const [isStructuring, setIsStructuring] = useState<string | null>(null);
  const [viewStructuredDataId, setViewStructuredDataId] = useState<string | null>(null);
  const [structuredData, setStructuredData] = useState<any | null>(null);
"""
content = content.replace(
    "const [dialogError, setDialogError] = useState<string | null>(null);",
    "const [dialogError, setDialogError] = useState<string | null>(null);" + state_vars
)

# 3. Add handlers
handlers = """
  const handleStructureResume = async (id: string, originalFilename: string) => {
    if (actionLoading || isUploading || isExtracting || isStructuring) return;
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
        } catch (_e) {}
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
        } catch (_e) {}
        setError(`Failed to retrieve structured data: ${errorDetail}`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "An unexpected error occurred retrieving structured data.");
    } finally {
      setIsStructuring(null);
    }
  };
"""

content = content.replace(
    "  const formatFileSize = (bytes: number) => {",
    handlers + "\n  const formatFileSize = (bytes: number) => {"
)

# 4. Buttons - We need to replace the logic around has_parsed_text
active_buttons = """
                    {activeResume.has_structured_data ? (
                      <Button 
                        variant="outline" 
                        size="sm" 
                        onClick={() => handleViewStructuredData(activeResume.id)}
                        disabled={actionLoading !== null || isUploading || isExtracting !== null || isStructuring !== null}
                      >
                        {isStructuring === activeResume.id ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <FileText className="mr-2 h-4 w-4" />
                        )}
                        View Structured Data
                      </Button>
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
"""
content = re.sub(
    r"\{activeResume\.has_parsed_text \? \([\s\S]*?View Extracted Text[\s\S]*?</Button>\n\s*\) : \(",
    active_buttons,
    content
)

# We also need to add isStructuring to Extract Text disable condition
content = content.replace(
    "disabled={actionLoading !== null || isUploading || isExtracting !== null}",
    "disabled={actionLoading !== null || isUploading || isExtracting !== null || isStructuring !== null}"
)

# Other resumes buttons
other_buttons = """
                        {resume.has_structured_data ? (
                          <Button 
                            variant="outline" 
                            size="sm" 
                            onClick={() => handleViewStructuredData(resume.id)}
                            disabled={actionLoading !== null || isUploading || isExtracting !== null || isStructuring !== null}
                          >
                            {isStructuring === resume.id ? (
                              <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                              <FileText className="mr-2 h-4 w-4" />
                            )}
                            View Structured Data
                          </Button>
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
"""
content = re.sub(
    r"\{resume\.has_parsed_text \? \([\s\S]*?View Extracted Text[\s\S]*?</Button>\n\s*\) : \(",
    other_buttons,
    content
)

# 5. Add Structured Data Dialog
dialog = """
      <Dialog open={viewStructuredDataId !== null} onOpenChange={(open) => !open && setViewStructuredDataId(null)}>
        <DialogContent className="sm:max-w-[800px] max-h-[85vh] flex flex-col overflow-hidden">
          <DialogHeader>
            <DialogTitle>Structured Resume Data</DialogTitle>
            <DialogDescription>
              Rule-based extraction results. This is not an AI-generated assessment.
            </DialogDescription>
          </DialogHeader>
          
          <div className="flex-1 overflow-y-auto pr-2 space-y-6">
            <div className="rounded-md bg-muted/50 p-4 border text-sm text-muted-foreground">
              <AlertCircle className="inline-block mr-2 h-4 w-4 mb-0.5 text-primary" />
              <strong>Review the extracted information for accuracy before using it.</strong> Automated extraction may miss details or misinterpret resume formatting. This extraction does not automatically update your Profile, Skills, Education, Experience or Projects.
            </div>

            {structuredData?.warnings?.length > 0 && (
              <div className="rounded-md bg-amber-500/15 p-4 border border-amber-500/20">
                <h4 className="font-semibold text-amber-700 dark:text-amber-400 mb-2 flex items-center">
                  <AlertCircle className="mr-2 h-4 w-4" />
                  Warnings
                </h4>
                <ul className="list-disc pl-5 space-y-1 text-sm text-amber-600 dark:text-amber-500">
                  {structuredData.warnings.map((w: string, i: number) => (
                    <li key={i}>{w}</li>
                  ))}
                </ul>
              </div>
            )}

            {structuredData?.structured_data && (
              <>
                {/* Contact Information */}
                {Object.values(structuredData.structured_data.contact || {}).some((arr: any) => arr && arr.length > 0) && (
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
                      {structuredData.structured_data.contact.phones?.length > 0 && (
                        <div>
                          <p className="text-sm font-medium text-muted-foreground">Phones</p>
                          <ul className="mt-1 space-y-1">
                            {structuredData.structured_data.contact.phones.map((p: string, i: number) => (
                              <li key={i} className="text-sm">{p}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {structuredData.structured_data.contact.linkedin_urls?.length > 0 && (
                        <div>
                          <p className="text-sm font-medium text-muted-foreground">LinkedIn</p>
                          <ul className="mt-1 space-y-1">
                            {structuredData.structured_data.contact.linkedin_urls.map((url: string, i: number) => (
                              <li key={i} className="text-sm truncate">
                                <a href={url.startsWith('http') ? url : `https://${url}`} target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">{url}</a>
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
                                <a href={url.startsWith('http') ? url : `https://${url}`} target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">{url}</a>
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
                                <a href={url.startsWith('http') ? url : `http://${url}`} target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">{url}</a>
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
                      {structuredData.structured_data.skills.map((s: any, i: number) => (
                        <div key={i} className="inline-flex flex-col bg-muted rounded-md p-2 text-sm border">
                          <span className="font-semibold">{s.name}</span>
                          {s.evidence?.length > 0 && (
                            <span className="text-xs text-muted-foreground mt-1 block max-w-[200px] truncate" title={s.evidence.join(", ")}>
                              Found in: {s.evidence.join(", ")}
                            </span>
                          )}
                        </div>
                      ))}
                    </div>
                  </section>
                )}

                {/* Sections */}
                {structuredData.structured_data.sections && Object.entries(structuredData.structured_data.sections).some(([_, v]) => v) && (
                  <section className="space-y-4">
                    <h3 className="text-lg font-semibold border-b pb-2">Resume Sections</h3>
                    
                    {['summary', 'skills', 'experience', 'education', 'projects', 'certifications', 'achievements', 'publications'].map((sectionKey) => {
                      const content = structuredData.structured_data.sections[sectionKey];
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
"""

content = content.replace("    </Card>\n  );\n}", dialog + "    </Card>\n  );\n}")

with open('components/profile/resume-section.tsx', 'w') as f:
    f.write(content)
