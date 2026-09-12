# SOPIQ API Specification

SOPIQ maintains two completely decoupled APIs with strict network and architectural separation.

---

## 1. Hosted Control Plane API (`/api/v1`)
Hosted in the cloud. Manages tenant metadata, agent lifecycles, and user accounts. Rejects raw company data.

### Authentication & Tenants
- `POST /api/v1/auth/login`
  - Body: `{"email": "...", "password": "..."}`
  - Returns: JWT session token and sanitized user profile.
- `POST /api/v1/tenants`
  - Body: `{"name": "...", "domain": "...", "admin_email": "...", "admin_password": "..."}`
  - Registers new enterprise tenant organization and default administrator.

### Agent Management
- `POST /api/v1/agents/enroll` (Admin only)
  - Body: `{"tenant_id": "...", "name": "Agent-Name"}`
  - Issues a short-lived `enrollment_token`.
- `POST /api/v1/agents/register` (Agent only)
  - Body: `{"enrollment_token": "...", "version": "1.0.4", "capabilities": [...]}`
  - Returns authenticated machine secret `auth_token`.
- `POST /api/v1/agents/heartbeat` (Agent only)
  - Body: `{"agent_id": "...", "auth_token": "...", "version": "1.0.4"}`
  - Reports uptime and checks for configuration jobs. Blocks company documents/transcripts.
- `POST /api/v1/agents/{id}/revoke` (Admin only)
  - Body: `{"tenant_id": "..."}`
  - Immediately invalidates agent access. Subsequent heartbeats return HTTP 403.

---

## 2. Private Knowledge API (`/internal/v1`)
Exposed strictly inside the customer's private perimeter (VPC / On-Premise). Handles all confidential company intelligence.

### Documents & Ingestion
- `POST /internal/v1/documents/upload`
  - Headers: `X-Tenant-ID`, `X-User-Role`, `X-User-Department`, `X-User-Email`
  - Body: `{"filename": "guide.pdf", "content": "...", "classification": "INTERNAL", "department": "Operations"}`
  - Performs secret redaction, text extraction, chunking, and embedding generation.
- `GET /internal/v1/documents`
  - Returns authorized document catalog for caller's department.
- `DELETE /internal/v1/documents/{id}`
  - Cascades deletion of document, derived chunks, and vector embeddings.

### Meetings & Transcription
- `POST /internal/v1/meetings/upload`
  - Body: `{"title": "Sync", "transcript_or_audio": "...", "participants": [...]}`
  - Transcribes audio, extracts decisions, and detects potential SOP process changes.
- `POST /internal/v1/meetings/{id}/generate-sop`
  - Synthesizes structured draft SOP with completeness scoring.

### SOP Management
- `GET /internal/v1/sops`
  - Returns active and draft company SOPs.
- `GET /internal/v1/sops/{id}/workflow`
  - Returns React Flow-compatible graph of nodes, steps, and decision points.
- `GET /internal/v1/sops/{id}/diff`
  - Headers: `X-Old-Version: v1`, `X-New-Version: v2`
  - Returns side-by-side comparison of procedural changes.
- `POST /internal/v1/sops/{id}/approve` (Manager/Admin only)
  - Transitions SOP status from `DRAFT` to `APPROVED`.

### AI Questions & Citations
- `POST /internal/v1/questions`
  - Body: `{"question": "What should I do after KYC verification?", "conversation_id": "..."}`
  - Executes hybrid retrieval (vector + keyword) with pre-retrieval department filtering, generates grounded answer, and returns structured citations.
  - Automatically logs repeated unanswered inquiries as **Knowledge Gaps**.

### Governance & Conflicts
- `GET /internal/v1/conflicts`
  - Returns detected contradictions between newly spoken meeting statements and existing SOPs.
- `POST /internal/v1/conflicts/{id}/resolve`
  - Resolves conflict status after human review.
- `GET /internal/v1/knowledge-gaps`
  - Returns ranked list of frequent unanswered queries to guide SOP creation.
- `GET /internal/v1/onboarding`
  - Returns personalized Day 1-7 curriculum, checklists, systems, and essential SOPs.
