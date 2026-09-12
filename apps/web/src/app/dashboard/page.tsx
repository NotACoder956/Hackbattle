import Link from "next/link";

export default function DashboardPage() {
  return (
    <div className="p-8 space-y-6">
      <div className="bg-slate-900 rounded-2xl p-6 text-white space-y-2">
        <span className="text-xs uppercase font-bold text-sky-400 bg-sky-950 px-2.5 py-1 rounded-full border border-sky-800">
          Private Infrastructure Active
        </span>
        <h2 className="text-2xl font-bold tracking-tight">Acme Technologies Knowledge Control Center</h2>
        <p className="text-slate-400 text-sm">
          All document parsing, transcription, embeddings, and RAG execution occur locally.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-5">
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <div className="text-xs font-semibold uppercase text-slate-500">Active SOPs</div>
          <div className="text-2xl font-bold text-slate-900 mt-1">1</div>
          <div className="text-xs text-emerald-600 font-semibold mt-1">100% Completeness</div>
        </div>
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <div className="text-xs font-semibold uppercase text-slate-500">Meetings Transcribed</div>
          <div className="text-2xl font-bold text-slate-900 mt-1">1</div>
          <div className="text-xs text-emerald-600 font-semibold mt-1">Diarized & Timestamped</div>
        </div>
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <div className="text-xs font-semibold uppercase text-slate-500">Documents Ingested</div>
          <div className="text-2xl font-bold text-slate-900 mt-1">3</div>
          <div className="text-xs text-slate-500 font-semibold mt-1">8 Chunks Indexed</div>
        </div>
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <div className="text-xs font-semibold uppercase text-slate-500">Detected Conflicts</div>
          <div className="text-2xl font-bold text-rose-600 mt-1">1</div>
          <div className="text-xs text-rose-600 font-semibold mt-1">Pending Review</div>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 p-6 space-y-4 shadow-sm">
        <h3 className="font-bold text-slate-900 text-base">Quick Access</h3>
        <div className="flex flex-wrap gap-4">
          <Link href="/chat" className="bg-slate-900 text-white text-xs font-bold px-4 py-2 rounded-lg">
            Ask AI Assistant
          </Link>
          <Link href="/sops" className="bg-slate-100 hover:bg-slate-200 text-slate-800 text-xs font-bold px-4 py-2 rounded-lg">
            View SOP Catalog
          </Link>
          <Link href="/meetings" className="bg-slate-100 hover:bg-slate-200 text-slate-800 text-xs font-bold px-4 py-2 rounded-lg">
            Inspect Meetings
          </Link>
          <Link href="/settings/privacy" className="bg-slate-100 hover:bg-slate-200 text-slate-800 text-xs font-bold px-4 py-2 rounded-lg">
            Privacy Architecture
          </Link>
        </div>
      </div>
    </div>
  );
}
