# AcadMind — System Architecture

## Overview

AcadMind is a unified agentic AI platform combining:

1. **Query Assistant** — institutional knowledge retrieval via RAG + Neo4j
2. **Jarvis (Memory Assistant)** — screenshot OCR, event extraction, reminders

Both modules share Neo4j (knowledge graph), Supabase (auth + relational data), and a FastAPI agent orchestration layer.

```
┌─────────────────────────────────────────────────────────────────┐
│                     React + Vite Frontend                        │
│  ┌──────────────────────┐    ┌──────────────────────────────┐ │
│  │  Query Assistant UI  │    │  Jarvis UI (upload + calendar)│ │
│  └──────────┬───────────┘    └──────────────┬───────────────┘ │
└─────────────┼────────────────────────────────┼─────────────────┘
              │ REST / WebSocket               │
┌─────────────▼────────────────────────────────▼─────────────────┐
│                      FastAPI Backend                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌────────────────┐ │
│  │ Query Crew      │  │ Jarvis Crew     │  │ Reminder Worker│ │
│  │ (LangChain/     │  │ (OCR → Extract  │  │ (Celery/APSched)│ │
│  │  CrewAI)        │  │  → Memory)      │  │                │ │
│  └────────┬────────┘  └────────┬────────┘  └───────┬────────┘ │
└───────────┼────────────────────┼───────────────────┼───────────┘
            │                    │                   │
     ┌──────▼──────┐      ┌──────▼──────┐     ┌──────▼──────┐
     │   Neo4j     │      │  Supabase   │     │    Redis    │
     │ (Graph KG)  │      │ (PG + Auth) │     │  (Task Q)   │
     └─────────────┘      └─────────────┘     └─────────────┘
            │
     ┌──────▼──────┐
     │ FAISS /     │
     │ pgvector    │
     └─────────────┘
```

## Layer Responsibilities

| Layer | Responsibility |
|-------|----------------|
| **Presentation** | Chat UI, screenshot upload, event dashboard, notifications |
| **API Gateway** | Auth (JWT), routing, validation, rate limits |
| **Agent Orchestration** | CrewAI crews, LangChain chains, tool invocation |
| **Knowledge** | Neo4j graph schema, vector embeddings, RAG retrieval |
| **Persistence** | Supabase profiles, chat logs, notification history |
| **Background** | Reminder escalation, graph refresh, scheduled jobs |

## Unified Knowledge Graph (Neo4j)

### Institutional entities (Query Assistant)
- `Department`, `Subject`, `Faculty`, `Exam`, `Rule`, `Timetable`, `Student`

### Personal entities (Jarvis)
- `User`, `Event`, `Date`, `Source`, `Reminder`

### Cross-module relationships
- `(Event)-[:BELONGS_TO]->(Subject)`
- `(Subject)-[:TAUGHT_BY]->(Faculty)`
- `(Student)-[:ENROLLED_IN]->(Subject)`
- `(User)-[:HAS_EVENT]->(Event)`

## Backend Module Layout

```
backend/app/
├── api/v1/           # HTTP routes (thin controllers)
├── agents/
│   ├── query/        # Query Answering, Context Retrieval, Notification
│   └── jarvis/       # Image, Extraction, Memory, Reminder, NL Query
├── core/             # Security, logging, exceptions
├── db/               # Neo4j, Supabase clients
├── models/           # Pydantic schemas
└── services/         # Business logic (graph writes, dedup, reminders)
```

## Design Principles

1. **Thin routes, fat services** — agents and services hold logic; routes only validate I/O.
2. **Shared graph, separate crews** — one Neo4j instance; module-specific agent pipelines.
3. **Provider abstraction** — LLM (Gemini vs OpenAI vs Ollama), OCR (Tesseract vs EasyOCR) swappable via config.
4. **Fail gracefully** — health checks report dependency status; degraded mode when Neo4j/LLM unavailable.
5. **Phase-gated features** — each phase delivers a runnable vertical slice.

## Security

- Supabase Auth JWT validated on protected routes
- Role-based access: `student` | `faculty` | `admin`
- File uploads: size limits, MIME validation, virus scan hook (future)
- Secrets only in `.env` (never committed)
