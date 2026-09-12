import Link from "next/link";

export default function LoginPage() {
  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center p-6 text-white">
      <div className="max-w-md w-full bg-slate-950 border border-slate-800 p-8 rounded-2xl shadow-xl space-y-6">
        <div className="text-center space-y-2">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-tr from-sky-400 to-indigo-600 flex items-center justify-center font-black text-2xl mx-auto shadow-md">
            S
          </div>
          <h2 className="text-2xl font-bold tracking-tight">Sign in to SOPIQ</h2>
          <p className="text-xs text-slate-400">Enterprise Private AI Knowledge & SOP Agent</p>
        </div>

        <form className="space-y-4">
          <div>
            <label className="text-xs font-semibold uppercase tracking-wider text-slate-400 block mb-1">Company Email</label>
            <input type="email" defaultValue="yash@acme.corp" className="w-full bg-slate-900 border border-slate-800 rounded-lg p-3 text-sm text-white focus:outline-none focus:ring-1 focus:ring-sky-500" />
          </div>
          <div>
            <label className="text-xs font-semibold uppercase tracking-wider text-slate-400 block mb-1">Password</label>
            <input type="password" defaultValue="AcmePass123!" className="w-full bg-slate-900 border border-slate-800 rounded-lg p-3 text-sm text-white focus:outline-none focus:ring-1 focus:ring-sky-500" />
          </div>
          <Link href="/dashboard" className="w-full block text-center bg-sky-600 hover:bg-sky-500 text-white font-bold py-3 rounded-lg transition">
            Sign In with Enterprise SSO
          </Link>
        </form>

        <div className="border-t border-slate-900 pt-4 text-center">
          <p className="text-xs text-slate-500">
            Protected by Private VPC Authentication • Zero Company Knowledge in Cloud
          </p>
        </div>
      </div>
    </div>
  );
}
