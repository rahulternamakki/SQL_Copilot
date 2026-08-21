import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Governed AI Database Copilot",
  description: "Enterprise multi-agent AI assistant with RAG grounding, safety critic, and MCP isolation.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="antialiased min-h-screen bg-[#070b14] text-slate-100 flex flex-col">
        {children}
      </body>
    </html>
  );
}
