/**
 * SOPIQ Web Application Client Logic
 * Handles interactive tabs, live queries, SOP workflows, version diffs, and chat.
 */

let currentUser = {
  role: "EMPLOYEE",
  email: "yash@acme.corp",
  name: "Yash Aggarwal",
  department: "Sales Operations"
};

let activeConversationId = "cnv_" + Math.random().toString(36).substring(2, 9);
const TENANT_ID = "ten_0bf7f488ef41";

function getHeaders() {
  return {
    "Content-Type": "application/json",
    "X-Tenant-ID": TENANT_ID,
    "X-User-Role": currentUser.role,
    "X-User-Email": currentUser.email,
    "X-User-Department": currentUser.department
  };
}

// Navigation between views
function navigate(pageId) {
  const pages = ["dashboard", "chat", "sops", "meetings", "documents", "conflicts", "gaps", "onboarding", "privacy", "agent-setup", "audit"];
  pages.forEach(p => {
    const el = document.getElementById("page-" + p);
    const nav = document.getElementById("nav-" + p);
    if (el) el.classList.add("hidden");
    if (nav) nav.classList.remove("nav-active");
  });

  const target = document.getElementById("page-" + pageId);
  const targetNav = document.getElementById("nav-" + pageId);
  if (target) target.classList.remove("hidden");
  if (targetNav) targetNav.classList.add("nav-active");

  const titles = {
    dashboard: "Executive Dashboard",
    chat: "Ask Company AI Assistant",
    sops: "Company Standard Operating Procedures",
    meetings: "Meeting Recordings & Diarized Transcripts",
    documents: "Document Repository & Parsers",
    conflicts: "Knowledge Conflict Review Engine",
    gaps: "Knowledge Gaps & Unanswered Questions",
    onboarding: "Personalized New Hire Portal",
    privacy: "Privacy Architecture & Zero-Knowledge Guarantee",
    "agent-setup": "Private Agent Deployment Wizard",
    audit: "Security Governance & Audit Trail"
  };
  document.getElementById("page-title").innerText = titles[pageId] || "SOPIQ";

  if (pageId === "dashboard") loadDashboardData();
  if (pageId === "sops") loadSOPs();
  if (pageId === "meetings") loadMeetings();
  if (pageId === "documents") loadDocuments();
  if (pageId === "conflicts") loadConflicts();
  if (pageId === "gaps") loadGaps();
  if (pageId === "onboarding") loadOnboarding();
  if (pageId === "audit") loadAudit();
}

function switchUserRole(val) {
  const [role, email, dept] = val.split("|");
  currentUser.role = role;
  currentUser.email = email;
  currentUser.department = dept;

  const names = {
    "yash@acme.corp": "Yash Aggarwal",
    "sarah.manager@acme.corp": "Sarah Jenkins",
    "david.km@acme.corp": "David Miller",
    "admin@acme.corp": "Administrator"
  };
  currentUser.name = names[email] || "User";

  document.getElementById("header-user-name").innerText = currentUser.name;
  document.getElementById("header-user-dept").innerText = `${currentUser.department} • ${currentUser.role}`;

  alert(`Switched active identity to: ${currentUser.name} (${currentUser.role})`);
  loadDashboardData();
}

