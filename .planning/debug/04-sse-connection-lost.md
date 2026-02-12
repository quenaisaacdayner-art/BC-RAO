---
status: diagnosed
trigger: "Draft Generation SSE Connection Lost - SSE progress starts but shows 'Error: Connection lost. Please try again.' and draft generation never completes"
created: 2026-02-11T00:00:00Z
updated: 2026-02-11T00:01:00Z
symptoms_prefilled: true
goal: find_root_cause_only
---

## Current Focus

hypothesis: CONFIRMED - Multiple interacting root causes: SSE event name mismatch (primary), SSE data format mismatch, and missing draft_id in SUCCESS payload
test: Traced complete SSE chain from frontend EventSource -> backend SSE generator
expecting: N/A - root causes identified
next_action: Report diagnosis

## Symptoms

expected: After clicking Generate, SSE progress streams updates and redirects to draft editor on completion
actual: SSE progress starts but then shows "Error: Connection lost. Please try again." and never completes
errors: "Error: Connection lost. Please try again."
reproduction: Click Generate on the draft generation form
started: Unknown

## Eliminated

- hypothesis: CORS blocking direct SSE connection to Railway backend
  evidence: Backend main.py has allow_origin_regex matching bc-rao-frontend*.vercel.app and explicit bc-rao-frontend.vercel.app in _cors_origins
  timestamp: 2026-02-11

- hypothesis: NEXT_PUBLIC_API_URL not available in client-side code
  evidence: NEXT_PUBLIC_* vars are inlined at build time by Next.js; .env and .env.local both set NEXT_PUBLIC_API_URL=https://production-production-a9aa.up.railway.app/v1
  timestamp: 2026-02-11

- hypothesis: Vercel 25s function timeout kills SSE proxy
  evidence: lib/sse.ts already handles this by connecting directly to Railway backend in production (bypasses Vercel proxy)
  timestamp: 2026-02-11

## Evidence

- timestamp: 2026-02-11
  checked: Frontend page.tsx (bc-rao-frontend/app/dashboard/campaigns/[id]/drafts/new/page.tsx)
  found: Lines 148-177 - Frontend uses `eventSource.onmessage` which only handles events WITHOUT a named event type (the default "message" event). It expects data fields: `data.state` ("PROGRESS"|"SUCCESS"|"FAILURE"), `data.status`, `data.meta?.phase`, `data.result?.draft_id`, `data.error`
  implication: Frontend is ONLY listening on `onmessage` which handles unnamed events. Named events (event: progress, event: success, event: error) are NEVER caught by onmessage.

- timestamp: 2026-02-11
  checked: Backend SSE endpoint (bc-rao-api/app/api/v1/drafts.py lines 240-313)
  found: Backend sends NAMED events: `event: progress`, `event: success`, `event: error`, `event: done`, `event: started`, `event: pending`. The data format is the raw meta dict from Redis (e.g., `{"type": "status", "message": "..."}` for progress, `{"type": "complete", "draft": {...}}` for success)
  implication: Backend uses named SSE events. Frontend's `onmessage` handler NEVER receives named events - those require `addEventListener('eventname', ...)`. This is the PRIMARY ROOT CAUSE.

- timestamp: 2026-02-11
  checked: Frontend data expectations vs backend data format
  found: Frontend expects `data.state === "PROGRESS"` but backend sends `event: progress` with data `{"type": "status", "message": "..."}`. Frontend expects `data.state === "SUCCESS"` but backend sends `event: success` with data `{"type": "complete", "draft": {...}}`. Frontend expects `data.result?.draft_id` but backend sends `{"type": "complete", "draft": {"id": "...", ...}}` (the draft_id is at `data.draft.id`, not `data.result.draft_id`).
  implication: Even if named events were properly listened to, the data format doesn't match what the frontend expects.

- timestamp: 2026-02-11
  checked: EventSource behavior on named events with no matching listener
  found: When EventSource receives events with named `event:` fields and there is no `addEventListener` for that event name, the events are silently dropped. The `onmessage` handler only fires for events with no `event:` field (or `event: message`). Since ALL backend events are named, the frontend receives NOTHING.
  implication: The EventSource connection stays open waiting for messages that never arrive via `onmessage`. Eventually, the backend SSE stream ends (after SUCCESS/FAILURE + done event), closing the HTTP response. The EventSource detects the closed connection and fires `onerror`, which triggers "Connection lost. Please try again."

- timestamp: 2026-02-11
  checked: Backend task runner (bc-rao-api/app/workers/task_runner.py)
  found: Redis-backed task state with get_task_state/update_task_state. SSE endpoint polls every 1.5s. Heartbeat keepalive every 15s (10 polls). All working correctly.
  implication: Backend infrastructure is sound. The issue is purely in the SSE event protocol mismatch.

