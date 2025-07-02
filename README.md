# SUBFRACTURE - AI-Native Brand Intelligence Platform

The world's first AI-native collaborative brand intelligence platform, powered by FastMCP and liquid glass visualization.

## 🚀 Architecture Overview

- **Backend**: FastMCP server with 15 brand intelligence tools
- **Frontend**: React + Three.js with real-time collaboration
- **Database**: SQLAlchemy with async operations
- **Real-time**: WebSocket for live collaboration
- **AI Integration**: FastMCP tool ecosystem with cognitive state management

## 📁 Project Structure

```
subfracture-production/
├── server/                 # FastMCP server (Python)
│   ├── main.py            # Server entry point
│   ├── database.py        # Database service
│   ├── models.py          # SQLAlchemy models
│   ├── metrics.py         # Prometheus metrics
│   └── tools/             # Brand intelligence tools
│       ├── brand_management.py
│       ├── workshop_collaboration.py
│       ├── coherence_analysis.py
│       ├── temporal_analysis.py
│       └── ai_integration.py
├── client/                # React application
│   ├── src/
│   │   ├── components/    # UI components
│   │   ├── hooks/         # Custom React hooks
│   │   ├── lib/          # MCP client library
│   │   ├── stores/       # Zustand state management
│   │   └── types/        # TypeScript definitions
│   └── package.json
├── config/               # Configuration files
└── docs/                # Documentation
```

## 🛠 Development Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL (optional, defaults to SQLite)

### Backend Setup
```bash
cd server
pip install -r requirements.txt
python main.py
```

### Frontend Setup
```bash
cd client
npm install
npm run dev
```

## 🌐 Production Deployment

### Option 1: Cloud Platform (Recommended)

#### Frontend (Vercel)
```bash
cd client
npm run build
vercel --prod
```

#### Backend (Railway/Render)
```bash
# Deploy FastMCP server
railway deploy
# or
render deploy
```

### Option 2: Docker Deployment
```bash
docker-compose up -d
```

## 🔧 Environment Variables

### Server (.env)
```bash
DATABASE_URL=postgresql://user:pass@host:port/db
SENTRY_DSN=your_sentry_dsn
ENVIRONMENT=production
METRICS_PORT=8000
```

### Client (.env)
```bash
VITE_MCP_SERVER_URL=wss://your-backend.com
VITE_ENVIRONMENT=production
```

## 🎯 Core Features

### Brand Intelligence Tools (15 total)
- **Brand Management**: Create, evolve, and snapshot brands
- **Workshop Collaboration**: Real-time multi-user sessions
- **Coherence Analysis**: Comprehensive brand coherence metrics
- **Temporal Analysis**: Evolution tracking and pattern detection
- **AI Integration**: Cognitive state and insight generation

### Real-time Collaboration
- Multi-user workshop sessions
- Live participant management
- Real-time signal collection
- Synchronized 3D visualization

### 3D Visualization
- Liquid glass brand dimension representation
- Real-time coherence updates
- Connection visualization
- Contradiction and gap indicators

## 🧠 AI-Native Features

### Cognitive State Management
- Analytical vs intuitive thinking balance
- Efficiency optimization
- Dynamic state evolution

### Brand Intelligence
- Narrative analysis
- Emotional mapping
- Competitive positioning
- Gap identification
- Contradiction detection

### Future: AG UI Protocol Integration
Phase 2 will integrate AG UI Protocol for revolutionary AI agent collaboration:
- Dynamic UI generation by AI agents
- Multi-agent workshop orchestration  
- AI-human collaborative brand exploration

## 📊 Monitoring & Analytics

### Built-in Metrics
- Prometheus metrics collection
- Tool execution monitoring
- Real-time session tracking
- Brand health analytics

### Error Handling
- Structured logging with structlog
- Sentry error tracking
- Graceful degradation
- Automatic retry mechanisms

## 🔐 Security Features

- Input validation with Pydantic
- SQL injection protection
- WebSocket security
- Error boundary protection
- Production-ready authentication hooks

## 🚀 Performance Optimizations

### Frontend
- Code splitting and lazy loading
- Three.js performance optimizations
- Efficient state management
- WebSocket connection pooling

### Backend
- Async database operations
- Connection pooling
- Metric-based monitoring
- Resource cleanup

## 📈 Scalability

### Horizontal Scaling
- Stateless FastMCP server design
- Database connection pooling
- Real-time message distribution
- Load balancer ready

### Future Enhancements
- Multi-tenant architecture
- Advanced caching strategies
- CDN integration
- Database sharding

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Implement changes with tests
4. Submit pull request

## 📄 License

Proprietary - SUBFRACTURE AI-Native Brand Intelligence Platform

## 🆘 Support

For technical support or questions:
- Create an issue in the repository
- Contact the development team
- Check the documentation in `/docs`

---

**SUBFRACTURE** - Transforming brand intelligence through AI-native collaboration and liquid glass visualization.