// ----------------- DASHBOARD -----------------
async function loadDashboardData() {
  try {
    const resSops = await fetch("/internal/v1/sops", { headers: getHeaders() });
    const dataSops = await resSops.json();
    const sops = dataSops.sops || [];

    const resMeetings = await fetch("/internal/v1/meetings", { headers: getHeaders() });
    const dataMeetings = await resMeetings.json();
    const meetings = dataMeetings.meetings || [];

    const resDocs = await fetch("/internal/v1/documents", { headers: getHeaders() });
    const dataDocs = await resDocs.json();
    const docs = dataDocs.documents || [];

    const resConflicts = await fetch("/internal/v1/conflicts", { headers: getHeaders() });
    const dataConflicts = await resConflicts.json();
    const conflicts = dataConflicts.conflicts || [];

    const resGaps = await fetch("/internal/v1/knowledge-gaps", { headers: getHeaders() });
    const dataGaps = await resGaps.json();
    const gaps = dataGaps.knowledge_gaps || [];

    document.getElementById("dash-sops-count").innerText = sops.length;
    document.getElementById("dash-meetings-count").innerText = meetings.length;
    document.getElementById("dash-docs-count").innerText = docs.length;
    document.getElementById("dash-conflicts-count").innerText = conflicts.length;

    // Render Recent SOPs
    const sopList = document.getElementById("dash-sops-list");
    sopList.innerHTML = sops.map(s => `
      <div class="p-4 flex items-center justify-between hover:bg-slate-50 transition">
        <div class="space-y-1">
          <div class="flex items-center gap-2">
            <span class="font-bold text-slate-900">${s.title}</span>
            <span class="text-xs bg-slate-100 text-slate-700 px-2 py-0.5 rounded font-mono font-semibold">${s.version}</span>
            <span class="text-xs ${s.status === 'APPROVED' ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'} px-2 py-0.5 rounded font-semibold">${s.status}</span>
          </div>
          <p class="text-xs text-slate-500">${s.purpose}</p>
        </div>
        <div class="text-right flex items-center gap-4">
          <div class="text-xs">
            <div class="font-bold text-emerald-600">${s.completeness_score}/100</div>
            <div class="text-[10px] text-slate-400">Score</div>
          </div>
          <button onclick="navigate('sops')" class="text-xs text-sky-600 hover:text-sky-700 font-semibold">Inspect &rarr;</button>
        </div>
      </div>
    `).join("") || `<div class="p-4 text-xs text-slate-400">No SOPs found.</div>`;

    // Render Knowledge Gaps
    const gapsList = document.getElementById("dash-gaps-list");
    gapsList.innerHTML = gaps.slice(0, 3).map(g => `
      <div class="p-3 bg-amber-50/60 border border-amber-200/60 rounded-lg space-y-1">
        <div class="flex items-center justify-between">
          <span class="text-xs font-bold text-slate-800">${g.question}</span>
          <span class="text-[10px] bg-amber-200 text-amber-900 font-bold px-1.5 py-0.5 rounded">${g.frequency}x Asked</span>
        </div>
        <div class="text-[11px] text-amber-800"><i class="fa-solid fa-arrow-right text-[9px]"></i> ${g.recommended_action}</div>
      </div>
    `).join("");

  } catch (err) {
    console.error("Failed to load dashboard data:", err);
  }
}

// ----------------- CHAT & AI INQUIRIES -----------------
function submitPrompt(text) {
  document.getElementById("chatInput").value = text;
  handleChatSubmit(new Event("submit"));
}

