## Plan: Lockd'In End-to-End Implementation + MVP Handoff

Lockd'In is a proactive personal software partner that helps users execute life and work reliably, not just chat. It should remind, nudge, prioritize, and safely automate recurring desktop workflows while preserving trust through strong consent, memory auditing, and action safety controls.

This document is a full continuity handoff for a new session: product intent, architecture, implementation plan, MVP slice, what is done, what is left, and how to continue immediately.

## 1. Product Vision and Full Picture

### 1.1 Core Product Promise
- Always available assistant from device startup.
- Understands user context from integrations and local activity.
- Suggests next actions and can execute approved workflows quickly.
- Learns user preferences over time with explicit safeguards.
- Scales from lightweight chat mode to deeper automation mode.

### 1.2 Core Experience Goals
- Fast enough for live interaction and voice loops.
- Safe enough for desktop control without surprise behavior.
- Personal enough to adapt to habits.
- Transparent enough for users to inspect, revoke, and control behavior.

### 1.3 Primary Use Cases
- Upcoming meeting detection with one-click join preparation.
- Routine preference execution (example: mic off and camera off on join).
- Priority nudges from calendar, email, and collaboration tools.
- Daily startup brief: meetings, tasks, urgent signals.

## 2. High-Level System Architecture

### 2.1 Client Layer
- Desktop runtime agent starts on login.
- Local context capture: active app metadata, accessibility tree snapshots, user-triggered events.
- User interaction surfaces: chat panel, voice mode, action confirmations, and reminders.

### 2.2 Orchestration Layer
- Intent router classifies incoming events and user requests.
- Planner creates structured action plans.
- Policy engine applies risk tiers and confirmation rules.
- Execution coordinator dispatches safe actions to desktop executor.

### 2.3 Reasoning and Voice Layer
- Primary reasoning: local DeepSeek.
- Fallback reasoning (free-tier strategy): StepFun and NVIDIA Nemotron.
- Voice synthesis: Sesame CSM.
- Optional speech input: Whisper.

### 2.4 Integration Layer
- Connectors for Gmail, Calendar, Slack, GitHub.
- OAuth-based access and scoped permissions.
- Unified event normalization into internal schemas.

### 2.5 Memory Layer
- Session memory: short-lived context.
- Candidate memory store: inferred but not trusted yet.
- Long-term memory: approved preferences, stable habits, user traits relevant to utility.
- Memory auditor gate controls all promotions.

### 2.6 Trust and Governance Layer
- Consent ledger per integration and data category.
- Audit trail for action attempts, outcomes, and memory changes.
- Data minimization and retention controls.
- User controls for export/delete/revoke.

## 3. Non-Negotiable Risks and Mitigations

### 3.1 Privacy and Consent Drift
- Mitigation: explicit per-integration consent, purpose tagging, minimal field ingestion, periodic consent renewal.
- Enforcement: no ingestion without active consent record.

### 3.2 Voice Loop Latency Spikes
- Mitigation: model cascade, streaming partial responses, strict timeout policy with graceful fallback.
- Enforcement: latency budgets and fallback logging.

### 3.3 Hallucinated Desktop Actions
- Mitigation: structured plans only, target element verification, simulation mode, risk-based confirmations.
- Enforcement: abort when verification fails.

### 3.4 Memory Poisoning
- Mitigation: candidate quarantine, contradiction checks, reinforcement requirements, easy rollback.
- Enforcement: no direct inference write to long-term memory.

### 3.5 Token Security and Lifecycle Risk
- Mitigation: vault-backed secret handling, short-lived tokens, refresh and revocation pipeline, scoped permissions.
- Enforcement: centralized token policy checks.

## 4. Full Implementation Plan (Entire Product, No Timeline)

