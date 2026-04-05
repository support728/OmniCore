# FastAPI RAG Backend (Async Postgres + pgvector + S3 + Celery)

## What This Includes
- Async FastAPI backend
- Async Postgres with pgvector for vector search
- File upload to S3 (MinIO-compatible)
- Backend ingestion pipeline with Celery
- RAG chat endpoint using vector similarity search
- Clarity engine response format: answer + sources + insight

## Project Structure
- app/main.py: FastAPI app entry
- app/api/routes.py: Upload, document status, and RAG chat endpoints
- app/models.py: Document and Chunk tables with pgvector embeddings
- app/workers/tasks.py: Celery ingestion task
- app/services/clarity_engine.py: answer + sources + insight output builder

## 1) Start Infrastructure
```bash
docker compose up -d
```

## 2) Install Python Dependencies
```bash
python -m venv .venv
. .venv/Scripts/activate
pip install -r requirements.txt
```

## 3) Configure Environment
```bash
copy .env.example .env
```

For production, start from:
```bash
copy .env.production.example .env
```

## 4) Run API
```bash
uvicorn run:app --reload --port 8000
```

## 5) Run Celery Worker
```bash
celery -A app.workers.celery_app.celery_app worker --loglevel=info
```

## Production Deployment (Simple Docker)

1) Create production env file and set real secrets:
```bash
copy .env.production.example .env
```

2) Update at minimum:
- POSTGRES_PASSWORD
- AWS_SECRET_ACCESS_KEY
- OPENAI_API_KEY
- CORS_ALLOWED_ORIGINS
- TRUSTED_HOSTS

3) Build and run production stack:
```bash
docker compose -f docker-compose.prod.yml --env-file .env up -d --build
```

Or on PowerShell, use helper script:
```powershell
pwsh ./scripts/deploy_prod.ps1 -EnvFile .env -ComposeFile docker-compose.prod.yml
```

4) Check status:
```bash
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f api
```

5) Health check:
```bash
curl http://localhost:8002/health
```

Run automated post-deploy smoke test:
```powershell
pwsh ./scripts/smoke_test.ps1
```

See 24-hour launch plan: [DEPLOY_24H_RUNBOOK.md](DEPLOY_24H_RUNBOOK.md)

## Production Config Notes
- [app/main.py](app/main.py): gzip enabled, optional CORS and trusted host middleware driven by env vars.
- [app/config.py](app/config.py): supports DEBUG, API host/port, log level, worker concurrency, and security-related env values.
- [docker-compose.prod.yml](docker-compose.prod.yml): single-command stack for postgres, redis, minio, api, and celery worker.

## Endpoints
- GET /health
- POST /api/upload (multipart file)
- GET /api/documents/{document_id}
- POST /api/chat/rag

## Sample RAG Request
```json
{
  "question": "Summarize the main risks in the uploaded report",
  "top_k": 5
}
```

## Clarity Response Shape
```json
{
  "answer": "...",
  "sources": [
    {
      "document_id": "...",
      "filename": "report.txt",
      "chunk_index": 0,
      "score": 0.88,
      "excerpt": "..."
    }
  ],
  "insight": {
    "confidence": 0.88,
    "retrieval_notes": "Retrieved 5 chunk(s)...",
    "recommended_next_question": "Do you want a deeper comparison across the top sources?"
  },
  "raw_context": []
}
```