async function handleChatSubmit(e) {
  e.preventDefault();
  const input = document.getElementById("chatInput");
  const query = input.value.trim();
  if (!query) return;
  input.value = "";

  const chatContainer = document.getElementById("chat-messages");

  // Append user bubble
  chatContainer.innerHTML += `
    <div class="flex justify-end gap-4 max-w-3xl ml-auto">
      <div class="bg-slate-900 text-white rounded-2xl rounded-tr-sm p-4 text-sm leading-relaxed shadow-sm">
        ${query}
      </div>
      <div class="w-8 h-8 rounded-full bg-slate-700 text-white flex items-center justify-center shrink-0 text-xs font-bold">
        YA
      </div>
    </div>
  `;
  chatContainer.scrollTop = chatContainer.scrollHeight;

  // Append thinking bubble
  const thinkingId = "think_" + Date.now();
  chatContainer.innerHTML += `
    <div id="${thinkingId}" class="flex gap-4 max-w-3xl">
      <div class="w-8 h-8 rounded-full bg-sky-600 text-white flex items-center justify-center shrink-0 text-sm font-bold animate-pulse">
        AI
      </div>
      <div class="bg-slate-100 rounded-2xl rounded-tl-sm p-4 text-sm text-slate-500 italic">
        Searching local vector store and grounded SOPs inside private agent...
      </div>
    </div>
  `;
  chatContainer.scrollTop = chatContainer.scrollHeight;

  try {
    const res = await fetch("/internal/v1/questions", {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify({
        question: query,
        conversation_id: activeConversationId
      })
    });
    const data = await res.json();
    document.getElementById(thinkingId).remove();

    const msg = data.message || {};
    const content = msg.content || "Unable to answer.";
    const citations = msg.citations || [];
    const confidence = msg.confidence || "High";

    // Format citations badge
    const badgeColor = confidence === "High" ? "bg-emerald-100 text-emerald-800" : (confidence === "Low" ? "bg-amber-100 text-amber-800" : "bg-rose-100 text-rose-800");

    chatContainer.innerHTML += `
      <div class="flex gap-4 max-w-3xl">
        <div class="w-8 h-8 rounded-full bg-sky-600 text-white flex items-center justify-center shrink-0 text-sm font-bold shadow-sm">
          AI
        </div>
        <div class="bg-slate-100 rounded-2xl rounded-tl-sm p-4 text-sm text-slate-800 leading-relaxed shadow-2xs space-y-3">
          <div class="flex items-center justify-between">
            <span class="text-[11px] uppercase tracking-wider font-bold text-slate-400">Grounded Company Knowledge</span>
            <span class="text-[10px] font-bold px-2 py-0.5 rounded-full ${badgeColor}">${confidence} Confidence</span>
          </div>
          <p class="whitespace-pre-line text-slate-900">${content}</p>
          <div class="pt-2 flex items-center justify-between border-t border-slate-200 text-xs text-slate-500">
            <div class="flex items-center gap-2">
              <span>Was this answer helpful?</span>
              <button onclick="alert('Feedback recorded: Helpful')" class="hover:text-emerald-600 px-1.5 py-0.5 rounded hover:bg-emerald-50"><i class="fa-solid fa-thumbs-up"></i></button>
              <button onclick="alert('Feedback recorded: Not helpful')" class="hover:text-rose-600 px-1.5 py-0.5 rounded hover:bg-rose-50"><i class="fa-solid fa-thumbs-down"></i></button>
            </div>
            <button onclick="navigator.clipboard.writeText('${content.replace(/\n/g, ' ')}')" class="hover:text-sky-600"><i class="fa-solid fa-copy"></i> Copy</button>
          </div>
        </div>
      </div>
    `;
    chatContainer.scrollTop = chatContainer.scrollHeight;

    // Render citations on the right panel
    const citContainer = document.getElementById("active-citations");
    if (citations.length > 0) {
      citContainer.innerHTML = citations.map((c, i) => `
        <div class="p-3 bg-slate-50 border border-slate-200 rounded-xl space-y-1.5 shadow-2xs hover:border-sky-300 transition">
          <div class="flex items-center justify-between text-xs font-bold text-slate-800">
            <span class="truncate">${i+1}. ${c.source_title}</span>
            <span class="text-[10px] bg-sky-100 text-sky-800 px-1.5 py-0.5 rounded font-mono">${c.reference}</span>
          </div>
          <p class="text-[11px] text-slate-600 italic bg-white p-2 rounded border border-slate-100">${c.snippet}</p>
          <div class="text-[10px] text-slate-400 flex items-center justify-between">
            <span>Score: ${Math.round(c.confidence * 100)}%</span>
            <span class="text-sky-600 font-semibold cursor-pointer" onclick="navigate('sops')">Open Source &rarr;</span>
          </div>
        </div>
      `).join("");
    } else {
      citContainer.innerHTML = `
        <div class="p-3 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-800 space-y-1">
          <div class="font-bold"><i class="fa-solid fa-triangle-exclamation"></i> No Source Found</div>
          <p>This query lacked direct supporting evidence in the company knowledge base and was logged as a Knowledge Gap.</p>
        </div>
      `;
    }

  } catch (err) {
    console.error("Chat error:", err);
  }
}

