import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ApplicationTracker } from "../application-tracker";

const mockPush = vi.fn();
const mockReplace = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: mockPush,
    replace: mockReplace,
    prefetch: vi.fn(),
    back: vi.fn(),
  }),
  useSearchParams: () => new URLSearchParams(),
  usePathname: () => "/applications",
}));

vi.mock("@/lib/supabase/client", () => ({
  createClient: () => ({
    auth: {
      getSession: vi.fn().mockResolvedValue({
        data: {
          session: {
            access_token: "mock-access-token",
            user: { id: "test-user-id", email: "candidate@test.com" },
          },
        },
      }),
    },
  }),
}));

const mockApplications = [
  {
    id: "app-1",
    profile_id: "prof-1",
    opportunity_id: "opp-1",
    status: "Applied",
    applied_at: "2026-03-01T10:00:00Z",
    status_updated_at: "2026-03-01T10:00:00Z",
    deadline: "2026-04-01T00:00:00Z",
    reminder_at: "2026-03-10T09:00:00Z",
    reminder_note: "Follow up with recruiter Sarah",
    notes: "Direct application via portal",
    created_at: "2026-03-01T10:00:00Z",
    updated_at: "2026-03-01T10:00:00Z",
    opportunity: {
      id: "opp-1",
      title: "Frontend Engineer",
      company_name: "Acme Labs",
      company_logo_url: null,
      opportunity_type: "Full-Time",
      work_model: "Remote",
      locations: ["San Francisco, CA"],
      application_url: "https://acme.example/jobs/1",
    },
    history: [
      {
        id: "hist-1",
        application_id: "app-1",
        from_status: null,
        to_status: "Applied",
        note: "Initial application submitted",
        created_at: "2026-03-01T10:00:00Z",
      },
    ],
  },
  {
    id: "app-2",
    profile_id: "prof-1",
    opportunity_id: "opp-2",
    status: "Interview",
    applied_at: "2026-02-15T10:00:00Z",
    status_updated_at: "2026-03-02T10:00:00Z",
    deadline: null,
    reminder_at: null,
    reminder_note: null,
    notes: "System design round scheduled",
    created_at: "2026-02-15T10:00:00Z",
    updated_at: "2026-03-02T10:00:00Z",
    opportunity: {
      id: "opp-2",
      title: "Backend Engineer",
      company_name: "Beta Corp",
      company_logo_url: null,
      opportunity_type: "Full-Time",
      work_model: "Hybrid",
      locations: ["New York, NY"],
      application_url: null,
    },
    history: [],
  },
];

const mockAnalytics = {
  total_tracked: 2,
  total_submitted: 2,
  by_status: { Applied: 1, Interview: 1 },
  active_in_progress: 1,
  response_rate_percent: 50,
  interview_rate_percent: 50,
  sample_size_note: "Based on 2 submitted applications",
  upcoming_reminders_count: 0,
  due_reminders_count: 1,
  upcoming_deadlines_count: 1,
};

const mockReminders = {
  due_reminders: [mockApplications[0]],
  upcoming_reminders: [],
  total_due: 1,
  total_upcoming: 0,
};

