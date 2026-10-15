import { describe, it, expect, vi, beforeEach } from "vitest";
import { getProfileStatus } from "../profile-status";
import type { User } from "@supabase/supabase-js";

describe("getProfileStatus helper", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  const mockUser: User = {
    id: "usr-123",
    email: "student@example.com",
    user_metadata: { full_name: "Test Student" },
    app_metadata: {},
    aud: "authenticated",
    created_at: new Date().toISOString(),
  };

  it("identifies a new student account when profile endpoint returns 404", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue({
      status: 404,
      ok: false,
    } as Response);

    const status = await getProfileStatus(mockUser, "token-123", "http://localhost:8000");

    expect(status.isConfigured).toBe(false);
    expect(status.isNewUser).toBe(true);
    expect(status.hasBasicInfo).toBe(false);
  });

  it("identifies an empty/unconfigured profile shell without substantive career records as incomplete", async () => {
    // 1. GET /api/v1/profile -> returns 200 with basic row but no headline/location
    // 2. GET /api/v1/profile/education -> []
    // 3. GET /api/v1/profile/skills -> []
    // 4. GET /api/v1/profile/preferences -> null
    // 5. GET /api/v1/profile/resumes -> []
    vi.spyOn(global, "fetch").mockImplementation(async (url) => {
      const u = String(url);
      if (u.endsWith("/api/v1/profile")) {
        return {
          ok: true,
          status: 200,
          json: async () => ({ full_name: "Test Student", role: "student" }),
        } as Response;
      }
      return {
        ok: true,
        status: 200,
        json: async () => [],
      } as Response;
    });

    const status = await getProfileStatus(mockUser, "token-123", "http://localhost:8000");

    expect(status.isConfigured).toBe(false);
    expect(status.isNewUser).toBe(false);
  });

  it("classifies an account with basic info and education/skills as configured", async () => {
    vi.spyOn(global, "fetch").mockImplementation(async (url) => {
      const u = String(url);
      if (u.endsWith("/api/v1/profile")) {
        return {
          ok: true,
          status: 200,
          json: async () => ({
            full_name: "Priyanshu Sharma",
            headline: "Frontend Engineer",
            location: "Kolkata, West Bengal",
            role: "student",
          }),
        } as Response;
      }
      if (u.endsWith("/api/v1/profile/education")) {
        return {
          ok: true,
          status: 200,
          json: async () => [
            { id: "edu-1", institution: "IIT", degree: "B.Tech" },
          ],
        } as Response;
      }
      return {
        ok: true,
        status: 200,
        json: async () => [],
      } as Response;
    });

    const status = await getProfileStatus(mockUser, "token-123", "http://localhost:8000");

    expect(status.isConfigured).toBe(true);
    expect(status.hasBasicInfo).toBe(true);
    expect(status.hasEducation).toBe(true);
  });

  it("honors server-backed profile_setup_completed user metadata flag", async () => {
    const completedUser: User = {
      ...mockUser,
      user_metadata: { full_name: "Completed Student", profile_setup_completed: true },
    };

    vi.spyOn(global, "fetch").mockImplementation(async (url) => {
      const u = String(url);
      if (u.endsWith("/api/v1/profile")) {
        return {
          ok: true,
          status: 200,
          json: async () => ({ full_name: "Completed Student", role: "student" }),
        } as Response;
      }
      return {
        ok: true,
        status: 200,
        json: async () => [],
      } as Response;
    });

    const status = await getProfileStatus(completedUser, "token-123", "http://localhost:8000");

    expect(status.isConfigured).toBe(true);
  });

  it("never forces administrator accounts into student onboarding", async () => {
    vi.spyOn(global, "fetch").mockImplementation(async (url) => {
      const u = String(url);
      if (u.endsWith("/api/v1/profile")) {
        return {
          ok: true,
          status: 200,
          json: async () => ({ full_name: "Admin User", role: "admin" }),
        } as Response;
      }
      return {
        ok: true,
        status: 200,
        json: async () => [],
      } as Response;
    });

    const status = await getProfileStatus(mockUser, "token-123", "http://localhost:8000");

    expect(status.isConfigured).toBe(true);
    expect(status.role).toBe("admin");
  });
});
