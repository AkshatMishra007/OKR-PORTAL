from unittest.mock import MagicMock, patch
from app.core.database import get_db


def test_get_db_yields_session_and_closes():
    """
    Verify get_db creates SessionLocal, yields db, and closes it in finally.
    """
    mock_session = MagicMock()
    with patch("app.core.database.SessionLocal", return_value=mock_session):
        gen = get_db()
        db = next(gen)
        assert db == mock_session
        try:
            next(gen)
        except StopIteration:
            pass
        mock_session.close.assert_called_once()
