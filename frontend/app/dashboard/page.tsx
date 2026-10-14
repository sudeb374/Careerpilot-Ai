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
            <Link href="/matches" className="w-full">
              <Button className="w-full bg-[#1B5E3B] text-white hover:bg-[#2E7D4F]">
                Your Matches
              </Button>
            </Link>
            <Link href="/applications" className="w-full">
              <Button className="w-full bg-[#14261C] text-white hover:bg-[#203a2b] font-semibold flex items-center justify-center gap-2">
                Application Tracker
              </Button>
            </Link>
            <Link href="/roadmap" className="w-full">
              <Button className="w-full bg-[#1B5E3B]/15 text-[#1B5E3B] border border-[#1B5E3B]/30 hover:bg-[#1B5E3B]/25 font-semibold">
                Skill-Gap Roadmap
              </Button>
            </Link>
            <Link href="/cover-letter" className="w-full">
              <Button className="w-full bg-[#1B5E3B]/15 text-[#1B5E3B] border border-[#1B5E3B]/30 hover:bg-[#1B5E3B]/25 font-semibold">
                Cover Letter Generator
              </Button>
            </Link>
            <Link href="/application-assistant" className="w-full">
              <Button className="w-full bg-[#1B5E3B]/15 text-[#1B5E3B] border border-[#1B5E3B]/30 hover:bg-[#1B5E3B]/25 font-semibold">
                Application Question Assistant
              </Button>
            </Link>
            <Link href="/interview-prep" className="w-full">
              <Button className="w-full bg-[#1B5E3B]/15 text-[#1B5E3B] border border-[#1B5E3B]/30 hover:bg-[#1B5E3B]/25 font-semibold">
                Interview Preparation Practice
              </Button>
            </Link>
            <Link href="/resume-recommendations" className="w-full">
              <Button className="w-full bg-[#1B5E3B]/15 text-[#1B5E3B] border border-[#1B5E3B]/30 hover:bg-[#1B5E3B]/25 font-semibold">
                Job-Specific Resume Recommendations
              </Button>
            </Link>
            <Link href="/opportunities" className="w-full">
              <Button className="w-full bg-[#1B5E3B]/10 text-[#1B5E3B] hover:bg-[#1B5E3B]/20">
                Discover Opportunities
              </Button>
            </Link>
            <Link href="/saved-opportunities" className="w-full">
              <Button className="w-full bg-white text-[#1B5E3B] border border-[#1B5E3B] hover:bg-[#F6FAF7]">
                Saved Opportunities
              </Button>
            </Link>
            <Link href="/profile" className="w-full">
              <Button className="w-full" variant="outline">
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
