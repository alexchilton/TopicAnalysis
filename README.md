# 📊 Topic Analysis Dashboard

A production-ready full-stack application for multilingual sentiment analysis, dynamic topic clustering, and anomaly detection on customer feedback data.

## Features

- **Multi-format ingestion**: CSV, JSON, Excel (.xlsx/.xls), ZIP archives with automatic text column detection
- **Multilingual support**: Automatic language detection (langdetect + cld3 fallback) with XLM-RoBERTa sentiment analysis
- **Dynamic topic clustering**: BERTopic (HDBSCAN + UMAP) with adaptive parameters based on data volume
- **Interactive dashboard**: Sentiment trends with confidence intervals, force-directed topic graph, data quality reports
- **Real-time updates**: Webhook ingestion with Stripe-style signature verification, SSE for live dashboard updates
- **Anomaly detection**: Alerts on sentiment drift below rolling average, unusual topic spikes, configurable thresholds
- **Notifications**: Slack webhook and email alerts for anomalies
- **Export**: CSV, JSON, PDF report with filtering
- **Comparison mode**: Contrast two time periods or data segments
- **Data quality**: Flags low-confidence predictions, mixed-language entries, and duplicates
- **Observability**: Structured logging (structlog), OpenTelemetry tracing, Prometheus metrics
- **Security**: API key authentication, rate limiting (slowapi), webhook signature verification, input sanitization

## Architecture

```
┌────────────────┐     ┌──────────────────┐     ┌─────────────┐
│   React/TS     │────▶│  Nginx Reverse   │────▶│   FastAPI    │
│   Frontend     │     │  Proxy (:8080)   │     │  Backend     │
│   (Vite)       │     └──────────────────┘     │  (:8000)     │
└────────────────┘                               └──────┬──────┘
                                                        │
                                    ┌───────────────────┼───────────────────┐
                                    │                   │                   │
                              ┌─────▼─────┐     ┌──────▼──────┐    ┌──────▼──────┐
                              │   Redis    │     │  ML Models  │    │  File Store │
                              │  Cache/SSE │     │  (HuggingFace)   │  (uploads/) │
                              └───────────┘     └─────────────┘    └─────────────┘
```

### ML Pipeline Flow

```
Input → Language Detection → Sentiment Analysis → Embedding → Topic Clustering → Anomaly Detection → Results
         (langdetect/cld3)   (XLM-RoBERTa)       (MiniLM)     (BERTopic)        (Z-score)
```

### Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Sentiment Model | `cardiffnlp/twitter-xlm-roberta-base-sentiment` | Multilingual, fine-tuned for social text, good accuracy |
| Embedding Model | `paraphrase-multilingual-MiniLM-L12-v2` | Fast, multilingual, 384-dim (efficient for clustering) |
| Topic Clustering | BERTopic (HDBSCAN + UMAP) | No preset cluster count needed, handles noise |
| Language Detection | langdetect → cld3 | langdetect is fast/accurate; cld3 as reliable fallback |
| Frontend Charts | Recharts | Declarative, React-native, good TS support |
| Caching/PubSub | Redis | Fast, SSE broadcast via pub/sub, standard |
| Rate Limiting | slowapi | Built for FastAPI, per-key limits |
| Logging | structlog | Structured JSON logs, correlation IDs, composable |

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- Redis (for caching/SSE) — optional for dev, required for production

### Development Setup

```bash
# Clone and enter the project
cd TopicAnalysis

# Copy environment config
cp .env.example .env

# Backend setup
cd backend
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
cd ..

# Frontend setup
cd frontend
npm ci
cd ..

# Generate demo data
python scripts/seed_data.py

# Start backend (in one terminal)
make dev-backend

# Start frontend (in another terminal)
make dev-frontend
```

The frontend runs at http://localhost:3000, backend API at http://localhost:8000.

### Docker Setup

```bash
# Copy environment config
cp .env.example .env

# Build and start all services
make build
make up

# View logs
make logs
```

All services run behind nginx at http://localhost:8080.

## API Usage

### Authentication

All API endpoints require an API key via the `X-API-Key` header:

```bash
curl -H "X-API-Key: dev-key-1" http://localhost:8000/api/v1/jobs
```

### Upload Data

```bash
# Upload a CSV file
curl -X POST -H "X-API-Key: dev-key-1" \
  -F "file=@demo_data/demo_feedback.csv" \
  http://localhost:8000/api/v1/upload

# Upload with source label
curl -X POST -H "X-API-Key: dev-key-1" \
  -F "file=@data.json" \
  "http://localhost:8000/api/v1/upload?source=app_store"
```

### Get Results

```bash
# Check job status
curl -H "X-API-Key: dev-key-1" http://localhost:8000/api/v1/jobs/{job_id}/status

# Get full results
curl -H "X-API-Key: dev-key-1" http://localhost:8000/api/v1/jobs/{job_id}
```

### Filter & Export

```bash
# Filter results
curl -X POST -H "X-API-Key: dev-key-1" -H "Content-Type: application/json" \
  -d '{"languages": ["en"], "sentiment_min": 0.7}' \
  http://localhost:8000/api/v1/jobs/{job_id}/filter

# Export as CSV
curl -X POST -H "X-API-Key: dev-key-1" \
  "http://localhost:8000/api/v1/jobs/{job_id}/export?fmt=csv" \
  -o results.csv
```

