"use client";

import { Suspense, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { resendConfirmationEmail, signup } from "../actions";
import { AlertCircle, CheckCircle2, MailCheck, ArrowRight, RefreshCw, Mail } from "lucide-react";

function RegisterForm() {
  const searchParams = useSearchParams();
  const nextParam = searchParams.get("next") || "";

  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [registeredEmail, setRegisteredEmail] = useState<string | null>(null);
  const [isPending, setIsPending] = useState(false);

  // Resend state
  const [isResending, setIsResending] = useState(false);
  const [resendMessage, setResendMessage] = useState<string | null>(null);
  const [resendError, setResendError] = useState<string | null>(null);
  const [resendCooldown, setResendCooldown] = useState(0);

  // Handle resend countdown
  const handleResend = async () => {
    if (!registeredEmail || resendCooldown > 0 || isResending) return;
    setIsResending(true);
    setResendMessage(null);
    setResendError(null);

    const fd = new FormData();
    fd.append("email", registeredEmail);
    if (nextParam) fd.append("next", nextParam);

    const result = await resendConfirmationEmail(fd);
    setIsResending(false);

    if (result?.error) {
      setResendError(result.error);
    } else {
      setResendMessage("Verification email resent. Please check your inbox.");
      setResendCooldown(60);
      const interval = setInterval(() => {
        setResendCooldown((prev) => {
          if (prev <= 1) {
            clearInterval(interval);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    }
  };

  async function handleSubmit(formData: FormData) {
    setIsPending(true);
    setError(null);
    setSuccess(null);

    const email = (formData.get("email") as string)?.trim();
    const password = formData.get("password") as string;
    const confirmPassword = formData.get("confirmPassword") as string;

    if (password !== confirmPassword) {
      setError("Passwords do not match");
      setIsPending(false);
      return;
    }

    const result = await signup(formData);

    if (result?.error) {
      setError(result.error);
    } else if (result?.success) {
      setSuccess(result.success);
      setRegisteredEmail(result.email || email);
    }

    setIsPending(false);
  }

  // Polished "Check Your Email" Confirmation State
  if (registeredEmail && success) {
    const loginUrl = nextParam ? `/login?next=${encodeURIComponent(nextParam)}` : "/login";

    return (
      <Card className="shadow-lg border-primary/20">
        <CardHeader className="text-center space-y-3 pb-4">
          <div className="mx-auto flex size-14 items-center justify-center rounded-2xl bg-primary/10 text-primary">
            <MailCheck className="size-8" />
          </div>
          <div>
            <CardTitle className="text-2xl font-bold text-foreground">
              Check your email
            </CardTitle>
            <CardDescription className="text-sm mt-1">
              We&apos;ve sent a verification link to activate your student account
            </CardDescription>
          </div>
        </CardHeader>

        <CardContent className="space-y-6">
          {/* Email badge */}
          <div className="rounded-xl border border-primary/20 bg-primary/5 p-4 text-center">
            <span className="text-xs uppercase tracking-wider text-muted-foreground font-semibold">
              Confirmation link sent to
            </span>
            <p className="text-base font-bold text-foreground mt-0.5 break-all">
              {registeredEmail}
            </p>
          </div>

          {/* Verification steps */}
          <div className="space-y-3 text-sm text-muted-foreground">
            <p className="font-semibold text-foreground text-xs uppercase tracking-wide">
              Next steps to complete your setup:
            </p>
            <ol className="space-y-2 list-decimal list-inside text-xs leading-relaxed">
              <li>
                Open your email inbox and look for the verification email from <span className="font-medium text-foreground">CareerPilot AI</span>.
              </li>
              <li>
                Click the confirmation link to verify your email address.
              </li>
              <li>
                Return to sign in, or you will be automatically redirected to your dashboard.
              </li>
            </ol>
            <p className="text-xs text-muted-foreground/80 italic pt-1">
              Tip: If you do not see the email in your inbox within a couple of minutes, please check your Spam or Junk folder.
            </p>
          </div>

          {/* Resend status banners */}
          {resendMessage && (
            <div className="flex items-center gap-2 rounded-md bg-emerald-500/15 p-3 text-xs text-emerald-700 dark:text-emerald-300">
              <CheckCircle2 className="size-4 shrink-0" />
              <span>{resendMessage}</span>
            </div>
          )}

          {resendError && (
            <div className="flex items-center gap-2 rounded-md bg-destructive/15 p-3 text-xs text-destructive">
              <AlertCircle className="size-4 shrink-0" />
              <span>{resendError}</span>
            </div>
          )}
        </CardContent>

        <CardFooter className="flex flex-col gap-3 pt-2">
          <Link href={loginUrl} className="w-full">
            <Button className="w-full bg-primary hover:bg-primary/90 text-primary-foreground gap-2">
              Proceed to Sign In
              <ArrowRight className="size-4" />
            </Button>
          </Link>

          <div className="flex items-center justify-between w-full text-xs text-muted-foreground pt-1">
            <button
              type="button"
              onClick={handleResend}
              disabled={isResending || resendCooldown > 0}
              className="text-primary hover:underline font-medium inline-flex items-center gap-1 disabled:opacity-50 disabled:no-underline"
            >
              {isResending ? (
                <>
                  <RefreshCw className="size-3 animate-spin" />
                  Resending...
                </>
              ) : resendCooldown > 0 ? (
                `Resend link in ${resendCooldown}s`
              ) : (
                <>
                  <Mail className="size-3" />
                  Resend confirmation email
                </>
              )}
            </button>

            <button
              type="button"
              onClick={() => {
                setRegisteredEmail(null);
                setSuccess(null);
                setResendMessage(null);
                setResendError(null);
              }}
              className="hover:underline text-muted-foreground"
            >
              Use a different email
            </button>
          </div>
        </CardFooter>
      </Card>
    );
  }

  return (
    <Card className="shadow-lg">
      <CardHeader className="space-y-1">
        <CardTitle className="text-2xl font-bold">Create an account</CardTitle>
        <CardDescription>
          Enter your details below to create your CareerPilot AI student account
        </CardDescription>
      </CardHeader>
      <form action={handleSubmit}>
        <input type="hidden" name="next" value={nextParam} />
        <CardContent className="space-y-4">
          {error && (
            <div className="flex items-center gap-2 rounded-md bg-destructive/15 p-3 text-sm text-destructive">
              <AlertCircle className="size-4" />
              {error}
            </div>
          )}
          <div className="space-y-2">
            <Label htmlFor="full_name">Full Name</Label>
            <Input
              id="full_name"
              name="full_name"
              type="text"
              placeholder="Jane Doe"
              required
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              name="email"
              type="email"
              placeholder="m.student@university.edu"
              required
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="password">Password</Label>
            <Input id="password" name="password" type="password" required />
          </div>
          <div className="space-y-2">
            <Label htmlFor="confirmPassword">Confirm Password</Label>
            <Input id="confirmPassword" name="confirmPassword" type="password" required />
          </div>
        </CardContent>
        <CardFooter className="flex flex-col gap-4">
          <Button type="submit" className="w-full" disabled={isPending}>
            {isPending ? "Creating student account..." : "Sign up as Student"}
          </Button>
          <div className="text-center text-sm text-muted-foreground">
            Already have an account?{" "}
            <Link
              href={nextParam ? `/login?next=${encodeURIComponent(nextParam)}` : "/login"}
              className="text-primary underline-offset-4 hover:underline"
            >
              Sign in
            </Link>
          </div>
        </CardFooter>
      </form>
    </Card>
  );
}

export default function RegisterPage() {
  return (
    <Suspense
      fallback={
        <Card className="shadow-lg">
          <CardHeader className="space-y-1">
            <CardTitle className="text-2xl font-bold">Create an account</CardTitle>
            <CardDescription>Loading registration form...</CardDescription>
          </CardHeader>
        </Card>
      }
    >
      <RegisterForm />
    </Suspense>
  );
}
