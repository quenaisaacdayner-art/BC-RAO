import { NextRequest } from "next/server";

/**
 * SSE Proxy Route: Streams draft generation progress from FastAPI backend
 * GET /api/campaigns/[id]/drafts/generate/stream/[taskId]
 *
 * Proxies Server-Sent Events from backend /v1/campaigns/{id}/drafts/generate/stream/{taskId}
 * No authentication required - task_id acts as unguessable bearer token
 */
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string; taskId: string }> }
) {
  const { id, taskId } = await params;

  // Determine backend API URL
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/v1";
  const backendUrl = `${apiUrl}/campaigns/${id}/drafts/generate/stream/${taskId}`;

  try {
    const response = await fetch(backendUrl, {
      method: "GET",
      headers: {
        Accept: "text/event-stream",
      },
    });

    if (!response.ok) {
      // Return error as SSE event
      return new Response(
        `event: error\ndata: ${JSON.stringify({ error: "Failed to connect to backend", status: response.status })}\n\n`,
        {
          status: 200,
          headers: {
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            Connection: "keep-alive",
          },
        }
      );
    }

    // Stream the backend SSE response to the client
    return new Response(response.body, {
      headers: {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        Connection: "keep-alive",
      },
    });
  } catch (error) {
    // Return error as SSE event
    const errorMessage = error instanceof Error ? error.message : "Unknown error";
    return new Response(
      `event: error\ndata: ${JSON.stringify({ error: errorMessage })}\n\n`,
      {
        status: 200,
        headers: {
          "Content-Type": "text/event-stream",
          "Cache-Control": "no-cache",
          Connection: "keep-alive",
        },
      }
    );
  }
}
