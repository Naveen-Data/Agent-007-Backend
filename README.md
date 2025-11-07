# Agent 007 Backend

🕵️ AI-powered chatbot backend built with FastAPI, LangChain, and Google Gemini.

## Features

- 🤖 **Multi-mode AI Agent**: RAG, Tools, and Heavy processing modes
- 🔗 **LangChain Integration**: Advanced prompt engineering and chain management
- 🧠 **Google Gemini**: Powered by Google's latest generative AI models
- 📚 **Vector Database**: ChromaDB for semantic search and retrieval
- 🛠️ **HTTP Tools**: Built-in tools for web requests and data fetching
- 📊 **LangSmith Tracing**: Optional observability and debugging
- 🚀 **FastAPI**: High-performance async API with automatic documentation

## Quick Start

### Prerequisites

- Python 3.11 or higher
- Google Gemini API key
- Virtual environment (recommended)

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd Agent_007_Backend
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

5. **Run the server:**
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

6. **Access the API:**
   - **API Base:** http://localhost:8000
   - **Health Check:** http://localhost:8000/health
   - **API Docs:** http://localhost:8000/docs
   - **Chat Endpoint:** POST http://localhost:8000/api/chat/send

## API Reference

### Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "ok"
}
```

### Chat Endpoint
```http
POST /api/chat/send
Content-Type: application/json

{
  "message": "Your message here",
  "mode": "rag"  // "rag" | "tools" | "heavy"
}
```

**Response:**
```json
{
  "reply": "AI response",
  "used_tools": []
}
```

## Agent Modes

### 1. RAG Mode (Default)
- Uses Retrieval-Augmented Generation
- Searches vector database for relevant context
- Best for knowledge-based questions

### 2. Tools Mode
- Can execute HTTP requests
- Use: "fetch https://api.example.com" to make web requests
- Best for real-time data fetching

### 3. Heavy Mode
- Uses the more powerful Gemini Pro model
- Slower but more capable reasoning
- Best for complex analysis tasks

## Configuration

### Environment Variables

```env
# Google Gemini API
GOOGLE_API_KEY=your_gemini_api_key_here
GEMINI_DEFAULT_MODEL=gemini-2.5-flash-lite
GEMINI_HEAVY_MODEL=gemini-2.5-pro
EMBEDDING_MODEL=gemini-embedding-001

# LangSmith (Optional)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_key
LANGCHAIN_PROJECT=agent_007

# Server Settings
BACKEND_PORT=8000
ALLOWED_ORIGINS=*

# Vector Database
CHROMA_DIR=./chroma_db
```

### API Keys Setup

1. **Google Gemini API Key:**
   - Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
   - Create a new API key
   - Add to `.env` file

2. **LangSmith API Key (Optional):**
   - Visit [LangSmith](https://smith.langchain.com/)
   - Create account and get API key
   - Add to `.env` file for tracing

## Project Structure

```
Agent_007_Backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Configuration and settings
│   ├── models.py            # Pydantic models for API
│   ├── embeddings.py        # Google Gemini embeddings
│   ├── vectorstore.py       # ChromaDB vector database
│   ├── routers/
│   │   └── chat.py         # Chat API endpoints
│   ├── services/
│   │   ├── agent_service.py # Main agent orchestration
│   │   └── llm_service.py  # LLM wrapper service
│   └── tools/
│       ├── base.py         # Base tool class
│       └── http_tool.py    # HTTP request tool
├── tests/
│   └── test_smoke.py       # Basic smoke tests
├── requirements.txt        # Python dependencies
├── Dockerfile             # Docker configuration
└── .env.example          # Environment variables template
```

## Development

### Running Tests
```bash
python -m pytest tests/ -v
```

### Docker Deployment
```bash
# Build image
docker build -t mr-agent-007-backend .

# Run container
docker run -p 8000:8000 --env-file .env mr-agent-007-backend
```

### Adding New Tools
1. Create tool class inheriting from `ToolSpec`
2. Implement `_run()` method
3. Add tool to agent service
4. Update documentation

## Performance

- **Startup:** ~3-5 seconds
- **RAG queries:** ~1-3 seconds
- **Tool execution:** Varies by tool
- **Heavy mode:** ~5-15 seconds

## Troubleshooting

### Common Issues

1. **ImportError: No module named 'app'**
   - Ensure you're running from the project root
   - Check virtual environment activation

2. **Google API Authentication Error**
   - Verify `GOOGLE_API_KEY` in `.env`
   - Check API key permissions

3. **ChromaDB Permission Error**
   - Ensure write permissions for `chroma_db/` directory
   - Check disk space

4. **CORS Issues**
   - Update `ALLOWED_ORIGINS` in `.env`
   - Check frontend URL configuration

### Debug Mode
```bash
uvicorn app.main:app --reload --log-level debug
```

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

- 📧 **Issues:** Use GitHub Issues for bug reports
- 📚 **Documentation:** Check `/docs` endpoint when running
- 💬 **Discussions:** Use GitHub Discussions for questions