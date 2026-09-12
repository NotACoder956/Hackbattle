import Link from "next/link";

export default function HomePage() {
  return (
    <main className="min-h-screen bg-slate-950 text-white selection:bg-sky-500 selection:text-white">
      {/* Top Nav */}
      <nav className="border-b border-slate-800 px-8 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-tr from-sky-400 to-indigo-600 flex items-center justify-center font-extrabold text-white text-lg">
            S
          </div>
          <div>
            <span className="font-extrabold tracking-tight text-xl text-white">SOPIQ</span>
            <span className="text-[10px] block text-sky-400 font-semibold tracking-wider uppercase">Privacy-First AI Agent</span>
          </div>
        </div>
        <div className="flex items-center gap-4 text-sm font-medium">
          <Link href="/dashboard" className="text-slate-300 hover:text-white transition">
            Dashboard
          </Link>
          <Link href="/settings/privacy" className="text-slate-300 hover:text-white transition">
            Privacy Architecture
          </Link>
          <Link href="/login" className="bg-sky-600 hover:bg-sky-500 text-white px-4 py-2 rounded-lg font-semibold transition shadow-sm">
            Launch Console
          </Link>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="max-w-5xl mx-auto px-8 pt-20 pb-16 text-center space-y-6">
        <div className="inline-flex items-center gap-2 bg-slate-900 border border-slate-800 text-sky-400 text-xs px-3 py-1.5 rounded-full font-semibold">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          Company Knowledge Stays Inside Your Infrastructure
        </div>
        <h1 className="text-5xl md:text-6xl font-extrabold tracking-tight text-white leading-tight">
          Your company's private <br />
          <span className="bg-gradient-to-r from-sky-400 via-indigo-300 to-teal-300 bg-clip-text text-transparent">
            AI knowledge & SOP agent.
          </span>
        </h1>
        <p className="max-w-2xl mx-auto text-slate-400 text-base md:text-lg leading-relaxed">
          Transforms company meetings, recordings, documents, and policies into continuously updated standard operating procedures. Answers employee questions with verifiable, grounded citations.
        </p>
        <div className="pt-4 flex justify-center gap-4">
          <Link href="/dashboard" className="bg-sky-600 hover:bg-sky-500 text-white font-bold px-6 py-3 rounded-xl transition shadow-lg shadow-sky-950">
            Open Platform Dashboard
          </Link>
          <Link href="/chat" className="bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 font-bold px-6 py-3 rounded-xl transition">
            Try Employee Chat
          </Link>
        </div>
      </section>

      {/* Privacy Guarantee Grid */}
      <section className="max-w-5xl mx-auto px-8 py-12 border-t border-slate-900 grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-slate-900/60 border border-slate-800 p-6 rounded-2xl space-y-3">
          <div className="text-sky-400 text-xl font-bold">1. Zero Cloud Data</div>
          <h3 className="text-white font-bold text-base">Local VPC Execution</h3>
          <p className="text-slate-400 text-xs leading-relaxed">
            Raw meeting recordings, transcripts, documents, and vectors are never sent to our central cloud. All processing occurs on your agent.
          </p>
        </div>
        <div className="bg-slate-900/60 border border-slate-800 p-6 rounded-2xl space-y-3">
          <div className="text-teal-400 text-xl font-bold">2. Continuous SOPs</div>
          <h3 className="text-white font-bold text-base">Meeting Intelligence</h3>
          <p className="text-slate-400 text-xs leading-relaxed">
            Automatically detects process modifications, extracts decisions, and detects conflicts between old SOPs and new meetings.
          </p>
        </div>
        <div className="bg-slate-900/60 border border-slate-800 p-6 rounded-2xl space-y-3">
          <div className="text-amber-400 text-xl font-bold">3. Grounded Q&A</div>
          <h3 className="text-white font-bold text-base">Verifiable Citations</h3>
          <p className="text-slate-400 text-xs leading-relaxed">
            Every employee answer links directly to the originating SOP step, document page, or meeting audio timestamp.
          </p>
        </div>
      </section>
    </main>
  );
}
