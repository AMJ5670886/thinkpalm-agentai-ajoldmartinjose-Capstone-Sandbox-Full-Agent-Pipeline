"use client";

import { useCallback, useEffect, useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

type AgentStep = { agent: string; status: string; summary: string };
type ToolCall = {
  tool: string;
  input: Record<string, unknown>;
  output: Record<string, unknown>;
};
type ComponentCode = { name: string; code: string };
type PRDRecord = {
  id: string;
  summary: string;
  prd_text: string;
  analysis: { devices: string[]; widgets: string[] };
  created_at: string;
};
type MemoryData = {
  preferences: Record<string, unknown>;
  previous_prds: PRDRecord[];
  generated_layouts: unknown[];
};
type PipelineResult = {
  steps: AgentStep[];
  tool_calls: ToolCall[];
  memory_display: string;
  analysis: { devices: string[]; widgets: string[] } | null;
  ui_plan: {
    layout: { sidebar: boolean; topbar: boolean; main_widgets: string[] };
  } | null;
  code: { components: ComponentCode[]; entrypoint: string | null } | null;
  component_tree: string[];
  error: string | null;
};

const SAMPLE_PRD = `Smart Building Energy Monitor

Devices: temperature sensors, smart meters, occupancy sensors.

KPIs: total power (kW), average zone temperature, daily cost.
Charts: 24h temperature line chart, weekly energy bar chart.
Alerts: high temperature warning, offline sensor banner.
Tables: device list with status; alert event log.
Controls: HVAC eco toggle, temperature setpoint slider.`;

export default function Home() {
  const [prd, setPrd] = useState(SAMPLE_PRD);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<PipelineResult | null>(null);
  const [memory, setMemory] = useState("");
  const [previousPrds, setPreviousPrds] = useState<PRDRecord[]>([]);
  const [selectedComponent, setSelectedComponent] = useState<string | null>(null);

  const loadMemory = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/memory`);
      const data = await res.json();
      setMemory(data.display ?? "");
      const mem = data.data as MemoryData | undefined;
      setPreviousPrds(mem?.previous_prds ?? []);
    } catch {
      setMemory("(API offline — start: uvicorn api.main:app --reload)");
      setPreviousPrds([]);
    }
  }, []);

  useEffect(() => {
    loadMemory();
  }, [loadMemory]);

  const generate = async () => {
    setLoading(true);
    setResult(null);
    setSelectedComponent(null);
    try {
      const res = await fetch(`${API_BASE}/api/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prd }),
      });
      const data: PipelineResult = await res.json();
      setResult(data);
      if (data.code?.components?.[0]) {
        setSelectedComponent(data.code.components[0].name);
      }
      await loadMemory();
    } catch (e) {
      setResult({
        steps: [],
        tool_calls: [],
        memory_display: "",
        analysis: null,
        ui_plan: null,
        code: null,
        component_tree: [],
        error: String(e),
      });
    } finally {
      setLoading(false);
    }
  };

  const previewCode =
    result?.code?.components.find((c) => c.name === selectedComponent)?.code ??
    result?.code?.components[0]?.code ??
    "// Generate a dashboard to preview code";

  return (
    <main className="min-h-screen p-6 max-w-7xl mx-auto">
      <header className="mb-8">
        <h1 className="text-2xl font-bold text-white">IoT Dashboard Generator</h1>
        <p className="text-slate-400 mt-1">
          Multi-agent pipeline · Memory · Tool: searchTailwindComponent
        </p>
      </header>

      <div className="grid lg:grid-cols-2 gap-6">
        {/* PRD input */}
        <section className="rounded-xl border border-slate-700 bg-slate-900/80 p-4">
          <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wide mb-3">
            PRD Input
          </h2>
          <textarea
            className="w-full h-48 rounded-lg bg-slate-950 border border-slate-600 p-3 text-sm font-mono text-slate-100 focus:outline-none focus:ring-2 focus:ring-cyan-500"
            value={prd}
            onChange={(e) => setPrd(e.target.value)}
            placeholder="Paste IoT product requirements..."
          />
          <div className="mt-3">
            <button
              type="button"
              onClick={generate}
              disabled={loading}
              className="px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 font-medium text-white"
            >
              {loading ? "Generating…" : "Generate Dashboard"}
            </button>
          </div>
        </section>

        {/* Memory */}
        <section className="min-w-0 rounded-xl border border-slate-700 bg-slate-900/80 p-4 overflow-hidden">
          <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wide mb-3">
            Memory
          </h2>
          <pre className="text-xs font-mono text-emerald-400/90 whitespace-pre-wrap break-words max-h-36 overflow-auto mb-3">
            {result?.memory_display || memory}
          </pre>
          {previousPrds.length > 0 && (
            <div className="border-t border-slate-700 pt-3">
              <h3 className="text-xs font-semibold text-slate-400 uppercase mb-2">
                Previous PRDs ({previousPrds.length}) — click to load
              </h3>
              <ul className="max-h-40 overflow-auto space-y-1">
                {[...previousPrds].reverse().map((rec) => (
                  <li key={rec.id}>
                    <button
                      type="button"
                      onClick={() => setPrd(rec.prd_text)}
                      className="w-full text-left text-xs rounded px-2 py-1.5 hover:bg-slate-800 text-slate-300 break-words [overflow-wrap:anywhere]"
                      title={rec.prd_text}
                    >
                      <span className="text-cyan-500 font-mono">[{rec.id}]</span>{" "}
                      {rec.summary.length > 90
                        ? `${rec.summary.slice(0, 87)}…`
                        : rec.summary}
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </section>
      </div>

      {result?.error && (
        <p className="mt-4 text-red-400 text-sm break-words [overflow-wrap:anywhere]">
          Error: {result.error}
        </p>
      )}

      {result && !result.error && (
        <div className="mt-6 grid lg:grid-cols-3 gap-6 min-w-0">
          {/* Agent workflow */}
          <section className="min-w-0 rounded-xl border border-slate-700 bg-slate-900/80 p-4 overflow-hidden">
            <h2 className="text-sm font-semibold text-slate-300 uppercase mb-3">
              Agent Workflow
            </h2>
            <ul className="space-y-2">
              {result.steps.map((s) => (
                <li
                  key={s.agent}
                  className="flex items-start gap-2 text-sm border-l-2 border-cyan-600 pl-3"
                >
                  <span
                    className={
                      s.status === "done"
                        ? "text-emerald-400"
                        : s.status === "error"
                          ? "text-red-400"
                          : "text-cyan-400"
                    }
                  >
                    {s.status === "done" ? "✓" : s.status === "error" ? "✗" : "…"}
                  </span>
                  <div>
                    <div className="font-medium text-slate-200">{s.agent}</div>
                    {s.summary && (
                      <div className="text-slate-500 text-xs">{s.summary}</div>
                    )}
                  </div>
                </li>
              ))}
            </ul>
            {result.tool_calls.length > 0 && (
              <div className="mt-4 pt-4 border-t border-slate-700">
                <h3 className="text-xs font-semibold text-slate-400 uppercase mb-2">
                  Tool Calls
                </h3>
                {result.tool_calls.map((t, i) => (
                  <div
                    key={i}
                    className="text-xs font-mono text-slate-400 mb-2 rounded-md bg-slate-950/60 p-2 break-words [overflow-wrap:anywhere]"
                  >
                    <span className="text-violet-400">{t.tool}</span>(
                    {JSON.stringify(t.input)}) →{" "}
                    <span className="text-emerald-400">
                      {JSON.stringify(t.output)}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </section>

          {/* Component tree */}
          <section className="min-w-0 rounded-xl border border-slate-700 bg-slate-900/80 p-4 overflow-hidden">
            <h2 className="text-sm font-semibold text-slate-300 uppercase mb-3">
              Component Tree
            </h2>
            <pre className="text-sm font-mono text-cyan-200/90 whitespace-pre-wrap break-words">
              {result.component_tree.join("\n") || "—"}
            </pre>
            {result.analysis && (
              <div className="mt-4 text-xs text-slate-500">
                <p>Devices: {result.analysis.devices.join(", ")}</p>
                <p className="mt-1">
                  Widgets: {result.analysis.widgets.slice(0, 5).join(", ")}
                  {result.analysis.widgets.length > 5 ? "…" : ""}
                </p>
              </div>
            )}
            {result.code?.components && (
              <ul className="mt-3 space-y-1">
                {result.code.components.map((c) => (
                  <li key={c.name}>
                    <button
                      type="button"
                      onClick={() => setSelectedComponent(c.name)}
                      className={`text-sm px-2 py-1 rounded w-full text-left ${
                        selectedComponent === c.name
                          ? "bg-cyan-900/50 text-cyan-200"
                          : "hover:bg-slate-800 text-slate-300"
                      }`}
                    >
                      {c.name}.tsx
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </section>

          {/* Code preview */}
          <section className="min-w-0 rounded-xl border border-slate-700 bg-slate-900/80 p-4 lg:col-span-1 overflow-hidden">
            <h2 className="text-sm font-semibold text-slate-300 uppercase mb-3">
              Code Preview
              {selectedComponent && (
                <span className="text-cyan-400 font-normal ml-2">
                  {selectedComponent}
                </span>
              )}
            </h2>
            <pre className="text-xs font-mono text-slate-300 h-80 overflow-auto bg-slate-950 rounded-lg p-3 border border-slate-800 whitespace-pre-wrap break-words">
              {previewCode}
            </pre>
          </section>
        </div>
      )}
    </main>
  );
}
