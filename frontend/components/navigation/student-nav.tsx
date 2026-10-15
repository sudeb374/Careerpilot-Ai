"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Leaf,
  LayoutDashboard,
  Sparkles,
  Compass,
  ClipboardCheck,
  User,
  Bookmark,
  Shield,
  LogOut,
  ChevronDown,
  Menu,
  X,
  FileEdit,
  FileCheck,
  BookOpen,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { createClient } from "@/lib/supabase/client";
import { signOut } from "@/app/(auth)/actions";

export function StudentNav() {
  const pathname = usePathname();
  const [isAdmin, setIsAdmin] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [copilotDropdownOpen, setCopilotDropdownOpen] = useState(false);

  useEffect(() => {
    let isMounted = true;
    async function checkRole() {
      try {
        const supabase = createClient();
        const { data: { session } } = await supabase.auth.getSession();
        if (!session) return;

        const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        const res = await fetch(`${API_URL}/api/v1/profile`, {
          headers: { Authorization: `Bearer ${session.access_token}` },
        });
        if (res.ok) {
          const profile = await res.json();
          if (isMounted && profile?.role === "admin") {
            setIsAdmin(true);
          }
        }
      } catch {
        // Non-admin or unauthenticated state
      }
    }
    checkRole();
    return () => {
      isMounted = false;
    };
  }, []);

  const isCopilotActive = [
    "/roadmap",
    "/cover-letter",
    "/application-assistant",
    "/interview-prep",
    "/resume-recommendations",
  ].some((path) => pathname === path || pathname.startsWith(`${path}/`));

  const navLinks = [
    { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
    { href: "/matches", label: "Matches", icon: Sparkles },
    { href: "/opportunities", label: "Opportunities", icon: Compass },
    { href: "/applications", label: "Tracker", icon: ClipboardCheck },
  ];

  const copilotLinks = [
    { href: "/roadmap", label: "Skill-Gap Roadmap", desc: "Prioritized learning sequence", icon: Compass },
    { href: "/cover-letter", label: "Cover Letter Generator", desc: "Targeted evidence-backed letters", icon: FileEdit },
    { href: "/application-assistant", label: "Question Assistant", desc: "AI answers grounded in profile", icon: Sparkles },
    { href: "/interview-prep", label: "Interview Prep", desc: "Database-driven practice lab", icon: BookOpen },
    { href: "/resume-recommendations", label: "Resume Recommendations", desc: "Job-specific bullet tailoring", icon: FileCheck },
  ];

  return (
    <header className="sticky top-0 z-40 w-full border-b border-border bg-card/90 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        {/* Brand */}
        <div className="flex items-center gap-6">
          <Link href="/dashboard" className="flex items-center gap-2">
            <Leaf className="size-6 text-primary" />
            <span className="text-lg font-bold tracking-tight text-foreground">
              CareerPilot<span className="text-primary"> AI</span>
            </span>
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center gap-1 lg:gap-2">
            {navLinks.map((link) => {
              const Icon = link.icon;
              const isActive = pathname === link.href || (link.href !== "/dashboard" && pathname.startsWith(`${link.href}/`));
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                    isActive
                      ? "bg-primary/10 text-primary font-semibold"
                      : "text-muted-foreground hover:text-foreground hover:bg-muted/50"
                  }`}
                >
                  <Icon className="size-4" />
                  {link.label}
                </Link>
              );
            })}

            {/* Career Copilot Dropdown */}
            <div className="relative">
              <button
                type="button"
                onClick={() => setCopilotDropdownOpen(!copilotDropdownOpen)}
                onBlur={() => setTimeout(() => setCopilotDropdownOpen(false), 200)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                  isCopilotActive
                    ? "bg-primary/10 text-primary font-semibold"
                    : "text-muted-foreground hover:text-foreground hover:bg-muted/50"
                }`}
                aria-expanded={copilotDropdownOpen}
              >
                <Sparkles className="size-4 text-primary" />
                <span>Career Copilot</span>
                <ChevronDown className="size-3.5 opacity-70" />
              </button>

              {copilotDropdownOpen && (
                <div className="absolute left-0 mt-2 w-72 rounded-xl border border-border bg-card p-2 shadow-lg z-50">
                  <div className="px-2 py-1.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Copilot Tools
                  </div>
                  {copilotLinks.map((subLink) => {
                    const SubIcon = subLink.icon;
                    const isSubActive = pathname === subLink.href;
                    return (
                      <Link
                        key={subLink.href}
                        href={subLink.href}
                        onClick={() => setCopilotDropdownOpen(false)}
                        className={`flex items-start gap-2.5 p-2 rounded-lg text-xs transition-colors ${
                          isSubActive
                            ? "bg-primary/10 text-primary font-semibold"
                            : "hover:bg-muted text-foreground"
                        }`}
                      >
                        <SubIcon className="size-4 shrink-0 text-primary mt-0.5" />
                        <div>
                          <p className="font-medium text-foreground">{subLink.label}</p>
                          <p className="text-[11px] text-muted-foreground">{subLink.desc}</p>
                        </div>
                      </Link>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Profile Link */}
            <Link
              href="/profile"
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                pathname === "/profile"
                  ? "bg-primary/10 text-primary font-semibold"
                  : "text-muted-foreground hover:text-foreground hover:bg-muted/50"
              }`}
            >
              <User className="size-4" />
              Profile
            </Link>
          </nav>
        </div>

        {/* Right actions */}
        <div className="hidden md:flex items-center gap-2.5">
          {/* Saved Opportunities */}
          <Link href="/saved-opportunities" title="Saved Opportunities">
            <Button
              variant="ghost"
              size="sm"
              className={`gap-1.5 ${
                pathname === "/saved-opportunities"
                  ? "bg-primary/10 text-primary"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <Bookmark className="size-4 text-primary" />
              <span className="text-xs">Saved</span>
            </Button>
          </Link>

          {/* Admin link (Only rendered if verified role is admin) */}
          {isAdmin && (
            <Link href="/admin/opportunities">
              <Button
                variant="outline"
                size="sm"
                className="gap-1.5 border-primary/30 text-primary hover:bg-primary/10"
              >
                <Shield className="size-3.5 text-primary" />
                <span className="text-xs font-semibold">Admin Portal</span>
              </Button>
            </Link>
          )}

          {/* Sign Out */}
          <form action={signOut}>
            <Button
              type="submit"
              variant="ghost"
              size="sm"
              className="text-xs text-muted-foreground hover:text-destructive hover:bg-destructive/10 gap-1.5"
            >
              <LogOut className="size-3.5" />
              <span>Sign Out</span>
            </Button>
          </form>
        </div>

        {/* Mobile menu button */}
        <div className="flex md:hidden items-center gap-2">
          {isAdmin && (
            <Link href="/admin/opportunities">
              <span className="text-xs font-semibold px-2 py-0.5 rounded-md bg-primary/15 text-primary">
                Admin
              </span>
            </Link>
          )}
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            aria-label="Toggle menu"
          >
            {mobileMenuOpen ? <X className="size-5" /> : <Menu className="size-5" />}
          </Button>
        </div>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="border-b border-border bg-card px-4 py-4 md:hidden space-y-3">
          <div className="space-y-1">
            {navLinks.map((link) => {
              const Icon = link.icon;
              const isActive = pathname === link.href;
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  onClick={() => setMobileMenuOpen(false)}
                  className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm ${
                    isActive
                      ? "bg-primary/10 text-primary font-semibold"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  <Icon className="size-4" />
                  {link.label}
                </Link>
              );
            })}

            <Link
              href="/profile"
              onClick={() => setMobileMenuOpen(false)}
              className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm ${
                pathname === "/profile"
                  ? "bg-primary/10 text-primary font-semibold"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <User className="size-4" />
              Profile
            </Link>

            <Link
              href="/saved-opportunities"
              onClick={() => setMobileMenuOpen(false)}
              className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm ${
                pathname === "/saved-opportunities"
                  ? "bg-primary/10 text-primary font-semibold"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <Bookmark className="size-4 text-primary" />
              Saved Opportunities
            </Link>
          </div>

          <div className="pt-2 border-t border-border">
            <p className="px-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
              Career Copilot
            </p>
            <div className="space-y-1">
              {copilotLinks.map((subLink) => (
                <Link
                  key={subLink.href}
                  href={subLink.href}
                  onClick={() => setMobileMenuOpen(false)}
                  className="block px-3 py-1.5 text-xs text-muted-foreground hover:text-foreground"
                >
                  {subLink.label}
                </Link>
              ))}
            </div>
          </div>

          <div className="pt-2 border-t border-border flex items-center justify-between">
            {isAdmin && (
              <Link
                href="/admin/opportunities"
                onClick={() => setMobileMenuOpen(false)}
                className="text-xs font-semibold text-primary hover:underline"
              >
                Go to Admin Portal →
              </Link>
            )}
            <form action={signOut} className="w-full sm:w-auto">
              <Button type="submit" variant="outline" size="sm" className="w-full text-xs">
                <LogOut className="size-3.5 mr-1" />
                Sign Out
              </Button>
            </form>
          </div>
        </div>
      )}
    </header>
  );
}
