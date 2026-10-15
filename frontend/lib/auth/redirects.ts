/**
 * CareerPilot AI — Route Security & Redirect Sanitization
 *
 * Centralized route definitions and safe redirect URI validation
 * to protect candidate and admin routes while preventing open-redirect
 * (CWE-601) vulnerabilities and redirect loops.
 */

export const PROTECTED_CANDIDATE_PREFIXES = [
  '/dashboard',
  '/applications',
  '/profile',
  '/matches',
  '/roadmap',
  '/interview-prep',
  '/cover-letter',
  '/application-assistant',
  '/resume-recommendations',
  '/saved-opportunities',
  '/opportunities',
] as const;

export const AUTH_PAGES = [
  '/login',
  '/register',
  '/forgot-password',
] as const;

/**
 * Normalizes a path by removing search params or hashes if present.
 */
function getCleanPath(pathname: string): string {
  return pathname.split(/[?#]/)[0] || '';
}

/**
 * Checks whether a given path is a protected candidate route.
 */
export function isCandidateRoute(pathname: string): boolean {
  const cleanPath = getCleanPath(pathname);
  return PROTECTED_CANDIDATE_PREFIXES.some(
    (prefix) => cleanPath === prefix || cleanPath.startsWith(`${prefix}/`)
  );
}

/**
 * Checks whether a given path is an admin route.
 */
export function isAdminRoute(pathname: string): boolean {
  const cleanPath = getCleanPath(pathname);
  return cleanPath === '/admin' || cleanPath.startsWith('/admin/');
}

/**
 * Checks whether a given path is an auth entry page.
 */
export function isAuthRoute(pathname: string): boolean {
  const cleanPath = getCleanPath(pathname);
  return AUTH_PAGES.some(
    (prefix) => cleanPath === prefix || cleanPath.startsWith(`${prefix}/`)
  );
}

/**
 * Sanitizes a redirect destination URL.
 *
 * Requirements:
 * - Must be a non-empty relative URL starting with a single '/'
 * - Must not start with '//' or '/\' (protocol-relative / authority confusion)
 * - Must not contain control characters, newlines, or backslashes
 * - Must not contain '://' (scheme confusion / smuggling)
 * - Must not resolve to an external host or smuggling scheme
 * - Must not point to auth routes (preventing login redirect loops)
 *
 * Returns the sanitized relative destination, or fallback (default: '/dashboard').
 */
export function sanitizeRedirectUrl(
  target: string | null | undefined,
  fallback: string = '/dashboard'
): string {
  if (!target || typeof target !== 'string') {
    return fallback;
  }

  const trimmed = target.trim();

  // Basic structure check: must begin with single '/', no backslashes, no '://', no control characters
  if (
    !trimmed.startsWith('/') ||
    trimmed.startsWith('//') ||
    trimmed.startsWith('/\\') ||
    trimmed.includes('\\') ||
    trimmed.includes('://') ||
    /[\r\n\t]/.test(trimmed)
  ) {
    return fallback;
  }

  try {
    const dummyOrigin = 'http://localhost';
    const parsed = new URL(trimmed, dummyOrigin);

    // Verify origin was not escaped or mutated
    if (parsed.host !== 'localhost' || parsed.protocol !== 'http:') {
      return fallback;
    }

    // Path must still be relative and not protocol-relative
    if (!parsed.pathname.startsWith('/') || parsed.pathname.startsWith('//')) {
      return fallback;
    }

    // Do not redirect to authentication pages or callbacks to prevent loops
    if (
      isAuthRoute(parsed.pathname) ||
      parsed.pathname === '/reset-password' ||
      parsed.pathname.startsWith('/reset-password/') ||
      parsed.pathname === '/auth/callback' ||
      parsed.pathname.startsWith('/auth/callback/')
    ) {
      return fallback;
    }

    return `${parsed.pathname}${parsed.search}${parsed.hash}`;
  } catch {
    return fallback;
  }
}
