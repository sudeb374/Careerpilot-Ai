import { createClient } from "@/lib/supabase/server";
import { redirect } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";

export default async function AdminLayout({ children }: { children: React.ReactNode }) {
  const supabase = await createClient();

  // Validate authenticated identity using verified auth server user check
  const {
    data: { user },
    error: authError,
  } = await supabase.auth.getUser();

  if (authError || !user) {
    redirect("/login?next=/admin/opportunities");
  }

  // Obtain access token for backend profile verification
  const {
    data: { session },
  } = await supabase.auth.getSession();

  if (!session?.access_token) {
    redirect("/login?next=/admin/opportunities");
  }

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  let profile: { role?: string } | null = null;

  try {
    const res = await fetch(`${API_URL}/api/v1/profile`, {
      headers: { Authorization: `Bearer ${session.access_token}` },
      cache: "no-store",
    });

    if (res.ok) {
      profile = await res.json();
    }
  } catch {
    // If backend profile verification fails or network is unavailable, fail closed
    profile = null;
  }

  // Strictly enforce admin role verification before rendering any admin shells
  if (!profile || profile.role !== "admin") {
    redirect("/dashboard?error=unauthorized");
  }

  return (
    <div className="flex min-h-screen flex-col bg-background">
      <nav className="border-b border-border bg-card px-6 py-4 flex items-center justify-between shadow-sm">
        <div className="flex items-center gap-6">
          <Link href="/admin/opportunities" className="flex items-center gap-2">
            <span className="text-lg font-bold tracking-tight text-primary">
              CareerPilot <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-primary/10 text-primary">Admin</span>
            </span>
          </Link>
          <div className="hidden md:flex items-center gap-4">
            <Link href="/admin/opportunities" className="text-sm font-medium text-muted-foreground hover:text-primary transition-colors">
              Opportunities
            </Link>
            <Link href="/admin/ingestion" className="text-sm font-medium text-muted-foreground hover:text-primary transition-colors">
              Job Ingestion
            </Link>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <Link href="/dashboard">
            <Button variant="outline" size="sm">Exit Admin</Button>
          </Link>
        </div>
      </nav>
      <main className="flex-1 overflow-auto">
        {children}
      </main>
    </div>
  );
}
