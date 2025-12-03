import pytest
from unittest.mock import Mock, MagicMock
from app.parsers.chat_parser import ChatParser

def test_chat_parser_extraction_logic():
    """
    Unit Test: Verify ChatParser correctly identifies columns and extracts data.
    We mock the SQLite cursor to simulate a database response.
    """
    # 1. Setup
    parser = ChatParser()
    parsed_data = {'chat_records': []}
    
    # 2. Define a Mock Schema
    # We simulate a table named 'messages' with columns that trigger the parser's detection
    schema = {
        'messages': ['sender_number', 'receiver_id', 'message_text', 'timestamp']
    }
    
    # 3. Create a Mock Cursor
    # When parser calls cursor.execute(), we want it to return our specific fake row.
    mock_cursor = Mock()
    
    # The parser builds a dynamic SELECT query. 
    # We assume it selects columns in the order: sender, receiver, text, timestamp
    # Fake Row: ('123', '456', 'Hello', 1600000000)
    mock_cursor.execute.return_value = [
        ('123', '456', 'Hello', 1600000000)
    ]
    
    # 4. Run the Parser
    parser.extract(mock_cursor, schema, parsed_data)
    
    # 5. Assertions
    # Check if data was extracted
    assert len(parsed_data['chat_records']) == 1
    
    record = parsed_data['chat_records'][0]
    
    # Check specific fields (The Goal)
    assert record['sender_number'] == '123'
    assert record['receiver_number'] == '456'
    assert record['message_content'] == 'Hello'
    
    # Verify the parser handled the timestamp conversion (if your logic supports ints)
    # or at least passed it through.
    assert record['message_type'] == 'text'