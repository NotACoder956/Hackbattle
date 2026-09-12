"use client";
import { useState } from "react";

export default function ChatPage() {
  const [messages, setMessages] = useState([
    {
      sender: "assistant",
      content: "Hello Yash! I am your private AI knowledge assistant. I answer based strictly on verified internal SOPs, documents, and meeting records.",
      confidence: "High",
      citations: []
    }
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const q = input.trim();
    setInput("");
    setMessages(prev => [...prev, { sender: "user", content: q, confidence: "", citations: [] }]);
    setLoading(true);

    try {
      const res = await fetch("/internal/v1/questions", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Tenant-ID": "ten_0bf7f488ef41",
          "X-User-Role": "EMPLOYEE",
          "X-User-Email": "yash@acme.corp",
          "X-User-Department": "Sales Operations"
        },
        body: JSON.stringify({ question: q })
      });
      const data = await res.json();
      const msg = data.message || {};
      setMessages(prev => [...prev, {
        sender: "assistant",
        content: msg.content || "No answer returned.",
        confidence: msg.confidence || "High",
        citations: msg.citations || []
      }]);
    } catch {
      setMessages(prev => [...prev, {
        sender: "assistant",
        content: "Error communicating with Private Agent.",
        confidence: "Low",
        citations: []
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8 h-full flex gap-6">
      <div className="flex-1 bg-white border border-slate-200 rounded-2xl flex flex-col overflow-hidden shadow-sm">
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.map((m, idx) => (
            <div key={idx} className={`flex gap-3 max-w-2xl ${m.sender === 'user' ? 'ml-auto justify-end' : ''}`}>
              <div className={`p-4 rounded-2xl text-sm leading-relaxed ${m.sender === 'user' ? 'bg-slate-900 text-white rounded-tr-none' : 'bg-slate-100 text-slate-900 rounded-tl-none space-y-2'}`}>
                {m.sender === 'assistant' && (
                  <div className="flex items-center justify-between text-[11px] uppercase tracking-wider font-bold text-slate-400">
                    <span>Grounded Answer</span>
                    <span className="text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded-full">{m.confidence}</span>
                  </div>
                )}
                <p className="whitespace-pre-line">{m.content}</p>
                {m.citations && m.citations.length > 0 && (
                  <div className="pt-2 border-t border-slate-200 text-xs text-slate-600">
                    <strong className="block text-[10px] uppercase font-bold text-slate-400 mb-1">Citations:</strong>
                    {m.citations.map((c: any, ci: number) => (
                      <div key={ci}>• {c.source_title} ({c.reference})</div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
          {loading && (
            <div className="text-xs text-slate-400 italic">Searching local private knowledge base...</div>
          )}
        </div>

        <form onSubmit={handleSubmit} className="p-4 border-t border-slate-200 flex gap-3">
          <input
            type="text"
            value={input}
            onChange={e => setInput(e.target.value)}
            placeholder="Ask about onboarding, KYC verification, invoice approvals..."
            className="flex-1 border border-slate-300 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500"
          />
          <button type="submit" className="bg-slate-900 text-white font-bold px-6 py-3 rounded-xl hover:bg-slate-800 transition">
            Send
          </button>
        </form>
      </div>
    </div>
  );
}
