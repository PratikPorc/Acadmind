# AcadMind — Development Phases

## Phase 0 — Foundation

**Status:** ✅ Complete

**Goal:** Runnable monorepo with health checks and dependency wiring.

| Deliverable | Status |
|-------------|--------|
| Monorepo folder structure | ✅ |
| FastAPI skeleton + CORS + config | ✅ |
| Neo4j + Redis via Docker Compose | ✅ |
| React shell (Query + Jarvis nav) | ✅ |
| `.env.example` + setup docs | ✅ |
| Health endpoint (`/api/v1/health`) | ✅ |

**Exit criteria:** `docker compose up`, backend on `:8000`, frontend on `:5173`, health returns OK.

---

## Phase 1 — Auth & User Profiles

**Status:** ✅ Complete

## Phase 2 — Batches, Notices & Query Assistant (Current)

**Status:** ✅ Complete

**Goal:** Faculty manages batches → posts notices → Neo4j seeded → students query graph.

| Deliverable | Status |
|-------------|--------|
| Batch CRUD (faculty) | ✅ |
| Add students by ID, create subjects | ✅ |
| Create post with Gemini parsing | ✅ |
| Neo4j Event/Post/Resource seeding | ✅ |
| Student query from enrolled batches | ✅ |
| Faculty batch tiles UI | ✅ |

## Parallel testing (faculty + student)

Open two tabs with **separate auth sessions**:

| Portal | URL | API prefix |
|--------|-----|------------|
| Faculty | http://localhost:5173/faculty | `/api/v1/faculty/*` |
| Student | http://localhost:5173/student | `/api/v1/student/*` |

Each portal uses its own Supabase storage key, so you can stay logged in as both roles simultaneously.

### Faculty API

| Method | Path |
|--------|------|
| GET | `/api/v1/faculty/me` |
| POST | `/api/v1/faculty/batches` |
| GET | `/api/v1/faculty/batches` |
| GET | `/api/v1/faculty/batches/{id}` |
| POST | `/api/v1/faculty/batches/{id}/subjects` |
| POST | `/api/v1/faculty/batches/{id}/students` |
| GET/POST | `/api/v1/faculty/batches/{id}/posts` |

### Student API

| Method | Path |
|--------|------|
| GET | `/api/v1/student/me` |
| GET | `/api/v1/student/batches` |
| POST | `/api/v1/student/query/chat` |
| POST | `/api/v1/student/jarvis/upload` |

---

**Exit criteria:** Faculty posts "CN exam on 15th July" → student asks "When is CN exam?" → correct answer.

---

## Phase 3 — Jarvis Memory Assistant

**Goal:** Screenshot → structured event in graph.

- Image upload endpoint + storage
- OCR pipeline (EasyOCR/Tesseract + OpenCV preprocess)
- Context Extraction Agent (LLM → Pydantic event model)
- Memory Management Agent (dedup, graph write, link to Subject)
- Event dashboard + calendar view

**Exit criteria:** WhatsApp screenshot upload creates `Event` node with date/subject in Neo4j.

---

## Phase 4 — Unified Graph & NL Query

**Goal:** Cross-domain queries across institutional + personal data.

- Merge graph schemas; cross-module relationship writes
- Jarvis Query Agent (NL-to-Cypher via LangChain)
- Compound queries: "What's due this week for my enrolled subjects?"
- Neo4j Browser seed visualization script

**Exit criteria:** Cross-domain query returns events grouped by faculty.

---

## Phase 5 — Reminders & Notifications

**Goal:** Proactive deadline management.

- Reminder Agent (7d / 1d / 1h escalation)
- Celery + Redis task queue
- Notification Agent (WebSocket + Supabase Realtime)
- Notification center in frontend

**Exit criteria:** Event due in 24h triggers notification; escalation visible in logs.

---

## Phase 6 — Production Hardening

**Goal:** Deployable demo for viva.

- Dockerfiles for API + frontend
- GPT-4 Vision fallback for low-quality OCR
- Integration tests for agent pipelines
- Deploy to Render/Railway + Vercel
- Demo seed script + viva checklist

**Exit criteria:** End-to-end demo from deployed URLs.

---

## Suggested Timeline (6-person team)

| Phase | Duration | Primary owners |
|-------|----------|----------------|
| 0 | Week 1 | Full team (scaffolding) |
| 1 | Week 2 | Backend + Frontend |
| 2 | Weeks 3–4 | Agents + Graph + UI |
| 3 | Weeks 4–5 | OCR + Memory agents |
| 4 | Week 6 | Graph integration |
| 5 | Week 7 | Background jobs |
| 6 | Week 8 | Deploy + polish |