// ----------------- SOPS & WORKFLOWS -----------------
async function loadSOPs() {
  try {
    const res = await fetch("/internal/v1/sops", { headers: getHeaders() });
    const data = await res.json();
    const sops = data.sops || [];

    const container = document.getElementById("sops-container");
    container.innerHTML = sops.map(s => `
      <div class="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-6">
        <!-- Header -->
        <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-100 pb-5">
          <div class="space-y-1">
            <div class="flex items-center gap-3">
              <h3 class="text-xl font-bold text-slate-900">${s.title}</h3>
              <span class="bg-slate-100 text-slate-800 text-xs font-mono font-bold px-2.5 py-1 rounded-md">${s.version}</span>
              <span class="text-xs ${s.status === 'APPROVED' ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'} font-bold px-2.5 py-1 rounded-full">${s.status}</span>
            </div>
            <p class="text-sm text-slate-500">${s.purpose}</p>
          </div>
          <div class="flex items-center gap-3">
            <div class="text-right">
              <div class="text-xs text-slate-400">Completeness</div>
              <div class="text-lg font-extrabold text-emerald-600">${s.completeness_score}/100</div>
            </div>
            ${s.status !== 'APPROVED' ? `
              <button onclick="approveSOP('${s.sop_id}')" class="bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold px-4 py-2 rounded-lg transition shadow-sm flex items-center gap-1.5">
                <i class="fa-solid fa-check"></i> Approve SOP
              </button>
            ` : `
              <button class="bg-slate-100 text-slate-400 text-xs font-bold px-4 py-2 rounded-lg cursor-default" disabled>
                <i class="fa-solid fa-circle-check text-emerald-500"></i> Approved
              </button>
            `}
          </div>
        </div>

        <!-- Metadata Attributes -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 bg-slate-50 p-4 rounded-xl text-xs text-slate-600">
          <div><strong class="text-slate-900 block">Owner Department:</strong> ${s.owner}</div>
          <div><strong class="text-slate-900 block">Roles Involved:</strong> ${s.roles_involved ? s.roles_involved.join(", ") : "All"}</div>
          <div><strong class="text-slate-900 block">Prerequisites:</strong> ${s.prerequisites ? s.prerequisites.join("; ") : "None"}</div>
          <div><strong class="text-slate-900 block">Last Reviewed:</strong> ${s.last_reviewed_at.split("T")[0]}</div>
        </div>

        <!-- Visual Workflow Graph (Nodes & Edges) -->
        <div class="space-y-2">
          <h4 class="text-xs font-bold uppercase tracking-wider text-slate-400">Interactive Process Workflow</h4>
          <div class="bg-slate-900 rounded-xl p-5 overflow-x-auto">
            <div class="flex items-center gap-4 min-w-max text-xs">
              <div class="bg-sky-950 border border-sky-600 text-sky-200 px-3 py-2 rounded-lg font-bold">Start: Lead Signed</div>
              <span class="text-slate-500">&rarr;</span>
              <div class="bg-slate-800 border border-slate-700 text-slate-200 px-3 py-2 rounded-lg">
                <div class="font-bold text-sky-400">Step 1: CRM Entry</div>
                <div class="text-[10px] text-slate-400">Sales Representative</div>
              </div>
              <span class="text-slate-500">&rarr;</span>
              <div class="bg-slate-800 border border-slate-700 text-slate-200 px-3 py-2 rounded-lg">
                <div class="font-bold text-sky-400">Step 2: Collect KYC</div>
                <div class="text-[10px] text-slate-400">Account Executive</div>
              </div>
              <span class="text-slate-500">&rarr;</span>
              <div class="bg-amber-950/60 border border-amber-600 text-amber-200 px-3 py-2 rounded-lg">
                <div class="font-bold text-amber-400">Step 3: KYC Decision?</div>
                <div class="text-[10px] text-slate-300">Compliance Officer</div>
              </div>
              <span class="text-slate-500">&rarr;</span>
              <div class="bg-slate-800 border border-slate-700 text-slate-200 px-3 py-2 rounded-lg">
                <div class="font-bold text-emerald-400">Step 4: Invoice Signoff</div>
                <div class="text-[10px] text-emerald-300 font-bold">Finance Lead</div>
              </div>
              <span class="text-slate-500">&rarr;</span>
              <div class="bg-emerald-950 border border-emerald-600 text-emerald-200 px-3 py-2 rounded-lg font-bold">Step 5: Account Activated</div>
            </div>
          </div>
        </div>

        <!-- Procedures Step-by-Step Table -->
        <div class="space-y-3">
          <h4 class="text-xs font-bold uppercase tracking-wider text-slate-400">Step-by-Step Procedure</h4>
          <div class="space-y-2">
            ${(s.steps || []).map(st => `
              <div class="flex items-start gap-4 p-3 bg-white border border-slate-200 rounded-xl hover:border-slate-300 transition">
                <div class="w-6 h-6 rounded-full bg-slate-100 text-slate-700 font-bold text-xs flex items-center justify-center shrink-0">
                  ${st.step_number}
                </div>
                <div class="flex-1 space-y-1 text-xs">
                  <div class="flex items-center justify-between">
                    <span class="font-bold text-slate-900 text-sm">${st.title}</span>
                    <span class="bg-sky-50 text-sky-700 border border-sky-200 px-2 py-0.5 rounded font-semibold text-[11px]">${st.responsible_role}</span>
                  </div>
                  <p class="text-slate-600 leading-relaxed">${st.description}</p>
                </div>
              </div>
            `).join("")}
          </div>
        </div>

        <!-- Exceptions & Common Mistakes -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
          <div class="p-4 bg-amber-50/70 border border-amber-200 rounded-xl space-y-1.5">
            <span class="font-bold text-amber-900 flex items-center gap-1.5"><i class="fa-solid fa-triangle-exclamation"></i> Exceptions</span>
            <ul class="list-disc list-inside text-amber-800 space-y-1">
              ${(s.exceptions || []).map(e => `<li>${e}</li>`).join("")}
            </ul>
          </div>
          <div class="p-4 bg-rose-50/70 border border-rose-200 rounded-xl space-y-1.5">
            <span class="font-bold text-rose-900 flex items-center gap-1.5"><i class="fa-solid fa-circle-xmark"></i> Common Mistakes</span>
            <ul class="list-disc list-inside text-rose-800 space-y-1">
              ${(s.common_mistakes || []).map(m => `<li>${m}</li>`).join("")}
            </ul>
          </div>
        </div>
      </div>
    `).join("");

  } catch (err) {
    console.error("Failed to load SOPs:", err);
  }
}

