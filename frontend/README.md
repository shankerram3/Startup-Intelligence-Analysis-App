# GraphRAG Frontend (React + Vite)

Simple web UI for running queries against the FastAPI backend in `api.py`.

## Prereqs
- Node.js 18+ and npm (or pnpm/yarn)
- Backend running locally at `http://localhost:8000` (see repository `HOW_TO_RUN.md`)

## Configure API base URL
Create a `.env.local` file in this folder to point to your backend (optional; defaults to `http://localhost:8000`).

```
VITE_API_BASE_URL=http://localhost:8000
```

## Install & run
```bash
# From repo root
cd frontend
npm install
npm run dev
# Open the URL shown (default: http://localhost:5173)
```

## Build for production
```bash
npm run build
npm run preview
```

## Features
- Query tab calls `POST /query` with `question`, `return_context`, `use_llm`
- Semantic Search tab calls `POST /search/semantic` with `query`, `top_k`, `entity_type`

You can expand the UI to include other endpoints (entities, analytics, etc.).

## Notes
- CORS is enabled in the backend (`allow_origins=["*"]`); restrict in production.
- If you prefer a proxy instead of CORS, add a Vite `server.proxy` entry and use relative `/api` paths.