describe("ApplicationTracker Component", () => {
  let user: ReturnType<typeof userEvent.setup>;

  beforeEach(() => {
    user = userEvent.setup();
    vi.clearAllMocks();
  });

  function setupFetchMock(customResponses?: {
    appsOk?: boolean;
    appsData?: unknown;
    analyticsOk?: boolean;
    analyticsData?: unknown;
    remindersOk?: boolean;
    remindersData?: unknown;
    patchOk?: boolean;
    patchData?: unknown;
    patchStatus?: number;
  }) {
    const appsOk = customResponses?.appsOk ?? true;
    const appsData = customResponses?.appsData ?? { items: mockApplications, total: 2 };
    const analyticsOk = customResponses?.analyticsOk ?? true;
    const analyticsData = customResponses?.analyticsData ?? mockAnalytics;
    const remindersOk = customResponses?.remindersOk ?? true;
    const remindersData = customResponses?.remindersData ?? mockReminders;
    const patchOk = customResponses?.patchOk ?? true;
    const patchStatus = customResponses?.patchStatus ?? (patchOk ? 200 : 500);
    const patchData = customResponses?.patchData ?? (patchOk ? mockApplications[0] : { detail: "Database connection failed during update." });

    const fetchMock = vi.fn().mockImplementation((url: string, options?: RequestInit) => {
      const urlStr = url.toString();
      const method = options?.method || "GET";

      if (urlStr.includes("/api/v1/applications/analytics")) {
        return Promise.resolve({
          ok: analyticsOk,
          status: analyticsOk ? 200 : 500,
          json: async () => analyticsData,
        });
      }

      if (urlStr.includes("/api/v1/applications/reminders")) {
        return Promise.resolve({
          ok: remindersOk,
          status: remindersOk ? 200 : 500,
          json: async () => remindersData,
        });
      }

      if (method === "PATCH") {
        return Promise.resolve({
          ok: patchOk,
          status: patchStatus,
          json: async () => patchData,
        });
      }

      const singleAppMatch = urlStr.match(/\/api\/v1\/applications\/(app-\d+)/);
      if (singleAppMatch && method === "GET") {
        const found = mockApplications.find((a) => a.id === singleAppMatch[1]) || mockApplications[0];
        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => found,
        });
      }

      if (urlStr.includes("/api/v1/applications")) {
        return Promise.resolve({
          ok: appsOk,
          status: appsOk ? 200 : 500,
          json: async () => appsData,
        });
      }

      return Promise.resolve({
        ok: true,
        status: 200,
        json: async () => ({}),
      });
    });

    global.fetch = fetchMock;
    return fetchMock;
  }

  it("renders loading state initially then displays application items and reminder alert", async () => {
    setupFetchMock();
    render(<ApplicationTracker />);

    // Initially loading state is visible
    expect(screen.getByText(/loading your application tracker/i)).toBeDefined();

    // After loading finishes
    await waitFor(() => {
      expect(screen.getByText("Application Tracker")).toBeDefined();
    });

    // Verify applications are rendered
    expect(screen.getByText("Frontend Engineer")).toBeDefined();
    expect(screen.getByText("Backend Engineer")).toBeDefined();
    expect(screen.getByText("Acme Labs")).toBeDefined();
    expect(screen.getByText("Beta Corp")).toBeDefined();

    // Verify reminder alert is shown
    expect(screen.getByText("Personal Reminders & Action Items")).toBeDefined();
    expect(screen.getAllByText(/Follow up with recruiter Sarah/).length).toBeGreaterThan(0);
  });

  it("filters applications by status tabs", async () => {
    setupFetchMock();
    render(<ApplicationTracker />);

    await waitFor(() => {
      expect(screen.getByText("Frontend Engineer")).toBeDefined();
    });

    // Click on "Interview" status tab
    const interviewTab = screen.getByRole("button", { name: /^Interview/i });
    await user.click(interviewTab);

    // Frontend Engineer (Applied) should be hidden, Backend Engineer (Interview) should be visible
    expect(screen.queryByText("Frontend Engineer")).toBeNull();
    expect(screen.getByText("Backend Engineer")).toBeDefined();

    // Click on "Applied" status tab
    const appliedTab = screen.getByRole("button", { name: /^Applied/i });
    await user.click(appliedTab);

    expect(screen.getByText("Frontend Engineer")).toBeDefined();
    expect(screen.queryByText("Backend Engineer")).toBeNull();

    // Click on "All" tab to restore both
    const allTab = screen.getByRole("button", { name: /^All/i });
    await user.click(allTab);

    expect(screen.getByText("Frontend Engineer")).toBeDefined();
    expect(screen.getByText("Backend Engineer")).toBeDefined();
  });

  it("filters applications via search query by company, title, or personal notes", async () => {
    setupFetchMock();
    render(<ApplicationTracker />);

    await waitFor(() => {
      expect(screen.getByText("Frontend Engineer")).toBeDefined();
    });

    const searchInput = screen.getByPlaceholderText(/search by job title, company name, or personal notes/i);

    // Search by title "Backend"
    await user.type(searchInput, "Backend");
    expect(screen.queryByText("Frontend Engineer")).toBeNull();
    expect(screen.getByText("Backend Engineer")).toBeDefined();

    // Clear search
    await user.clear(searchInput);
    expect(screen.getByText("Frontend Engineer")).toBeDefined();
    expect(screen.getByText("Backend Engineer")).toBeDefined();

    // Search by personal notes "System design"
    await user.type(searchInput, "System design");
    expect(screen.queryByText("Frontend Engineer")).toBeNull();
    expect(screen.getByText("Backend Engineer")).toBeDefined();

    // Search query with no match shows empty filter message
    await user.clear(searchInput);
    await user.type(searchInput, "UnknownJobTitleXYZ");
    expect(screen.getByText(/no applications match your filter/i)).toBeDefined();
  });

  it("opens and closes the Manage & History modal interface", async () => {
    setupFetchMock();
    render(<ApplicationTracker />);

    await waitFor(() => {
      expect(screen.getByText("Frontend Engineer")).toBeDefined();
    });

    const manageButtons = screen.getAllByRole("button", { name: /manage & history/i });
    await user.click(manageButtons[0]);

    // Modal should now be open
    await waitFor(() => {
      expect(screen.getByRole("dialog")).toBeDefined();
      expect(screen.getByText("Manage Application")).toBeDefined();
    });

    // Close the modal via Cancel button
    const cancelButton = screen.getByRole("button", { name: /cancel/i });
    await user.click(cancelButton);

    await waitFor(() => {
      expect(screen.queryByRole("dialog")).toBeNull();
    });
  });

  it("edits an application's status and notes and sends PATCH request", async () => {
    const fetchMock = setupFetchMock();
    render(<ApplicationTracker />);

    await waitFor(() => {
      expect(screen.getByText("Frontend Engineer")).toBeDefined();
    });

    const manageButtons = screen.getAllByRole("button", { name: /manage & history/i });
    await user.click(manageButtons[0]);

    await waitFor(() => {
      expect(screen.getByRole("dialog")).toBeDefined();
    });

    // Click "Offer" status in modal
    const modal = screen.getByRole("dialog");
    const offerButton = Array.from(modal.querySelectorAll("button")).find(
      (b) => b.textContent?.trim() === "Offer"
    );
    expect(offerButton).toBeDefined();
    if (offerButton) {
      await user.click(offerButton);
    }

    // Add note
    const notesTextarea = screen.getByPlaceholderText(/record interview thoughts/i);
    await user.clear(notesTextarea);
    await user.type(notesTextarea, "Received verbal offer of $140k");

    // Submit form
    const saveButton = screen.getByRole("button", { name: /save changes/i });
    await user.click(saveButton);

    // Verify PATCH request
    await waitFor(() => {
      const patchCall = fetchMock.mock.calls.find((call) => call[1]?.method === "PATCH");
      expect(patchCall).toBeDefined();
      const body = JSON.parse(patchCall?.[1]?.body as string);
      expect(body.status).toBe("Offer");
      expect(body.notes).toBe("Received verbal offer of $140k");
    });

    // Verify success banner appears
    await waitFor(() => {
      expect(screen.getByText(/application updated to offer successfully/i)).toBeDefined();
    });
  });

  it("updates reminders using PATCH with the correct request payload", async () => {
    const fetchMock = setupFetchMock();
    render(<ApplicationTracker />);

    await waitFor(() => {
      expect(screen.getByText("Frontend Engineer")).toBeDefined();
    });

    const manageButtons = screen.getAllByRole("button", { name: /manage & history/i });
    await user.click(manageButtons[0]);

    await waitFor(() => {
      expect(screen.getByRole("dialog")).toBeDefined();
    });

    // Set reminder note in modal
    const reminderNoteInput = screen.getByPlaceholderText(/follow up with hr/i);
    await user.clear(reminderNoteInput);
    await user.type(reminderNoteInput, "Prepare questions for lead engineer");

    // Submit form
    const saveButton = screen.getByRole("button", { name: /save changes/i });
    await user.click(saveButton);

    await waitFor(() => {
      const patchCall = fetchMock.mock.calls.find((call) => call[1]?.method === "PATCH");
      expect(patchCall).toBeDefined();
      const body = JSON.parse(patchCall?.[1]?.body as string);
      expect(body.reminder_note).toBe("Prepare questions for lead engineer");
    });
  });

  it("clears or dismisses a reminder using PATCH with null reminder fields", async () => {
    const fetchMock = setupFetchMock();
    render(<ApplicationTracker />);

    await waitFor(() => {
      expect(screen.getByText("Personal Reminders & Action Items")).toBeDefined();
    });

    // Find the Dismiss button inside the reminder banner
    const dismissButtons = screen.getAllByRole("button", { name: /dismiss/i });
    expect(dismissButtons.length).toBeGreaterThan(0);
    await user.click(dismissButtons[0]);

    // Verify PATCH request with null reminder fields
    await waitFor(() => {
      const patchCall = fetchMock.mock.calls.find(
        (call) => call[0].toString().includes("/api/v1/applications/app-1") && call[1]?.method === "PATCH"
      );
      expect(patchCall).toBeDefined();
      const body = JSON.parse(patchCall?.[1]?.body as string);
      expect(body.reminder_at).toBeNull();
      expect(body.reminder_note).toBeNull();
      expect(body.status_change_note).toBe("Reminder cleared / dismissed.");
    });

    // Success banner
    await waitFor(() => {
      expect(screen.getByText(/reminder dismissed/i)).toBeDefined();
    });
  });

  it("handles unsuccessful API responses without falsely displaying success", async () => {
    const fetchMock = setupFetchMock({
      patchOk: false,
      patchStatus: 500,
      patchData: { detail: "Database connection failed during update." },
    });

    render(<ApplicationTracker />);

    await waitFor(() => {
      expect(screen.getByText("Frontend Engineer")).toBeDefined();
    });

    const manageButtons = screen.getAllByRole("button", { name: /manage & history/i });
    await user.click(manageButtons[0]);

    await waitFor(() => {
      expect(screen.getByRole("dialog")).toBeDefined();
    });

    // Submit form
    const form = screen.getByRole("dialog").querySelector("form")!;
    fireEvent.submit(form);

    // Verify error banner is displayed
    await waitFor(() => {
      const patchCall = fetchMock.mock.calls.find((call) => call[1]?.method === "PATCH");
      expect(patchCall).toBeDefined();
      expect(screen.getByText(/database connection failed during update/i)).toBeDefined();
    });

    // Ensure success banner is NOT displayed
    expect(screen.queryByText(/updated to .* successfully/i)).toBeNull();
  });

  it("displays empty state when no applications are tracked", async () => {
    setupFetchMock({
      appsData: { items: [], total: 0 },
      analyticsData: {
        total_tracked: 0,
        total_submitted: 0,
        by_status: {},
        active_in_progress: 0,
        response_rate_percent: 0,
        interview_rate_percent: 0,
        sample_size_note: "No applications tracked yet",
        upcoming_reminders_count: 0,
        due_reminders_count: 0,
        upcoming_deadlines_count: 0,
      },
      remindersData: {
        due_reminders: [],
        upcoming_reminders: [],
        total_due: 0,
        total_upcoming: 0,
      },
    });

    render(<ApplicationTracker />);

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: /no applications tracked yet/i })).toBeDefined();
      expect(screen.getByRole("button", { name: /track first application/i })).toBeDefined();
      expect(screen.getByRole("button", { name: /discover opportunities/i })).toBeDefined();
    });
  });

  it("displays error state when initial loading fails", async () => {
    setupFetchMock({ appsOk: false });

    render(<ApplicationTracker />);

    await waitFor(() => {
      expect(screen.getByText(/failed to load tracked applications/i)).toBeDefined();
    });
  });
});