### Phase A: Platform Foundations
1. Build backend service skeleton with clear modules for integrations, orchestration, memory, policy, and execution.
2. Establish PostgreSQL and Redis infrastructure.
3. Add configuration, secret loading, and environment validation.
4. Add migration framework and baseline schema.
5. Add structured logging and metrics hooks.

### Phase B: Integration Ingestion
1. Implement OAuth connection flow and token lifecycle management.
2. Build Google Calendar and Gmail connectors first.
3. Normalize incoming provider payloads into canonical Event schema.
4. Add ingestion scheduler and idempotent upserts.
5. Add connector health and sync status tracking.

### Phase C: Orchestration and Suggestions
1. Implement intent classification for chat, reminder, suggestion, action.
2. Add suggestion engine for near-term priorities.
3. Add rule-based triggers for startup brief and meeting reminders.
4. Add reasoner routing with primary and fallback models.
5. Emit structured action plans, never free-form executable text.

### Phase D: Desktop Action Safety and Execution
1. Build accessibility abstraction driver and target verification logic.
2. Implement restricted meeting-join action template.
3. Add dry-run execution previews.
4. Add explicit confirmation UX for confirm-tier actions.
5. Add execution snapshots and action audit records.

### Phase E: Memory Intelligence
1. Implement memory candidate ingestion pipeline.
2. Score candidates by recurrence, confidence, utility, sensitivity.
3. Add promotion gate requiring threshold plus confirmation signal.
4. Add contradiction resolution and stale candidate expiry.
5. Add user-facing memory management controls.

### Phase F: Settings and Controls
1. Build integrations settings page.
2. Build privacy and retention settings.
3. Build policy settings for reminders and confirmation strictness.
4. Build memory review UI.
5. Build account-level data controls (delete/export/disconnect all).

### Phase G: Reliability, Security, and Launch Readiness
1. Add retry queues and dead-letter handling.
2. Add alerting for connector failures and execution failures.
3. Add secret rotation and token revocation tests.
4. Add compliance-oriented data deletion and audit retrieval paths.
5. Complete end-to-end acceptance test pack.

## 5. MVP Implementation Plan (Focused Build)

### 5.1 MVP Objective
Prove real user value and trust using a safe, narrow workflow set with free or low-cost infrastructure.

### 5.2 MVP In Scope
- Text-first assistant with optional CSM voice output.
- Startup summary and proactive reminders.
- Google Calendar and Gmail integrations.
- Meeting reminder and Join Prepared suggestion.
- Restricted meeting-related desktop action template.
- Confirmation gate before any actionable execution.
- Candidate-memory flow and manual review.
- Settings for integrations, reminders, meeting defaults, and memory/privacy controls.

### 5.3 MVP Out of Scope
- Arbitrary desktop autonomy across any application.
- Always-on microphone by default.
- Enterprise billing and team administration.
- Broad connector marketplace.

### 5.4 MVP Acceptance Criteria
1. User connects Calendar and Gmail successfully.
2. Upcoming meeting appears in reminders.
3. Join Prepared flow requires confirmation and logs outcome.
4. Mic and camera default preference can be set and applied.
5. Inferred preferences appear as memory candidates before promotion.
6. User can disconnect integrations and remove memory entries at any time.

## 6. Target Technical Stack (Agreed)

### 6.1 Backend
- Python 3.11
- FastAPI + Uvicorn
- Pydantic
- Celery + Redis (chosen)
- PostgreSQL

### 6.2 Intelligence
- DeepSeek local inference (primary)
- StepFun free tier (fallback)
- NVIDIA Nemotron free tier (fallback)
- Sesame CSM for TTS
- Whisper optional for STT

### 6.3 Frontend
- Next.js (chosen)
- Settings dashboard plus assistant interaction panels

### 6.4 Observability and Ops
- Structured application logs
- OpenTelemetry-ready instrumentation
- Error monitoring (Sentry free tier acceptable)
- Metrics pipeline for latency, action safety, and memory quality

## 7. Data Contracts and Core Entities

