# SOPIQ Architecture Documentation

## 1. Executive Summary
**SOPIQ** ("Your company's private AI knowledge and SOP agent") is built from the ground up on a **privacy-first enterprise architecture**. 

Unlike conventional SaaS AI platforms where corporate files and confidential recordings are uploaded to a shared vendor cloud, SOPIQ cleanly splits platform responsibilities into two decoupled tiers:
1. **RankPilot Hosted Control Plane**: Manages tenant identity, user licensing, agent enrollment tokens, configuration synchronization, and minimal non-sensitive telemetry.
2. **RankPilot Private Agent**: A self-contained Dockerized software package deployed directly inside the customer's private infrastructure (VPC, private subnet, or on-premise server).

```
 CUSTOMER PRIVATE INFRASTRUCTURE (VPC / On-Premise)
 ┌─────────────────────────────────────────────────────────────────────────┐
 │                                                                         │
 │  Employee Browser / Company Internal Apps                              │
 │       │                                                                 │
 │       ▼ (Internal Network / TLS)                                        │
 │  ┌───────────────────────────────────────────────────────────────────┐  │
 │  │ SOPIQ PRIVATE AGENT (Internal API /internal/v1)                  │  │
 │  │                                                                   │  │
 │  │  ┌──────────────┐   ┌──────────────┐   ┌───────────────────────┐  │  │
 │  │  │ Doc Parsers  │   │ Local Whisper│   │ Secret Scanner        │  │  │
 │  │  │ PDF/DOCX/CSV │   │ Engine       │   │ & Egress Gate         │  │  │
 │  │  └──────┬───────┘   └──────┬───────┘   └───────────┬───────────┘  │  │
 │  │         │                  │                       │              │  │
 │  │  ┌──────▼──────────────────▼───────────────────────▼───────────┐  │  │
 │  │  │ Ingestion & Chunking Engine (Provenance & Sensitive Scopes) │  │  │
 │  │  └──────┬──────────────────────────────────────────────────────┘  │  │
 │  │         │                                                         │  │
 │  │  ┌──────▼──────────────────────────────────────────────────────┐  │  │
 │  │  │ Vector & Full-Text Store (pgvector / Local Embedding DB)    │  │  │
 │  │  └──────┬──────────────────────────────────────────────────────┘  │  │
 │  │         │                                                         │  │
 │  │  ┌──────▼──────────────────────────────────────────────────────┐  │  │
 │  │  │ RAG & SOP Intelligence Engine (Conflict / Version / Gaps)   │  │  │
 │  │  └──────┬──────────────────────────────────────────────────────┘  │  │
 │  │         │                                                         │  │
 │  │  ┌──────▼──────────────────────────────────────────────────────┐  │  │
 │  │  │ Local LLM Provider (Ollama / Local Server / Strict Defense) │  │  │
 │  │  └─────────────────────────────────────────────────────────────┘  │  │
 │  └──────────────────────────────────┬────────────────────────────────┘  │
 │                                     │ Outbound-only Heartbeat & Config  │
 └─────────────────────────────────────┼───────────────────────────────────┘
                                       │ (TLS, Minimal Metrics, No Data)
                                       ▼
 CENTRAL CONTROL PLANE (Cloud Hosted)
 ┌─────────────────────────────────────────────────────────────────────────┐
 │  SOPIQ Cloud Control API (/api/v1) & Global Management Web App          │
 │  - Tenant Accounts & RBAC                                               │
 │  - Agent Enrollment, Tokens & Heartbeat Health Monitor                  │
 │  - Config Dispatch & Minimal Audit Telemetry                            │
 └─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Component Boundaries

### A. Central Control Plane (`apps/control-api`)
- **Location**: Hosted by vendor in cloud.
- **Data Stored**:
  - Tenant ID, name, corporate domain, active subscription tier.
  - User accounts (email, hashed password, assigned role, department).
  - Agent registrations (agent ID, version, status, enrollment tokens, last heartbeat timestamp).
  - Non-sensitive operational audit logs (e.g. `USER_LOGIN`, `AGENT_REGISTERED`).
- **Privacy Firewall**: Intercepts and rejects any payload containing raw document text, chunk contents, embeddings, audio files, or employee questions.

### B. Private Agent (`agent/`)
- **Location**: Installed inside customer infrastructure.
- **Capabilities**:
  - **Parsing**: Multi-format extraction for PDF, DOCX, TXT, Markdown, CSV, and PPTX with page and section tracking.
  - **Transcription**: Local Whisper provider supporting diarization and timestamped segments (e.g. `00:14:21`).
  - **Storage**: Multi-tenant local database and pgvector vector store.
  - **SOP Lifecycle**: Draft generation, completeness scoring (0-100), human approval workflows, version snapshots, and visual workflow graphs.
  - **Knowledge Consistency**: Conflict detection engine comparing newly spoken meeting procedures against existing active SOPs.
  - **RAG & Grounding**: Dense vector + BM25 keyword hybrid retrieval, pre-retrieval department filtering, strict grounding verification, and citation links.
  - **Security Gate**: Secret scanner (redacting AWS/OpenAI/database credentials) and outbound Egress Gate (`PRIVATE_ONLY`).

---

## 3. The Continuous SOP Workflow
Unlike traditional knowledge bots that operate as passive search indices, SOPIQ treats meetings and documentation as active process streams:
1. **Ingest**: Company meeting audio or documents uploaded to the local agent.
2. **Transcribe / Parse**: Extracts timestamped speaker segments or structured headings.
3. **Understand**: Identifies transition phrases ("From now on...", "Instead of...", "Finance Lead approves now").
4. **Conflict Check**: Compares detected process changes against existing active SOPs; flags conflicts without silent overwrites.
5. **Draft SOP Generation**: Synthesizes formal procedure with Purpose, Scope, Steps, Decision Points, and Exceptions.
6. **Human Approval**: Department Lead reviews, edits, and approves the SOP.
7. **Grounded Q&A**: Employees query the AI and receive verified answers with clickable citations back to the source step, page, or meeting timestamp.
