import { test, describe } from 'node:test';
import assert from 'node:assert/strict';
import {
  isCandidateRoute,
  isAdminRoute,
  isAuthRoute,
  sanitizeRedirectUrl,
} from '../lib/auth/redirects.ts';

describe('Route Classification', () => {
  test('correctly classifies candidate routes', () => {
    const candidatePaths = [
      '/dashboard',
      '/dashboard/settings',
      '/applications',
      '/applications?status=applied',
      '/profile',
      '/profile/edit',
      '/matches',
      '/roadmap',
      '/interview-prep',
      '/cover-letter',
      '/application-assistant',
      '/resume-recommendations',
      '/saved-opportunities',
      '/opportunities',
      '/opportunities/550e8400-e29b-41d4-a716-446655440000',
    ];

    for (const path of candidatePaths) {
      assert.strictEqual(
        isCandidateRoute(path),
        true,
        `Expected ${path} to be classified as candidate route`
      );
    }
  });

  test('correctly identifies non-candidate routes', () => {
    const nonCandidatePaths = [
      '/',
      '/login',
      '/register',
      '/forgot-password',
      '/reset-password',
      '/auth/callback',
      '/admin',
      '/admin/opportunities',
      '/admin/ingestion',
      '/api/v1/health',
    ];

    for (const path of nonCandidatePaths) {
      assert.strictEqual(
        isCandidateRoute(path),
        false,
        `Expected ${path} NOT to be classified as candidate route`
      );
    }
  });

  test('correctly classifies admin routes', () => {
    const adminPaths = [
      '/admin',
      '/admin/',
      '/admin/opportunities',
      '/admin/ingestion',
      '/admin/users/details',
    ];

    for (const path of adminPaths) {
      assert.strictEqual(
        isAdminRoute(path),
        true,
        `Expected ${path} to be classified as admin route`
      );
    }
  });

  test('correctly identifies non-admin routes', () => {
    const nonAdminPaths = [
      '/',
      '/dashboard',
      '/applications',
      '/login',
      '/register',
      '/administration', // Prefix mismatch
      '/admin-dashboard', // Prefix mismatch
    ];

    for (const path of nonAdminPaths) {
      assert.strictEqual(
        isAdminRoute(path),
        false,
        `Expected ${path} NOT to be classified as admin route`
      );
    }
  });

  test('correctly classifies auth routes', () => {
    const authPaths = [
      '/login',
      '/register',
      '/forgot-password',
    ];

    for (const path of authPaths) {
      assert.strictEqual(
        isAuthRoute(path),
        true,
        `Expected ${path} to be classified as auth route`
      );
    }
  });

  test('correctly identifies non-auth routes', () => {
    const nonAuthPaths = [
      '/',
      '/dashboard',
      '/applications',
      '/admin',
      '/reset-password',
      '/auth/callback',
    ];

    for (const path of nonAuthPaths) {
      assert.strictEqual(
        isAuthRoute(path),
        false,
        `Expected ${path} NOT to be classified as auth route`
      );
    }
  });
});

describe('Redirect URL Sanitization (CWE-601 Defense)', () => {
  test('allows safe relative paths with query parameters and fragments', () => {
    assert.strictEqual(sanitizeRedirectUrl('/dashboard'), '/dashboard');
    assert.strictEqual(sanitizeRedirectUrl('/applications?status=applied'), '/applications?status=applied');
    assert.strictEqual(sanitizeRedirectUrl('/opportunities/123#details'), '/opportunities/123#details');
    assert.strictEqual(sanitizeRedirectUrl('/admin/opportunities'), '/admin/opportunities');
    assert.strictEqual(sanitizeRedirectUrl('/admin/ingestion?filter=rss'), '/admin/ingestion?filter=rss');
  });

  test('blocks absolute URLs and protocol-relative URLs', () => {
    assert.strictEqual(sanitizeRedirectUrl('https://evil.com'), '/dashboard');
    assert.strictEqual(sanitizeRedirectUrl('http://attacker.com/steal'), '/dashboard');
    assert.strictEqual(sanitizeRedirectUrl('//evil.com'), '/dashboard');
    assert.strictEqual(sanitizeRedirectUrl('//evil.com/path'), '/dashboard');
    assert.strictEqual(sanitizeRedirectUrl('///evil.com'), '/dashboard');
  });

  test('blocks backslash and control character bypass attempts', () => {
    assert.strictEqual(sanitizeRedirectUrl('/\\evil.com'), '/dashboard');
    assert.strictEqual(sanitizeRedirectUrl('\\\\evil.com'), '/dashboard');
    assert.strictEqual(sanitizeRedirectUrl('/dashboard\\path'), '/dashboard');
    assert.strictEqual(sanitizeRedirectUrl('/dashboard\r\nevil'), '/dashboard');
    assert.strictEqual(sanitizeRedirectUrl('/dashboard\nevil'), '/dashboard');
    assert.strictEqual(sanitizeRedirectUrl('/dashboard\tevil'), '/dashboard');
  });

  test('blocks scheme smuggling and javascript/data URIs', () => {
    assert.strictEqual(sanitizeRedirectUrl('javascript:alert(1)'), '/dashboard');
    assert.strictEqual(sanitizeRedirectUrl('data:text/html,<script>alert(1)</script>'), '/dashboard');
    assert.strictEqual(sanitizeRedirectUrl('/http://evil.com'), '/dashboard');
    assert.strictEqual(sanitizeRedirectUrl('/https://evil.com'), '/dashboard');
  });

  test('prevents redirect loops by rejecting auth destinations', () => {
    assert.strictEqual(sanitizeRedirectUrl('/login'), '/dashboard');
    assert.strictEqual(sanitizeRedirectUrl('/login?next=/admin'), '/dashboard');
    assert.strictEqual(sanitizeRedirectUrl('/register'), '/dashboard');
    assert.strictEqual(sanitizeRedirectUrl('/forgot-password'), '/dashboard');
    assert.strictEqual(sanitizeRedirectUrl('/reset-password'), '/dashboard');
    assert.strictEqual(sanitizeRedirectUrl('/auth/callback'), '/dashboard');
  });

  test('handles null, empty, and invalid inputs with fallback', () => {
    assert.strictEqual(sanitizeRedirectUrl(null), '/dashboard');
    assert.strictEqual(sanitizeRedirectUrl(undefined), '/dashboard');
    assert.strictEqual(sanitizeRedirectUrl(''), '/dashboard');
    assert.strictEqual(sanitizeRedirectUrl('   '), '/dashboard');
    assert.strictEqual(sanitizeRedirectUrl('not-a-path'), '/dashboard');
    assert.strictEqual(sanitizeRedirectUrl('//evil.com', '/matches'), '/matches');
  });
});