async function approveSOP(sopId) {
  try {
    const res = await fetch(`/internal/v1/sops/${sopId}/approve`, {
      method: "POST",
      headers: getHeaders()
    });
    if (res.ok) {
      alert("SOP approved successfully by manager.");
      loadSOPs();
    } else {
      const data = await res.json();
      alert("Approval blocked: " + (data.error || "Permission Denied. Only Managers and Admins can approve SOPs."));
    }
  } catch (err) {
    console.error("Failed to approve SOP:", err);
  }
}

async function showSOPDiff() {
  try {
    const res = await fetch("/internal/v1/sops", { headers: getHeaders() });
    const data = await res.json();
    const sop = (data.sops || [])[0];
    if (!sop) return alert("No SOP found to compare.");

    const diffRes = await fetch(`/internal/v1/sops/${sop.sop_id}/diff`, {
      headers: { ...getHeaders(), "X-Old-Version": "v1", "X-New-Version": "v2" }
    });
    const diff = await diffRes.json();

    const diffModal = `
      ================ SOP VERSION COMPARISON: v1 vs v2 ================
      SOP: ${sop.title}
      Change Summary: ${diff.change_summary || "Updated Step 4 approval role"}

      CHANGED FIELDS:
      ${diff.changes ? diff.changes.map(c => `
      • ${c.field}:
        OLD (v1): ${c.old}
        NEW (v2): ${c.new}
        Role Reassigned: ${c.responsible_role_changed ? 'YES (Finance Manager -> Finance Lead)' : 'NO'}
      `).join("\n") : "No step differences"}
      ==================================================================
    `;
    alert(diffModal);
  } catch (err) {
    console.error("Failed to load diff:", err);
  }
}

