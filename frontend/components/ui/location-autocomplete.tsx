"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { createPortal } from "react-dom";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import { Loader2, MapPin, X, Plus, AlertCircle, Building2 } from "lucide-react";
import { searchLocations, type LocationSuggestion } from "@/lib/locations/location-service";

interface LocationAutocompleteProps {
  label?: string;
  placeholder?: string;
  values?: string[];
  onChange?: (locations: string[]) => void;
  value?: string;
  onValueChange?: (location: string) => void;
  singleSelect?: boolean;
  disabled?: boolean;
  maxLocations?: number;
  description?: string;
}

export function LocationAutocomplete({
  label = "Preferred Locations",
  placeholder = "Type a city or locality (e.g., Kolkata, Sector V, Pune, Hinjawadi)...",
  values = [],
  onChange,
  value = "",
  onValueChange,
  singleSelect = false,
  disabled = false,
  maxLocations = 10,
  description,
}: LocationAutocompleteProps) {
  const [query, setQuery] = useState(singleSelect ? value : "");
  const [suggestions, setSuggestions] = useState<LocationSuggestion[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState<number>(-1);
  const [providerError, setProviderError] = useState<string | null>(null);
  const [mounted, setMounted] = useState(false);
  const [dropdownStyle, setDropdownStyle] = useState<React.CSSProperties | null>(null);

  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setMounted(true);
  }, []);

  useEffect(() => {
    if (singleSelect && value !== query) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setQuery(value);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value, singleSelect]);

  // Compute portal position to prevent clipping by overflow-hidden containers, cards, or sticky footers
  const updateDropdownPosition = useCallback(() => {
    if (!inputRef.current) return;
    const rect = inputRef.current.getBoundingClientRect();
    const viewportHeight = window.innerHeight;
    const viewportWidth = window.innerWidth;

    const spaceBelow = viewportHeight - rect.bottom;
    const spaceAbove = rect.top;
    const dropdownHeight = 280;

    // Flip upwards if space below is constrained (< 240px) and there is more headroom above
    const placeAbove = spaceBelow < 240 && spaceAbove > spaceBelow;

    // Width matches the input or stretches safely on mobile
    const targetWidth = Math.max(rect.width, Math.min(360, viewportWidth - 24));
    let left = rect.left;
    if (left + targetWidth > viewportWidth - 12) {
      left = Math.max(12, viewportWidth - 12 - targetWidth);
    }

    if (placeAbove) {
      setDropdownStyle({
        position: "fixed",
        bottom: `${viewportHeight - rect.top + 4}px`,
        left: `${left}px`,
        width: `${targetWidth}px`,
        maxHeight: `${Math.min(spaceAbove - 16, dropdownHeight)}px`,
        zIndex: 99999,
      });
    } else {
      setDropdownStyle({
        position: "fixed",
        top: `${rect.bottom + 4}px`,
        left: `${left}px`,
        width: `${targetWidth}px`,
        maxHeight: `${Math.min(spaceBelow - 16, dropdownHeight)}px`,
        zIndex: 99999,
      });
    }
  }, []);

  useEffect(() => {
    if (!isOpen) return;
    updateDropdownPosition();
    window.addEventListener("scroll", updateDropdownPosition, true);
    window.addEventListener("resize", updateDropdownPosition);
    return () => {
      window.removeEventListener("scroll", updateDropdownPosition, true);
      window.removeEventListener("resize", updateDropdownPosition);
    };
  }, [isOpen, updateDropdownPosition, suggestions]);

  // Close dropdown on outside click
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      const target = e.target as Node;
      if (
        containerRef.current &&
        !containerRef.current.contains(target) &&
        dropdownRef.current &&
        !dropdownRef.current.contains(target)
      ) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Debounced search
  useEffect(() => {
    const trimmed = query.trim();
    if (trimmed.length < 2) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setSuggestions([]);
      setIsLoading(false);
      setProviderError(null);
      return;
    }

    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    const controller = new AbortController();
    abortControllerRef.current = controller;

    setIsLoading(true);
    setProviderError(null);

    const timer = setTimeout(async () => {
      try {
        const results = await searchLocations(trimmed, controller.signal);
        setSuggestions(results);
        setSelectedIndex(results.length > 0 ? 0 : -1);
      } catch (err: unknown) {
        if ((err as Error)?.name !== "AbortError") {
          setProviderError("Locality lookup temporarily slow. You can still add your custom location.");
        }
      } finally {
        setIsLoading(false);
      }
    }, 350);

    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [query]);

  const handleSelectLocation = useCallback(
    (locationString: string) => {
      const clean = locationString.trim();
      if (!clean) return;

      if (singleSelect) {
        onValueChange?.(clean);
        setQuery(clean);
        setIsOpen(false);
        setSuggestions([]);
        return;
      }

      // Multi-select duplicate check
      const exists = values.some((v) => v.toLowerCase() === clean.toLowerCase());
      if (!exists && values.length < maxLocations) {
        onChange?.([...values, clean]);
      }
      setQuery("");
      setSuggestions([]);
      setIsOpen(false);
      setSelectedIndex(-1);
      inputRef.current?.focus();
    },
    [singleSelect, onValueChange, values, maxLocations, onChange]
  );

  const handleRemoveLocation = (locationToRemove: string) => {
    onChange?.(values.filter((v) => v !== locationToRemove));
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!isOpen && (e.key === "ArrowDown" || e.key === "ArrowUp")) {
      setIsOpen(true);
      return;
    }

    if (e.key === "ArrowDown") {
      e.preventDefault();
      const totalOptions = suggestions.length + (query.trim() ? 1 : 0);
      setSelectedIndex((prev) => (prev + 1) % totalOptions);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      const totalOptions = suggestions.length + (query.trim() ? 1 : 0);
      setSelectedIndex((prev) => (prev <= 0 ? totalOptions - 1 : prev - 1));
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (selectedIndex >= 0 && selectedIndex < suggestions.length) {
        handleSelectLocation(suggestions[selectedIndex].value);
      } else if (query.trim()) {
        handleSelectLocation(query.trim());
      }
    } else if (e.key === "Escape") {
      e.preventDefault();
      setIsOpen(false);
    } else if (e.key === "Tab") {
      setIsOpen(false);
    }
  };

  return (
    <div className="space-y-3" ref={containerRef}>
      <div className="flex items-center justify-between">
        <Label className="text-sm font-medium text-foreground">{label}</Label>
        {!singleSelect && (
          <span className="text-xs text-muted-foreground">
            {values.length} of {maxLocations} selected
          </span>
        )}
      </div>

      {description && <p className="text-xs text-muted-foreground">{description}</p>}

      {/* Selected location chips (multi-select mode) */}
      {!singleSelect && values.length > 0 && (
        <div className="flex flex-wrap gap-2 pt-0.5">
          {values.map((loc) => (
            <Badge
              key={loc}
              variant="secondary"
              className="px-2.5 py-1 text-xs font-medium rounded-lg flex items-center gap-1.5 bg-[#EBF3ED] text-[#14261C] border border-primary/20 shadow-2xs"
            >
              <MapPin className="size-3 text-primary shrink-0" />
              <span>{loc}</span>
              {!disabled && (
                <button
                  type="button"
                  onClick={() => handleRemoveLocation(loc)}
                  className="text-muted-foreground hover:text-foreground hover:bg-black/5 rounded-full p-0.5 transition-colors"
                  aria-label={`Remove ${loc}`}
                >
                  <X className="size-3" />
                </button>
              )}
            </Badge>
          ))}
        </div>
      )}

      {/* Autocomplete Input */}
      <div className="relative">
        <div className="relative flex items-center">
          <Input
            ref={inputRef}
            type="text"
            role="combobox"
            aria-expanded={isOpen}
            aria-autocomplete="list"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              if (singleSelect) {
                onValueChange?.(e.target.value);
              }
              setIsOpen(true);
            }}
            onFocus={() => {
              if (query.trim().length >= 2 || suggestions.length > 0) {
                setIsOpen(true);
              }
            }}
            onKeyDown={handleKeyDown}
            placeholder={
              !singleSelect && values.length >= maxLocations
                ? `Maximum ${maxLocations} locations reached`
                : placeholder
            }
            disabled={disabled || (!singleSelect && values.length >= maxLocations)}
            className="pr-10 bg-background"
          />
          <div className="absolute right-3 flex items-center gap-1 text-muted-foreground">
            {isLoading ? (
              <Loader2 className="size-4 animate-spin text-primary" />
            ) : (
              <MapPin className="size-4 opacity-50" />
            )}
          </div>
        </div>

        {/* Portaled Suggestions Dropdown — Immune to overflow-hidden and sticky stacking */}
        {mounted && isOpen && query.trim().length >= 2 && dropdownStyle && createPortal(
          <div
            ref={dropdownRef}
            style={dropdownStyle}
            role="listbox"
            className="rounded-xl border border-border bg-popover p-1.5 shadow-2xl text-popover-foreground overflow-y-auto animate-in fade-in-0 zoom-in-95 duration-100"
          >
            {providerError && (
              <div className="flex items-center gap-2 p-2 text-xs text-amber-700 bg-amber-50 rounded-lg mb-1 border border-amber-200">
                <AlertCircle className="size-3.5 shrink-0" />
                <span>{providerError}</span>
              </div>
            )}

            {/* Official Indian locality results */}
            {suggestions.length > 0 && (
              <div className="space-y-0.5">
                <div className="px-2.5 py-1 text-[11px] font-semibold text-muted-foreground uppercase tracking-wider flex items-center gap-1">
                  <Building2 className="size-3" />
                  Matching Localities & Post Offices
                </div>
                {suggestions.map((item, idx) => {
                  const isSelected = selectedIndex === idx;
                  return (
                    <button
                      key={`${item.displayName}-${idx}`}
                      type="button"
                      role="option"
                      aria-selected={isSelected}
                      onClick={() => handleSelectLocation(item.value)}
                      onMouseEnter={() => setSelectedIndex(idx)}
                      className={`w-full text-left px-3 py-2 rounded-lg text-xs flex flex-col transition-colors ${
                        isSelected
                          ? "bg-primary text-primary-foreground font-medium"
                          : "hover:bg-muted text-foreground"
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-semibold">{item.name}</span>
                        {item.pincode && (
                          <span
                            className={`text-[10px] px-1.5 py-0.5 rounded ${
                              isSelected
                                ? "bg-white/20 text-white"
                                : "bg-muted text-muted-foreground"
                            }`}
                          >
                            PIN {item.pincode}
                          </span>
                        )}
                      </div>
                      <span
                        className={`text-[11px] mt-0.5 ${
                          isSelected
                            ? "text-primary-foreground/80"
                            : "text-muted-foreground"
                        }`}
                      >
                        {item.district && item.district !== item.name
                          ? `${item.district}, `
                          : ""}
                        {item.state}
                      </span>
                    </button>
                  );
                })}
              </div>
            )}

            {/* Custom location fallback */}
            {query.trim().length > 0 && (
              <div
                className={`mt-1 pt-1 ${
                  suggestions.length > 0 ? "border-t border-border" : ""
                }`}
              >
                <button
                  type="button"
                  role="option"
                  aria-selected={selectedIndex === suggestions.length}
                  onClick={() => handleSelectLocation(query.trim())}
                  onMouseEnter={() => setSelectedIndex(suggestions.length)}
                  className={`w-full text-left px-3 py-2 rounded-lg text-xs flex items-center gap-2 transition-colors ${
                    selectedIndex === suggestions.length
                      ? "bg-primary text-primary-foreground font-medium"
                      : "hover:bg-muted text-foreground"
                  }`}
                >
                  <Plus className="size-3.5 text-primary shrink-0" />
                  <span>
                    Use custom location:{" "}
                    <strong className="underline underline-offset-2">
                      &quot;{query.trim()}&quot;
                    </strong>
                  </span>
                </button>
              </div>
            )}

            {suggestions.length === 0 && !isLoading && (
              <div className="p-3 text-center text-xs text-muted-foreground">
                No official postal records found for &quot;{query.trim()}&quot;. Press Enter or click below to save as custom location.
              </div>
            )}
          </div>,
          document.body
        )}
      </div>
    </div>
  );
}
