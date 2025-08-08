# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Running the Application
```bash
# Quick start using provided script
chmod +x run.sh
./run.sh

# Manual start (from backend directory)
cd backend
uv run uvicorn app:app --reload --port 8000
```

### Package Management
```bash
# Install/sync dependencies
uv sync

# Add new dependencies
uv add package-name

# Development dependencies
uv add --dev package-name
```

### Environment Setup
- Create `.env` file in root directory with `ANTHROPIC_API_KEY=your_key_here`
- Python 3.13 required (configured in pyproject.toml)
- Always use uv to run the server do not use pip directly
- Make sure to use uv to manage all dependencies
- Use uv to run Python files for consistent environment management

## Architecture Overview

This is a **Retrieval-Augmented Generation (RAG) system** for course materials built with:

### Backend Architecture (FastAPI + RAG Pipeline)
```
RAGSystem (rag_system.py) - Main orchestrator
├── DocumentProcessor - Extracts course structure from text files
├── VectorStore (ChromaDB) - Stores course chunks and metadata
├── AIGenerator (Anthropic Claude) - Generates responses using tools
├── SessionManager - Manages conversation history
└── ToolManager + CourseSearchTool - Provides semantic search capabilities
```

### Core Components
- **Models** (`models.py`): `Course`, `Lesson`, `CourseChunk` data structures
- **Vector Store** (`vector_store.py`): ChromaDB-based semantic search with sentence transformers
- **Document Processing** (`document_processor.py`): Text chunking with sentence-aware splitting
- **AI Generation** (`ai_generator.py`): Claude API integration with tool calling
- **Search Tools** (`search_tools.py`): Semantic search tool for course content

### Frontend
- Vanilla JavaScript SPA in `/frontend/`
- Real-time chat interface with session management
- Course statistics sidebar
- Served as static files by FastAPI

### Key Data Flow
1. Course documents (txt files) → DocumentProcessor → structured Course/Lesson objects
2. Course content → VectorStore (ChromaDB) for semantic search
3. User queries → AI Generator with tool access → CourseSearchTool → ChromaDB → contextual response

## Configuration

All settings in `config.py`:
- `CHUNK_SIZE`: 800 characters for vector chunks
- `CHUNK_OVERLAP`: 100 characters between chunks
- `MAX_RESULTS`: 5 search results per query
- `MAX_HISTORY`: 2 conversation messages remembered
- `CHROMA_PATH`: "./chroma_db" for vector storage

## Development Notes

### Adding Course Content
- Place text files in `/docs/` directory
- App auto-loads documents on startup from `../docs` relative to backend
- Uses `add_course_folder()` method with duplicate detection

### API Endpoints
- `POST /api/query` - Main chat endpoint with session management
- `GET /api/courses` - Course analytics and statistics
- Static file serving for frontend at root `/`

### Tool-Based Search Architecture
The system uses Claude's tool calling capabilities rather than traditional RAG context injection:
- AI Generator has access to CourseSearchTool
- Tool performs semantic search when needed
- Responses synthesized from tool results
- Session management maintains conversation context
