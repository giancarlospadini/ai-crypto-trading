# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Open Alpha Arena is an AI-powered cryptocurrency paper trading platform inspired by nof1 Alpha Arena. It enables users to set up AI trading bots for the crypto market with paper trading capabilities, integrating OpenAI-compatible APIs and CCXT for market data.

**Tech Stack:**
- Backend: FastAPI + SQLAlchemy + Uvicorn (Python 3.10+)
- Frontend: React + Vite + TypeScript
- Package Management: pnpm (frontend/workspace), uv (Python)
- Database: SQLite (via SQLAlchemy)
- Market Data: CCXT library
- Scheduling: APScheduler for automated trading and data tasks

## Development Commands

### Installation
```bash
# Install all dependencies (JS + Python)
pnpm run install:all
```

### Development Servers
```bash
# Start both backend (5611) and frontend (5621)
pnpm run dev

# Backend only (with uv sync)
pnpm run dev:backend

# Frontend only
pnpm run dev:frontend

# Backend with custom port
cd backend && uv sync && uv run uvicorn main:app --reload --port 5621 --host 0.0.0.0
```

**Port Configuration Note:** Frontend source expects port 5621, but workspace default runs backend on 5611. Update [frontend/app/main.tsx](frontend/app/main.tsx) WebSocket URL and API_BASE if using different ports.

### Build
```bash
# Build frontend (backend has no build step yet)
pnpm run build
```

### Code Quality
```bash
# Format Python code
cd backend && uv run black backend

# Lint Python code
cd backend && uv run ruff check backend

# Run backend tests (if implemented)
cd backend && uv run pytest backend/tests
```

## Architecture

### Backend Structure (`backend/`)

**Entry Point:** [main.py](backend/main.py)
- FastAPI application with CORS middleware
- Startup: creates DB tables, seeds default configs, initializes default user/account, starts scheduler and auto-trading
- Serves static frontend files from `backend/static/`
- Includes WebSocket endpoint at `/ws` for real-time updates

**Database Models:** [database/models.py](database/models.py)
- **User**: Authentication entity (currently uses single "default" user)
- **Account**: Trading accounts with AI model configuration (model, base_url, api_key) and balances
- **Position**: Holdings for each account (supports fractional crypto quantities)
- **Order**: Trading orders with status tracking
- **Trade**: Executed trade records with commission
- **TradingConfig**: Market-specific trading rules (commission rates, lot sizes)
- **CryptoPrice/CryptoKline**: Market data storage
- **AIDecisionLog**: Tracks AI reasoning and trading decisions

**Domain Layers:**
- `api/`: Route handlers (market_data, orders, accounts, crypto, config, ranking, websocket)
- `services/`: Business logic including:
  - `startup.py`: Service initialization/shutdown orchestration
  - `auto_trader.py`: AI-driven and random crypto trading logic
  - `scheduler.py`: APScheduler wrapper for recurring tasks
  - `market_data.py`: CCXT integration for price/kline data
  - `order_executor.py`, `order_matching.py`: Order processing
  - `ai_decision_service.py`: AI model integration for trading decisions
  - `price_cache.py`: In-memory price caching with TTL
- `repositories/`: Data access layer (account_repo, order_repo, position_repo, etc.)
- `schemas/`: Pydantic DTOs for request/response validation
- `factors/`: Trading factors/indicators (momentum, support levels)
- `config/`: Application settings and default configurations

**Service Lifecycle:**
1. On startup, `services/startup.py` initializes:
   - Scheduler service
   - Market data tasks (price updates, kline fetching)
   - Auto-trading tasks (5-minute interval by default)
   - Price cache cleanup (2-minute interval)
2. Auto-trading executes immediately on startup, then on schedule
3. WebSocket broadcasts real-time updates (trades, orders, positions, AI decisions)

### Frontend Structure (`frontend/`)

**Entry Point:** [app/main.tsx](app/main.tsx)
- Single-file React app with WebSocket singleton
- Manages global state for accounts, positions, orders, trades, AI decisions
- Uses react-hot-toast for notifications

**Components:** `frontend/app/components/`
- `layout/`: Header, Sidebar navigation
- `portfolio/`: Portfolio overview, ComprehensiveView
- `trading/`: Trading interface components
- `crypto/`: Crypto-specific UI components
- `ui/`: Reusable UI primitives (Radix UI + Tailwind)
- `common/`: Shared utilities

**Styling:** Tailwind CSS with custom configuration, lucide-react icons

**Charts:** chart.js + react-chartjs-2, lightweight-charts for candlestick views

### Key Integration Points

1. **AI Trading Flow:**
   - `services/auto_trader.py` → `services/ai_decision_service.py` (calls AI API with market context)
   - AI returns decision (buy/sell/hold) with reasoning
   - Logs decision to `AIDecisionLog`
   - If actionable, creates order via `services/order_executor.py`
   - Order processed by `services/order_matching.py` (simulated matching)
   - Updates account balances and positions via repositories
   - Broadcasts updates via WebSocket

2. **Market Data Pipeline:**
   - Scheduler triggers `services/market_data.py` at intervals
   - Fetches crypto prices/klines from CCXT
   - Stores in `CryptoPrice`/`CryptoKline` tables
   - Updates `price_cache.py` for fast access
   - Frontend polls or receives updates via WebSocket

3. **WebSocket Communication:**
   - Single connection per client at `/ws`
   - Server broadcasts: trades, orders, positions, AI decisions, account updates
   - Frontend updates UI reactively on message receipt

## Development Guidelines

### Python Code Style
- Format with `black` (4-space indentation)
- Lint with `ruff`
- Use explicit service/repository names
- DTOs in `backend/schemas/`
- SQLAlchemy models use DECIMAL for monetary values

### TypeScript/React Style
- Functional components in PascalCase
- Hooks and utils in camelCase
- Tailwind classes grouped: layout → typography → effects
- Co-locate UI primitives in `components/`

### Database Considerations
- SQLite default (file-based, created automatically)
- All models use SQLAlchemy ORM
- Use repositories for data access, not direct model queries in routes
- Decimal precision: 18 decimal places for crypto quantities, 6 for prices

### Testing
- Backend tests run via `uv run pytest backend/tests` (directory may not exist yet)
- Test naming convention: `test_<behavior_under_test>`
- No frontend tests currently implemented

### Commit Style
- Short, imperative messages (e.g., "fix trader retry", "add candles chart")
- Squash noisy commits before merge
- Reference issues/tickets in PR descriptions
- Attach screenshots for UI changes

## Important Notes

- **Default User System**: Currently uses single "default" user (no authentication). Non-default users are cleaned on startup.
- **Paper Trading Only**: No real money involved. Future TODO: leverage, real trading.
- **AI Model Config**: Each account stores its own `model`, `base_url`, `api_key` for OpenAI-compatible APIs.
- **Port Mismatch**: Be aware of frontend hardcoded ports vs. workspace defaults when debugging connectivity issues.
- **Auto-Trading**: Starts immediately on app launch and runs every 5 minutes by default.
- **WebSocket Singleton**: Frontend uses module-level singleton to prevent duplicate connections in React StrictMode.

## References

- [AGENTS.md](AGENTS.md): Repository coding guidelines, module organization, testing conventions (more detailed than README)
- [README.md](README.md): Basic getting started, prerequisites, star history
