# SOPIQ Privacy Model & Guarantees

## 1. The Core Privacy Guarantee
> **SOPIQ is engineered so that customer company knowledge remains inside the customer's private infrastructure by default.**

We make no absolute claims that cannot technically be guaranteed (e.g. "100% unbreakable"), but we provide an architectural model that enforces zero raw company knowledge transmission to vendor servers.

---

## 2. Telemetry vs. Company Knowledge Matrix

| Data Element | Storage Location | Leaves Customer Network? | Control Plane Visibility |
| :--- | :--- | :--- | :--- |
| **Meeting Recordings** | Customer Local Disk / S3 | **NO** | Zero Knowledge |
| **Diarized Transcripts** | Customer Local Database | **NO** | Zero Knowledge |
| **Uploaded Documents (PDF/DOCX/etc.)** | Customer Local Disk | **NO** | Zero Knowledge |
| **Extracted Text Chunks** | Customer Local Database | **NO** | Zero Knowledge |
| **Embedding Vectors** | Customer pgvector / SQLite | **NO** | Zero Knowledge |
| **Employee Inquiries & Chat Q&A** | Customer Local Database | **NO** | Zero Knowledge |
| **Generated SOP Procedures** | Customer Local Database | **NO** | Zero Knowledge |
| **Detected Conflict Details** | Customer Local Database | **NO** | Zero Knowledge |
| **Agent Heartbeat (ID, Version, Status)**| Control Plane Cloud DB | **YES (Minimal)** | Status & Uptime Only |
| **Tenant Account Metadata** | Control Plane Cloud DB | **YES** | Organization Name, Domain |
| **User Authentication Accounts** | Control Plane Cloud DB | **YES** | Email, Hashed Password |

---

## 3. Data Egress Policy Engine
The Private Agent enforces an outbound data egress policy gate before any external network connection is initiated.

Modes:
- `PRIVATE_ONLY` (Default): All external network requests to non-loopback addresses are blocked and trigger a security audit event. Localhost AI providers (such as Ollama or local inference servers) are permitted.
- `SANITIZED`: Outbound requests pass through strict regex secret redaction and PII minimization.
- `CUSTOMER_PROVIDER`: Connects strictly to a pre-approved, customer-owned LLM endpoint.
- `REMOTE_PROVIDER`: Explicitly approved remote third-party AI provider with mandatory warning displays in the UI.

### Remote AI Warning Policy
If an administrator switches the agent to use an external AI provider:
1. The UI displays prominent notification: *"Company data may be processed by the configured external AI provider."*
2. If the local or external AI model encounters a failure, the system **FAILS SAFELY**. Under no circumstances will it silently fall back to an unapproved external service.
