import { createClient } from "@/lib/supabase/server";
import { redirect } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";

export default async function AdminLayout({ children }: { children: React.ReactNode }) {
  const supabase = await createClient();
  const { data: { session } } = await supabase.auth.getSession();
  
  if (!session) {
    redirect("/login");
  }

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  const res = await fetch(`${API_URL}/api/v1/profile`, {
    headers: { Authorization: `Bearer ${session.access_token}` },
    cache: "no-store",
  });

  if (!res.ok) {
    redirect("/dashboard");
  }

  const profile = await res.json();
  if (profile.role !== "admin") {
    redirect("/dashboard");
  }

  return (
    <div className="flex min-h-screen flex-col bg-background">
      <nav className="border-b border-border bg-card px-6 py-4 flex items-center justify-between shadow-sm">
        <div className="flex items-center gap-6">
          <h1 className="text-xl font-bold tracking-tight text-primary">CareerPilot Admin</h1>
          <div className="hidden md:flex items-center gap-4">
            <Link href="/admin/opportunities" className="text-sm font-medium text-foreground hover:text-primary">
              Opportunities
            </Link>
            <Link href="/admin/ingestion" className="text-sm font-medium text-foreground hover:text-primary">
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
