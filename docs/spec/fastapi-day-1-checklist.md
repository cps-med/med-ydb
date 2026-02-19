# FastAPI Day 1 Checklist (med-ydb)

## Purpose

Day 1 setup plan for starting the FastAPI + HTMX + Jinja2 app in the `vehu-311` container, with the first feature mapped from `cli/01_env_check.py`.

This document is intentionally task-oriented and will expand as development progresses.

## Scope (Day 1)

1. Confirm baseline runtime/dependency assumptions for containerized FastAPI development.
2. Define initial app structure under `app/`.
3. Stand up a minimal FastAPI app that runs in `vehu-311` and is reachable from host browser.
4. Define the first feature contract for Env Check (without implementing full feature yet).
5. Identify immediate follow-up tasks for Day 2+.

## Assumptions

1. Container: `vehu-311`
2. Image: `med-ydb-vista-dev`
3. App port: `8010` (mapped in compose)
4. Development mode: run uvicorn inside container and access from host browser.
5. Initial feature target: `cli/01_env_check.py`

## Current Status Snapshot (2026-02-18)

Current `app/` structure detected:

- `app/__init__.py`
- `app/config.py`
- `app/main.py`
- `app/models/`
- `app/routes/`
- `app/services/`
- `app/static/`
- `app/templates/`

Status by Day 1 section:

1. Align App Structure: `IN PROGRESS`
   - Existing structure is close, but naming is not yet aligned with final convention (`routes/` exists, target is `routers/`).
   - `models/` exists and should be explicitly included in the blueprint.
2. Runtime Command Strategy: `PENDING`
   - `app/main.py` comments still reference non-container style local run and port `8005`.
   - Canonical container uvicorn command not yet documented in this spec.
3. Minimal FastAPI Bootstrap: `NOT STARTED`
   - No app instance or routes in `app/main.py` yet.
4. Jinja2 Baseline: `NOT STARTED`
   - `templates/` directory exists, but no template files yet.
5. HTMX Baseline: `NOT STARTED`
6. Env Check Contract: `NOT STARTED`
7. Guardrails: `PARTIALLY DEFINED`
   - Guardrails are listed in checklist, not yet attached to a concrete feature contract.

Immediate next 3 actions:

1. Rename `app/routes/` to `app/routers/` to align with FastAPI `APIRouter` conventions.
2. Update `app/main.py` header comments for containerized uvicorn usage on port `8010` with host browser access at `http://localhost:8010`.
3. Add a minimal FastAPI app instance with a root/health route to complete Day 1 bootstrap baseline.

## Naming Convention Decision (Locked)

Final convention: `app/routers/`

Rationale:

1. Aligns with FastAPI terminology (`APIRouter`) and common project patterns.
2. Improves readability for route registration and feature-based route modules.
3. Scales cleanly as both API and server-rendered page endpoints grow.

Migration note:

- Current directory in workspace: `app/routes/`
- Target directory: `app/routers/`
- Action: migrate before adding first real route module.

## Day 1 Checklist

## 1) Align App Structure

- [x] Confirm current subdirectories under `app/` and map to standard roles.
- [ ] Establish initial folder blueprint:
  - `app/main.py`
  - `app/routers/`
  - `app/models/`
  - `app/services/`
  - `app/templates/`
  - `app/static/` (optional Day 1)
  - `app/config.py` (or equivalent settings module)
- [ ] Decide naming convention for route modules and template files.

Acceptance criteria:
- A clear, documented directory blueprint exists and matches actual folders.

## 2) Define Runtime Command Strategy

- [ ] Standardize the uvicorn run command for container use:
  - `--host 0.0.0.0`
  - `--port 8010`
  - `--reload` for development
- [ ] Confirm host access URL: `http://localhost:8010`
- [ ] Confirm command location and usage notes in project docs.

Acceptance criteria:
- One canonical dev-start command is documented and verified.

## 3) Bootstrap Minimal FastAPI App

- [ ] Create minimal app instance in `app/main.py`.
- [ ] Add root/health route (simple JSON response is sufficient).
- [ ] Validate response from host browser and/or curl.

Acceptance criteria:
- App starts inside container and responds on `http://localhost:8010`.

## 4) Add Jinja2 Template Rendering Baseline

- [ ] Configure template engine.
- [ ] Add one basic page route that renders a template.
- [ ] Add base template scaffold for future HTMX UI.

Acceptance criteria:
- A rendered HTML page loads successfully from browser.

## 5) Add HTMX Baseline Wiring

- [ ] Include HTMX in base template.
- [ ] Add one test interaction (button or link) that fetches a partial.
- [ ] Confirm partial swap works without full page reload.

Acceptance criteria:
- One end-to-end HTMX interaction is working.

## 6) Define Env Check Feature Contract (from `cli/01_env_check.py`)

- [ ] Define service output fields (example):
  - runtime metadata (`cwd`, `python_executable`, `python_version`, `user`)
  - YottaDB metadata (`$ZYRELEASE`)
  - probe target (`probe_global`)
  - probe summary (`root_has_value`, `root_has_subtree`, sampled children)
  - status/errors
- [ ] Define route surfaces:
  - full page route (e.g., `/env-check`)
  - optional HTMX fragment route (e.g., `/partials/env-check`)
- [ ] Decide request input shape (`probe_global` query/form input).

Acceptance criteria:
- Contract is documented before implementation starts.

## 7) Safety + Performance Guardrails

- [ ] Preserve bounded child iteration behavior (sample first 3 only).
- [ ] Keep feature read-only.
- [ ] Define user-facing error handling for YottaDB exceptions.

Acceptance criteria:
- Guardrails are explicitly listed in feature notes and implementation tasks.

## 8) Day 1 Closeout

- [ ] Update this document with what was completed today.
- [ ] Capture blockers and unknowns.
- [ ] Generate Day 2 task list from unchecked items.

Acceptance criteria:
- Next working session can resume from this doc without re-planning.

## Suggested Day 2+ Follow-Up

1. Implement Env Check service module.
2. Implement Env Check route + template.
3. Add HTMX refresh action for Env Check.
4. Add lightweight tests for the service layer.
5. Add logging and structured error responses.

## Document Growth Plan

When this document gets too large, split into:

1. `docs/spec/fastapi-architecture.md`
2. `docs/spec/fastapi-env-check-feature-spec.md`
3. `docs/spec/fastapi-dev-workflow.md`

Keep this file as the execution checklist and link to detailed specs.
