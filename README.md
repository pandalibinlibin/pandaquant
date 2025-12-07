# 🐼 PandaQuant

**A Modern Quantitative Trading Research & Backtesting SaaS Platform**

PandaQuant is a comprehensive quantitative trading platform that enables researchers and traders to develop, backtest, and deploy algorithmic trading strategies with ease. Built with modern technologies and best practices, it provides a professional-grade infrastructure for quantitative research.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://react.dev/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 🌟 Key Features

### 📊 Data Management
- **Multi-Source Data Integration**: Seamless integration with TuShare and AKShare for Chinese market data
- **Intelligent Caching**: InfluxDB-based time-series data caching with automatic validation
- **Data Types Support**: Daily OHLCV, minute-level data, financial statements, macro indicators, and industry data
- **Automatic Fallback**: Smart source switching when primary data source fails

### 🧮 Factor Engineering
- **Factor Class System**: Extensible factor framework with automatic discovery
- **Built-in Factors**: Technical indicators (MA, RSI, MACD, KDJ, BOLL), fundamental factors, and report-based factors
- **Parameter Extraction**: Automatic parameter definition extraction using Python reflection
- **Required Fields Detection**: Automatic detection of data fields required by each factor

### 🎯 Strategy Development
- **DataGroup Architecture**: Flexible multi-timeframe and multi-asset strategy design
- **Backtrader Integration**: Professional backtesting engine with comprehensive performance metrics
- **Strategy Templates**: Pre-built strategy templates (Dual Moving Average, RSI Mean Reversion, etc.)
- **Factor Composition**: Combine multiple factors within DataGroups for complex strategies

### 📈 Backtesting Engine
- **Comprehensive Metrics**: Total return, Sharpe ratio, max drawdown, win rate, and 20+ performance indicators
- **Asynchronous Execution**: Non-blocking backtest execution with real-time status updates
- **Historical Records**: Complete backtest history with detailed performance analysis
- **Signal Persistence**: Automatic signal saving to database with backtest association
- **Visual Analytics**: Performance charts and equity curves (coming soon)

### 🔔 Signal Management
- **Signal Persistence**: All trading signals automatically saved to database during backtesting
- **Signal Query API**: RESTful API to retrieve signals by backtest ID and strategy name
- **Signal History**: Complete audit trail of all generated signals with timestamps and prices
- **Backtest Association**: Signals linked to backtest results via foreign key relationships
- **Frontend Integration**: Signal list embedded in backtest detail page with color-coded display
- **Signal Visualization**: Tabular display with time, symbol, action, price, strength, and description
- **Real-time Signals**: Live trading signal generation and monitoring (coming soon)
- **Signal Push**: WebSocket-based signal delivery (coming soon)

### 🎨 Modern UI/UX
- **Responsive Design**: Beautiful and intuitive interface built with Chakra UI v3
- **Dark Mode**: Full dark mode support for comfortable viewing
- **Internationalization**: Complete Chinese and English language support
- **Real-time Updates**: Live data updates using TanStack Query

---

## 🛠️ Technology Stack

