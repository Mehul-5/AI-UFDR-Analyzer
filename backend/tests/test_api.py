import pytest
from httpx import AsyncClient, ASGITransport
from main import app  # Importing your FastAPI app instance
import os

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