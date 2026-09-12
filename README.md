# SOPIQ
> *"Your company's private AI knowledge and SOP agent."*

[![Tests](https://img.shields.io/badge/tests-34%20passed-emerald)](tests/)
[![Security](https://img.shields.io/badge/security-zero--cloud--data-blue)](docs/privacy.md)
[![Architecture](https://img.shields.io/badge/architecture-control%20plane%20%2B%20private%20agent-indigo)](docs/architecture.md)

---

## What is SOPIQ?
**SOPIQ** is a production-quality, privacy-first enterprise AI platform that converts company meetings, recordings, documents, policies, and internal handoffs into a searchable, continuously improving company knowledge base.

Unlike standard chatbots that simply answer from a folder of uploaded documents, **SOPIQ continuously maintains your company's Standard Operating Procedures (SOPs)**:
1. Managers and employees explain how processes work in weekly meetings.
2. The AI transcribes the audio locally, detects process changes (*"From now on...", "Instead of...", "Finance Lead approves now"*), flags contradictions with existing SOPs, and generates draft SOP updates.
3. Department Leads review, diff, and approve updates with one click.
4. Employees ask natural language questions and receive grounded answers backed by traceable citations (linking to exact SOP steps, document pages, and meeting timestamps).

---

## Core Privacy Architecture
**Company data must never leave your private infrastructure by default.**

- **RankPilot Hosted Control Plane (`apps/control-api`, `apps/web`)**: Manages tenant metadata, user accounts, agent enrollment, and health heartbeats. It strictly enforces a zero-knowledge firewall that blocks any incoming company recordings, transcripts, documents, chunks, or queries.
- **RankPilot Private Agent (`agent/`)**: Installed inside your VPC or on-premise infrastructure. Performs all transcription (Whisper), document parsing (PDF, DOCX, TXT, CSV, PPTX), secret redaction, chunking, embeddings, pgvector storage, conflict detection, and RAG Q&A.

---

## Repository Monorepo Structure

```
sopiq/
├── apps/
│   ├── web/                     # Enterprise Next.js + React Web Console
│   │   ├── src/app/             # 19 App Router pages (Dashboard, Chat, SOPs, etc.)
│   │   └── server.py            # Standalone browser-ready server on port 3000
│   └── control-api/             # Hosted Cloud Control Plane (FastAPI)
│       ├── main.py              # Auth, Tenants, Agents, and Privacy Guard
│       └── server.py            # Server runner on port 8000
├── agent/                       # Private Agent (Customer Infrastructure)
│   ├── main.py                  # Private Agent server on port 8001 (/internal/v1/...)
│   ├── config.py                # Environment & Egress settings
│   ├── security/                # Secret scanner, path traversal, prompt injection defense
│   ├── egress/                  # Data Egress Policy Gate (PRIVATE_ONLY)
│   ├── storage/                 # Multi-tenant local SQLite/Postgres + vector DB
│   ├── parsing/                 # Parsers for PDF, DOCX, TXT, MD, CSV, PPTX
│   ├── chunking/                # Provenance chunker (page, section, char offsets)
│   ├── embeddings/              # Normalized vector embeddings & cosine similarity
│   ├── transcription/           # Local Whisper provider & timestamped segments
│   ├── meetings/                # Meeting ingestion & process change intelligence
│   ├── sop/                     # SOP generation, approval, scoring, and version diffs
│   ├── knowledge/               # Knowledge conflict engine & knowledge gap detector
│   ├── workflows/               # React Flow visual graph generator
│   └── rag/                     # Grounded Q&A with verifiable citations
├── packages/
│   ├── shared/                  # RBAC permissions, constants, enums
│   ├── schemas/                 # Data models (Tenant, SOP, Meeting, Citation, etc.)
│   └── prompts/                 # Versioned prompt templates
├── infra/
│   ├── docker/                  # Dockerfiles for Control Plane, Agent, and Web
│   └── scripts/                 # Demo seed script
├── docs/                        # Complete documentation suite
│   ├── architecture.md
│   ├── privacy.md
│   ├── security.md
│   ├── threat-model.md
│   ├── deployment.md
│   └── api.md
├── tests/                       # 34 Automated unit, security, integration, and RAG tests
│   ├── security/
│   ├── unit/
│   ├── integration/
│   └── rag/
├── docker-compose.yml           # Unified local Docker orchestration
├── .env.example                 # Environment configuration template
└── README.md
```

---

## Quickstart & Demo Setup

### 1. Run Automated Tests
Execute the automated test suite across tenant isolation, RBAC, secret redaction, prompt injection defense, data egress blocks, and RAG citations:
```bash
python3 -m unittest discover -s tests -t . -v
```
*(All 34 tests pass with 100% success).*

### 2. Seed Demo Data (Acme Technologies)
Seed the complete demonstration company, users, meetings, documents, SOPs, and knowledge gaps:
```bash
python3 infra/scripts/seed.py
```

### 3. Launch Services Locally
You can launch the stack using Docker Compose:
```bash
docker compose up -d
```

Or run directly with Python 3:
```bash
# Terminal 1: Control Plane
python3 apps/control-api/server.py

# Terminal 2: Private Agent (Customer Perimeter)
python3 agent/main.py

# Terminal 3: Web Console
python3 apps/web/server.py
```

Open your browser to: **`http://localhost:3000`**.

---

## Demo Walkthrough Story

1. **Open Dashboard**: View Acme Technologies knowledge base (Documents, Transcripts, 100/100 Completeness SOPs, Agent status `ONLINE`).
2. **Verify Privacy Center**: Open `/settings/privacy` to confirm:
   - Raw Company Data to Cloud: **NO**
   - Local Vector Database: **YES**
   - Local Transcription & AI: **YES**
   - Data Egress Mode: **`PRIVATE_ONLY`**
3. **Inspect Meeting**: View the *Operations Weekly Sync* transcript. Notice clickable timestamps (`00:00`, `00:45`) and extracted process change: *"Finance Lead now approves invoices instead of Finance Manager"*.
4. **Inspect Conflict Alert**: The conflict engine detects that earlier documentation specified *Finance Manager*, while the new meeting assigned *Finance Lead*. Review and resolve with one click.
5. **Inspect SOP & Workflow**: Open *New Client Onboarding SOP*. View the interactive visual workflow graph and side-by-side version diff (v1 vs v2).
6. **Ask AI Assistant (`/chat`)**:
   - Query: *"What should I do after KYC verification?"*
   - Grounded Response: Proceed to Step 4: Invoice Generation & Approval (Finance Lead sign-off), followed by account activation.
   - Citations: Shows Step 4 of the SOP, KYC Guidelines, and Meeting Decisions.
   - Query: *"What changed recently?"*
   - Response: Details the reassignment of invoice approval to the Finance Lead.
   - Query unmentioned topic (*"How do I launch a lunar satellite?"*): Returns safe uncertainty fallback and logs a **Knowledge Gap**.
7. **Personalized Onboarding**: Open `/onboarding` to view the Day 1-7 curriculum and checklists tailored for *Sales Operations*.

---

## Demo Credentials
- **Executive / Admin**: `admin@acme.corp` (Password: `AcmePass123!`)
- **Operations Manager**: `sarah.manager@acme.corp` (Password: `AcmePass123!`)
- **Knowledge Manager**: `david.km@acme.corp` (Password: `AcmePass123!`)
- **Employee (Sales Ops)**: `yash@acme.corp` (Password: `AcmePass123!`)
- **Finance Lead**: `elena.finance@acme.corp` (Password: `AcmePass123!`)
