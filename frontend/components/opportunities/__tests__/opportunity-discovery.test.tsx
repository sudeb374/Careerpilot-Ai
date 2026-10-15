import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent, act } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { OpportunityDiscovery } from "../opportunity-discovery";

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
  usePathname: () => "/opportunities",
}));

let mockSession: { access_token: string; user: { id: string } } | null = {
  access_token: "mock-opp-token",
  user: { id: "user-opp-1" },
};

vi.mock("@/lib/supabase/client", () => ({
  createClient: () => ({
    auth: {
      getSession: vi.fn().mockImplementation(() =>
        Promise.resolve({
          data: { session: mockSession },
        })
      ),
    },
  }),
}));

const sampleOpportunities = [
  {
    id: "opp-101",
    title: "Senior Frontend Engineer",
    company_name: "Stripe",
    company_logo_url: null,
    opportunity_type: "Full-Time",
    work_model: "Remote",
    locations: ["Remote - US"],
    domain: "Fintech",
    skills: [{ id: "sk-1", name: "React" }, { id: "sk-2", name: "TypeScript" }],
    deadline: "2026-05-01T00:00:00Z",
  },
  {
    id: "opp-102",
    title: "Machine Learning Intern",
    company_name: "DeepMind",
    company_logo_url: null,
    opportunity_type: "Internship",
    work_model: "On-Site",
    locations: ["London, UK"],
    domain: "AI Research",
    skills: [{ id: "sk-3", name: "Python" }, { id: "sk-4", name: "PyTorch" }],
    deadline: null,
  },
];

describe("OpportunityDiscovery Component", () => {
  let user: ReturnType<typeof userEvent.setup>;

  beforeEach(() => {
    user = userEvent.setup();
    vi.clearAllMocks();
    mockSession = { access_token: "mock-opp-token", user: { id: "user-opp-1" } };
    mockSearchParams = new URLSearchParams();
  });

  function setupFetch(options?: {
    ok?: boolean;
    status?: number;
    items?: unknown[];
    total?: number;
    totalPages?: number;
  }) {
    const isOk = options?.ok ?? true;
    const statusCode = options?.status ?? (isOk ? 200 : 500);
    const items = options?.items ?? sampleOpportunities;
    const total = options?.total ?? items.length;
    const totalPages = options?.totalPages ?? 1;

    const fetchMock = vi.fn().mockImplementation((url: string) => {
      const urlStr = url.toString();

      if (urlStr.includes("/saved")) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => ({ saved: false }),
        });
      }

      if (urlStr.includes("/api/v1/applications")) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => ({ is_tracked: false, application: null }),
        });
      }

      if (urlStr.includes("/api/v1/skills/search")) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => [],
        });
      }

      if (urlStr.includes("/api/v1/opportunities")) {
        return Promise.resolve({
          ok: isOk,
          status: statusCode,
          json: async () => ({
            items,
            total,
            total_pages: totalPages,
            page: 1,
            page_size: 10,
          }),
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

  it("renders loading skeletons initially, then displays opportunity cards", async () => {
    setupFetch();
    const { container } = render(<OpportunityDiscovery />);

    // Initially pulse skeleton elements are rendered
    expect(container.querySelectorAll(".animate-pulse").length).toBeGreaterThan(0);

    // After loading completes
    await waitFor(() => {
      expect(screen.getByText("Senior Frontend Engineer")).toBeDefined();
      expect(screen.getByText("Machine Learning Intern")).toBeDefined();
    });

    // Check count overview text
    expect(screen.getByText(/showing 1–2 of 2 opportunities/i)).toBeDefined();
  });

  it("redirects to /login when unauthenticated", async () => {
    mockSession = null;
    setupFetch();
    render(<OpportunityDiscovery />);

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith("/login");
    });
  });

  it("displays error state and retries on button click", async () => {
    setupFetch({ ok: false, status: 500 });
    render(<OpportunityDiscovery />);

    await waitFor(() => {
      expect(screen.getByText("Unable to load opportunities")).toBeDefined();
      expect(screen.getByText("Please try again.")).toBeDefined();
    });

    // Reset fetch to succeed on retry
    setupFetch({ ok: true });
    const retryBtn = screen.getByRole("button", { name: /retry/i });
    await user.click(retryBtn);

    await waitFor(() => {
      expect(screen.getByText("Senior Frontend Engineer")).toBeDefined();
    });
  });

  it("displays empty state when no opportunities are found and filters are active", async () => {
    mockSearchParams = new URLSearchParams("q=UnicornJob");
    setupFetch({ items: [], total: 0 });

    render(<OpportunityDiscovery />);

    await waitFor(() => {
      expect(screen.getByText("No opportunities found")).toBeDefined();
      expect(screen.getByText("Try changing your search or filters.")).toBeDefined();
    });

    const clearBtns = screen.getAllByRole("button", { name: /clear filters/i });
    expect(clearBtns.length).toBeGreaterThan(0);
    await user.click(clearBtns[0]);

    expect(mockReplace).toHaveBeenCalledWith("/opportunities?", { scroll: false });
  });

  it("displays empty state when no opportunities exist and no filters are active", async () => {
    setupFetch({ items: [], total: 0 });

    render(<OpportunityDiscovery />);

    await waitFor(() => {
      expect(screen.getByText("No opportunities available yet")).toBeDefined();
      expect(screen.getByText(/new opportunities will appear here as they are published/i)).toBeDefined();
    });
  });

  it("debounces search input by 500ms before syncing URL and triggering fetch", () => {
    vi.useFakeTimers();
    setupFetch();

    render(<OpportunityDiscovery />);

    // Advance past initial load
    act(() => {
      vi.advanceTimersByTime(10);
    });

    const searchInput = screen.getByPlaceholderText(/search roles, companies, skills, or keywords/i);

    // Simulate user typing
    act(() => {
      fireEvent.change(searchInput, { target: { value: "Staff Engineer" } });
    });

    // Immediately after typing, router.replace should NOT have been called yet because of 500ms debounce
    expect(mockReplace).not.toHaveBeenCalled();

    // Advance timers past 500ms
    act(() => {
      vi.advanceTimersByTime(550);
    });

    // router.replace should now have been invoked with safely formatted URL
    expect(mockReplace).toHaveBeenCalledWith(
      expect.stringContaining("q=Staff+Engineer"),
      { scroll: false }
    );

    vi.useRealTimers();
  });

  it("safely serializes and handles query parameters in updateUrl", async () => {
    setupFetch();
    render(<OpportunityDiscovery />);

    await waitFor(() => {
      expect(screen.getByText("Senior Frontend Engineer")).toBeDefined();
    });

    const locationInput = screen.getByPlaceholderText(/location/i);
    await user.type(locationInput, "San Francisco & New York");

    // Wait for 500ms debounce
    await waitFor(
      () => {
        expect(mockReplace).toHaveBeenCalledWith(
          expect.stringContaining("location=San+Francisco+%26+New+York"),
          { scroll: false }
        );
      },
      { timeout: 2000 }
    );
  });
});