// ----------------- MEETINGS -----------------
async function loadMeetings() {
  try {
    const res = await fetch("/internal/v1/meetings", { headers: getHeaders() });
    const data = await res.json();
    const meetings = data.meetings || [];

    const container = document.getElementById("meetings-container");
    container.innerHTML = meetings.map(m => `
      <div class="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-6">
        <div class="flex items-center justify-between border-b border-slate-100 pb-4">
          <div>
            <h3 class="text-lg font-bold text-slate-900">${m.title}</h3>
            <p class="text-xs text-slate-500">${m.date.split("T")[0]} &bull; Participants: ${(m.participants || []).join(", ")}</p>
          </div>
          <span class="text-xs bg-emerald-100 text-emerald-800 font-bold px-2.5 py-1 rounded-full">${m.status}</span>
        </div>

        <!-- Summary & Decisions -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="bg-slate-50 p-4 rounded-xl space-y-2 text-xs">
            <span class="font-bold text-slate-900 block uppercase tracking-wider text-[10px]">AI Meeting Summary</span>
            <p class="text-slate-600 leading-relaxed">${m.summary}</p>
          </div>
          <div class="bg-emerald-50/70 border border-emerald-200 p-4 rounded-xl space-y-2 text-xs">
            <span class="font-bold text-emerald-900 block uppercase tracking-wider text-[10px]">Key Decisions Made</span>
            <ul class="list-disc list-inside text-emerald-800 space-y-1">
              ${(m.decisions || []).map(d => `<li>${d}</li>`).join("")}
            </ul>
          </div>
        </div>

        <!-- Diarized Timestamped Transcript -->
        <div class="space-y-2">
          <h4 class="text-xs font-bold uppercase tracking-wider text-slate-400">Diarized Transcript (Click Timestamp to jump)</h4>
          <div class="bg-slate-900 rounded-xl p-4 space-y-2.5 max-h-64 overflow-y-auto font-mono text-xs">
            <div class="flex items-start gap-3 text-slate-300">
              <span class="text-sky-400 font-bold shrink-0 cursor-pointer" onclick="alert('Audio playing from 00:00')">[00:00]</span>
              <span><strong class="text-white">Manager:</strong> Good morning team. Today we are aligning on the New Customer Onboarding workflow.</span>
            </div>
            <div class="flex items-start gap-3 text-slate-300">
              <span class="text-sky-400 font-bold shrink-0 cursor-pointer" onclick="alert('Audio playing from 00:15')">[00:15]</span>
              <span><strong class="text-white">Yash:</strong> Once the client agreement is signed, I create the CRM profile and collect KYC paperwork.</span>
            </div>
            <div class="flex items-start gap-3 text-slate-300">
              <span class="text-sky-400 font-bold shrink-0 cursor-pointer" onclick="alert('Audio playing from 00:45')">[00:45]</span>
              <span><strong class="text-amber-400">Elena:</strong> Regarding invoices: we decided that the Finance Lead now approves invoices instead of the Finance Manager.</span>
            </div>
            <div class="flex items-start gap-3 text-slate-300">
              <span class="text-sky-400 font-bold shrink-0 cursor-pointer" onclick="alert('Audio playing from 01:15')">[01:15]</span>
              <span><strong class="text-white">Sarah:</strong> Perfect. So the flow is CRM -> KYC -> Compliance -> Finance Lead -> Activation.</span>
            </div>
          </div>
        </div>
      </div>
    `).join("");
  } catch (err) {
    console.error("Failed to load meetings:", err);
  }
}

