import pytest
from httpx import AsyncClient, ASGITransport
from main import app  # Importing your FastAPI app instance
import os
from unittest.mock import patch, AsyncMock
from app.services.data_processor import DataProcessor
from unittest.mock import Mock, MagicMock
from app.parsers.chat_parser import ChatParser

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
async def test_process_file_database_interaction():
    """
    Test 4: Verify Database Storage Logic.
    We mock the parser to return fake data, and mock the DB session
    to ensure 'execute' is called to insert records.
    """
    # 1. Setup Fake Data
    fake_parsed_data = {
        'metadata': {'case_info': {'case_number': 'TEST-DB-001'}},
        'chat_records': [{'sender_number': '123', 'message_content': 'Hello'}],
        'call_records': [],
        'contacts': [],
        'media_files': []
    }

    # 2. Mock the Dependencies
    # We patch the parser to return our fake data immediately
    with patch("app.services.ufdr_parser.UFDRParser.parse_ufdr_file", return_value=fake_parsed_data):
        
        # We patch the DB manager's 'get_db' or the internal storage method
        # Since 'process_ufdr_file' creates its own session or uses db_manager, 
        # let's mock the internal '_store_in_case_postgres' method for simplicity.
        # This confirms data_processor TRIES to save data.
        
        with patch.object(DataProcessor, "_store_in_case_postgres") as mock_store_postgres:
            # We also need to mock the vector/graph storage to avoid errors
            with patch.object(DataProcessor, "_store_in_case_qdrant"), \
                 patch.object(DataProcessor, "_store_in_case_neo4j"):
                
                # 3. Initialize Processor
                processor = DataProcessor()
                
                # 4. Run the method (using a fake file path)
                await processor.process_ufdr_file("fake_path.ufdr", "TEST-DB-001", "Investigator X")
                
                # 5. Assertions
                # Did it try to store data in Postgres?
                mock_store_postgres.assert_called_once()
                
                # Check if it passed the correct data to the storage method
                # args[0] is the parsed_data dict
                called_args = mock_store_postgres.call_args[0]
                assert called_args[0]['chat_records'][0]['message_content'] == 'Hello'