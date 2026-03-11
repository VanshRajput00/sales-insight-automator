"use client";

import { useState, useCallback, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import axios, { AxiosError } from "axios";
import {
  UploadCloud, Mail, Zap, CheckCircle2, XCircle,
  FileSpreadsheet, Loader2, TrendingUp, Package, Tag,
} from "lucide-react";

// ─── Types ──────────────────────────────────────────────────────────────────
interface Stats {
  total_revenue: number;
  total_units_sold: number;
  top_category: string;
  top_category_revenue: number;
}

interface ApiResponse {
  status: string;
  filename: string;
  rows_analyzed: number;
  stats: Stats;
  ai_brief: string;
  recipient_email: string;
  email_status: string;
  message: string;
}

type ToastType = "success" | "error";

interface Toast {
  id: number;
  type: ToastType;
  message: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ─── Sub-components ──────────────────────────────────────────────────────────

function StatCard({ icon: Icon, label, value, accent = false }: {
  icon: React.ElementType; label: string; value: string; accent?: boolean;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-xl p-4 flex gap-3 items-start"
      style={{ background: "var(--muted)", border: "1px solid var(--border)" }}
    >
      <div className="p-2 rounded-lg" style={{ background: "var(--slate)" }}>
        <Icon size={16} color={accent ? "var(--emerald)" : "var(--sub)"} />
      </div>
      <div>
        <p className="text-xs font-mono uppercase tracking-widest" style={{ color: "var(--sub)" }}>
          {label}
        </p>
        <p className="text-base font-semibold mt-0.5" style={{ color: accent ? "var(--emerald)" : "var(--text)" }}>
          {value}
        </p>
      </div>
    </motion.div>
  );
}

function ToastItem({ toast, onDismiss }: { toast: Toast; onDismiss: (id: number) => void }) {
  return (
    <motion.div
      initial={{ opacity: 0, x: 60, scale: 0.95 }}
      animate={{ opacity: 1, x: 0,  scale: 1 }}
      exit={{    opacity: 0, x: 60,  scale: 0.95 }}
      transition={{ type: "spring", stiffness: 300, damping: 25 }}
      onClick={() => onDismiss(toast.id)}
      className="flex items-center gap-3 px-4 py-3 rounded-xl cursor-pointer select-none"
      style={{
        background: toast.type === "success" ? "#052e16" : "#1c0a0a",
        border: `1px solid ${toast.type === "success" ? "#166534" : "#7f1d1d"}`,
        minWidth: "280px",
        boxShadow: "0 8px 32px rgba(0,0,0,0.4)",
      }}
    >
      {toast.type === "success"
        ? <CheckCircle2 size={18} color="var(--emerald)" />
        : <XCircle     size={18} color="var(--danger)" />
      }
      <p className="text-sm font-medium" style={{ color: "var(--text)" }}>
        {toast.message}
      </p>
    </motion.div>
  );
}

// ─── Main Page ───────────────────────────────────────────────────────────────
export default function SalesUploadPage() {
  const [file, setFile]           = useState<File | null>(null);
  const [email, setEmail]         = useState("");
  const [isDragging, setIsDragging] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult]       = useState<ApiResponse | null>(null);
  const [toasts, setToasts]       = useState<Toast[]>([]);
  const fileInputRef              = useRef<HTMLInputElement>(null);
  const toastCounter              = useRef(0);

  const addToast = useCallback((type: ToastType, message: string) => {
    const id = ++toastCounter.current;
    setToasts(prev => [...prev, { id, type, message }]);
    setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), 4500);
  }, []);

  const dismissToast = useCallback((id: number) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  }, []);

  const handleFile = useCallback((f: File) => {
    if (!f.name.endsWith(".csv")) {
      addToast("error", "Only CSV files are supported.");
      return;
    }
    if (f.size > 10 * 1024 * 1024) {
      addToast("error", "File exceeds 10MB limit. Please reduce the file size.");
      return;
    }
    setFile(f);
    setResult(null);
  }, [addToast]);

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const dropped = e.dataTransfer.files[0];
    if (dropped) handleFile(dropped);
  }, [handleFile]);

  const handleSubmit = async () => {
    if (!file || !email) {
      addToast("error", "Please select a file and enter an email address.");
      return;
    }

    setIsLoading(true);
    setResult(null);

    const form = new FormData();
    form.append("file", file);
    form.append("recipient_email", email);

    try {
      const { data } = await axios.post<ApiResponse>(`${API_BASE}/api/v1/upload`, form, {
        headers: { "Content-Type": "multipart/form-data" },
        timeout: 60000,
      });

      setResult(data);
      addToast(
        data.email_status === "sent" ? "success" : "error",
        data.email_status === "sent"
          ? `Report sent to ${data.recipient_email} ✓`
          : "Analysis done, but email delivery failed."
      );
    } catch (err) {
      const error = err as AxiosError<{ detail: string }>;
      const detail = error.response?.data?.detail || "Request failed. Is the backend running?";
      addToast("error", detail);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      {/* ── Background grid ── */}
      <div className="fixed inset-0 pointer-events-none" style={{
        backgroundImage: `
          linear-gradient(rgba(255,255,255,0.02) 1px, transparent 1px),
          linear-gradient(90deg, rgba(255,255,255,0.02) 1px, transparent 1px)
        `,
        backgroundSize: "48px 48px",
      }} />

      {/* ── Toast rack ── */}
      <div className="fixed top-5 right-5 z-50 flex flex-col gap-2">
        <AnimatePresence>
          {toasts.map(t => (
            <ToastItem key={t.id} toast={t} onDismiss={dismissToast} />
          ))}
        </AnimatePresence>
      </div>

      <main className="relative z-10 min-h-screen flex flex-col items-center justify-center px-4 py-16">
        {/* ── Header ── */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="text-center mb-12"
        >
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-mono
                          tracking-widest uppercase mb-6"
               style={{ background: "var(--slate)", border: "1px solid var(--border)", color: "var(--sub)" }}>
            <Zap size={11} color="var(--emerald)" />
            Powered by Gemini AI
          </div>
          <h1 className="font-display text-5xl md:text-6xl leading-tight mb-3"
              style={{ color: "var(--text)" }}>
            Sales Insight
            <span className="block italic" style={{ color: "var(--emerald)" }}>Automator</span>
          </h1>
          <p className="text-base max-w-sm mx-auto" style={{ color: "var(--sub)" }}>
            Upload your Q1 CSV and receive an executive-grade AI brief in your inbox within seconds.
          </p>
        </motion.div>

        {/* ── Card ── */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, duration: 0.5 }}
          className="w-full max-w-lg rounded-2xl p-8 space-y-6"
          style={{
            background: "var(--slate)",
            border: "1px solid var(--border)",
            boxShadow: "0 24px 64px rgba(0,0,0,0.5)",
          }}
        >
          {/* Drop Zone */}
          <div
            onDrop={onDrop}
            onDragOver={e => { e.preventDefault(); setIsDragging(true); }}
            onDragLeave={() => setIsDragging(false)}
            onClick={() => fileInputRef.current?.click()}
            className="rounded-xl border-2 border-dashed p-8 text-center cursor-pointer
                       transition-all duration-200 select-none"
            style={{
              borderColor: isDragging ? "var(--emerald)" : file ? "var(--emerald)" : "var(--border)",
              background:  isDragging ? "rgba(16,185,129,0.05)" : "var(--muted)",
            }}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv"
              className="hidden"
              onChange={e => { const f = e.target.files?.[0]; if (f) handleFile(f); }}
            />
            <AnimatePresence mode="wait">
              {file ? (
                <motion.div key="file" initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                            className="flex flex-col items-center gap-2">
                  <FileSpreadsheet size={28} color="var(--emerald)" />
                  <p className="font-medium text-sm" style={{ color: "var(--emerald)" }}>
                    {file.name}
                  </p>
                  <p className="text-xs font-mono" style={{ color: "var(--sub)" }}>
                    {(file.size / 1024).toFixed(1)} KB · Click to replace
                  </p>
                </motion.div>
              ) : (
                <motion.div key="empty" initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                            className="flex flex-col items-center gap-2">
                  <UploadCloud size={28} style={{ color: "var(--sub)" }} />
                  <p className="text-sm font-medium" style={{ color: "var(--text)" }}>
                    Drop your CSV here
                  </p>
                  <p className="text-xs font-mono" style={{ color: "var(--sub)" }}>
                    or click to browse · max 10MB
                  </p>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Email Field */}
          <div className="relative">
            <Mail size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2"
                  style={{ color: "var(--sub)" }} />
            <input
              type="email"
              placeholder="CEO's email address"
              value={email}
              onChange={e => setEmail(e.target.value)}
              onKeyDown={e => e.key === "Enter" && handleSubmit()}
              className="w-full pl-10 pr-4 py-3 rounded-xl text-sm outline-none
                         transition-all duration-150 font-mono placeholder-opacity-50"
              style={{
                background: "var(--muted)",
                border: "1px solid var(--border)",
                color: "var(--text)",
              }}
            />
          </div>

          {/* Submit Button */}
          <motion.button
            onClick={handleSubmit}
            disabled={isLoading || !file || !email}
            whileHover={{ scale: isLoading ? 1 : 1.02 }}
            whileTap={{  scale: isLoading ? 1 : 0.98 }}
            className="w-full py-3.5 rounded-xl font-semibold text-sm flex items-center
                       justify-center gap-2.5 transition-all duration-200"
            style={{
              background: isLoading || !file || !email
                ? "var(--muted)" : "var(--emerald)",
              color: isLoading || !file || !email
                ? "var(--sub)" : "#022c22",
              cursor: isLoading || !file || !email ? "not-allowed" : "pointer",
            }}
          >
            {isLoading ? (
              <>
                <Loader2 size={16} className="animate-spin" />
                AI is analyzing your data...
              </>
            ) : (
              <>
                <Zap size={16} />
                Generate & Send Report
              </>
            )}
          </motion.button>
        </motion.div>

        {/* ── Results Panel ── */}
        <AnimatePresence>
          {result && (
            <motion.div
              key="result"
              initial={{ opacity: 0, y: 24 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{    opacity: 0, y: 24 }}
              transition={{ duration: 0.45 }}
              className="w-full max-w-lg mt-6 rounded-2xl p-8 space-y-6"
              style={{
                background: "var(--slate)",
                border: "1px solid var(--border)",
                boxShadow: "0 24px 64px rgba(0,0,0,0.4)",
              }}
            >
              {/* Stats grid */}
              <div>
                <p className="text-xs font-mono uppercase tracking-widest mb-3"
                   style={{ color: "var(--sub)" }}>
                  Key Metrics — {result.rows_analyzed} records
                </p>
                <div className="grid grid-cols-1 gap-3">
                  <StatCard icon={TrendingUp} label="Total Revenue" accent
                    value={`$${result.stats.total_revenue.toLocaleString("en-US", { minimumFractionDigits: 2 })}`}
                  />
                  <StatCard icon={Package} label="Units Sold"
                    value={result.stats.total_units_sold.toLocaleString()}
                  />
                  <StatCard icon={Tag} label={`Top Category · $${result.stats.top_category_revenue.toLocaleString()}`}
                    value={result.stats.top_category}
                  />
                </div>
              </div>

              {/* AI Brief */}
              <div>
                <p className="text-xs font-mono uppercase tracking-widest mb-3"
                   style={{ color: "var(--sub)" }}>
                  Executive Brief
                </p>
                <div className="rounded-xl p-5 space-y-3"
                     style={{ background: "var(--muted)", border: "1px solid var(--border)" }}>
                  {result.ai_brief.split("\n").filter(Boolean).map((line, i) => (
                    <motion.p
                      key={i}
                      initial={{ opacity: 0, x: -8 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.12 }}
                      className="text-sm leading-relaxed"
                      style={{ color: "var(--text)" }}
                    >
                      {line.replace(/^[•\-]\s*/, "→ ")}
                    </motion.p>
                  ))}
                </div>
              </div>

              {/* Delivery status */}
              <div className="flex items-center gap-2 text-xs font-mono"
                   style={{ color: result.email_status === "sent" ? "var(--emerald)" : "var(--amber)" }}>
                {result.email_status === "sent"
                  ? <><CheckCircle2 size={13} /> Report delivered to {result.recipient_email}</>
                  : <><XCircle size={13} /> Email failed · Check SMTP config in .env</>
                }
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </main>
    </>
  );
}
