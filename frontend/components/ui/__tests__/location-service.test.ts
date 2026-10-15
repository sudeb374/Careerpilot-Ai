import { describe, it, expect, vi, beforeEach } from "vitest";
import { searchLocations } from "@/lib/locations/location-service";

describe("Location Service", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("matches multiple Kolkata localities like Sector V, Salt Lake, and New Town with PIN codes", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue({
      ok: true,
      json: async () => [],
    } as Response);

    const results = await searchLocations("Kolkata");
    expect(results.length).toBeGreaterThanOrEqual(3);

    const names = results.map((r) => r.name);
    expect(names).toContain("Sector V");
    expect(names).toContain("Salt Lake");
    expect(names).toContain("New Town");

    const sectorV = results.find((r) => r.name === "Sector V");
    expect(sectorV?.pincode).toBe("700091");
    expect(sectorV?.state).toBe("West Bengal");

    const saltLake = results.find((r) => r.name === "Salt Lake");
    expect(saltLake?.pincode).toBe("700091");
    expect(saltLake?.district).toContain("Kolkata");
  });

  it("matches curated Indian tech hubs like Salt Lake", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue({
      ok: true,
      json: async () => [],
    } as Response);

    const results = await searchLocations("Salt Lake");

    expect(results.length).toBeGreaterThan(0);
    const saltLake = results.find((r) => r.displayName.includes("Salt Lake") || r.name.includes("Salt Lake"));
    expect(saltLake).toBeDefined();
    expect(saltLake?.state).toBe("West Bengal");
    expect(saltLake?.pincode).toBe("700091");
  });

  it("matches Pune tech hubs like Hinjawadi from curated list", async () => {
    const results = await searchLocations("Hinjawadi");
    const hinjawadi = results.find((r) => r.displayName.includes("Hinjawadi") || r.name.includes("Hinjawadi"));
    expect(hinjawadi).toBeDefined();
    expect(hinjawadi?.district).toBe("Pune");
    expect(hinjawadi?.state).toBe("Maharashtra");
    expect(hinjawadi?.pincode).toBe("411057");
  });

  it("falls back to postal API when query is not in curated tech hubs", async () => {
    const mockPostalResponse = [
      {
        Status: "Success",
        PostOffice: [
          {
            Name: "Kalyani",
            District: "Nadia",
            State: "West Bengal",
            Pincode: "741235",
          },
        ],
      },
    ];

    vi.spyOn(global, "fetch").mockResolvedValueOnce({
      ok: true,
      json: async () => mockPostalResponse,
    } as Response);

    const results = await searchLocations("Kalyani");
    expect(results.length).toBeGreaterThan(0);
    const kalyani = results.find((r) => r.displayName.includes("Kalyani") || r.name.includes("Kalyani"));
    expect(kalyani).toBeDefined();
    expect(kalyani?.district).toBe("Nadia");
    expect(kalyani?.pincode).toBe("741235");
  });

  it("returns empty suggestions gracefully when query is less than 2 characters", async () => {
    const results = await searchLocations("k");
    expect(results).toEqual([]);
  });

  it("handles provider network errors gracefully without crashing", async () => {
    vi.spyOn(global, "fetch").mockRejectedValue(new Error("Network timeout"));
    const results = await searchLocations("Chandigarh");
    expect(Array.isArray(results)).toBe(true);
  });
});
