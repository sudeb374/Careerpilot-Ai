import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ProfileSetupWizard } from "../wizard/profile-setup-wizard";

const mockPush = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: mockPush,
  }),
}));

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

describe("ProfileSetupWizard Component", () => {
  let user: ReturnType<typeof userEvent.setup>;

  beforeEach(() => {
    user = userEvent.setup();
    vi.restoreAllMocks();
    window.scrollTo = vi.fn();

    global.fetch = vi.fn().mockImplementation(async (url: string) => {
      if (url.includes("/api/v1/profile")) {
        return {
          ok: true,
          status: 200,
          json: async () => ({
            full_name: "Rahul Verma",
            headline: "Software Engineer",
            location: "Kolkata, West Bengal",
          }),
        } as Response;
      }
      return { ok: true, status: 200, json: async () => [] } as Response;
    });
  });

  it("renders the 6 visual groups and initial step indicator", async () => {
    render(<ProfileSetupWizard />);

    await waitFor(() => {
      expect(screen.getByText("9 Steps • 6 Visual Sections")).toBeDefined();
      expect(screen.getByText("Profile Identity")).toBeDefined();
      expect(screen.getByText("Education")).toBeDefined();
      expect(screen.getByText("Skills")).toBeDefined();
      expect(screen.getByText("Experience & Portfolio")).toBeDefined();
      expect(screen.getByText("Career Direction")).toBeDefined();
      expect(screen.getByText("Application Materials")).toBeDefined();
    });

    expect(screen.getByText("Basic Information")).toBeDefined();
  });

  it("loads existing candidate name into basic information step", async () => {
    render(<ProfileSetupWizard />);

    const nameInput = (await screen.findByLabelText(/Full Name/i)) as HTMLInputElement;
    await waitFor(() => {
      expect(nameInput.value).toBe("Rahul Verma");
    });
  });

  it("validates required Full Name field when advancing", async () => {
    render(<ProfileSetupWizard />);

    const nameInput = await screen.findByLabelText(/Full Name/i);
    await user.clear(nameInput);

    const nextButton = screen.getByRole("button", { name: /Save & Continue/i });
    await user.click(nextButton);

    await waitFor(() => {
      expect(screen.getByText(/Full Name is required\./i)).toBeDefined();
    });
  });

  it("advances to Step 2 (About) when Full Name is valid", async () => {
    render(<ProfileSetupWizard />);

    const nextButton = await screen.findByRole("button", { name: /Save & Continue/i });
    await user.click(nextButton);

    await waitFor(() => {
      expect(screen.getByText("About")).toBeDefined();
      expect(screen.getByLabelText(/Personal Bio \/ Summary/i)).toBeDefined();
    });
  });
});
