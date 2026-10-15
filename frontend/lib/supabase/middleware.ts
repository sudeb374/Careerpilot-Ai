import { createServerClient } from '@supabase/ssr'
import { NextResponse, type NextRequest } from 'next/server'
import {
  isCandidateRoute,
  isAdminRoute,
  isAuthRoute,
  sanitizeRedirectUrl,
} from '@/lib/auth/redirects'

function createRedirectResponse(
  request: NextRequest,
  redirectUrl: URL,
  supabaseResponse: NextResponse
): NextResponse {
  const redirectResponse = NextResponse.redirect(redirectUrl)
  // Preserve refreshed session cookies so auth state is not lost across redirects
  supabaseResponse.cookies.getAll().forEach((cookie) => {
    redirectResponse.cookies.set(cookie.name, cookie.value, cookie)
  })
  return redirectResponse
}

export async function updateSession(request: NextRequest) {
  let supabaseResponse = NextResponse.next({
    request,
  })

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return request.cookies.getAll()
        },
        setAll(cookiesToSet) {
          cookiesToSet.forEach(({ name, value }) => request.cookies.set(name, value))
          supabaseResponse = NextResponse.next({
            request,
          })
          cookiesToSet.forEach(({ name, value, options }) =>
            supabaseResponse.cookies.set(name, value, options)
          )
        },
      },
    }
  )

  // IMPORTANT: Avoid writing any logic between createServerClient and
  // supabase.auth.getUser(). A simple mistake could make it very hard to debug
  // issues with cross-browser cookies.
  const {
    data: { user },
  } = await supabase.auth.getUser()

  const pathname = request.nextUrl.pathname
  const search = request.nextUrl.search

  // 1. Protect unauthenticated access to candidate and admin routes
  if (!user && (isCandidateRoute(pathname) || isAdminRoute(pathname))) {
    const originalDestination = `${pathname}${search}`
    const loginUrl = request.nextUrl.clone()
    loginUrl.pathname = '/login'
    loginUrl.search = `?next=${encodeURIComponent(originalDestination)}`
    return createRedirectResponse(request, loginUrl, supabaseResponse)
  }

  // 2. Redirect authenticated users away from public auth pages (/login, /register, /forgot-password)
  if (user && isAuthRoute(pathname)) {
    const rawNext = request.nextUrl.searchParams.get('next')
    const safeNext = sanitizeRedirectUrl(rawNext, '/dashboard')
    const destinationUrl = new URL(safeNext, request.url)
    return createRedirectResponse(request, destinationUrl, supabaseResponse)
  }

  return supabaseResponse
}
