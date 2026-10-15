import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { CoverLetterGenerator } from "../cover-letter-generator";
import { InterviewPrep } from "../interview-prep";
import { ApplicationAssistant } from "../application-assistant";
import { SkillGapRoadmap } from "../skill-gap-roadmap";
import { JobResumeRecommendations } from "../job-resume-recommendations";

const mockPush = vi.fn();
const mockReplace = vi.fn();
let mockSearchParams = new URLSearchParams();

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: mockPush,
    replace: mockReplace,
    prefetch: vi.fn(),
    back: vi.fn(),
  }),
  useSearchParams: () => mockSearchParams,
  usePathname: () => "/copilot",
}));

const mockSupabase = {
  auth: {
    getSession: vi.fn().mockResolvedValue({
      data: {
        session: {
          access_token: "mock-copilot-token",
          user: { id: "test-user-id", email: "copilot@test.com" },
        },
      },
    }),
  },
};

vi.mock("@/lib/supabase/client", () => ({
  createClient: () => mockSupabase,
}));

const mockOpportunity = {
  id: "opp-copilot-1",
  title: "Cloud Infrastructure Engineer",
  company_name: "CloudTech Inc",
  opportunity_type: "Full-Time",
  work_model: "Remote",
  locations: ["Seattle, WA"],
  skills: [{ id: "s-1", name: "Terraform" }, { id: "s-2", name: "AWS" }],
};

