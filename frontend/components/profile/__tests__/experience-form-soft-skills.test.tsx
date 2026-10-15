import { describe, it, expect, vi, beforeEach } from "vitest";
import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { ExperienceForm, COMMON_SOFT_SKILLS } from "../experience-form";

// Mock Supabase
vi.mock("@/lib/supabase/client", () => ({
  createClient: () => ({
    auth: {
      getSession: vi.fn().mockResolvedValue({
        data: { session: { access_token: "mock-token" } },
      }),
    },
  }),
}));

describe("ExperienceForm Soft Skills & Inline Skill Addition", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("exposes common soft skills including Communication, Leadership, and Problem Solving", () => {
    expect(COMMON_SOFT_SKILLS).toContain("Communication");
    expect(COMMON_SOFT_SKILLS).toContain("Leadership");
    expect(COMMON_SOFT_SKILLS).toContain("Teamwork");
    expect(COMMON_SOFT_SKILLS).toContain("Problem Solving");
    expect(COMMON_SOFT_SKILLS).toContain("Critical Thinking");
    expect(COMMON_SOFT_SKILLS).toContain("Adaptability");
    expect(COMMON_SOFT_SKILLS).toContain("Time Management");
    expect(COMMON_SOFT_SKILLS).toContain("Presentation");
  });

  it("renders quick attach soft skill chips in the form", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue({
      ok: true,
      json: async () => [],
    } as Response);

    render(
      <ExperienceForm
        onSave={vi.fn()}
        onCancel={vi.fn()}
        isSaving={false}
        error={null}
      />
    );

    // Wait for skills loading to settle
    await waitFor(() => {
      expect(screen.queryByText("Loading skills...")).toBeNull();
    });

    expect(screen.getByText("Quick attach soft & collaborative skills:")).toBeDefined();
    expect(screen.getByText("Communication")).toBeDefined();
    expect(screen.getByText("Leadership")).toBeDefined();
    expect(screen.getByText("Problem Solving")).toBeDefined();
  });

  it("preserves unsaved experience fields while adding a soft skill inline", async () => {
    const existingSkills = [
      { id: "sk-1", skill_name: "Python", proficiency: "Advanced" },
    ];

    vi.spyOn(global, "fetch").mockImplementation(async (url, init) => {
      const u = String(url);
      const method = init?.method || "GET";

      if (u.endsWith("/api/v1/profile/skills") && method === "GET") {
        return {
          ok: true,
          json: async () => existingSkills,
        } as Response;
      }

      if (u.endsWith("/api/v1/profile/skills") && method === "POST") {
        const body = JSON.parse(String(init?.body || "{}"));
        return {
          ok: true,
          json: async () => ({
            id: "sk-2",
            skill_name: body.skill_name,
            proficiency: body.proficiency || "Intermediate",
          }),
        } as Response;
      }

      return {
        ok: true,
        json: async () => [],
      } as Response;
    });

    render(
      <ExperienceForm
        onSave={vi.fn()}
        onCancel={vi.fn()}
        isSaving={false}
        error={null}
      />
    );

    await waitFor(() => {
      expect(screen.queryByText("Loading skills...")).toBeNull();
    });

    // 1. Fill in experience fields
    const titleInput = screen.getByLabelText(/Job Title/i) as HTMLInputElement;
    const companyInput = screen.getByLabelText(/Company/i) as HTMLInputElement;
    const descInput = screen.getByLabelText(/Description/i) as HTMLTextAreaElement;

    fireEvent.change(titleInput, { target: { value: "Lead Engineer Intern" } });
    fireEvent.change(companyInput, { target: { value: "Tech Ventures Kolkata" } });
    fireEvent.change(descInput, { target: { value: "Led 5 engineers building scalable backend services." } });

    expect(titleInput.value).toBe("Lead Engineer Intern");
    expect(companyInput.value).toBe("Tech Ventures Kolkata");
    expect(descInput.value).toBe("Led 5 engineers building scalable backend services.");

    // 2. Click quick soft skill button: "Leadership"
    const leadershipBtn = screen.getByText("Leadership");
    fireEvent.click(leadershipBtn);

    // 3. Verify POST /api/v1/profile/skills was called with Leadership
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining("/api/v1/profile/skills"),
        expect.objectContaining({
          method: "POST",
          body: JSON.stringify({ skill_name: "Leadership", proficiency: "Intermediate" }),
        })
      );
    });

    // 4. Verify unsaved experience fields are completely preserved
    expect(titleInput.value).toBe("Lead Engineer Intern");
    expect(companyInput.value).toBe("Tech Ventures Kolkata");
    expect(descInput.value).toBe("Led 5 engineers building scalable backend services.");
  });
});
