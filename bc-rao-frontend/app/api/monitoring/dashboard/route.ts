import { NextRequest, NextResponse } from "next/server";
import { getSupabaseClient, getToken } from "@/lib/auth-helpers";

/**
 * GET /api/monitoring/dashboard - Get dashboard stats
 *
 * Query params: campaign_id (required)
 * Validates user authentication and proxies to FastAPI backend
 */
export async function GET(request: NextRequest) {
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

  // Extract query parameters
  const { searchParams } = new URL(request.url);
  const campaign_id = searchParams.get("campaign_id");

  if (!campaign_id) {
    return NextResponse.json(
      { error: { code: "VALIDATION_ERROR", message: "campaign_id is required" } },
      { status: 400 }
    );
  }

  // Build query string
  const queryParams = new URLSearchParams({ campaign_id });

  // Proxy to FastAPI backend
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/v1";
  const backendUrl = `${apiUrl}/monitoring/dashboard?${queryParams.toString()}`;

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

    return NextResponse.json(data);
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json(
      { error: { code: "SERVER_ERROR", message: errorMessage } },
      { status: 500 }
    );
  }
}