describe("Career Copilot Deterministic Fallback UI Tests", () => {
  let user: ReturnType<typeof userEvent.setup>;

  beforeEach(() => {
    user = userEvent.setup();
    mockSearchParams = new URLSearchParams();
    mockSupabase.auth.getSession.mockResolvedValue({
      data: {
        session: {
          access_token: "mock-copilot-token",
          user: { id: "test-user-id", email: "copilot@test.com" },
        },
      },
    });
  });

  describe("CoverLetterGenerator Component", () => {
    it("displays initial empty state before generation", async () => {
      global.fetch = vi.fn().mockImplementation((url: string) => {
        if (url.includes("/api/v1/opportunities")) {
          return Promise.resolve({
            ok: true,
            status: 200,
            json: async () => ({ items: [mockOpportunity], total: 1 }),
          });
        }
        return Promise.resolve({ ok: true, status: 200, json: async () => ({}) });
      });

      render(<CoverLetterGenerator />);

      await waitFor(() => {
        expect(screen.getByText("Ready to Generate Your Draft")).toBeDefined();
        expect(screen.getByText(/Truthful Facts Only/i)).toBeDefined();
      });
    });

    it("displays deterministic template draft fallback badge and text when template fallback is used", async () => {
      global.fetch = vi.fn().mockImplementation((url: string, options?: RequestInit) => {
        const urlStr = url.toString();
        const method = options?.method || "GET";

        if (urlStr.includes("/api/v1/opportunities")) {
          return Promise.resolve({
            ok: true,
            status: 200,
            json: async () => ({ items: [mockOpportunity], total: 1 }),
          });
        }

        if (urlStr.includes("/cover-letter/generate") && method === "POST") {
          return Promise.resolve({
            ok: true,
            status: 200,
            json: async () => ({
              opportunity_id: "opp-copilot-1",
              opportunity_title: "Cloud Infrastructure Engineer",
              company_name: "CloudTech Inc",
              recipient_name: "Hiring Manager",
              tone: "professional",
              length: "standard",
              subject_line: "Application for Cloud Infrastructure Engineer - Candidate Name",
              cover_letter_text: "Dear Hiring Manager,\n\nI am writing to express my interest in the Cloud Infrastructure Engineer role...",
              provider: "deterministic",
              provider_model: null,
              is_template_fallback: true,
              provider_note: "Grounded template generation without external LLM dependencies.",
              verified_evidence: {
                matched_skills: ["AWS", "Terraform"],
                included_projects: ["Infrastructure as Code Setup"],
                included_experiences: [],
                included_education: ["B.S. in Computer Science"],
                resume_evidence_snippets: [],
              },
              data_warnings: [],
              disclaimer: "CareerPilot AI does not fabricate achievements.",
            }),
          });
        }

        return Promise.resolve({ ok: true, status: 200, json: async () => ({}) });
      });

      render(<CoverLetterGenerator />);

      await waitFor(() => {
        expect(screen.getAllByText(/Cloud Infrastructure Engineer/).length).toBeGreaterThan(0);
      });

      // Click generate button
      const genBtn = screen.getByRole("button", { name: /generate tailored cover letter/i });
      await user.click(genBtn);

      // Verify deterministic fallback badge and drafted letter are displayed
      await waitFor(() => {
        expect(screen.getByText("Deterministic Template Draft")).toBeDefined();
        expect(screen.getByText(/I am writing to express my interest in the Cloud Infrastructure Engineer role/i)).toBeDefined();
        expect(screen.getByText("Application for Cloud Infrastructure Engineer - Candidate Name")).toBeDefined();
      });
    });

    it("displays generation error banner when generation request fails", async () => {
      global.fetch = vi.fn().mockImplementation((url: string, options?: RequestInit) => {
        const urlStr = url.toString();
        const method = options?.method || "GET";

        if (urlStr.includes("/api/v1/opportunities")) {
          return Promise.resolve({
            ok: true,
            status: 200,
            json: async () => ({ items: [mockOpportunity], total: 1 }),
          });
        }

        if (urlStr.includes("/cover-letter/generate") && method === "POST") {
          return Promise.resolve({
            ok: false,
            status: 503,
            json: async () => ({ detail: "Copilot generation service unavailable." }),
          });
        }

        return Promise.resolve({ ok: true, status: 200, json: async () => ({}) });
      });

      render(<CoverLetterGenerator />);

      await waitFor(() => {
        expect(screen.getAllByText(/Cloud Infrastructure Engineer/).length).toBeGreaterThan(0);
      });

      const genBtn = screen.getByRole("button", { name: /generate tailored cover letter/i });
      await user.click(genBtn);

      await waitFor(() => {
        expect(screen.getByText("Generation Error")).toBeDefined();
        expect(screen.getByText("Copilot generation service unavailable.")).toBeDefined();
      });
    });
  });

  describe("InterviewPrep Component", () => {
    it("displays deterministic fallback when question bank is not seeded", async () => {
      global.fetch = vi.fn().mockImplementation((url: string, options?: RequestInit) => {
        const urlStr = url.toString();
        const method = options?.method || "GET";

        if (urlStr.includes("/copilot/interview-prep/config")) {
          return Promise.resolve({
            ok: true,
            status: 200,
            json: async () => ({
              roles: ["Backend Developer"],
              categories: ["All Categories", "System Design"],
              difficulties: ["All Levels", "Medium"],
              published_opportunities: [mockOpportunity],
            }),
          });
        }

        if (urlStr.includes("/copilot/interview-prep/session") && method === "POST") {
          return Promise.resolve({
            ok: true,
            status: 200,
            json: async () => ({
              session_id: "empty-session",
              questions: [],
              total_questions: 0,
              selected_role: "Backend Developer",
              opportunity_title: null,
              opportunity_company: null,
              category_filter: null,
              difficulty_filter: null,
              is_empty_bank: true,
              insufficient_coverage: false,
              notice: "The interview question bank has not been seeded yet in this environment.",
            }),
          });
        }

        return Promise.resolve({ ok: true, status: 200, json: async () => ({}) });
      });

      render(<InterviewPrep />);

      await waitFor(() => {
        expect(screen.getByRole("button", { name: /start practice session/i })).toBeDefined();
      });

      const startBtn = screen.getByRole("button", { name: /start practice session/i });
      await user.click(startBtn);

      // Verify question bank not seeded notice and command are rendered
      await waitFor(() => {
        expect(screen.getByText("Question Bank Not Seeded")).toBeDefined();
        expect(screen.getByText(/the interview question bank has not been seeded yet/i)).toBeDefined();
        expect(screen.getByText(/python -m app.seeds.seed_interview_questions/i)).toBeDefined();
      });
    });

    it("displays error alert when session start request fails", async () => {
      global.fetch = vi.fn().mockImplementation((url: string, options?: RequestInit) => {
        const urlStr = url.toString();
        const method = options?.method || "GET";

        if (urlStr.includes("/copilot/interview-prep/config")) {
          return Promise.resolve({
            ok: true,
            status: 200,
            json: async () => ({
              roles: ["Full Stack"],
              categories: ["All Categories"],
              difficulties: ["All Levels"],
              published_opportunities: [],
            }),
          });
        }

        if (urlStr.includes("/copilot/interview-prep/session") && method === "POST") {
          return Promise.resolve({
            ok: false,
            status: 500,
            json: async () => ({ detail: "Database connection failed for interview session." }),
          });
        }

        return Promise.resolve({ ok: true, status: 200, json: async () => ({}) });
      });

      render(<InterviewPrep />);

      await waitFor(() => {
        expect(screen.getByRole("button", { name: /start practice session/i })).toBeDefined();
      });

      const startBtn = screen.getByRole("button", { name: /start practice session/i });
      await user.click(startBtn);

      await waitFor(() => {
        expect(screen.getByText("Database connection failed for interview session.")).toBeDefined();
      });
    });
  });

  describe("ApplicationAssistant Component", () => {
    it("displays initial empty prompt and renders deterministic template draft badge on generation", async () => {
      global.fetch = vi.fn().mockImplementation((url: string, options?: RequestInit) => {
        const urlStr = url.toString();
        const method = options?.method || "GET";

        if (urlStr.includes("/api/v1/opportunities")) {
          return Promise.resolve({
            ok: true,
            status: 200,
            json: async () => ({ items: [mockOpportunity], total: 1 }),
          });
        }

        if (urlStr.includes("/suggested-questions")) {
          return Promise.resolve({
            ok: true,
            status: 200,
            json: async () => [
              {
                category: "Technical",
                question: "Why are you interested in this position?",
                description: "Standard motivation prompt",
              },
            ],
          });
        }

        if (urlStr.includes("/application-assistant/generate") && method === "POST") {
          return Promise.resolve({
            ok: true,
            status: 200,
            json: async () => ({
              question: "Why are you interested in this position?",
              opportunity_id: "opp-copilot-1",
              opportunity_title: "Cloud Infrastructure Engineer",
              company_name: "CloudTech Inc",
              style: "professional",
              word_limit: null,
              answer_text: "My technical experience with AWS and Terraform directly aligns with CloudTech Inc's goals.",
              provider: "deterministic",
              provider_model: null,
              is_template_fallback: true,
              provider_note: "Grounded template response.",
              verified_evidence: {
                matched_skills: ["AWS", "Terraform"],
                verified_skills: ["AWS"],
                resume_skills: ["Terraform"],
                included_projects: [],
                included_experiences: [],
                included_education: [],
                missing_information_notes: [],
              },
              data_warnings: [],
              disclaimer: "Strictly grounded in verified records.",
            }),
          });
        }

        return Promise.resolve({ ok: true, status: 200, json: async () => ({}) });
      });

      render(<ApplicationAssistant />);

      // Verify empty prompt card is initially visible
      await waitFor(() => {
        expect(screen.getByText("Ready to Answer Your Questions")).toBeDefined();
      });

      // Enter question
      const questionInput = screen.getByPlaceholderText(/why should we hire you/i);
      await user.type(questionInput, "Why are you interested in this position?");

      // Click generate button
      const genBtn = screen.getByRole("button", { name: /generate tailored answer/i });
      await user.click(genBtn);

      // Verify deterministic fallback badge and answer are rendered
      await waitFor(() => {
        expect(screen.getByText("Deterministic Template Draft")).toBeDefined();
        expect(screen.getByText(/my technical experience with aws and terraform directly aligns/i)).toBeDefined();
      });
    });

    it("disables generate button when question is empty and displays validation error when question is too short", async () => {
      global.fetch = vi.fn().mockImplementation((url: string) => {
        if (url.includes("/api/v1/opportunities")) {
          return Promise.resolve({
            ok: true,
            status: 200,
            json: async () => ({ items: [], total: 0 }),
          });
        }
        if (url.includes("/suggested-questions")) {
          return Promise.resolve({ ok: true, status: 200, json: async () => [] });
        }
        return Promise.resolve({ ok: true, status: 200, json: async () => ({}) });
      });

      render(<ApplicationAssistant />);

      await waitFor(() => {
        expect(screen.getByRole("button", { name: /generate tailored answer/i })).toBeDefined();
      });

      const genBtn = screen.getByRole("button", { name: /generate tailored answer/i });
      expect(genBtn.hasAttribute("disabled")).toBe(true);

      const questionInput = screen.getByPlaceholderText(/why should we hire you/i);
      await user.type(questionInput, "Why");
      expect(genBtn.hasAttribute("disabled")).toBe(false);

      await user.click(genBtn);

      await waitFor(() => {
        expect(screen.getByText(/please enter an application question \(at least 5 characters\)/i)).toBeDefined();
      });
    });
  });

  describe("SkillGapRoadmap Component", () => {
    it("displays deterministic fallback alert when candidate profile is incomplete", async () => {
      global.fetch = vi.fn().mockImplementation((url: string) => {
        if (url.includes("/copilot/skill-gap-roadmap")) {
          return Promise.resolve({
            ok: true,
            status: 200,
            json: async () => ({
              target_role: "DevOps Engineer",
              available_target_roles: ["DevOps Engineer", "Software Engineer"],
              total_analyzed_opportunities: 5,
              coverage: {
                total_market_skills: 10,
                acquired_skills_count: 3,
                missing_skills_count: 7,
                coverage_percentage: 30,
                disclaimer: "Based on active listings",
              },
              data_status: {
                has_insufficient_profile: true,
                profile_message: "Your profile has no designated target roles or career preferences configured.",
                has_insufficient_jobs: false,
                jobs_message: null,
              },
              acquired_skills: [],
              missing_skills: [],
              learning_sequence: [],
            }),
          });
        }
        return Promise.resolve({ ok: true, status: 200, json: async () => ({}) });
      });

      render(<SkillGapRoadmap />);

      await waitFor(() => {
        expect(screen.getByText("Incomplete Profile Preferences")).toBeDefined();
        expect(screen.getByText(/your profile has no designated target roles or career preferences configured/i)).toBeDefined();
        expect(screen.getByRole("button", { name: /configure preferences in profile/i })).toBeDefined();
      });
    });

    it("displays deterministic fallback alert when employer job data is insufficient", async () => {
      global.fetch = vi.fn().mockImplementation((url: string) => {
        if (url.includes("/copilot/skill-gap-roadmap")) {
          return Promise.resolve({
            ok: true,
            status: 200,
            json: async () => ({
              target_role: "Quantum Computing Specialist",
              available_target_roles: ["Quantum Computing Specialist"],
              total_analyzed_opportunities: 0,
              coverage: {
                total_market_skills: 0,
                acquired_skills_count: 0,
                missing_skills_count: 0,
                coverage_percentage: 0,
                disclaimer: "No active postings",
              },
              data_status: {
                has_insufficient_profile: false,
                profile_message: null,
                has_insufficient_jobs: true,
                jobs_message: "Fewer than 1 active opportunities match this target role in the database.",
              },
              acquired_skills: [],
              missing_skills: [],
              learning_sequence: [],
            }),
          });
        }
        return Promise.resolve({ ok: true, status: 200, json: async () => ({}) });
      });

      render(<SkillGapRoadmap />);

      await waitFor(() => {
        expect(screen.getByText("No Verified Job Data Available")).toBeDefined();
        expect(screen.getByText(/fewer than 1 active opportunities match this target role/i)).toBeDefined();
        expect(screen.getByText(/skill demand is never invented or simulated when live employer postings are absent/i)).toBeDefined();
      });
    });
  });

  describe("JobResumeRecommendations Component", () => {
    it("displays fallback message when no active resume is uploaded", async () => {
      global.fetch = vi.fn().mockImplementation((url: string) => {
        const urlStr = url.toString();

        if (urlStr.includes("/api/v1/opportunities")) {
          return Promise.resolve({
            ok: true,
            status: 200,
            json: async () => ({ items: [mockOpportunity], total: 1 }),
          });
        }

        if (urlStr.includes("/resume-recommendations/context")) {
          return Promise.resolve({
            ok: true,
            status: 200,
            json: async () => ({
              opportunity_id: "opp-copilot-1",
              opportunity_title: "Cloud Infrastructure Engineer",
              company_name: "CloudTech Inc",
              opportunity_type: "Full-Time",
              work_model: "Remote",
              locations: ["Seattle, WA"],
              has_description: true,
              description_char_count: 500,
              skills_required: ["AWS", "Terraform"],
              active_resume: null,
              is_ready_for_analysis: false,
              readiness_notes: ["Upload an active resume to compare against this job."],
            }),
          });
        }

        return Promise.resolve({ ok: true, status: 200, json: async () => ({}) });
      });

      render(<JobResumeRecommendations />);

      await waitFor(() => {
        expect(screen.getByText("No Active Resume Found")).toBeDefined();
        expect(screen.getByText(/you must have an uploaded and activated resume in your profile/i)).toBeDefined();
      });

      // Verify analysis button is disabled
      const analyzeBtn = screen.getByRole("button", { name: /analyze resume against job/i });
      expect(analyzeBtn.hasAttribute("disabled")).toBe(true);
    });

    it("displays deterministic analysis engine badge when deterministic provider is returned", async () => {
      global.fetch = vi.fn().mockImplementation((url: string, options?: RequestInit) => {
        const urlStr = url.toString();
        const method = options?.method || "GET";

        if (urlStr.includes("/api/v1/opportunities")) {
          return Promise.resolve({
            ok: true,
            status: 200,
            json: async () => ({ items: [mockOpportunity], total: 1 }),
          });
        }

        if (urlStr.includes("/resume-recommendations/context")) {
          return Promise.resolve({
            ok: true,
            status: 200,
            json: async () => ({
              opportunity_id: "opp-copilot-1",
              opportunity_title: "Cloud Infrastructure Engineer",
              company_name: "CloudTech Inc",
              opportunity_type: "Full-Time",
              work_model: "Remote",
              locations: ["Seattle, WA"],
              has_description: true,
              description_char_count: 500,
              skills_required: ["AWS", "Terraform"],
              active_resume: {
                resume_id: "res-1",
                original_filename: "candidate_resume.pdf",
                file_size: 1048576,
                file_type: "application/pdf",
                has_parsed_text: true,
                has_structured_data: true,
                has_analysis: true,
                completeness_score: 90,
                score_label: "High Quality",
                uploaded_at: "2026-03-01T00:00:00Z",
              },
              is_ready_for_analysis: true,
              readiness_notes: [],
            }),
          });
        }

        if (urlStr.includes("/resume-recommendations/analyze") && method === "POST") {
          return Promise.resolve({
            ok: true,
            status: 200,
            json: async () => ({
              opportunity_id: "opp-copilot-1",
              opportunity_title: "Cloud Infrastructure Engineer",
              company_name: "CloudTech Inc",
              resume_id: "res-1",
              resume_filename: "candidate_resume.pdf",
              resume_completeness_score: 90,
              resume_completeness_label: "High Quality",
              data_sufficiency: {
                has_active_resume: true,
                has_resume_text: true,
                has_job_description: true,
                has_job_skills: true,
                status: "sufficient",
                details: [],
              },
              strengths: [
                {
                  category: "skill",
                  title: "AWS Cloud Infrastructure",
                  source: "resume",
                  evidence: "Managed EC2 clusters and VPC peering in AWS",
                  relevance_explanation: "Directly matches CloudTech infrastructure requirements",
                },
              ],
              gaps: [
                {
                  skill_name: "Terraform",
                  requirement_level: "required",
                  gap_type: "missing_requirement",
                  explanation: "Terraform is required for infrastructure automation.",
                  student_guidance: "Highlight any infrastructure as code or configuration scripts.",
                },
              ],
              improvements: [],
              ats_guidance: [],
              disclaimers: ["Grounded report"],
              provider: "deterministic",
              provider_model: null,
              created_at: new Date().toISOString(),
            }),
          });
        }

        return Promise.resolve({ ok: true, status: 200, json: async () => ({}) });
      });

      render(<JobResumeRecommendations />);

      // Wait for active resume to load
      await waitFor(() => {
        expect(screen.getByText("Active Resume Ready")).toBeDefined();
        expect(screen.getByText("candidate_resume.pdf")).toBeDefined();
      });

      // Click analyze button
      const analyzeBtn = screen.getByRole("button", { name: /analyze resume against job/i });
      expect(analyzeBtn.hasAttribute("disabled")).toBe(false);
      await user.click(analyzeBtn);

      await waitFor(() => {
        expect(screen.getByText(/Deterministic Engine/i)).toBeDefined();
        expect(screen.getByText(/Data Completeness & Sufficiency/i)).toBeDefined();
        expect(screen.getByText(/Executive Recommendation Summary/i)).toBeDefined();
      });
    });
  });
});