### Webhook Ingestion

```bash
# Send data via webhook (with signature)
TIMESTAMP=$(date +%s)
PAYLOAD='{"event_type":"feedback","data":[{"text":"Great product!"}]}'
SIGNATURE="v1=$(echo -n "${TIMESTAMP}.${PAYLOAD}" | openssl dgst -sha256 -hmac "whsec_change-me" | awk '{print $2}')"

curl -X POST http://localhost:8000/api/v1/webhooks/ingest \
  -H "Content-Type: application/json" \
  -H "X-Signature: ${SIGNATURE}" \
  -H "X-Timestamp: ${TIMESTAMP}" \
  -d "${PAYLOAD}"
```

### SSE Events

```bash
curl -N -H "X-API-Key: dev-key-1" http://localhost:8000/api/v1/events/analysis
```

## Testing

```bash
# Run all tests
make test

# Backend tests only
make test-backend

# Frontend tests only
make test-frontend

# With coverage
cd backend && python -m pytest tests/ -v --cov=app --cov-report=html
cd frontend && npm test -- --coverage
```

## Linting

```bash
# Run all linters
make lint

# Format code
make format
```

## Project Structure

```
TopicAnalysis/
├── backend/
│   ├── app/
│   │   ├── api/                 # FastAPI route handlers
│   │   │   ├── analysis.py      # Upload, filter, compare endpoints
│   │   │   ├── export.py        # CSV/JSON/PDF export
│   │   │   ├── health.py        # Health/readiness checks
│   │   │   └── webhooks.py      # Webhook + SSE endpoints
│   │   ├── core/                # Framework configuration
│   │   │   ├── config.py        # Pydantic settings
│   │   │   ├── logging.py       # Structured logging + correlation IDs
│   │   │   ├── middleware.py    # Request logging middleware
│   │   │   ├── security.py      # API keys, rate limiting, webhook auth
│   │   │   └── telemetry.py     # OpenTelemetry + Prometheus
│   │   ├── models/
│   │   │   └── schemas.py       # All Pydantic models
│   │   ├── services/            # Business logic
│   │   │   ├── analysis_pipeline.py  # Orchestrates full ML pipeline
│   │   │   ├── anomaly_detection.py  # Sentiment/topic anomalies
│   │   │   ├── data_quality.py       # Quality scoring
│   │   │   ├── export.py             # Export formatters
│   │   │   ├── file_processing.py    # File parsing (CSV/JSON/Excel/ZIP)
│   │   │   ├── language_detection.py # langdetect + cld3
│   │   │   ├── notifications.py      # Slack/email alerts
│   │   │   ├── redis_client.py       # Cache + pub/sub
│   │   │   ├── sentiment.py          # XLM-RoBERTa sentiment
│   │   │   └── topic_clustering.py   # BERTopic clustering
│   │   └── main.py              # FastAPI app entry point
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/          # Reusable UI components
│   │   ├── hooks/               # React hooks
│   │   ├── pages/               # Route pages
│   │   ├── services/            # API client
│   │   ├── types/               # TypeScript types
│   │   └── styles/              # Global CSS
│   ├── package.json
│   └── Dockerfile
├── nginx/                       # Reverse proxy config
├── scripts/                     # Seed data, utilities
├── docker-compose.yml
├── Makefile
├── .github/workflows/ci.yml
├── .pre-commit-config.yaml
└── README.md
```

## Troubleshooting

### Models fail to load / Out of memory

Models download on first use (~1GB total). If you hit OOM:
- Set `MODEL_CACHE_DIR` to a directory with enough space
- The app gracefully degrades: sentiment falls back to keyword-based, clustering is skipped
- For very large files, use chunked upload (automatic for >10MB in the UI)

### Redis connection failed

- In development, the app works without Redis but SSE and caching are disabled
- For Docker: ensure Redis container is healthy (`docker compose ps`)
- Check `REDIS_URL` in your `.env`

### Language detection returns "unknown"

- Very short texts (<3 characters) default to "unknown"
- If langdetect fails, cld3 fallback is tried
- If cld3 isn't installed (`pycld3`), install it: `pip install pycld3`

### Frontend won't connect to backend

- In development, Vite proxies `/api` to `localhost:8000` (configured in `vite.config.ts`)
- In Docker, nginx handles routing
- Check CORS origins in `.env` match your frontend URL

### Webhook signature validation fails

- Ensure `WEBHOOK_SECRET` in `.env` matches the signing secret
- Timestamp must be within 5 minutes of current time
- Signature format: `v1=<hex-hmac-sha256>`

### Rate limiting

- Default: 60 requests/minute per API key
- Configure via `RATE_LIMIT_PER_MINUTE` in `.env`
- Rate limits are per API key, not per IP

## Monitoring

- **Prometheus metrics**: `GET /metrics`
- **Health check**: `GET /health`
- **Liveness probe**: `GET /health/live`
- **Readiness probe**: `GET /health/ready`
- **Structured logs**: JSON format to stdout with correlation IDs

## License

MIT
