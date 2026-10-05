import { Leaf } from "lucide-react";
import Link from "next/link";

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-background p-4 sm:p-8">
      <Link href="/" className="mb-8 flex items-center gap-2">
        <Leaf className="size-6 text-primary" />
        <span className="text-xl font-bold tracking-tight text-foreground">
          CareerPilot<span className="text-primary"> AI</span>
        </span>
      </Link>
      <div className="w-full max-w-md">
        {children}
      </div>
    </div>
  );
}
