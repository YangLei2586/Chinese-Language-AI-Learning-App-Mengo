"use client";
import { useEffect, useState } from "react";

type Metrics = { mode: string; learners: number; completed_lessons: number; allowlisted_events: number; privacy_note: string };
const api = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000/v1";
const user = process.env.NEXT_PUBLIC_DEMO_USER ?? "demo-learner";

export default function Dashboard() {
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => { fetch(`${api}/admin/analytics`, { headers: { "X-Demo-User": user } }).then(async (res) => { if (!res.ok) throw new Error("The local API is unavailable."); return res.json() as Promise<Metrics>; }).then(setMetrics).catch((reason: unknown) => setError(reason instanceof Error ? reason.message : "Unable to load metrics.")); }, []);
  return <main className="dashboard"><nav><a className="brand" href="/">mengo</a><span className="adminBadge">LOCAL DEMO · ADMIN VIEW</span></nav><section><p className="eyebrow">ENTERPRISE / ADMIN</p><h1>Learning signals,<br/><em>not learner surveillance.</em></h1><p className="lede">This protected-looking demo page intentionally exposes aggregate local metrics only. Production needs SSO, roles, audit logs, and tenant isolation.</p></section>{error && <p className="error">{error} Start the FastAPI server on port 8000, then refresh.</p>}{!metrics && !error && <p>Loading local demo metrics…</p>}{metrics && <><div className="metricGrid"><Metric label="Demo learners" value={metrics.learners}/><Metric label="Completed lessons" value={metrics.completed_lessons}/><Metric label="Allowlisted events" value={metrics.allowlisted_events}/></div><section className="adminCard"><h2>Data boundary</h2><p>{metrics.privacy_note}</p><ul><li>No raw audio or transcripts in analytics.</li><li>Only a small allowlist of product events is collected.</li><li>Mock providers make this local dashboard safe to explore.</li></ul></section></>}</main>;
}
function Metric({ label, value }: { label: string; value: number }) { return <article className="metric"><span>{label}</span><strong>{value}</strong><small>Local demo data</small></article>; }
