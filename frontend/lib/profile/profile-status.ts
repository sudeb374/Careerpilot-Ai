import { type User } from "@supabase/supabase-js";

export interface ProfileStatus {
  isConfigured: boolean;
  isNewUser: boolean;
  role: string;
  hasBasicInfo: boolean;
  hasEducation: boolean;
  hasSkills: boolean;
  hasPreferences: boolean;
  hasResume: boolean;
  displayName: string;
}

/**
 * Evaluates whether a student profile is configured or genuinely incomplete.
 *
 * Rules:
 * - A profile is NOT complete merely because a database row exists (e.g. initial shell with just full_name).
 * - A profile IS complete if explicitly marked in server-backed user metadata (profile_setup_completed),
 *   OR if the user already has substantive server-backed profile data (basic info + education/skills/preferences/resume).
 * - Fully configured users are NEVER forced back into onboarding because an optional field is empty.
 * - Administrators are never forced into student onboarding.
 */
export async function getProfileStatus(
  user: User | null,
  accessToken: string | null,
  apiUrl: string = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
): Promise<ProfileStatus> {
  if (!user || !accessToken) {
    return {
      isConfigured: false,
      isNewUser: true,
      role: "student",
      hasBasicInfo: false,
      hasEducation: false,
      hasSkills: false,
      hasPreferences: false,
      hasResume: false,
      displayName: "Student",
    };
  }

  // If user metadata explicitly flags onboarding completed, they are configured
  const metadataCompleted = user.user_metadata?.profile_setup_completed === true;

  const headers = { Authorization: `Bearer ${accessToken}` };

  try {
    const profileRes = await fetch(`${apiUrl}/api/v1/profile`, {
      headers,
      cache: "no-store",
    });

    if (profileRes.status === 404) {
      return {
        isConfigured: false,
        isNewUser: true,
        role: "student",
        hasBasicInfo: false,
        hasEducation: false,
        hasSkills: false,
        hasPreferences: false,
        hasResume: false,
        displayName: user.user_metadata?.full_name || "Student",
      };
    }

    if (!profileRes.ok) {
      // In case of transient server errors, fallback safely without trapping user
      return {
        isConfigured: metadataCompleted,
        isNewUser: false,
        role: "student",
        hasBasicInfo: false,
        hasEducation: false,
        hasSkills: false,
        hasPreferences: false,
        hasResume: false,
        displayName: user.user_metadata?.full_name || "Student",
      };
    }

    const profileData = await profileRes.json();
    const role = profileData.role || "student";
    const displayName = profileData.full_name || user.user_metadata?.full_name || "Student";

    // Administrators never go through student profile onboarding
    if (role === "admin") {
      return {
        isConfigured: true,
        isNewUser: false,
        role: "admin",
        hasBasicInfo: true,
        hasEducation: true,
        hasSkills: true,
        hasPreferences: true,
        hasResume: true,
        displayName,
      };
    }

    // If metadata was already set to completed, fast-path return
    if (metadataCompleted) {
      return {
        isConfigured: true,
        isNewUser: false,
        role: "student",
        hasBasicInfo: !!profileData.full_name,
        hasEducation: true,
        hasSkills: true,
        hasPreferences: true,
        hasResume: true,
        displayName,
      };
    }

    // Query core profile sections to verify substantive completion
    const [eduRes, skillsRes, prefsRes, resumeRes] = await Promise.all([
      fetch(`${apiUrl}/api/v1/profile/education`, { headers, cache: "no-store" }).catch(() => null),
      fetch(`${apiUrl}/api/v1/profile/skills`, { headers, cache: "no-store" }).catch(() => null),
      fetch(`${apiUrl}/api/v1/profile/preferences`, { headers, cache: "no-store" }).catch(() => null),
      fetch(`${apiUrl}/api/v1/profile/resumes`, { headers, cache: "no-store" }).catch(() => null),
    ]);

    const educations = eduRes && eduRes.ok ? await eduRes.json() : [];
    const skills = skillsRes && skillsRes.ok ? await skillsRes.json() : [];
    const preferences = prefsRes && prefsRes.ok ? await prefsRes.json() : null;
    const resumes = resumeRes && resumeRes.ok ? await resumeRes.json() : [];

    const hasBasicInfo = !!(profileData.full_name && (profileData.headline || profileData.location));
    const hasEducation = Array.isArray(educations) && educations.length > 0;
    const hasSkills = Array.isArray(skills) && skills.length > 0;
    const hasPreferences = !!(preferences && (preferences.desired_roles?.length > 0 || preferences.locations?.length > 0));
    const hasResume = Array.isArray(resumes) && resumes.length > 0;

    // A student is configured if they have basic info AND at least one core career section
    // (education, skills, preferences, or a resume)
    const isSubstantivelyConfigured = hasBasicInfo && (hasEducation || hasSkills || hasPreferences || hasResume);

    return {
      isConfigured: isSubstantivelyConfigured,
      isNewUser: false,
      role: "student",
      hasBasicInfo,
      hasEducation,
      hasSkills,
      hasPreferences,
      hasResume,
      displayName,
    };
  } catch (err) {
    console.error("Failed to evaluate profile status:", err);
    return {
      isConfigured: metadataCompleted,
      isNewUser: false,
      role: "student",
      hasBasicInfo: false,
      hasEducation: false,
      hasSkills: false,
      hasPreferences: false,
      hasResume: false,
      displayName: user.user_metadata?.full_name || "Student",
    };
  }
}
