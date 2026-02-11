import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";

function getSupabaseClient(accessToken: string) {
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

function getToken(request: NextRequest): string | null {
  const auth = request.headers.get("Authorization");
  if (!auth?.startsWith("Bearer ")) return null;
  return auth.slice(7);
}

/**
 * GET /api/campaigns/[id]/analyzed-posts - Fetch analyzed posts with scoring
 *
 * Query params: subreddit, sort_by, sort_dir, page, per_page
 * Validates user ownership and proxies to FastAPI backend
 */
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const token = getToken(request);

  if (!token) {
    return NextResponse.json(
      { error: { code: "AUTH_REQUIRED", message: "Authentication required" } },
      { status: 401 }
    );
  }

  const supabase = getSupabaseClient(token);

  // Verify user authentication
  const { data: { user }, error: authError } = await supabase.auth.getUser();
  if (authError || !user) {
    return NextResponse.json(
      { error: { code: "AUTH_INVALID", message: "Invalid or expired token" } },
      { status: 401 }
    );
  }

  // Verify campaign ownership
  const { data: campaign, error: campaignError } = await supabase
    .from("campaigns")
    .select("id")
    .eq("id", id)
    .eq("user_id", user.id)
    .single();

  if (campaignError || !campaign) {
    return NextResponse.json(
      { error: { code: "NOT_FOUND", message: "Campaign not found" } },
      { status: 404 }
    );
  }

  // Build query params
  const queryParams = new URLSearchParams();
  const subreddit = request.nextUrl.searchParams.get("subreddit");
  const sortBy = request.nextUrl.searchParams.get("sort_by");
  const sortDir = request.nextUrl.searchParams.get("sort_dir");
  const page = request.nextUrl.searchParams.get("page");
  const perPage = request.nextUrl.searchParams.get("per_page");

  if (subreddit) queryParams.set("subreddit", subreddit);
  if (sortBy) queryParams.set("sort_by", sortBy);
  if (sortDir) queryParams.set("sort_dir", sortDir);
  if (page) queryParams.set("page", page);
  if (perPage) queryParams.set("per_page", perPage);

  // Proxy to FastAPI backend
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/v1";
  const backendUrl = `${apiUrl}/analysis/campaigns/${id}/analyzed-posts${queryParams.toString() ? `?${queryParams.toString()}` : ""}`;

  try {
    const backendResponse = await fetch(backendUrl, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
    });

    const data = await backendResponse.json();

    if (!backendResponse.ok) {
      return NextResponse.json(data, { status: backendResponse.status });
    }

    return NextResponse.json(data, { status: 200 });
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json(
      { error: { code: "SERVER_ERROR", message: errorMessage } },
      { status: 500 }
    );
  }
}
