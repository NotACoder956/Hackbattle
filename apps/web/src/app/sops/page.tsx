export default function SOPsPage() {
  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Standard Operating Procedures</h2>
          <p className="text-sm text-slate-500">Continuously updated from meetings and approved by leadership.</p>
        </div>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 p-6 space-y-4 shadow-sm">
        <div className="flex items-center justify-between border-b border-slate-100 pb-4">
          <div className="space-y-1">
            <div className="flex items-center gap-3">
              <h3 className="text-lg font-bold text-slate-900">New Client Onboarding SOP</h3>
              <span className="bg-slate-100 text-slate-800 text-xs font-mono font-bold px-2 py-0.5 rounded">v2</span>
              <span className="bg-emerald-100 text-emerald-800 text-xs font-bold px-2 py-0.5 rounded-full">APPROVED</span>
            </div>
            <p className="text-xs text-slate-500">Standardize the end-to-end customer onboarding workflow.</p>
          </div>
          <div className="text-right">
            <div className="text-xs text-slate-400 font-semibold">Completeness</div>
            <div className="text-lg font-black text-emerald-600">100/100</div>
          </div>
        </div>

        <div className="space-y-2">
          <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs">
            <strong className="text-slate-900">Step 1: Create CRM Entry</strong> &bull; Responsible: Sales Representative
          </div>
          <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs">
            <strong className="text-slate-900">Step 2: Collect KYC Documents</strong> &bull; Responsible: Account Executive
          </div>
          <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs">
            <strong className="text-slate-900">Step 3: KYC Verification</strong> &bull; Responsible: Compliance Officer
          </div>
          <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-xs font-semibold text-emerald-900">
            <strong className="text-emerald-950">Step 4: Invoice Generation & Approval</strong> &bull; Responsible: Finance Lead (Updated from Finance Manager)
          </div>
          <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs">
            <strong className="text-slate-900">Step 5: Account Activation</strong> &bull; Responsible: Operations Team
          </div>
        </div>
      </div>
    </div>
  );
}
