# NPL PDP Audit Copilot

A conversational web application that audits Dell Product Detail Pages (PDPs) against Sprint/Launch, R2, or R3 checkpoints using agentic LLM evaluation.

## Features

- Multi-URL PDP auditing (up to 5 URLs)
- Agentic checkpoint application using Dell DSX
- Evidence-backed findings with exact rule and page citations
- Cross-page and run-over-run comparisons
- Interactive dashboard with filtering and drill-down
- Deterministic fact tools for units, links, and accessibility

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 18+
- MongoDB 7+ (or use Docker Compose)
- Dell DSX API credentials (optional for demo)

### Using Docker Compose

```bash
# Start services
docker compose up -d

# View logs
docker compose logs -f

# Stop services
docker compose down
```

### Local Development

#### Backend

```bash
cd backend

# Install dependencies
uv sync --python 3.12 --extra dev

# Install Playwright browsers
uv run playwright install chromium

# Set environment variables
Copy-Item .env.example .env
# Live audits need DSX credentials; SMTP is only needed for report delivery

# Start MongoDB (or use Docker)
docker run -d -p 27017:27017 --name mongodb mongo:7

# Run API
uvicorn app.main:app --reload
```

#### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev

# Run DDS frontend E2E smoke test
npm run test:e2e
```

## API Endpoints

- `GET /health` - Health check
- `GET /api/framework` - Rule version and ingestion status
- `POST /api/chat` - Conversation interface
- `POST /api/audits` - Create audit definition
- `POST /api/audits/{id}/runs` - Queue audit run
- `GET /api/runs/{id}/status` - Poll run progress
- `GET /api/runs/{id}/issues` - Filter issues
- `GET /api/runs/{id}/report` - Generate report
- `GET /api/runs/{id}/comparison` - Compare runs
- `POST /api/schedules` - Create recurring schedule
- `GET /api/schedules` - List schedules
- `PATCH /api/schedules/{id}` - Pause/resume/update schedule
- `DELETE /api/schedules/{id}` - Delete schedule
- `POST /api/deliveries/{id}/retry` - Retry report delivery

## Configuration

See `backend/.env.example` for environment variables:

- `MONGODB_URI` - MongoDB connection string
- `MONGODB_DB_NAME` - Database name
- `DSX_BASE_URL` - Dell GenAI gateway URL
- `DSX_CLIENT_ID` - Dell GenAI client ID (client-credentials auth)
- `DSX_CLIENT_SECRET` - Dell GenAI client secret
- `DSX_API_KEY` - Dell GenAI API key (secondary)
- `DSX_AUTH_METHOD` - Auth method: `client` or `server` (default: `client`)
- `DSX_MODEL` - Model name (default: `gpt-oss-120b`)
- `DSX_VERIFY_TLS` - TLS verification (default: `true`, uses OS trust store)
- `DSX_CA_BUNDLE` - Optional custom CA bundle PEM path
- `DSX_JSON_MODE` - Use JSON-object response mode (default: `true`)
- `DSX_TIMEOUT_SECONDS` - Request timeout (default: `60.0`)
- `DSX_MAX_CONCURRENT` - Parallel DSX checkpoint calls per page (default: `4`)
- `PLAYWRIGHT_TIMEOUT_MS` - Page load timeout
- `PLAYWRIGHT_MAX_CONCURRENT` - Max concurrent browsers
- `PLAYWRIGHT_SAME_HOST_DELAY_MS` - Delay between same-host requests
- `PLAYWRIGHT_HEADLESS` - `true` runs Chromium hidden (default); `false` shows each audited page in a visible browser window (needs a desktop session, not for Docker)
- `CRAWL_MAX_CONCURRENT` - Concurrent page fetches
- `CRAWL_SAME_HOST_DELAY_MS` - Per-host crawl delay
- `CRAWL_MAX_DEPTH` - Maximum crawl depth
- `CRAWL_DEFAULT_PAGE_LIMIT` - Default page limit
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD` - Dell SMTP relay configuration
- `SMTP_USE_TLS` - Enable SMTP TLS
- `SMTP_FROM` - Report sender address
- `SCHEDULER_ENABLED` - Enable recurring schedule worker
- `SCHEDULER_POLL_SECONDS` - Schedule polling interval
- `SCHEDULER_TIMEZONE` - Default schedule timezone
- `DEMO_MODE` - Reported in `/health` and diagnostics only; no effect on audits

## Testing

```bash
cd backend

# Run all backend tests
uv run pytest

# Run E2E tests against a running stack
uv run pytest tests/e2e/ -v

# Lint
ruff check .

# Type check
basedpyright app
```

## Architecture

- **Backend**: FastAPI + Pydantic + MongoDB + Playwright
- **Frontend**: React + Vite + TypeScript
- **AI**: Dell GenAI gateway via `csoutils[ai]` DSXClient (OpenAI-compatible) for agentic checkpoint evaluation
- **Persistence**: MongoDB for audit history and findings

## Documentation

- [Hackathon Design](docs/superpowers/specs/2026-10-05-npl-agentic-pdp-audit-hackathon-design.md)
- [Glossary](GLOSSARY.md)
- [ADR-0001: Agentic Rule Application](docs/adr/0001-agentic-rule-application.md)
- [ADR-0002: Hackathon Runtime](docs/adr/0002-hackathon-runtime.md)
- [Implementation Plan](docs/superpowers/plans/2026-10-05-npl-agentic-pdp-audit-implementation.md)

## License

Internal hackathon project.
