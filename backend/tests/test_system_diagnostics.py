"""
System diagnostic tests - these help identify real issues when the system isn't working
"""
import pytest
import tempfile
import os
import sys
from unittest.mock import patch

# Add backend to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from rag_system import RAGSystem
from config import Config
from vector_store import VectorStore
from search_tools import CourseSearchTool


class TestSystemDiagnostics:
    """High-value diagnostic tests that help identify real system issues"""

    def test_system_components_work_independently(self, temp_chroma_db):
        """Step-by-step test of each system component in isolation"""
        print("\n=== SYSTEM DIAGNOSTICS ===")

        # 1. Vector Store
        print("1. Testing VectorStore...")
        vector_store = VectorStore(temp_chroma_db, "all-MiniLM-L6-v2", 5)
        results = vector_store.search("test query")
        print(f"   Empty search result: {results.is_empty()}")
        print(f"   Error: {results.error}")

        # 2. Search Tool
        print("2. Testing CourseSearchTool...")
        search_tool = CourseSearchTool(vector_store)
        search_result = search_tool.execute("test query")
        print(f"   Search tool result: '{search_result}'")

        # Assertions - these should work even with empty database
        assert results.is_empty()  # Empty database should return empty results
        assert results.error is None  # But no error should occur
        assert search_result == "No relevant content found."  # Should be user-friendly message

        print("✅ All components work independently")

    @patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key-123'})
    def test_system_with_real_documents(self, temp_chroma_db):
        """Test the system with actual document loading and searching"""
        config = Config()
        config.CHROMA_PATH = temp_chroma_db

        rag_system = RAGSystem(config)

        # Create a realistic test document
        test_content = """Course Title: Machine Learning Fundamentals
Course Instructor: Dr. ML Expert

Lesson 1: Introduction to ML
Machine learning is a subset of AI that enables computers to learn from data.
It involves algorithms that can identify patterns and make predictions.

Lesson 2: Types of Machine Learning
There are three main types: supervised, unsupervised, and reinforcement learning.
Each type has different applications and use cases.
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(test_content)
            temp_file_path = f.name

        try:
            print("\n=== DOCUMENT LOADING TEST ===")
            # Load document
            course, chunks = rag_system.add_course_document(temp_file_path)
            print(f"Course loaded: {course.title if course else 'None'}")
            print(f"Chunks created: {chunks}")

            # Test search functionality
            search_result = rag_system.search_tool.execute("machine learning")
            print(f"Search result length: {len(search_result)}")
            print(f"Contains 'machine learning': {'machine learning' in search_result.lower()}")

            # Basic assertions
            assert course is not None
            assert chunks > 0
            assert "machine learning" in search_result.lower()

            print("✅ Document loading and search working")

        finally:
            os.unlink(temp_file_path)

    def test_documents_folder_loading(self):
        """Test loading documents from the actual docs folder (if it exists)"""
        docs_path = os.path.join(os.path.dirname(__file__), '..', '..', 'docs')
        print(f"\n=== DOCS FOLDER TEST ===")
        print(f"Docs path: {os.path.abspath(docs_path)}")
        print(f"Docs folder exists: {os.path.exists(docs_path)}")

        if os.path.exists(docs_path):
            files = os.listdir(docs_path)
            txt_files = [f for f in files if f.endswith('.txt')]
            print(f"Text files found: {len(txt_files)}")

            # Test with temporary config to avoid affecting real database
            with tempfile.TemporaryDirectory() as temp_dir:
                config = Config()
                config.CHROMA_PATH = temp_dir

                rag_system = RAGSystem(config)

                if txt_files:
                    courses, chunks = rag_system.add_course_folder(docs_path)
                    print(f"Courses loaded: {courses}")
                    print(f"Total chunks: {chunks}")

                    if courses > 0:
                        # Test search with loaded data
                        search_result = rag_system.search_tool.execute("introduction")
                        print(f"Search with real data works: {len(search_result) > 50}")

                        analytics = rag_system.get_course_analytics()
                        print(f"Course titles: {analytics['course_titles']}")

                        assert courses > 0
                        assert chunks > 0
                        print("✅ Real document loading working")
                else:
                    print("⚠️  No .txt files found in docs folder")
        else:
            print("⚠️  Docs folder doesn't exist - this is OK for testing")

    @patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key-123'})
    @patch('anthropic.Anthropic')
    def test_api_integration_basic(self, mock_anthropic, temp_chroma_db):
        """Test basic API integration without complex scenarios"""
        # Simple mock setup
        mock_client = mock_anthropic.return_value
        mock_response = type('MockResponse', (), {})()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [type('MockContent', (), {'text': 'Test AI response'})()]
        mock_client.messages.create.return_value = mock_response

        config = Config()
        config.CHROMA_PATH = temp_chroma_db
        rag_system = RAGSystem(config)

        print("\n=== API INTEGRATION TEST ===")
        try:
            response, sources = rag_system.query("What is 2+2?")
            print(f"Got response: {len(response) > 0}")
            print(f"Response type: {type(response)}")
            print(f"Sources type: {type(sources)}")

            assert isinstance(response, str)
            assert len(response) > 0
            assert isinstance(sources, list)

            print("✅ API integration working")

        except Exception as e:
            print(f"❌ API integration failed: {e}")
            raise

    def test_configuration_values(self):
        """Test that configuration values are reasonable"""
        config = Config()

        print("\n=== CONFIGURATION TEST ===")
        print(f"Chunk size: {config.CHUNK_SIZE}")
        print(f"Chunk overlap: {config.CHUNK_OVERLAP}")
        print(f"Max results: {config.MAX_RESULTS}")
        print(f"Max history: {config.MAX_HISTORY}")
        print(f"API key present: {'Yes' if config.ANTHROPIC_API_KEY else 'No'}")

        # Basic sanity checks
        assert config.CHUNK_SIZE > 0
        assert config.CHUNK_OVERLAP >= 0
        assert config.MAX_RESULTS > 0
        assert config.MAX_HISTORY >= 0

        print("✅ Configuration values are reasonable")


@pytest.fixture
def temp_chroma_db():
    """Temporary ChromaDB directory"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)
