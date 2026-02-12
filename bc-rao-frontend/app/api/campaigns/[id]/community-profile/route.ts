import { NextRequest, NextResponse } from "next/server";
import { getSupabaseClient, getToken } from "@/lib/auth-helpers";

/**
 * GET /api/campaigns/[id]/community-profile?subreddit={subreddit} - Fetch single community profile
 *
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

  // Extract subreddit query param
  const subreddit = request.nextUrl.searchParams.get("subreddit");
  if (!subreddit) {
    return NextResponse.json(
      { error: { code: "INVALID_REQUEST", message: "subreddit query parameter required" } },
      { status: 400 }
    );
  }

  // Proxy to FastAPI backend
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/v1";
  const backendUrl = `${apiUrl}/analysis/campaigns/${id}/community-profile?subreddit=${encodeURIComponent(subreddit)}`;

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
