import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MultiSkillEditor, type ProfileSkill } from "../multi-skill-editor";

vi.mock("@/lib/supabase/client", () => ({
  createClient: () => ({
    auth: {
      getSession: async () => ({
        data: {
          session: { access_token: "fake-jwt-token" },
        },
      }),
    },
  }),
}));

describe("MultiSkillEditor Component", () => {
  let user: ReturnType<typeof userEvent.setup>;

  const initialSkills: ProfileSkill[] = [
    { id: "skill-1", skill_name: "Python", proficiency: "Advanced" },
    { id: "skill-2", skill_name: "PostgreSQL", proficiency: "Intermediate" },
  ];

  beforeEach(() => {
    user = userEvent.setup();
    vi.restoreAllMocks();
  });

  it("renders with initial skills and display elements", async () => {
    render(<MultiSkillEditor initialSkills={initialSkills} />);

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/e\.g\. Python, React, SQL/i)).toBeDefined();
      expect(screen.getByText("Python")).toBeDefined();
      expect(screen.getByText("PostgreSQL")).toBeDefined();
      expect(screen.getByText(/Review Your Skills \(2\)/i)).toBeDefined();
    });
  });

  it("stages a newly entered skill without immediately saving", async () => {
    render(<MultiSkillEditor initialSkills={initialSkills} />);

    const input = await screen.findByPlaceholderText(/e\.g\. Python, React, SQL/i);
    await user.type(input, "React");

    const addButton = screen.getByRole("button", { name: /Add Skill/i });
    await user.click(addButton);

    await waitFor(() => {
      expect(screen.getByText("React")).toBeDefined();
      expect(screen.getByText("New")).toBeDefined();
      expect(screen.getByRole("button", { name: /Save Skills \(3\)/i })).toBeDefined();
    });
  });

  it("prevents adding duplicate skills", async () => {
    render(<MultiSkillEditor initialSkills={initialSkills} />);

    const input = await screen.findByPlaceholderText(/e\.g\. Python, React, SQL/i);
    await user.type(input, "python"); // Case-insensitive duplicate check

    const addButton = screen.getByRole("button", { name: /Add Skill/i });
    await user.click(addButton);

    await waitFor(() => {
      expect(screen.getByText(/"python" is already in your skills list\./i)).toBeDefined();
    });
  });

  it("stages removal of an existing skill", async () => {
    render(<MultiSkillEditor initialSkills={initialSkills} />);

    await waitFor(() => {
      expect(screen.getByText("Python")).toBeDefined();
    });

    const removeButtons = screen.getAllByTitle("Remove skill");
    expect(removeButtons.length).toBe(2);

    await user.click(removeButtons[0]);

    await waitFor(() => {
      expect(screen.getByText("To Remove")).toBeDefined();
      expect(screen.getByRole("button", { name: /Save Skills \(1\)/i })).toBeDefined();
    });
  });

  it("executes batch save when Save Skills is clicked", async () => {
    const onSavedMock = vi.fn();
    const fetchSpy = vi.spyOn(global, "fetch").mockImplementation(async (url, init) => {
      const method = (init as RequestInit)?.method || "GET";
      if (method === "POST") {
        return { ok: true, status: 201, json: async () => ({ id: "skill-3" }) } as Response;
      }
      return {
        ok: true,
        json: async () => [
          ...initialSkills,
          { id: "skill-3", skill_name: "Docker", proficiency: "Beginner" },
        ],
      } as Response;
    });

    render(<MultiSkillEditor initialSkills={initialSkills} onSaved={onSavedMock} />);

    const input = await screen.findByPlaceholderText(/e\.g\. Python, React, SQL/i);
    await user.type(input, "Docker");
    await user.click(screen.getByRole("button", { name: /Add Skill/i }));

    const saveButton = await screen.findByRole("button", { name: /Save Skills \(3\)/i });
    await user.click(saveButton);

    await waitFor(() => {
      expect(fetchSpy).toHaveBeenCalledWith(
        expect.stringContaining("/api/v1/profile/skills"),
        expect.objectContaining({ method: "POST" })
      );
      expect(onSavedMock).toHaveBeenCalled();
    });
  });
});
