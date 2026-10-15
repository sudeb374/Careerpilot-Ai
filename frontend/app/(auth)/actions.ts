"use server";

import { createClient } from "@/lib/supabase/server";
import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { sanitizeRedirectUrl } from "@/lib/auth/redirects";

export async function login(formData: FormData) {
  const supabase = await createClient();

  const data = {
    email: formData.get("email") as string,
    password: formData.get("password") as string,
  };

  const rawNext = formData.get("next") as string | null;
  const nextDestination = sanitizeRedirectUrl(rawNext, "/dashboard");

  try {
    const { error } = await supabase.auth.signInWithPassword(data);

    if (error) {
      return { error: error.message };
    }
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : "An unexpected error occurred during sign in.";
    return { error: message };
  }

  revalidatePath("/", "layout");
  redirect(nextDestination);
}

export async function signup(formData: FormData) {
  const supabase = await createClient();

  // URL to redirect to after email confirmation
  const origin = process.env.NEXT_PUBLIC_API_URL || "http://localhost:3000";

  const data = {
    email: formData.get("email") as string,
    password: formData.get("password") as string,
    options: {
      emailRedirectTo: `${origin}/auth/callback`,
      data: {
        full_name: formData.get("full_name") as string,
      }
    },
  };

  try {
    const { error } = await supabase.auth.signUp(data);

    if (error) {
      return { error: error.message };
    }
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : "An unexpected error occurred during sign up.";
    return { error: message };
  }

  return { success: "Check your email to continue sign in process" };
}

export async function signOut() {
  const supabase = await createClient();
  await supabase.auth.signOut();
  revalidatePath("/", "layout");
  redirect("/login");
}

export async function resetPassword(formData: FormData) {
  const supabase = await createClient();
  const origin = process.env.NEXT_PUBLIC_API_URL || "http://localhost:3000";

  const email = formData.get("email") as string;
  try {
    const { error } = await supabase.auth.resetPasswordForEmail(email, {
      redirectTo: `${origin}/reset-password`,
    });

    if (error) {
      return { error: error.message };
    }
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : "An unexpected error occurred.";
    return { error: message };
  }
  return { success: "Password reset instructions sent to your email" };
}

export async function updatePassword(formData: FormData) {
  const supabase = await createClient();
  const password = formData.get("password") as string;

  try {
    const { error } = await supabase.auth.updateUser({
      password,
    });

    if (error) {
      return { error: error.message };
    }
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : "An unexpected error occurred.";
    return { error: message };
  }
  redirect("/dashboard");
}
