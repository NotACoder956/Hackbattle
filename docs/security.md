# SOPIQ Security Specification & Controls

## 1. Multi-Tenancy & Data Isolation
- **Tenant Context Derivation**: The tenant identifier (`tenant_id`) is derived strictly from verified credentials (JWT claims or machine agent tokens). Client-supplied `tenant_id` query parameters or JSON body fields are never trusted for authorization.
- **Repository Scope Guarantee**: Every query accessing documents, chunks, embeddings, meetings, SOPs, or conversations includes `WHERE tenant_id = ?`. There are zero unscoped `get_by_id` or `list_all` methods in the database layer.

---

## 2. Server-Side Role-Based Access Control (RBAC)
Role permissions are evaluated exclusively on the server/agent side. UI visibility toggles are convenience only and do not constitute security boundaries.

- **OWNER**: Full administrative, user, tenant, and agent management.
- **ADMIN**: Manages company configuration, users, agents, and knowledge sources.
- **MANAGER**: Uploads operational documents, creates meetings, approves SOPs, and reviews conflicts.
- **KNOWLEDGE_MANAGER**: Curates SOP versions, categorizes documents, and resolves knowledge gaps.
- **EMPLOYEE**: Asks AI questions, views approved department SOPs and onboarding curriculums.
- **VIEWER**: Read-only access to published department content.

---

## 3. Pre-Retrieval Scoping & Department Access Control
Before vector cosine similarity or full-text search is executed, the candidate knowledge set is restricted:
- Knowledge scope levels: `PUBLIC_COMPANY`, `DEPARTMENT`, `TEAM`, `ROLE`, `PRIVATE`.
- An employee in *Sales Operations* cannot retrieve confidential *Finance* or *Legal* chunks.
- Chunks classified as `HIGHLY_CONFIDENTIAL` are never retrieved during regular employee chat sessions.
- Citations undergo an additional secondary authorization check before rendering to the user.

---

## 4. Secret Detection & Automatic Redaction
Before any parsed document or meeting transcript is chunked or embedded into vectors, it passes through the `SecretDetector`:
- Identifies AWS Access Keys (`AKIA...`), AWS Secret Keys, OpenAI API keys (`sk-...`), GitHub personal access tokens (`ghp_...`), Slack tokens (`xoxb-...`), database connection strings with passwords, and private RSA/EC keys.
- Detected secrets are automatically replaced with `[REDACTED_...]` placeholders.
- A `SECRET_DETECTED` audit event is recorded without writing the secret string to logs.

---

## 5. Untrusted Content & Prompt Injection Defense
- Uploaded PDFs, Word documents, and transcripts are treated as **untrusted data**.
- All retrieved context provided to the LLM is isolated inside delimited tags: `<untrusted_company_content>`.
- System instructions explicitly mandate that text within untrusted blocks cannot override system behavior, modify permissions, or alter security policies.
- Adversarial phrases (e.g. *"Ignore previous instructions"*, *"System prompt override"*) are suppressed prior to prompt assembly.

---

## 6. File & Path Traversal Protections
- **Filename Sanitization**: Normalizes slashes, strips parent directory traversal (`..`), and removes illegal characters.
- **Path Confinement**: Asserts that resolved absolute storage paths remain strictly inside the configured `STORAGE_PATH` root.
- **MIME & Size Validation**: Verifies allowable extensions (`pdf`, `docx`, `txt`, `md`, `csv`, `pptx`, `mp3`, `wav`, `m4a`, `mp4`, `webm`) and enforces `MAX_FILE_SIZE` (default: 50 MB) and `MAX_AUDIO_DURATION` (default: 4 hours).
