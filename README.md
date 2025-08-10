# Course Materials RAG System

A Retrieval-Augmented Generation (RAG) system designed to answer questions about course materials using semantic search and AI-powered responses.

## Overview

This application is a full-stack web application that enables users to query course materials and receive intelligent, context-aware responses. It uses ChromaDB for vector storage, Anthropic's Claude for AI generation, and provides a web interface for interaction.

## Architecture

### Backend Components (FastAPI + RAG Pipeline)
```
RAGSystem (rag_system.py) - Main orchestrator
├── DocumentProcessor - Extracts course structure from text files
├── VectorStore (ChromaDB) - Stores course chunks and metadata
├── AIGenerator (Anthropic Claude) - Generates responses using tools
├── SessionManager - Manages conversation history
└── ToolManager + CourseSearchTool - Provides semantic search capabilities
```

### Frontend
- Vanilla JavaScript SPA with real-time chat interface
- Course statistics sidebar
- Enhanced error handling with contextual help messages

## Prerequisites

- Python 3.13 or higher
- uv (Python package manager)
- An Anthropic API key (for Claude AI)
- **For Windows**: Use Git Bash to run the application commands - [Download Git for Windows](https://git-scm.com/downloads/win)

## Installation

1. **Install uv** (if not already installed)
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Install Python dependencies**
   ```bash
   uv sync
   ```

3. **Set up environment variables**

   Create a `.env` file in the root directory:
   ```bash
   ANTHROPIC_API_KEY=your_anthropic_api_key_here
   ```

## Running the Application

### Quick Start

Use the provided shell script:
```bash
chmod +x run.sh
./run.sh
```

### Manual Start

```bash
cd backend
uv run uvicorn app:app --reload --port 8000
```

The application will be available at:
- Web Interface: `http://localhost:8000`
- API Documentation: `http://localhost:8000/docs`

## Development

### Running Tests

Always use `uv` to run tests and manage dependencies:

```bash
# Run all tests
uv run pytest tests/ -v

# Run specific test file
uv run pytest tests/test_search_tools.py -v

# Run specific test with output
uv run pytest tests/test_real_system.py -v -s

# Add dev dependencies
uv add --dev pytest httpx
```

### Test Coverage

- **Core Functionality**: Essential search, vector store, and RAG system operations
- **System Diagnostics**: Real-world testing with actual documents and components
- **Error Handling**: Basic error scenarios and graceful degradation
- **Total**: 15 focused, high-value tests that catch real issues

### Adding Course Content

1. Place text files in `/docs/` directory
2. App auto-loads documents on startup from `../docs` relative to backend
3. Uses `add_course_folder()` method with duplicate detection

Expected document format:
```
Course Title: [title]
Course Link: [url]
Course Instructor: [instructor]

Lesson 1: [lesson title]
Lesson Link: [lesson url]
[lesson content]

Lesson 2: [lesson title]
...
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

## Configuration

All settings in `config.py`:
- `CHUNK_SIZE`: 800 characters for vector chunks
- `CHUNK_OVERLAP`: 100 characters between chunks
- `MAX_RESULTS`: 5 search results per query
- `MAX_HISTORY`: 2 conversation messages remembered
- `CHROMA_PATH`: "./chroma_db" for vector storage

## API Endpoints

- `POST /api/query` - Main chat endpoint with session management
- `GET /api/courses` - Course analytics and statistics
- Static file serving for frontend at root `/`

## Error Handling

The system includes enhanced error handling with:
- **Detailed error messages** instead of generic "query failed"
- **Contextual help tips** for common issues (API key, network, rate limits)
- **Automatic retry** with exponential backoff for transient failures
- **User-friendly error displays** in the UI

## Troubleshooting

### Common Issues

1. **"Query failed" errors**: Fixed in latest version with detailed error reporting
2. **API key issues**: Check `.env` file contains valid `ANTHROPIC_API_KEY`
3. **Database connection**: ChromaDB creates local storage in `./chroma_db`
4. **Import errors**: Run `uv sync` to install all dependencies
