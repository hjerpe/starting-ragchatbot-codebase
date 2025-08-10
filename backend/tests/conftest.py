"""
Comprehensive pytest configuration with shared fixtures for API testing
"""

import pytest
import tempfile
import shutil
import os
import sys
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from httpx import AsyncClient

# Add backend to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from config import Config


@pytest.fixture
def temp_chroma_db():
    """Temporary ChromaDB directory for testing"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Clean up after test
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def test_config(temp_chroma_db):
    """Test configuration with safe defaults and temp database"""
    config = Config()
    config.ANTHROPIC_API_KEY = "test-key-123"  # Mock API key for testing
    config.EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    config.CHUNK_SIZE = 800
    config.CHUNK_OVERLAP = 100
    config.MAX_RESULTS = 5
    config.MAX_HISTORY = 2
    config.CHROMA_PATH = temp_chroma_db
    return config


@pytest.fixture
def mock_rag_system():
    """Mock RAG system for API testing"""
    mock = Mock()
    mock.query.return_value = (
        "This is a test answer from the mocked RAG system.",
        [{"title": "Test Course", "link": None}]
    )
    mock.get_course_analytics.return_value = {
        "total_courses": 2,
        "course_titles": ["Test Course 1", "Test Course 2"]
    }
    mock.session_manager.create_session.return_value = "test-session-123"
    return mock


@pytest.fixture
def test_app(mock_rag_system):
    """Create a test FastAPI app with mocked dependencies"""
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    from typing import List, Optional

    # Create test app without static file mounting to avoid directory issues
    app = FastAPI(title="Test Course Materials RAG System")

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Pydantic models for request/response
    class QueryRequest(BaseModel):
        query: str
        session_id: Optional[str] = None

    class SourceInfo(BaseModel):
        title: str
        link: Optional[str] = None

    class QueryResponse(BaseModel):
        answer: str
        sources: List[SourceInfo]
        session_id: str

    class CourseStats(BaseModel):
        total_courses: int
        course_titles: List[str]

    # API Endpoints with mocked RAG system
    @app.post("/api/query", response_model=QueryResponse)
    async def query_documents(request: QueryRequest):
        session_id = request.session_id or mock_rag_system.session_manager.create_session()
        answer, sources = mock_rag_system.query(request.query, session_id)

        source_infos = []
        for source in sources:
            if isinstance(source, dict):
                source_infos.append(SourceInfo(title=source.get('title', ''), link=source.get('link')))
            else:
                source_infos.append(SourceInfo(title=str(source), link=None))

        return QueryResponse(
            answer=answer,
            sources=source_infos,
            session_id=session_id
        )

    @app.get("/api/courses", response_model=CourseStats)
    async def get_course_stats():
        analytics = mock_rag_system.get_course_analytics()
        return CourseStats(
            total_courses=analytics["total_courses"],
            course_titles=analytics["course_titles"]
        )

    @app.get("/")
    async def read_root():
        return {"message": "Course Materials RAG System API"}

    return app


@pytest.fixture
def client(test_app):
    """Synchronous test client for FastAPI testing"""
    return TestClient(test_app)


@pytest.fixture
async def async_client(test_app):
    """Asynchronous test client for FastAPI testing"""
    from httpx import ASGITransport
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def sample_query_request():
    """Sample query request data for testing"""
    return {
        "query": "What is machine learning?",
        "session_id": "test-session-456"
    }


@pytest.fixture
def sample_course_data():
    """Sample course data for testing"""
    return {
        "total_courses": 3,
        "course_titles": ["Python Basics", "Data Science", "Machine Learning"]
    }
