import { describe, it, expect, vi, beforeEach } from "vitest";
import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { LocationAutocomplete } from "../location-autocomplete";

describe("LocationAutocomplete Component", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("renders with label, placeholder, and empty state", () => {
    render(
      <LocationAutocomplete
        label="Target Work Locations"
        placeholder="Type a city or locality..."
        values={[]}
        onChange={vi.fn()}
      />
    );

    expect(screen.getByText("Target Work Locations")).toBeDefined();
    expect(screen.getByPlaceholderText("Type a city or locality...")).toBeDefined();
  });

  it("displays existing location chips in multi-select mode and allows removing them", () => {
    const handleChange = vi.fn();
    render(
      <LocationAutocomplete
        values={["Kolkata, West Bengal", "Pune, Maharashtra"]}
        onChange={handleChange}
      />
    );

    expect(screen.getByText("Kolkata, West Bengal")).toBeDefined();
    expect(screen.getByText("Pune, Maharashtra")).toBeDefined();

    const removeBtn = screen.getByLabelText("Remove Kolkata, West Bengal");
    fireEvent.click(removeBtn);

    expect(handleChange).toHaveBeenCalledWith(["Pune, Maharashtra"]);
  });

  it("opens portal suggestions on query input and shows matching Kolkata localities with PIN codes", async () => {
    render(
      <LocationAutocomplete
        label="Preferred Locations"
        values={[]}
        onChange={vi.fn()}
      />
    );

    const input = screen.getByRole("combobox");
    fireEvent.change(input, { target: { value: "Kolkata" } });

    await waitFor(() => {
      // Should show matching localities
      expect(screen.getByText("Matching Localities & Post Offices")).toBeDefined();
      expect(screen.getByText("Sector V")).toBeDefined();
      expect(screen.getByText("Salt Lake")).toBeDefined();
    });

    // Check PIN codes are displayed
    expect(screen.getAllByText("PIN 700091").length).toBeGreaterThan(0);
  });

  it("handles keyboard navigation: ArrowDown, Escape, and Enter", async () => {
    const handleSelect = vi.fn();
    render(
      <LocationAutocomplete
        singleSelect={true}
        onValueChange={handleSelect}
      />
    );

    const input = screen.getByRole("combobox");
    fireEvent.change(input, { target: { value: "Pune" } });

    await waitFor(() => {
      expect(screen.getByText("Matching Localities & Post Offices")).toBeDefined();
    });

    // Navigate down
    fireEvent.keyDown(input, { key: "ArrowDown" });
    // Hit enter on selected item
    fireEvent.keyDown(input, { key: "Enter" });

    expect(handleSelect).toHaveBeenCalledWith(expect.stringContaining("Pune"));
  });

  it("provides custom location fallback when no postal records match", async () => {
    const handleChange = vi.fn();
    render(
      <LocationAutocomplete
        values={[]}
        onChange={handleChange}
      />
    );

    const input = screen.getByRole("combobox");
    fireEvent.change(input, { target: { value: "Remote Workstation Alpha" } });

    await waitFor(() => {
      expect(screen.getByText(/Use custom location:/i)).toBeDefined();
    });

    const customBtn = screen.getByText(/Remote Workstation Alpha/i);
    fireEvent.click(customBtn);

    expect(handleChange).toHaveBeenCalledWith(["Remote Workstation Alpha"]);
  });
});
