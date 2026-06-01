# AI IoT Dashboard Generator Pipeline

Multi-agent pipeline: IoT PRD → analysis → UI plan → React/Tailwind code, with **memory**, a **custom tool**, and a **Next.js UI**.

## Agents

| Agent | Role |
|-------|------|
| **1 — PRD Analysis** | Extract `devices` + `widgets` |
| **2 — UI Planner** | Layout + `main_widgets` hierarchy |
| **3 — Code Generator** | React + Tailwind TSX (uses tool hints) |

## Custom tool: `searchTailwindComponent`

```powershell
python run_tool_demo.py chart
```

```json
{
  "widget_type": "chart",
  "component": "LineChartCard",
  "style": "responsive",
  "classes": "rounded-lg border bg-card p-4 ..."
}
```

The pipeline calls this tool before Agent 3 for each widget type; results appear in the UI **Tool Calls** panel.

## Memory

```powershell
python run_memory.py set --theme dark --chart-preference line
python run_memory.py show
```

Stored in `data/memory.json`: preferences, previous PRDs, generated layouts.

## Web UI (Next.js + Tailwind)

Single-page app with:

- PRD textarea + **Generate** button
- Agent workflow panel
- Tool calls log
- Component tree
- Code preview
- Memory display

### Run the UI

**Terminal 1 — API**

```powershell
cd "c:\Users\ajold.m\Documents\New folder\LAB3"
.venv\Scripts\activate
pip install -r requirements.txt
python run_api.py
```

**Terminal 2 — Frontend**

```powershell
cd web
copy .env.local.example .env.local
npm install
npm run dev
```

Open http://localhost:3000

## Setup

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

## CLI pipeline

```powershell
python run_pipeline.py examples/sample_prd.txt
```

## Project layout

```
LAB3/
├── agents/
├── tools/
│   └── tailwind_search.py   # searchTailwindComponent
├── pipeline/
│   └── orchestrator.py      # agents + tool calls
├── api/main.py              # FastAPI for UI
├── web/                     # Next.js UI
├── memory/
├── run_tool_demo.py
├── run_api.py
└── run_pipeline.py
```