// ----------------- DOCUMENTS -----------------
async function loadDocuments() {
  try {
    const res = await fetch("/internal/v1/documents", { headers: getHeaders() });
    const data = await res.json();
    const docs = data.documents || [];

    const container = document.getElementById("documents-container");
    container.innerHTML = `
      <table class="w-full text-left text-sm">
        <thead class="bg-slate-50 text-slate-500 font-semibold border-b border-slate-200 text-xs">
          <tr>
            <th class="p-4">Document Title</th>
            <th class="p-4">Format</th>
            <th class="p-4">Department</th>
            <th class="p-4">Classification</th>
            <th class="p-4">Chunks Indexed</th>
            <th class="p-4">Status</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100">
          ${docs.map(d => `
            <tr class="hover:bg-slate-50 transition">
              <td class="p-4 font-semibold text-slate-900">${d.title}</td>
              <td class="p-4"><span class="text-xs bg-slate-100 px-2 py-0.5 rounded font-mono font-semibold uppercase">${d.filename.split('.').pop()}</span></td>
              <td class="p-4 text-xs text-slate-600">${d.department}</td>
              <td class="p-4"><span class="text-xs bg-blue-50 text-blue-700 px-2 py-0.5 rounded font-semibold">${d.classification}</span></td>
              <td class="p-4 text-xs font-mono">${d.total_chunks} chunks</td>
              <td class="p-4"><span class="text-xs bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded-full font-semibold"><i class="fa-solid fa-check text-[10px]"></i> Processed</span></td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    `;
  } catch (err) {
    console.error("Failed to load documents:", err);
  }
}

function openUploadModal() {
  const title = prompt("Enter Document Title:", "Travel & Expense Reimbursement Policy");
  if (!title) return;
  const content = prompt("Enter Document Body Content:", "All employees must submit travel receipts within 30 days. The Department Lead approves expenses up to $2,000.");
  if (!content) return;

  fetch("/internal/v1/documents/upload", {
    method: "POST",
    headers: getHeaders(),
    body: JSON.stringify({
      filename: "reimbursement_policy.txt",
      title: title,
      content: content,
      classification: "INTERNAL",
      department: currentUser.department
    })
  }).then(r => r.json()).then(res => {
    alert("Document ingested and embedded successfully into local vector database!");
    loadDocuments();
  }).catch(e => alert("Error uploading: " + e));
}

// ----------------- CONFLICTS -----------------
async function loadConflicts() {
  try {
    const res = await fetch("/internal/v1/conflicts", { headers: getHeaders() });
    const data = await res.json();
    const conflicts = data.conflicts || [];

    const container = document.getElementById("conflicts-container");
    container.innerHTML = conflicts.map(c => `
      <div class="bg-white rounded-2xl border border-rose-200 shadow-sm p-6 space-y-4">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2 text-rose-700 font-bold text-sm">
            <i class="fa-solid fa-triangle-exclamation"></i> CONFLICT IN: ${c.sop_title}
          </div>
          <span class="text-xs bg-rose-100 text-rose-800 font-bold px-2.5 py-1 rounded-full">${c.status}</span>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
          <div class="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-1">
            <strong class="text-slate-900 block font-bold">Existing Active SOP Rule:</strong>
            <p class="text-slate-700 leading-relaxed">${c.existing_statement}</p>
          </div>
          <div class="p-4 bg-rose-50 border border-rose-200 rounded-xl space-y-1">
            <strong class="text-rose-900 block font-bold">New Statement from ${c.new_source_title} (${c.new_source_reference}):</strong>
            <p class="text-rose-800 leading-relaxed font-semibold">"${c.new_statement}"</p>
          </div>
        </div>
        <div class="bg-amber-50 border border-amber-200 p-3 rounded-xl text-xs text-amber-900 flex items-center justify-between">
          <span><strong>Recommended Action:</strong> ${c.recommended_action}</span>
          <button onclick="resolveConflict('${c.conflict_id}')" class="bg-emerald-600 hover:bg-emerald-700 text-white font-bold px-4 py-1.5 rounded-lg text-xs transition">
            Mark Resolved
          </button>
        </div>
      </div>
    `).join("") || `<div class="p-8 text-center text-sm text-slate-400">No unresolved conflicts detected.</div>`;
  } catch (err) {
    console.error("Failed to load conflicts:", err);
  }
}

async function resolveConflict(cid) {
  try {
    const res = await fetch(`/internal/v1/conflicts/${cid}/resolve`, {
      method: "POST",
      headers: getHeaders()
    });
    if (res.ok) {
      alert("Conflict marked as resolved.");
      loadConflicts();
    }
  } catch (err) {
    console.error("Resolve conflict error:", err);
  }
}

// ----------------- KNOWLEDGE GAPS -----------------
async function loadGaps() {
  try {
    const res = await fetch("/internal/v1/knowledge-gaps", { headers: getHeaders() });
    const data = await res.json();
    const gaps = data.knowledge_gaps || [];

    const container = document.getElementById("gaps-container");
    container.innerHTML = gaps.map(g => `
      <div class="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 flex items-center justify-between hover:border-amber-300 transition">
        <div class="space-y-1.5">
          <div class="flex items-center gap-3">
            <span class="font-bold text-slate-900 text-sm">${g.question}</span>
            <span class="text-xs bg-amber-100 text-amber-800 font-bold px-2 py-0.5 rounded-full">${g.frequency} Employees Asked</span>
          </div>
          <div class="text-xs text-slate-500">Department: ${g.department} &bull; Recommendation: ${g.recommended_action}</div>
        </div>
        <button onclick="alert('Creating draft SOP for: ${g.question}')" class="bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold px-4 py-2 rounded-lg transition shadow-sm">
          Create Missing SOP
        </button>
      </div>
    `).join("");
  } catch (err) {
    console.error("Failed to load gaps:", err);
  }
}

// ----------------- ONBOARDING -----------------
async function loadOnboarding() {
  try {
    const res = await fetch("/internal/v1/onboarding", { headers: getHeaders() });
    const data = await res.json();

    const container = document.getElementById("onboarding-container");
    container.innerHTML = `
      <div class="lg:col-span-2 space-y-6">
        <!-- Checklist -->
        <div class="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-3">
          <h3 class="font-bold text-slate-900 text-sm flex items-center gap-2">
            <i class="fa-solid fa-list-check text-teal-600"></i> First Week Interactive Checklist
          </h3>
          <div class="space-y-2 text-xs">
            ${(data.first_week_checklist || []).map(item => `
              <label class="flex items-center gap-3 p-3 bg-slate-50 border border-slate-200 rounded-lg cursor-pointer hover:bg-slate-100 transition">
                <input type="checkbox" class="rounded text-teal-600 focus:ring-teal-500">
                <span class="font-semibold text-slate-800">Day ${item.day}:</span>
                <span class="text-slate-600">${item.task}</span>
              </label>
            `).join("")}
          </div>
        </div>

        <!-- Essential SOPs -->
        <div class="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-3">
          <h3 class="font-bold text-slate-900 text-sm flex items-center gap-2">
            <i class="fa-solid fa-book text-teal-600"></i> Essential SOPs for ${data.department}
          </h3>
          <div class="space-y-2 text-xs">
            ${(data.essential_sops || []).map(s => `
              <div class="flex items-center justify-between p-3 border border-slate-200 rounded-lg hover:border-teal-400 transition">
                <div>
                  <div class="font-bold text-slate-900">${s.title} (${s.version})</div>
                  <div class="text-slate-500">${s.summary}</div>
                </div>
                <button onclick="navigate('sops')" class="text-teal-600 font-bold">Read &rarr;</button>
              </div>
            `).join("")}
          </div>
        </div>
      </div>

      <!-- Right Column: Systems & Contacts -->
      <div class="space-y-6">
        <div class="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-3 text-xs">
          <h3 class="font-bold text-slate-900 text-sm flex items-center gap-2">
            <i class="fa-solid fa-laptop-code text-teal-600"></i> Core Enterprise Systems
          </h3>
          <ul class="space-y-2">
            ${(data.core_systems || []).map(sys => `
              <li class="p-2.5 bg-slate-50 rounded-lg border border-slate-200">
                <div class="font-bold text-slate-900">${sys.name}</div>
                <div class="text-slate-500 text-[11px]">${sys.purpose}</div>
              </li>
            `).join("")}
          </ul>
        </div>

        <div class="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-3 text-xs">
          <h3 class="font-bold text-slate-900 text-sm flex items-center gap-2">
            <i class="fa-solid fa-address-book text-teal-600"></i> Key Department Contacts
          </h3>
          <ul class="space-y-2">
            ${(data.key_contacts || []).map(c => `
              <li class="p-2.5 bg-slate-50 rounded-lg border border-slate-200">
                <div class="font-bold text-slate-900">${c.role}: ${c.contact}</div>
                <div class="text-slate-500 text-[11px]">${c.scope}</div>
              </li>
            `).join("")}
          </ul>
        </div>
      </div>
    `;
  } catch (err) {
    console.error("Failed to load onboarding:", err);
  }
}

// ----------------- AUDIT -----------------
async function loadAudit() {
  try {
    const res = await fetch("/internal/v1/audit", { headers: getHeaders() });
    const data = await res.json();
    const events = data.audit_events || [];

    const container = document.getElementById("audit-container");
    container.innerHTML = `
      <table class="w-full text-left text-xs">
        <thead class="bg-slate-50 text-slate-500 font-semibold border-b border-slate-200">
          <tr>
            <th class="p-3">Timestamp</th>
            <th class="p-3">Actor</th>
            <th class="p-3">Event Type</th>
            <th class="p-3">Resource</th>
            <th class="p-3">Result</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100 font-mono">
          ${events.map(e => `
            <tr class="hover:bg-slate-50">
              <td class="p-3 text-slate-500">${e.timestamp}</td>
              <td class="p-3 font-semibold text-slate-800">${e.actor}</td>
              <td class="p-3 text-sky-700">${e.event_type}</td>
              <td class="p-3 text-slate-600">${e.resource}</td>
              <td class="p-3"><span class="bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded font-bold">${e.result}</span></td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    `;
  } catch (err) {
    console.error("Failed to load audit:", err);
  }
}

// Auto-boot on load
window.addEventListener("DOMContentLoaded", () => {
  loadDashboardData();
});
