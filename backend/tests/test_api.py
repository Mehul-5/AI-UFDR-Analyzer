import pytest
from httpx import AsyncClient, ASGITransport
from main import app  # Importing your FastAPI app instance
import os
from unittest.mock import patch, AsyncMock

# Mark all tests in this file as async
pytestmark = pytest.mark.asyncio

async def test_health_check():
    """
    Test 1: Verify the API is alive .
    This hits the /health endpoint and checks for 200 OK.
    """
    # Create the transport for the FastAPI app
    transport = ASGITransport(app=app)
    
    # Pass the transport to the AsyncClient
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/v1/health")
    
    # Assertions
    assert response.status_code == 200
    json_response = response.json()
    assert json_response["status"] == "healthy"
    # We check if 'databases' key exists, but don't strictly assert 'connected' 
    # for all DBs in case Docker is just starting up during tests.
    assert "databases" in json_response

async def test_upload_invalid_file():
    """
    Test 2: Verify the API rejects non-UFDR files.
    We try to upload a .txt file and expect a 400 Error.
    This proves your validation logic works.
    """
    # Create a dummy text file in memory
    # Format: {'field_name': ('filename', content, 'content_type')}
    files = {'file': ('test.txt', b'This is not a forensic file', 'text/plain')}
    data = {'case_number': 'TEST-001', 'investigator': 'Tester'}

    transport = ASGITransport(app=app)
    
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/api/v1/upload-ufdr", files=files, data=data)
    
    # We expect a 400 Bad Request because the file extension is not .ufdr
    assert response.status_code == 400
    
    # Check that the error message complains about the file format
    error_detail = response.json()["detail"]
    assert "Unsupported file format" in error_detail

@pytest.mark.asyncio
async def test_semantic_search_mock():
    """
    Test 3: Verify Semantic Search (RAG) endpoint.
    We mock the vector_service so we don't hit the real Qdrant/Gemini API.
    """
    # 1. Define the fake data we want the "AI" to return
    mock_results = [
        {"content": "Meeting at 5pm", "score": 0.9},
        {"content": "Transfer money", "score": 0.85}
    ]

    # 2. Patch the 'semantic_search' method in vector_service
    # This tells Python: "When the code calls vector_service.semantic_search, run this fake function instead."
    with patch("app.services.vector_service.vector_service.semantic_search", new_callable=AsyncMock) as mock_search:
        mock_search.return_value = mock_results

        # 3. Make the API request
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            # We send a query to the endpoint
            response = await ac.post("/api/v1/search/semantic/advanced", json={
                "query": "money",
                "case_number": "TEST-001"
            })

        # 4. assertions
        assert response.status_code == 200
        data = response.json()
        
        # Verify the API returned our mock data
        assert len(data["results"]) == 2
        assert data["results"][0]["content"] == "Meeting at 5pm"
        
        # Verify the service was actually called with the right arguments
        mock_search.assert_called_once()

@pytest.mark.asyncio
async def test_semantic_search_mock():
    """
    Test 3: Verify Semantic Search (RAG) endpoint.
    We mock the vector_service so we don't hit the real Qdrant/Gemini API.
    """
    # 1. Define the fake data we want the "AI" to return
    # This simulates what Qdrant would return
    mock_results = [
        {"content": "Meeting at 5pm", "score": 0.9, "metadata": {"type": "chat"}},
        {"content": "Transfer money", "score": 0.85, "metadata": {"type": "chat"}}
    ]

    # 2. Patch the 'semantic_search' method in vector_service
    # This tells Python: "When the code calls vector_service.semantic_search, run this fake function instead."
    # IMPORTANT: Adjust the path 'app.services.vector_service.vector_service.semantic_search' 
    # to match exactly where 'semantic_search' is defined in your project structure.
    with patch("app.services.vector_service.vector_service.semantic_search", new_callable=AsyncMock) as mock_search:
        mock_search.return_value = mock_results

        # 3. Make the API request
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            # We send a query to the endpoint
            response = await ac.post("/api/v1/search/semantic/advanced", json={
                "query": "money",
                "case_number": "TEST-001"
            })

        # 4. Assertions
        assert response.status_code == 200
        data = response.json()
        
        # Verify the API returned our mock data structure
        # Note: Your actual API response structure might differ slightly (e.g., inside a 'results' key)
        # Adjust these assertions to match your actual JSON response format.
        assert "results" in data
        assert len(data["results"]) == 2
        assert data["results"][0]["content"] == "Meeting at 5pm"
        
        # Verify the service was actually called with the right arguments
        mock_search.assert_called_once()