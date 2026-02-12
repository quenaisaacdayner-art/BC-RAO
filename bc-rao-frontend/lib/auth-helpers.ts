import { NextRequest } from "next/server";
import { createClient } from "@supabase/supabase-js";

/**
 * Create a Supabase client with a user's access token.
 * Used in API routes to authenticate requests.
 */
export function getSupabaseClient(accessToken: string) {
  return createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      global: {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      },
    }
  );
}

/**
 * Extract the Bearer token from the Authorization header.
 * Returns null if no valid token is found.
 */
export function getToken(request: NextRequest): string | null {
  const auth = request.headers.get("Authorization");
  if (!auth?.startsWith("Bearer ")) return null;
  return auth.slice(7);
}
