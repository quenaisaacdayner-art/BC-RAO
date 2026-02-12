import { NextRequest, NextResponse } from "next/server";
import { getSupabaseClient, getToken } from "@/lib/auth-helpers";

// GET /api/campaigns - List user's campaigns
export async function GET(request: NextRequest) {
  const token = getToken(request);
  if (!token) {
    return NextResponse.json(
      { error: { code: "AUTH_REQUIRED", message: "Authentication required" } },
      { status: 401 }
    );
  }

  const supabase = getSupabaseClient(token);

  const { data: { user }, error: authError } = await supabase.auth.getUser();
  if (authError || !user) {
    return NextResponse.json(
      { error: { code: "AUTH_INVALID", message: "Invalid or expired token" } },
      { status: 401 }
    );
  }

  const { data: campaigns, error } = await supabase
    .from("campaigns")
    .select("*")
    .eq("user_id", user.id)
    .order("created_at", { ascending: false });

  if (error) {
    return NextResponse.json(
      { error: { code: "SERVER_ERROR", message: error.message } },
      { status: 500 }
    );
  }

  return NextResponse.json({
    campaigns: campaigns || [],
    total: campaigns?.length || 0,
  });
}

// POST /api/campaigns - Create a campaign
export async function POST(request: NextRequest) {
  const token = getToken(request);
  if (!token) {
    return NextResponse.json(
      { error: { code: "AUTH_REQUIRED", message: "Authentication required" } },
      { status: 401 }
    );
  }

  const supabase = getSupabaseClient(token);

  const { data: { user }, error: authError } = await supabase.auth.getUser();
  if (authError || !user) {
    return NextResponse.json(
      { error: { code: "AUTH_INVALID", message: "Invalid or expired token" } },
      { status: 401 }
    );
  }

  const body = await request.json();

  // Validate required fields
  if (!body.name || !body.product_context || !body.keywords || !body.target_subreddits) {
    return NextResponse.json(
      { error: { code: "VALIDATION_ERROR", message: "Missing required fields" } },
      { status: 400 }
    );
  }

  if (body.keywords.length < 5 || body.keywords.length > 15) {
    return NextResponse.json(
      { error: { code: "VALIDATION_ERROR", message: "Between 5 and 15 keywords required" } },
      { status: 400 }
    );
  }

  if (body.target_subreddits.length < 1) {
    return NextResponse.json(
      { error: { code: "VALIDATION_ERROR", message: "At least one subreddit required" } },
      { status: 400 }
    );
  }

  const { data: campaign, error } = await supabase
    .from("campaigns")
    .insert({
      user_id: user.id,
      name: body.name,
      product_context: body.product_context,
      product_url: body.product_url || "",
      keywords: body.keywords,
      target_subreddits: body.target_subreddits,
      status: "active",
    })
    .select()
    .single();

  if (error) {
    return NextResponse.json(
      { error: { code: "SERVER_ERROR", message: error.message } },
      { status: 500 }
    );
  }

  return NextResponse.json(campaign, { status: 201 });
}
