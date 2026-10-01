import pytest

from src.config import settings
from src.database import close_db, get_database, init_db

TEST_DB_NAME = "test_ner_chatbot"


@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    """Override database name for testing."""
    # run tests against an isolated test database
    settings.database_name = TEST_DB_NAME


@pytest.fixture(autouse=True)
async def clean_database():
    """Wipe the test database before and after each test."""
    await init_db()
    db = get_database()
    await db.client.drop_database(TEST_DB_NAME)
    yield
    await db.client.drop_database(TEST_DB_NAME)
    close_db()
