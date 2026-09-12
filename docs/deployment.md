# SOPIQ Deployment Guide

## 1. Quickstart with Docker Compose

Deploy the complete multi-service stack (Control Plane, Customer Private Agent, and Web Console) with a single command:

```bash
docker compose up -d
```

Services launched:
- **Control Plane API**: `http://localhost:8000`
- **Private Agent API**: `http://localhost:8001`
- **Web Console Application**: `http://localhost:3000`

---

## 2. Standalone On-Premise Installation

If running without Docker, start services directly using Python 3:

### Step 1: Seed Initial Data
```bash
python3 infra/scripts/seed.py
```

### Step 2: Start Control Plane
```bash
python3 apps/control-api/server.py
```
*(Runs on port 8000)*

### Step 3: Start Private Agent (Inside Company Firewall)
```bash
python3 agent/main.py
```
*(Runs on port 8001)*

### Step 4: Start Web Console
```bash
python3 apps/web/server.py
```
*(Runs on port 3000)*

Open your browser to `http://localhost:3000`.

---

## 3. Customer Agent Enrollment Experience
1. **Log in to Control Plane Web Console** as Admin (`admin@acme.corp`).
2. Navigate to **Agent Deployment** (`/settings/agent`).
3. Click **Generate Enrollment Token** to receive a one-time enrollment secret (`sopq_enr_...`).
4. Run the Private Agent on your internal server:
   ```bash
   docker run -d \
     --name sopiq-agent \
     -e CONTROL_PLANE_URL=https://api.sopiq.ai \
     -e AGENT_ENROLLMENT_TOKEN=sopq_enr_8a7dfa8721c4 \
     -p 8001:8001 \
     sopiq/agent:1.0.4
   ```
5. The agent initiates an outbound TLS handshake, exchanges the enrollment token for an authenticated machine key, and displays **ONLINE** in the dashboard.
6. Begin ingesting confidential company documents and recordings without data ever leaving your firewall.
