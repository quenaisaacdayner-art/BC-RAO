# Phase 5: Monitoring & Feedback Loop - Context

**Gathered:** 2026-02-11
**Status:** Ready for planning

<domain>
## Phase Boundary

System monitors posted content with dual-check shadowban detection (authenticated + anonymous request), alerts users on removals, and feeds removal data back into the syntax blacklist for continuous learning. Covers post registration, scheduled monitoring, email alerts, 7-day post audit, and negative reinforcement pattern injection. Billing enforcement and onboarding belong in Phase 6.

</domain>

<decisions>
## Implementation Decisions

### Post registration flow
- Two entry points: "I posted this" button in draft editor + standalone URL paste on monitoring page
- URL only — no extra metadata required from user (system infers draft mapping automatically)
- Format validation only (valid Reddit post URL pattern) — no API fetch to verify existence
- After registration: toast notification + redirect to monitoring dashboard where new post appears

### Alert & notification UX
- Shadowban alerts only — removals and audits shown passively in dashboard, not actively alerted
- Dual channel for shadowbans: immediate email + in-app alert
- In-app alert: full-screen modal on first dashboard visit after detection, then dismissable banner
- Email includes urgency messaging and link back to dashboard
- Alert call-to-action: Claude's discretion on best CTA design (pause instruction + pattern analysis link)

### Monitoring dashboard
- Stats header at top: active / removed / shadowbanned counts + success rate
- Minimal post cards below: post title, subreddit, status badge (active/removed/shadowbanned), time since posted
- Filter by status: tabs or chips for All / Active / Removed / Shadowbanned
- Click post card to expand inline: shows check history, ISC snapshot, outcome classification, pattern analysis

### Feedback loop visibility
- Passive visibility: auto-added patterns tagged on blacklist page, no active notifications on injection
- 7-day audit results shown as status badge update on post card (SocialSuccess green / Rejection red / Inertia gray)
- No separate learning history view — blacklist page already shows all patterns including auto-added ones
- Keep it simple — the system learns silently, user sees results in blacklist and future generation quality

### Dashboard journey stages
- Add Stage 5 only: Deployment & Monitoring — covers registration, monitoring, and audit in one stage
- Single stage encompasses the full post-deployment lifecycle

### Claude's Discretion
- Dual-check scheduling logic (4h established vs 1h new accounts)
- Email template design and content
- Shadowban alert CTA design (pause instruction + pattern analysis balance)
- Pattern extraction algorithm from removed posts
- Monitoring check retry/backoff strategy
- Expandable card layout and information hierarchy

</decisions>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 05-monitoring-feedback-loop*
*Context gathered: 2026-02-11*
