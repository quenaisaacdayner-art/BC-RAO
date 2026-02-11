/**
 * SSE URL builder for direct backend connections.
 *
 * Vercel Hobby plan has a 25-second serverless function timeout,
 * which kills SSE proxy routes before long-running tasks complete.
 * Solution: connect EventSource directly to the Railway backend.
 */

export function getSSEUrl(path: string): string {
  // In production, NEXT_PUBLIC_API_URL points to Railway backend
  // (e.g., https://production-production-a9aa.up.railway.app/v1)
  // Connect directly to avoid Vercel's 25s function timeout.
  const backendUrl = process.env.NEXT_PUBLIC_API_URL;

  if (backendUrl && !backendUrl.includes("localhost")) {
    // Production: connect directly to Railway backend
    return `${backendUrl}${path}`;
  }

  // Development: use Next.js proxy (no timeout issue locally)
  return `/api${path}`;
}