### Backend
- ⚡ **[FastAPI](https://fastapi.tiangolo.com)**: High-performance Python web framework
- 🧰 **[SQLModel](https://sqlmodel.tiangolo.com)**: Type-safe ORM for database operations
- 🔍 **[Pydantic](https://docs.pydantic.dev)**: Data validation and settings management
- 💾 **[PostgreSQL](https://www.postgresql.org)**: Relational database for metadata
- 📊 **[InfluxDB](https://www.influxdata.com)**: Time-series database for market data
- 📉 **[Backtrader](https://www.backtrader.com)**: Professional backtesting framework
- 🐼 **[Pandas](https://pandas.pydata.org)**: Data manipulation and analysis
- 📚 **[TuShare](https://tushare.pro)** & **[AKShare](https://akshare.akfamily.xyz)**: Chinese market data sources

### Frontend
- 🚀 **[React 18](https://react.dev)**: Modern UI library with hooks
- 💎 **[TypeScript](https://www.typescriptlang.org)**: Type-safe JavaScript
- ⚡ **[Vite](https://vitejs.dev)**: Lightning-fast build tool
- 🎨 **[Chakra UI v3](https://chakra-ui.com)**: Beautiful component library
- 🔄 **[TanStack Router](https://tanstack.com/router)**: Type-safe routing
- 🔍 **[TanStack Query](https://tanstack.com/query)**: Powerful data fetching
- 🌐 **[React i18next](https://react.i18next.com)**: Internationalization
- 🧪 **[Playwright](https://playwright.dev)**: End-to-end testing

### DevOps
- 🐋 **[Docker](https://www.docker.com)**: Containerization
- 🔧 **[Docker Compose](https://docs.docker.com/compose)**: Multi-container orchestration
- 🔒 **JWT Authentication**: Secure token-based authentication
- 📞 **[Traefik](https://traefik.io)**: Reverse proxy and load balancer
- ✅ **[Pytest](https://pytest.org)**: Backend testing framework

---

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+ (for local development)
- Node.js 18+ (for frontend development)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/pandaquant.git
   cd pandaquant
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start with Docker Compose**
   ```bash
   docker-compose up -d
   ```

4. **Access the application**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Development Setup

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

---

## 📖 Architecture

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (React)                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │   Data   │  │ Factors  │  │Strategies│  │Backtests │   │
│  │Management│  │Management│  │Management│  │ Analysis │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                    ┌───────▼────────┐
                    │   FastAPI      │
                    │   REST API     │
                    └───────┬────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
┌───────▼────────┐  ┌──────▼──────┐  ┌────────▼────────┐
│   PostgreSQL   │  │  InfluxDB   │  │   Backtrader    │
│   (Metadata)   │  │(Time-Series)│  │(Backtest Engine)│
└────────────────┘  └─────────────┘  └─────────────────┘
        │                   │
        │           ┌───────▼────────┐
        │           │  Data Sources  │
        │           │ TuShare/AKShare│
        │           └────────────────┘
        │
┌───────▼────────┐
│  Signal Push   │
│   (WebSocket)  │
└────────────────┘
```

### DataGroup Architecture

PandaQuant uses a unique **DataGroup** architecture for strategy development:

```python
Strategy
  └── DataGroup (e.g., "daily")
       ├── Data Type: daily OHLCV
       ├── Weight: 1.0
       └── Factors
            ├── MA_5_SMA (MovingAverageFactor, period=5)
            ├── MA_20_SMA (MovingAverageFactor, period=20)
            └── RSI_14 (RSIFactor, period=14)
```

This architecture allows:
- Multiple timeframes in one strategy
- Clear factor organization
- Easy strategy composition
- Flexible weight allocation

---

## 📚 Documentation

Detailed documentation is available in Chinese:
- **[Development Documentation](QUANTITATIVE_SYSTEM_DEVELOPMENT.md)**: Complete technical implementation guide
- **API Documentation**: Available at `/docs` when running the backend

---

## 🗺️ Roadmap

### ✅ Completed
- [x] Data management with multi-source integration
- [x] Factor class system with automatic discovery
- [x] Strategy management with DataGroup architecture
- [x] Backtest engine with comprehensive metrics
- [x] Strategy detail page with configuration display
- [x] Signal persistence and query API
- [x] Backtest-signal association with foreign keys
- [x] Signal list integration in backtest detail page
- [x] Internationalization (Chinese/English)

### 🚧 In Progress
- [ ] Real-time signal push (WebSocket)
- [ ] Performance charts and visualizations

### 📋 Planned
- [ ] Paper trading simulation
- [ ] Live trading integration
- [ ] Portfolio management
- [ ] Risk management tools
- [ ] Strategy optimization
- [ ] Machine learning factor discovery
- [ ] Multi-user support with permissions
- [ ] Cloud deployment templates

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Built on top of [FastAPI Full Stack Template](https://github.com/fastapi/full-stack-fastapi-template)
- Data provided by [TuShare](https://tushare.pro) and [AKShare](https://akshare.akfamily.xyz)
- Backtesting powered by [Backtrader](https://www.backtrader.com)

---

## 📧 Contact

For questions and support, please open an issue on GitHub.

---

**⚠️ Disclaimer**: This software is for research and educational purposes only. Use at your own risk. Past performance does not guarantee future results.
