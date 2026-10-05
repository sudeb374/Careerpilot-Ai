import { signOut } from "@/app/(auth)/actions";
import { Button } from "@/components/ui/button";
import Link from "next/link";

export default function DashboardPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-background p-4 sm:p-8">
      <div className="w-full max-w-md space-y-8 text-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground">
            Dashboard
          </h1>
          <p className="mt-2 text-muted-foreground">
            (Coming Soon)
          </p>
        </div>
        
        <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
          <p className="mb-6 text-sm text-card-foreground">
            You are successfully logged in. The full student dashboard is currently under construction.
          </p>
          
          <div className="flex flex-col gap-3">
            <Link href="/profile" className="w-full">
              <Button className="w-full bg-primary text-primary-foreground hover:bg-primary/90">
                Manage Profile
              </Button>
            </Link>
            
            <form action={signOut}>
              <Button type="submit" className="w-full" variant="outline">
                Sign Out
              </Button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
