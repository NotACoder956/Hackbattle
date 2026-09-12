import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SOPIQ - Private AI SOP & Company Knowledge Agent",
  description: "Privacy-first enterprise AI platform for company SOPs and internal knowledge.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="h-full bg-slate-50">
      <body className="h-full antialiased text-slate-900">{children}</body>
    </html>
  );
}
