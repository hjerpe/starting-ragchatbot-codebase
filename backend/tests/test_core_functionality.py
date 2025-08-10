"""
Streamlined core functionality tests for the RAG system.
Focus on the most important user workflows and system behavior.
"""
import pytest
import tempfile
import shutil
import os
import sys
from unittest.mock import Mock, patch

# Add backend to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from search_tools import CourseSearchTool, ToolManager
from vector_store import VectorStore, SearchResults
from rag_system import RAGSystem
from config import Config


class TestCoreSearchFunctionality:
    """Test core search functionality - the heart of the RAG system"""

    def test_search_tool_with_results(self, mock_vector_store):
        """Test that search tool returns formatted results when data exists"""
        # Setup mock data
        mock_results = SearchResults(
            documents=["Test content about machine learning"],
            metadata=[{"course_title": "ML Course", "lesson_number": 1}],
            distances=[0.1]
        )
        mock_vector_store.search.return_value = mock_results

        search_tool = CourseSearchTool(mock_vector_store)

        # Execute
        result = search_tool.execute("machine learning")

        # Verify basic functionality
        assert isinstance(result, str)
        assert len(result) > 0
        assert "ML Course" in result
        assert "Test content about machine learning" in result

    def test_search_tool_empty_results(self, mock_vector_store):
        """Test that search tool handles empty results gracefully"""
        # Setup empty results
        mock_results = SearchResults(documents=[], metadata=[], distances=[])
        mock_vector_store.search.return_value = mock_results

        search_tool = CourseSearchTool(mock_vector_store)

        # Execute
        result = search_tool.execute("nonexistent content")

        # Verify graceful handling
        assert result == "No relevant content found."

    def test_tool_manager_basic_functionality(self, mock_vector_store):
        """Test that tool manager can register and execute tools"""
        # Setup
        tool_manager = ToolManager()
        search_tool = CourseSearchTool(mock_vector_store)
        tool_manager.register_tool(search_tool)

        # Mock successful search
        mock_results = SearchResults(
            documents=["Sample content"],
            metadata=[{"course_title": "Test Course"}],
            distances=[0.1]
        )
        mock_vector_store.search.return_value = mock_results

        # Execute
        result = tool_manager.execute_tool("search_course_content", query="test")

        # Verify
        assert isinstance(result, str)
        assert "Sample content" in result


class TestCoreVectorStoreFunctionality:
    """Test core vector storage operations"""

    def test_vector_store_add_and_search(self, temp_chroma_db, sample_course_data, sample_course_chunks):
        """Test that we can add data and retrieve it with search"""
        # Setup real vector store
        vector_store = VectorStore(temp_chroma_db, "all-MiniLM-L6-v2", 5)

        # Add data
        vector_store.add_course_metadata(sample_course_data)
        vector_store.add_course_content(sample_course_chunks)

        # Test search
        results = vector_store.search("Anthropic")

        # Verify we can find data
        assert not results.is_empty()
        assert results.error is None
        assert len(results.documents) > 0

    def test_vector_store_empty_search(self, temp_chroma_db):
        """Test search on empty database returns empty results"""
        vector_store = VectorStore(temp_chroma_db, "all-MiniLM-L6-v2", 5)

        results = vector_store.search("anything")

        assert results.is_empty()
        assert results.error is None


