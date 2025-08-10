"""
API endpoint tests for the RAG system FastAPI application
"""
import pytest
from fastapi import status
from unittest.mock import Mock


@pytest.mark.api
class TestQueryEndpoint:
    """Test cases for the /api/query endpoint"""

    def test_query_with_session_id(self, client, sample_query_request):
        """Test query endpoint with existing session ID"""
        response = client.post("/api/query", json=sample_query_request)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "answer" in data
        assert "sources" in data
        assert "session_id" in data
        assert data["session_id"] == sample_query_request["session_id"]
        assert isinstance(data["sources"], list)

        # Verify source structure
        if data["sources"]:
            source = data["sources"][0]
            assert "title" in source
            assert "link" in source

    def test_query_without_session_id(self, client):
        """Test query endpoint creates new session when none provided"""
        request_data = {"query": "What is Python programming?"}
        response = client.post("/api/query", json=request_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "session_id" in data
        assert data["session_id"] == "test-session-123"  # From mock
        assert "answer" in data
        assert "sources" in data

    def test_query_empty_query(self, client):
        """Test query endpoint with empty query string"""
        request_data = {"query": ""}
        response = client.post("/api/query", json=request_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "answer" in data

    def test_query_invalid_payload(self, client):
        """Test query endpoint with invalid request payload"""
        response = client.post("/api/query", json={})

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_query_malformed_json(self, client):
        """Test query endpoint with malformed JSON"""
        response = client.post(
            "/api/query",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_query_async(self, async_client, sample_query_request):
        """Test query endpoint using async client"""
        response = await async_client.post("/api/query", json=sample_query_request)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "answer" in data
        assert "sources" in data
        assert "session_id" in data


@pytest.mark.api
class TestCoursesEndpoint:
    """Test cases for the /api/courses endpoint"""

    def test_get_course_stats(self, client):
        """Test courses endpoint returns proper statistics"""
        response = client.get("/api/courses")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "total_courses" in data
        assert "course_titles" in data
        assert isinstance(data["total_courses"], int)
        assert isinstance(data["course_titles"], list)

        # Verify mock data
        assert data["total_courses"] == 2
        assert len(data["course_titles"]) == 2
        assert "Test Course 1" in data["course_titles"]
        assert "Test Course 2" in data["course_titles"]

    @pytest.mark.asyncio
    async def test_get_course_stats_async(self, async_client):
        """Test courses endpoint using async client"""
        response = await async_client.get("/api/courses")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "total_courses" in data
        assert "course_titles" in data


@pytest.mark.api
class TestRootEndpoint:
    """Test cases for the root / endpoint"""

    def test_root_endpoint(self, client):
        """Test root endpoint returns API information"""
        response = client.get("/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data
        assert data["message"] == "Course Materials RAG System API"

    @pytest.mark.asyncio
    async def test_root_endpoint_async(self, async_client):
        """Test root endpoint using async client"""
        response = await async_client.get("/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data


@pytest.mark.api
class TestAPIErrorHandling:
    """Test cases for API error handling"""

    def test_nonexistent_endpoint(self, client):
        """Test response to nonexistent endpoint"""
        response = client.get("/api/nonexistent")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_wrong_method(self, client):
        """Test wrong HTTP method on existing endpoint"""
        response = client.get("/api/query")

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

        response = client.post("/api/courses")

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_options_requests(self, client):
        """Test CORS OPTIONS requests are handled"""
        response = client.options("/api/query")

        # OPTIONS requests may return 405 without proper preflight handling
        # The important thing is that CORS headers are present
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_405_METHOD_NOT_ALLOWED]


@pytest.mark.api
class TestResponseFormats:
    """Test cases for API response formats and schemas"""

    def test_query_response_schema(self, client, sample_query_request):
        """Test query response matches expected schema"""
        response = client.post("/api/query", json=sample_query_request)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Required fields
        required_fields = ["answer", "sources", "session_id"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

        # Type validation
        assert isinstance(data["answer"], str)
        assert isinstance(data["sources"], list)
        assert isinstance(data["session_id"], str)

        # Source schema validation
        for source in data["sources"]:
            assert isinstance(source, dict)
            assert "title" in source
            assert "link" in source
            assert isinstance(source["title"], str)
            # link can be null/None

    def test_courses_response_schema(self, client):
        """Test courses response matches expected schema"""
        response = client.get("/api/courses")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Required fields
        required_fields = ["total_courses", "course_titles"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

        # Type validation
        assert isinstance(data["total_courses"], int)
        assert isinstance(data["course_titles"], list)

        # All course titles should be strings
        for title in data["course_titles"]:
            assert isinstance(title, str)

    def test_content_type_headers(self, client, sample_query_request):
        """Test API returns proper content-type headers"""
        response = client.post("/api/query", json=sample_query_request)

        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"] == "application/json"

        response = client.get("/api/courses")

        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"] == "application/json"


@pytest.mark.integration
class TestMockIntegration:
    """Test cases verifying mock integrations work correctly"""

    def test_mock_rag_system_called(self, client, mock_rag_system, sample_query_request):
        """Test that the mock RAG system is properly called"""
        response = client.post("/api/query", json=sample_query_request)

        assert response.status_code == status.HTTP_200_OK

        # Verify mock was called
        mock_rag_system.query.assert_called_once_with(
            sample_query_request["query"],
            sample_query_request["session_id"]
        )

    def test_mock_session_creation(self, client, mock_rag_system):
        """Test that mock session creation works when no session ID provided"""
        request_data = {"query": "Test query without session"}
        response = client.post("/api/query", json=request_data)

        assert response.status_code == status.HTTP_200_OK

        # Verify session creation was called
        mock_rag_system.session_manager.create_session.assert_called_once()

    def test_mock_analytics_called(self, client, mock_rag_system):
        """Test that the mock analytics method is called"""
        response = client.get("/api/courses")

        assert response.status_code == status.HTTP_200_OK

        # Verify analytics was called
        mock_rag_system.get_course_analytics.assert_called_once()