### 7.1 Core Schemas
- Event: normalized integration event with source, time, metadata, confidence.
- TaskSuggestion: nudge/reminder item with reason, urgency, and actionability.
- ActionPlan: structured, validated list of executable steps with risk tier.
- ActionRun: execution result record with validation evidence and outcome.
- MemoryCandidate: inferred preference or pattern pending audit.
- MemoryRecord: approved long-term memory with provenance and confidence.
- PolicyRule: user controls for automation, confirmations, and retention.

### 7.2 Mandatory Invariants
- No action execution without policy check.
- No long-term memory write without auditor path.
- No integration ingestion without consent record.

## 8. What Has Been Done Already (Planning State)

1. Product direction translated into executable architecture and boundaries.
2. Major risk areas identified with mitigation strategy.
3. Full MVP scope drafted with explicit in-scope and out-of-scope items.
4. Free-first stack choices selected for initial build.
5. First implementation slice defined (backend skeleton + normalization + reminder jobs).
6. Owner setup checklist drafted (secrets, infra, OAuth, local assets).

## 9. What Is Left (Implementation Work Remaining)

### 9.1 Immediate Build Tasks
1. Scaffold backend modules and settings loader.
2. Create initial DB schema and migration scripts.
3. Implement Google Calendar and Gmail connector stubs.
4. Implement event normalization and reminder pipeline.
5. Implement queue worker and job dispatch flow.

### 9.2 Next Build Tasks
1. Implement OAuth connect/refresh/revoke flow.
2. Build consent APIs and storage model.
3. Build candidate memory write API and basic review endpoints.
4. Build minimal Next.js settings pages.
5. Add policy engine baseline and risk-tier checks.

### 9.3 Advanced MVP Completion Tasks
1. Add meeting action template in dry-run then live-confirm mode.
2. Add action audit logging and replay view.
3. Add fallback model router with timeout policies.
4. Add acceptance tests for reminder, action safety, and memory audit.
5. Harden error handling, retries, and observability.

## 10. Implementation Start Slice (First Commit Scope)

### 10.1 Slice Goal
Create a runnable service foundation proving ingestion-to-reminder flow without desktop execution yet.

### 10.2 Slice Deliverables
1. Health endpoint and app boot.
2. Environment validation for required keys and URLs.
3. Pydantic schemas for Event and TaskSuggestion.
4. Connector stubs for Calendar and Gmail with normalization methods.
5. Reminder job queue and worker task.
6. Persistence for normalized events and generated reminders.

### 10.3 Slice Definition of Done
- Service boots cleanly.
- Mock events normalize successfully.
- Reminder job executes and persists output.
- Logs show end-to-end flow.
- Missing critical env config fails clearly at startup.

## 11. Owner Setup Requirements (Before Coding Session)

1. Provision and confirm PostgreSQL and Redis connection details.
2. Create Google OAuth client and set callback URLs for local and staging.
3. Prepare fallback model API keys (StepFun and NVIDIA).
4. Validate local DeepSeek and CSM assets are accessible for later integration.
5. Prepare encryption key and local secret storage method.

## 12. Suggested Next Session Startup Prompt

Use this in the next session to continue immediately:
- Implement Lockd'In MVP slice 1 using FastAPI, PostgreSQL, Redis, and Celery.
- Create backend scaffolding, config validation, Event and TaskSuggestion schemas, Google Calendar and Gmail connector stubs, event normalization, and reminder queue job.
- Add initial migrations and repository layer.
- Keep all action execution in non-desktop mode for now.
- Include a simple test proving normalization and reminder creation.

## 13. Continuity Notes

- Current state is planning-complete and implementation-ready.
- Agreed stack selections are already decided: Celery + Redis, Next.js.
- MVP success depends on trust controls being built with core logic, not postponed.
- Do not broaden automation scope before meeting-flow safety and memory-audit baseline are proven.
