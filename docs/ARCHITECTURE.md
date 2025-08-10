# RAG System Architecture

This document provides a detailed overview of the Course Materials RAG System architecture.

## System Overview

The RAG (Retrieval-Augmented Generation) system combines vector search capabilities with large language models to provide intelligent responses about course materials.

## Component Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │     Backend      │    │   External      │
│  (JavaScript)   │    │    (FastAPI)     │    │   Services      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
    HTTP Requests             RAG System            Anthropic API
         │                       │                   ChromaDB
    ┌────▼────┐              ┌───▼────┐                   │
    │  Chat   │              │  API   │                   │
    │Interface│              │Endpoints│                   │
    └─────────┘              └────────┘                   │
         │                       │                       │
    Error Handling         Session Management        Vector Storage
    Auto Retry             Tool Execution           Semantic Search
```

## Backend Components

### 1. RAGSystem (`rag_system.py`)
**Purpose**: Main orchestrator that coordinates all components

**Key Responsibilities**:
- Document loading and processing
- Query handling and response generation
- Component initialization and coordination

### 2. DocumentProcessor (`document_processor.py`)
**Purpose**: Parses and chunks course documents

**Key Features**:
- Extracts course metadata (title, instructor, lessons)
- Splits content into semantic chunks with overlap
- Handles structured course document format

### 3. VectorStore (`vector_store.py`)
**Purpose**: Manages ChromaDB operations and vector search

**Key Features**:
- Dual collections (course catalog + content)
- Semantic course name resolution
- Advanced filtering (by course, lesson, etc.)
- Metadata management

### 4. AIGenerator (`ai_generator.py`)
**Purpose**: Integrates with Anthropic's Claude API

**Key Features**:
- Tool calling support
- Conversation context management
- Optimized API parameters
- Error handling and retry logic

### 5. ToolManager & Search Tools (`search_tools.py`)
**Purpose**: Provides search capabilities as tools for the AI

**Tools Available**:
- `CourseSearchTool`: Semantic content search
- `CourseOutlineTool`: Course structure retrieval
- Extensible tool architecture

### 6. SessionManager (`session_manager.py`)
**Purpose**: Manages conversation history and user sessions

**Key Features**:
- Session isolation
- Conversation history limits
- Message formatting for AI context

## Frontend Architecture

### Core Components
- **Chat Interface**: Real-time messaging with users
- **Error Handling**: Enhanced error reporting with contextual help
- **Retry Logic**: Automatic retry with exponential backoff
- **Course Statistics**: Sidebar showing available courses

### Error Handling Strategy
1. **Detailed Error Extraction**: Parse backend error responses
2. **Contextual Help**: Provide specific guidance for common issues
3. **Automatic Recovery**: Retry transient failures
4. **User Feedback**: Clear, actionable error messages

## Data Flow

### 1. Document Ingestion
```
Text Files → DocumentProcessor → Course Objects → VectorStore
                ↓
        (Chunking & Metadata)     (ChromaDB Storage)
```

### 2. Query Processing
```
User Query → Frontend → API Endpoint → RAGSystem
                                         ↓
              AI Generator ← Tool Manager ← VectorStore
                   ↓
            Claude API (with tools) → Semantic Search → Response
```

### 3. Response Generation
```
Search Results → AI Generator → Response Synthesis → Frontend Display
                     ↓
              (Context + Tools)    (Formatted Response)
```

## Key Design Decisions

### 1. Tool-Based Architecture
- **Why**: Allows AI to decide when/how to search
- **Benefit**: More natural, context-aware responses
- **Alternative**: Traditional RAG with context injection

### 2. Dual ChromaDB Collections
- **Course Catalog**: Metadata and course structure
- **Course Content**: Actual searchable content chunks
- **Benefit**: Efficient course resolution and content search

### 3. Frontend Error Handling
- **Problem**: Generic "query failed" messages
- **Solution**: Detailed error parsing + contextual help
- **Result**: Better user experience and debugging

### 4. Session Management
- **Approach**: Server-side session storage
- **Benefit**: Consistent conversation context
- **Limitation**: Memory-based (resets on restart)

## Performance Considerations

### Vector Search Optimization
- **Chunk Size**: 800 characters (balance between context and precision)
- **Overlap**: 100 characters (maintains context across chunks)
- **Result Limits**: Configurable maximum results per query

### API Efficiency
- **Request Batching**: Multiple operations in single API call
- **Caching**: Static system prompt to avoid rebuilding
- **Error Handling**: Intelligent retry only for appropriate errors

### Memory Management
- **Session Limits**: Maximum conversation history per session
- **Vector Storage**: Persistent ChromaDB storage
- **Cleanup**: Automatic session management

## Security Considerations

### API Key Management
- **Storage**: Environment variables only
- **Access**: Never exposed to frontend
- **Validation**: Handled at application startup

### Data Handling
- **Course Content**: Stored locally in ChromaDB
- **User Sessions**: Memory-based, not persistent
- **Error Logging**: Sanitized to avoid sensitive data exposure

## Scalability Notes

### Current Limitations
- **Single Instance**: No horizontal scaling support
- **Memory Sessions**: Lost on restart
- **Local Storage**: ChromaDB file-based storage

### Scaling Considerations
- **Database**: Could migrate to hosted vector DB
- **Sessions**: Could use Redis or database storage
- **Load Balancing**: Would need session affinity or external storage

## Testing Strategy

### Test Coverage
- **Unit Tests**: Individual component functionality
- **Integration Tests**: Component interactions
- **End-to-End Tests**: Full user workflows
- **Error Handling**: Failure scenarios and recovery

### Test Categories
- **Backend Components**: 42 tests covering all major functions
- **API Endpoints**: HTTP request/response handling
- **Error Scenarios**: Various failure modes and recovery
- **Real System**: Actual behavior validation

## Monitoring and Debugging

### Logging Strategy
- **Application Logs**: Server-side error tracking
- **API Logs**: Request/response monitoring
- **Frontend Logs**: Browser console debugging
- **Vector Search**: Query performance tracking

### Debug Tools
- **FastAPI Docs**: Interactive API documentation
- **Test Suite**: Comprehensive diagnostic tests
- **Error Reporting**: Detailed error context in responses
