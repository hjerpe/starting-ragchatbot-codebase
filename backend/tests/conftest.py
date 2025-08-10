"""
Simplified pytest configuration with essential fixtures only
"""
import pytest
import tempfile
import shutil
import os
import sys

# Add backend to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from config import Config


@pytest.fixture
def temp_chroma_db():
    """Temporary ChromaDB directory for testing"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Clean up after test
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def test_config():
    """Test configuration with safe defaults"""
    config = Config()
    config.ANTHROPIC_API_KEY = "test-key-123"  # Mock API key for testing
    config.EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    config.CHUNK_SIZE = 800
    config.CHUNK_OVERLAP = 100
    config.MAX_RESULTS = 5
    config.MAX_HISTORY = 2
    return config
