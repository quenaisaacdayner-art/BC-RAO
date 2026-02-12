---
status: resolved
trigger: "analysis-pipeline-broken: Analysis pipeline runs visually but doesn't work in backend. Stage 3 never completes."
created: 2026-02-12T00:00:00Z
updated: 2026-02-12T00:03:00Z
---

## Current Focus

hypothesis: CONFIRMED -- Multiple compounding bugs causing silent analysis pipeline failure
test: All fixes implemented, frontend builds clean, backend tests pass (excluding pre-existing failures)
expecting: Analysis pipeline now creates profiles, reports failures properly, and manual re-analysis works
next_action: Archive session

## Symptoms

expected: After collection completes, analysis should auto-trigger. Analysis should create community_profiles in the database. Campaign stats should update to mark Stage 3 complete. Stage 4 (Draft Generation) should unlock.
actual: Collection completes (Stage 2 done). Analysis either doesn't auto-trigger or runs but produces no real results. Campaign stays stuck at Stage 3.
errors: No visible errors - the UI shows the analysis completing but nothing changes in the system.
reproduction: Collect data for a campaign, then try to analyze. The visual feedback shows completion but Stage 3 never completes.
started: Potentially since Phase 3 implementation.

## Eliminated

- hypothesis: Auto-trigger chain from collection to analysis is broken
  evidence: task_runner.py correctly generates analysis_task_id, adds it to SUCCESS state, and launches run_analysis_background_task. Frontend ProgressTracker extracts analysis_task_id and transitions to "analyzing" phase. Chain is correct.
  timestamp: 2026-02-12T00:01:00Z

- hypothesis: SSE progress endpoints are broken
  evidence: SSE endpoints exist on both backend and frontend. getSSEUrl connects directly to Railway in production. Working correctly.
  timestamp: 2026-02-12T00:01:00Z

- hypothesis: RLS policies block backend writes
  evidence: Backend uses service role key which bypasses RLS. Not the issue.
  timestamp: 2026-02-12T00:01:00Z

- hypothesis: Stage navigation URLs are wrong
  evidence: Both computeStages and getStageUrl correctly point Stage 3 to /profiles. StageIndicator uses stage.url. Not the issue.
  timestamp: 2026-02-12T00:02:00Z

## Evidence

- timestamp: 2026-02-12T00:01:00Z
  checked: analysis_service.py _build_community_profile (lines 349-352) + migration 003
  found: Profile data conditionally includes style_metrics and style_guide. If migration 003 not applied, upsert fails with column-not-found error. Error caught by broad except on line 270, profile is NOT created. SILENT FAILURE.
  implication: ROOT CAUSE 1 -- Every subreddit fails to create a profile, but analysis reports "complete".

- timestamp: 2026-02-12T00:01:00Z
  checked: analysis_worker.py SUCCESS reporting (lines 60-66)
  found: Worker reports SUCCESS state regardless of whether profiles_created is 0 or not. Frontend sees SUCCESS, shows completion toast.
  implication: ROOT CAUSE 2 -- No feedback to user that analysis produced nothing.

- timestamp: 2026-02-12T00:01:00Z
  checked: ManualAnalysisTrigger.tsx (line 38)
  found: Sends force_refresh=false. If any profiles exist from partial success, analysis returns "exists" early without re-analyzing.
  implication: ROOT CAUSE 3 -- Manual re-analysis button is a no-op when partial profiles exist.

- timestamp: 2026-02-12T00:02:00Z
  checked: AnalysisProgress.tsx SSE field mapping (line 51)
  found: Frontend reads data.step but backend sends data.current_step. Step name always empty.
  implication: BUG 4 -- Progress step names never display during analysis.

## Resolution

root_cause: MULTIPLE COMPOUNDING BUGS causing silent analysis pipeline failure:
1. DB upsert fails silently when migration 003 (style_metrics/style_guide columns) not applied
2. Analysis worker reports SUCCESS even when zero profiles created
3. Manual analysis trigger uses force_refresh=false, blocking re-runs when partial profiles exist
4. SSE field name mismatch (step vs current_step) hides progress step names

fix:
1. analysis_service.py: Added try/except around upsert with fallback that strips style columns
2. analysis_worker.py: Reports FAILURE when profiles_created=0 and status!="exists"
3. ManualAnalysisTrigger.tsx: Changed force_refresh from false to true
4. AnalysisProgress.tsx: Fixed SSE field to read data.current_step || data.step
5. AnalysisProgress.tsx: Enhanced success toast to show profiles_created count

verification:
- Frontend builds successfully (npx next build passes)
- Backend tests pass (excluding 3 pre-existing test failures unrelated to changes)
- All changes are minimal and targeted to the identified bugs

files_changed:
- bc-rao-api/app/services/analysis_service.py (resilient upsert with style column fallback)
- bc-rao-api/app/workers/analysis_worker.py (FAILURE when 0 profiles created)
- bc-rao-frontend/components/analysis/ManualAnalysisTrigger.tsx (force_refresh=true)
- bc-rao-frontend/components/analysis/AnalysisProgress.tsx (SSE field fix + success toast)