- timestamp: 2026-02-11
  checked: SSE URL construction in production
  found: lib/sse.ts returns `${backendUrl}${path}` where backendUrl = "https://production-production-a9aa.up.railway.app/v1" and path = "/campaigns/{id}/drafts/generate/stream/{taskId}". Result: "https://production-production-a9aa.up.railway.app/v1/campaigns/{id}/drafts/generate/stream/{taskId}"
  implication: URL construction is correct. The SSE connection opens successfully (hence "progress starts") but no messages arrive via onmessage.

## Resolution

root_cause: |
  **PRIMARY: SSE Event Name Mismatch (Protocol Mismatch)**

  The backend FastAPI SSE endpoint (bc-rao-api/app/api/v1/drafts.py:266-303) sends
  ALL events as NAMED SSE events:
    - `event: started\ndata: {...}\n\n`
    - `event: progress\ndata: {...}\n\n`
    - `event: success\ndata: {...}\n\n`
    - `event: error\ndata: {...}\n\n`
    - `event: done\ndata: {}\n\n`

  The frontend (bc-rao-frontend/app/dashboard/campaigns/[id]/drafts/new/page.tsx:148)
  uses ONLY `eventSource.onmessage` which per the SSE specification ONLY fires for
  events that have NO `event:` field (or `event: message`).

  Named events require `eventSource.addEventListener('eventname', callback)`.

  RESULT: The SSE connection opens successfully. Backend sends all progress updates
  and the final success/failure event. The frontend's onmessage handler NEVER fires
  because all events are named. The backend stream eventually completes and closes
  the HTTP connection. The EventSource detects the closed connection and fires the
  `onerror` handler (line 179), which sets "Connection lost. Please try again."

  **SECONDARY: SSE Data Format Mismatch**

  Even after fixing the event listeners, the frontend expects a different data
  structure than what the backend sends:

  | What frontend expects              | What backend sends                           |
  |-------------------------------------|----------------------------------------------|
  | `data.state === "PROGRESS"`         | Named event `progress`, data has `type/message` |
  | `data.state === "SUCCESS"`          | Named event `success`, data has `type/draft`    |
  | `data.state === "FAILURE"`          | Named event `error`, data has `type/message`    |
  | `data.status` (progress text)       | `data.message` (progress text)                  |
  | `data.meta?.phase`                  | Not sent by backend                             |
  | `data.result?.draft_id`             | `data.draft.id` (full draft object)             |
  | `data.error` (error message)        | `data.message` (error message)                  |

fix: |
  Two approaches (pick one):

  **Option A: Fix Frontend to match Backend (Recommended - smaller change)**
  File: bc-rao-frontend/app/dashboard/campaigns/[id]/drafts/new/page.tsx

  Replace `eventSource.onmessage` (lines 148-177) with named event listeners:
  ```typescript
  eventSource.addEventListener('started', (event) => {
    setProgress({ status: "Starting generation..." });
  });

  eventSource.addEventListener('progress', (event) => {
    const data = JSON.parse(event.data);
    setProgress({
      status: data.message || "Processing...",
    });
  });

  eventSource.addEventListener('success', (event) => {
    const data = JSON.parse(event.data);
    const draftId = data.draft?.id;
    setProgress({ status: "Complete", draftId });
    setPhase("complete");
    eventSource.close();
    if (draftId) {
      setTimeout(() => {
        router.push(`/dashboard/drafts/${draftId}/edit`);
      }, 1500);
    }
  });

  eventSource.addEventListener('error', (event) => {
    try {
      const data = JSON.parse(event.data);
      setError(data.message || "Generation failed");
    } catch {
      setError("Connection lost. Please try again.");
    }
    setPhase("error");
    eventSource.close();
  });

  eventSource.addEventListener('done', () => {
    eventSource.close();
  });
  ```

  **Option B: Fix Backend to match Frontend**
  File: bc-rao-api/app/api/v1/drafts.py

  Change all named events to unnamed (remove `event: xxx\n` prefix) and
  restructure data to match frontend expectations:
  ```python
  yield f"data: {json.dumps({'state': 'PROGRESS', 'status': meta.get('message', ''), 'meta': {}})}\n\n"
  yield f"data: {json.dumps({'state': 'SUCCESS', 'result': {'draft_id': meta.get('draft', {}).get('id')}})}\n\n"
  yield f"data: {json.dumps({'state': 'FAILURE', 'error': meta.get('message', 'Generation failed')})}\n\n"
  ```

verification:
files_changed: []
