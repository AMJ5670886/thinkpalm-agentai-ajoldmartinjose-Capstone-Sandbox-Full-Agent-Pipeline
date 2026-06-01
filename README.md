# IoT Dashboard Generator

Multi-agent app that turns an IoT PRD into a UI plan and React + Tailwind code. FastAPI backend + Next.js UI.

## Prerequisites

- Python 3.11+
- Node.js 18+
- API key (OpenAI or Groq)

## Setup

```bash
# From project root
python -m venv .venv

# Windows
.venv\Scripts\activate

pip install -r requirements.txt
copy .env.example .env          # Windows
# cp .env.example .env          # macOS/Linux

Edit .env and set GROQAI_API_KEY.

cd web
npm install
copy .env.local.example .env.local   # Windows

## Run
Terminal 1 — API (port 8000)

python run_api.py

Terminal 2 — Web UI (port 3000)

cd web
npm run dev
Open http://localhost:3000, paste a PRD, and click Generate Dashboard.
