# AI Crypto Trading Arena

An advanced AI-powered cryptocurrency paper trading platform that enables users to create and manage multiple AI trading bots with customizable strategies. Inspired by [nof1 Alpha Arena](https://nof1.ai).

## Features

### 🤖 AI Trading Bots
- **Multiple AI Accounts**: Create and manage multiple trading accounts, each with its own AI configuration
- **OpenAI-Compatible APIs**: Support for any OpenAI-compatible API (OpenAI, Anthropic, local LLMs via Ollama/LM Studio)
- **Custom Instructions**: Add specific trading instructions per account (e.g., "Focus on meme coins", "Keep 50% cash")
- **Configurable Analysis**:
  - Toggle **News Feed Integration** (CoinJournal crypto news)
  - Toggle **Technical Analysis** (RSI, SMA, Bollinger Bands, MACD, Momentum, Support Levels)
- **Automated Trading**: AI analyzes market data every 30 minutes and makes trading decisions

### 📊 Trading & Market Data
- **Paper Trading**: Risk-free simulation environment with realistic order execution
- **Real-time Price Feeds**: Live cryptocurrency prices via CCXT library
- **Technical Indicators**:
  - RSI (Relative Strength Index)
  - SMA 20/50 (Simple Moving Averages)
  - EMA 12/26 (Exponential Moving Averages)
  - Bollinger Bands
  - MACD (Moving Average Convergence Divergence)
  - Momentum and Support Factor calculations
- **Historical Kline Data**: Candlestick data for chart analysis
- **Supported Cryptocurrencies**: BTC, ETH, SOL, DOGE, XRP, BNB, ADA, USDC, PENGU, PEPE, XPL, KAITO, LTC, W, VANA

### 📈 Portfolio Management
- **Multi-Account Tracking**: Monitor multiple AI traders simultaneously
- **Real-time Asset Curves**: Visualize portfolio performance over 5-minute, 1-hour, and 1-day intervals
- **Account Rankings**: Compare performance across all trading accounts
- **Position Management**: Track holdings, average costs, and P&L
- **Order & Trade History**: Complete audit trail of all trading activity

### 💬 AI Chat Interface
- **Ask Questions**: Query your AI trading bot about its decisions and market analysis
- **Decision Explanations**: Get detailed reasoning for each trading action
- **Chat History**: Persistent Q&A log linked to trading decisions

### 🔧 Technical Stack
- **Backend**: FastAPI + SQLAlchemy + APScheduler (Python 3.10+)
- **Frontend**: React + Vite + TypeScript + Tailwind CSS
- **Database**: SQLite (easy setup, no external dependencies)
- **Real-time Communication**: WebSocket for live updates
- **Package Management**: pnpm (frontend), uv (Python)

## What's New in This Fork

This project extends the original Open Alpha Arena with:
- ✅ **Configurable News & Technical Analysis**: Toggle features per account
- ✅ **Enhanced Technical Indicators**: Comprehensive TA integration in AI prompts
- ✅ **30-minute Trading Interval**: Reduced from 5 minutes for more deliberate decisions
- ✅ **AI Chat System**: Ask your trading bot questions about its decisions
- ✅ **Multi-account Support**: Run multiple AI strategies simultaneously
- ✅ **Improved UI**: Better chart sizing and account ranking display

## Roadmap

- [ ] Leverage trading simulation
- [ ] Real trading integration (exchange APIs)
- [ ] Custom technical indicator builder
- [ ] Backtesting framework
- [ ] Performance analytics dashboard
- [ ] Risk management rules

## Getting Started

### Prerequisites
- Node.js 18+ and pnpm
- Python 3.10+ and uv

### Install
```bash
# install JS deps and sync Python env
pip install uv
npm install -g pnpm
pnpm run install:all
```

### Development
By default, the workspace scripts launch:
- Backend on port 5611
- Frontend on port 5621

Start both dev servers:
```bash
pnpm run dev
```
Open:
- Frontend: http://localhost:5621
- Backend WS: ws://localhost:5611/ws

Important: The frontend source is currently configured for port  5621. To use the workspace defaults (5611), update the following in frontend/app/main.tsx:
- WebSocket URL: ws://localhost:5611/ws
- API_BASE: http://127.0.0.1:5611

Alternatively, run the backend on  5621:
```bash
# from repo root
cd backend
uv sync
uv run uvicorn main:app --reload --port  5621 --host 0.0.0.0
```

### Build
```bash
# build frontend; backend has no dedicated build step
pnpm run build
```
Static assets for the frontend are produced by Vite. The backend is a standard FastAPI app that can be run with Uvicorn or any ASGI server.



## License
MIT
