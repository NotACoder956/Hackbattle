export default function PrivacyPage() {
  return (
    <div className="p-8 space-y-6">
      <div className="bg-white rounded-2xl border border-slate-200 p-6 space-y-6 shadow-sm">
        <div>
          <span className="text-xs uppercase font-bold text-emerald-600 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-100">
            Architectural Guarantees
          </span>
          <h2 className="text-2xl font-bold text-slate-900 mt-2 tracking-tight">Privacy Center & Data Flow Architecture</h2>
          <p className="text-sm text-slate-500 mt-1">
            Zero company knowledge leaves your private infrastructure.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-slate-900 text-white p-5 rounded-xl space-y-3">
            <h3 className="text-emerald-400 font-bold text-sm">Customer Infrastructure (Private Agent)</h3>
            <ul className="text-xs text-slate-300 space-y-2">
              <li>• Document Storage: Customer On-Premise / VPC</li>
              <li>• Meeting Transcription: Local Faster-Whisper</li>
              <li>• Vector Embeddings: Local pgvector / SQLite</li>
              <li>• LLM Inference: Local Ollama / vLLM</li>
              <li>• Data Egress Policy: PRIVATE_ONLY</li>
            </ul>
          </div>
          <div className="bg-slate-50 border border-slate-200 p-5 rounded-xl space-y-3">
            <h3 className="text-slate-800 font-bold text-sm">RankPilot Control Plane (Cloud Hosted)</h3>
            <ul className="text-xs text-slate-600 space-y-2">
              <li>• Tenant Metadata & Licensing: Yes</li>
              <li>• Agent Status & Heartbeat: Yes (Minimal metrics)</li>
              <li>• Raw Documents & Transcripts: NEVER STORED</li>
              <li>• Employee AI Inquiries: NEVER TRANSMITTED</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
