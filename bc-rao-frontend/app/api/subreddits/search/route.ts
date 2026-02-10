import { NextRequest, NextResponse } from "next/server";

export async function GET(request: NextRequest) {
  const query = request.nextUrl.searchParams.get("q");

  if (!query || query.length < 2) {
    return NextResponse.json({ data: { children: [] } });
  }

  try {
    const response = await fetch(
      `https://www.reddit.com/subreddits/search.json?q=${encodeURIComponent(query)}&limit=10`,
      {
        headers: {
          "User-Agent": "BC-RAO/1.0 (server-side proxy)",
        },
      }
    );

    if (!response.ok) {
      return NextResponse.json({ data: { children: [] } });
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch {
    return NextResponse.json({ data: { children: [] } });
  }
}
