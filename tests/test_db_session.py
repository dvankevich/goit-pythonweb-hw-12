# pytest --cov=src.db.session --cov-report=term-missing tests/test_db_session.py
import pytest
from unittest.mock import AsyncMock, patch
from src.db.session import get_db

@pytest.mark.asyncio
async def test_get_db_lifecycle():
    """
    Test the database session lifecycle.
    Verify that the session is created, yielded, and closed correctly.
    """
    # Create a mock for the session
    mock_session = AsyncMock()
    mock_session.close = AsyncMock()
    
    # Patch SessionLocal to return our mock session
    # Use MagicMock to support the asynchronous context manager protocol (__aenter__/__aexit__)
    with patch("src.db.session.SessionLocal") as mock_session_local:
        # Configure the context manager: async with SessionLocal() as session
        mock_instance = mock_session_local.return_value
        mock_instance.__aenter__.return_value = mock_session
        
        # Get the generator
        db_gen = get_db()
        
        # 1. Enter the try block and reach the yield statement
        session = await anext(db_gen)
        
        # Verify that we received our mock session
        assert session == mock_session
        assert mock_session_local.called
        
        # 2. Exit the generator to trigger the finally block
        try:
            await anext(db_gen)
        except StopAsyncIteration:
            pass
            
    # 3. Verify that the close() method was called (covering the line in the finally block)
    assert mock_session.close.called


@pytest.mark.asyncio
async def test_get_db_exception_handling():
    """
    Verify that the session is still closed in the finally block 
    even if an exception occurs within the try block.
    """
    mock_session = AsyncMock()
    mock_session.close = AsyncMock()
    
    with patch("src.db.session.SessionLocal") as mock_session_local:
        mock_instance = mock_session_local.return_value
        mock_instance.__aenter__.return_value = mock_session
        
        db_gen = get_db()
        await anext(db_gen)
        
        # Simulate an error during session usage (e.g., within API code)
        # In reality, this happens outside of get_db, but the finally block 
        # must execute when the generator is terminated
        try:
            await db_gen.athrow(Exception("Test error"))
        except Exception:
            pass
            
    # Verify that the session is closed despite the error
    assert mock_session.close.called