class TestCoreRAGSystemFunctionality:
    """Test the main RAG system workflows"""

    @patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key-123'})
    def test_rag_system_initialization(self, temp_chroma_db):
        """Test that RAG system initializes all components correctly"""
        # Setup config
        config = Config()
        config.CHROMA_PATH = temp_chroma_db

        # Initialize system
        rag_system = RAGSystem(config)

        # Verify all components exist
        assert rag_system.document_processor is not None
        assert rag_system.vector_store is not None
        assert rag_system.ai_generator is not None
        assert rag_system.session_manager is not None
        assert rag_system.tool_manager is not None
        assert rag_system.search_tool is not None

    @patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key-123'})
    def test_document_loading_workflow(self, temp_chroma_db):
        """Test that we can load documents into the system"""
        # Setup
        config = Config()
        config.CHROMA_PATH = temp_chroma_db
        rag_system = RAGSystem(config)

        # Create test document
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("""Course Title: Test ML Course
Course Instructor: Dr. Test

Lesson 1: Introduction
This is a test lesson about machine learning basics.
Machine learning is the study of algorithms that improve through experience.

Lesson 2: Advanced Topics
This covers advanced machine learning concepts and techniques.
""")
            temp_file_path = f.name

        try:
            # Add document
            course, chunks = rag_system.add_course_document(temp_file_path)

            # Verify document was processed
            assert course is not None
            assert course.title == "Test ML Course"
            assert chunks > 0

            # Verify it's in the system
            analytics = rag_system.get_course_analytics()
            assert analytics['total_courses'] == 1
            assert "Test ML Course" in analytics['course_titles']

        finally:
            os.unlink(temp_file_path)

    @patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key-123'})
    @patch('anthropic.Anthropic')
    def test_end_to_end_query_workflow(self, mock_anthropic, temp_chroma_db):
        """Test complete query workflow from user input to response"""
        # Setup mock AI response
        mock_client = mock_anthropic.return_value

        # Mock simple response (no tool use for simplicity)
        mock_response = Mock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [Mock()]
        mock_response.content[0].text = "This is a test response about machine learning."
        mock_client.messages.create.return_value = mock_response

        # Setup RAG system
        config = Config()
        config.CHROMA_PATH = temp_chroma_db
        rag_system = RAGSystem(config)

        # Execute query
        response, sources = rag_system.query("What is machine learning?")

        # Verify we get a response
        assert isinstance(response, str)
        assert len(response) > 0
        assert isinstance(sources, list)

        # Verify AI was called
        mock_client.messages.create.assert_called_once()


class TestErrorHandlingCore:
    """Test core error handling scenarios"""

    def test_search_tool_with_vector_store_error(self):
        """Test search tool handles vector store errors gracefully"""
        # Setup mock that raises exception
        mock_vector_store = Mock()
        mock_vector_store.search.side_effect = Exception("Database connection failed")

        search_tool = CourseSearchTool(mock_vector_store)

        # Execute and expect exception (this is correct behavior)
        with pytest.raises(Exception, match="Database connection failed"):
            search_tool.execute("test query")

    def test_rag_system_handles_missing_documents_folder(self, temp_chroma_db):
        """Test RAG system handles missing documents folder gracefully"""
        config = Config()
        config.CHROMA_PATH = temp_chroma_db

        rag_system = RAGSystem(config)

        # Try to load from non-existent folder
        courses, chunks = rag_system.add_course_folder("/nonexistent/path")

        # Should handle gracefully
        assert courses == 0
        assert chunks == 0


# Keep the essential fixtures simple
@pytest.fixture
def mock_vector_store():
    """Simple mock vector store for unit testing"""
    mock_store = Mock()

    # Default empty search results
    mock_store.search.return_value = SearchResults(
        documents=[], metadata=[], distances=[]
    )

    return mock_store


@pytest.fixture
def temp_chroma_db():
    """Temporary ChromaDB directory for testing"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_course_data():
    """Simple sample course data"""
    from models import Course, Lesson
    return Course(
        title="Building Towards Computer Use with Anthropic",
        instructor="Colt Steele",
        lessons=[
            Lesson(lesson_number=0, title="Introduction"),
            Lesson(lesson_number=1, title="API Basics")
        ]
    )


@pytest.fixture
def sample_course_chunks():
    """Simple sample course chunks"""
    from models import CourseChunk
    return [
        CourseChunk(
            content="Welcome to Building Toward Computer Use with Anthropic.",
            course_title="Building Towards Computer Use with Anthropic",
            lesson_number=0,
            chunk_index=0
        ),
        CourseChunk(
            content="Anthropic made a recent breakthrough with computer use.",
            course_title="Building Towards Computer Use with Anthropic",
            lesson_number=0,
            chunk_index=1
        )
    ]
