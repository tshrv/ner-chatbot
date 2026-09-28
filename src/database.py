"""Async MongoDB client lifecycle and collection index management."""

from typing import Optional

from motor.motor_asyncio import (
    AsyncIOMotorClient,
    AsyncIOMotorCollection,
    AsyncIOMotorDatabase,
)
from pymongo import ASCENDING, DESCENDING, IndexModel

from src.config import settings
from src.utils.logging import logger

_client: Optional[AsyncIOMotorClient] = None


def get_client() -> AsyncIOMotorClient:
    """Retrieve or initialize the singleton AsyncIOMotorClient."""
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(settings.mongodb_uri)
    return _client


def get_database() -> AsyncIOMotorDatabase:
    """Retrieve the application database handle."""
    client = get_client()
    return client[settings.database_name]


def get_jobs_collection() -> AsyncIOMotorCollection:
    """Return the 'jobs' collection."""
    return get_database()["jobs"]


def get_documents_collection() -> AsyncIOMotorCollection:
    """Return the 'documents' collection."""
    return get_database()["documents"]


def get_pages_collection() -> AsyncIOMotorCollection:
    """Return the 'pages' collection."""
    return get_database()["pages"]


def get_entities_collection() -> AsyncIOMotorCollection:
    """Return the 'entities' collection."""
    return get_database()["entities"]


def get_occurrences_collection() -> AsyncIOMotorCollection:
    """Return the 'occurrences' collection."""
    return get_database()["occurrences"]


async def init_db() -> None:
    """Initialize collections and ensure all required indexes exist."""
    db = get_database()
    logger.debug("Ensuring MongoDB indexes for database: {}", db.name)

    # Indexes for 'jobs'
    await db["jobs"].create_indexes(
        [
            IndexModel([("status", ASCENDING)], name="idx_jobs_status"),
            IndexModel([("started_at", DESCENDING)], name="idx_jobs_started_at"),
        ]
    )

    # Indexes for 'documents'
    await db["documents"].create_indexes(
        [
            IndexModel([("job_id", ASCENDING)], name="idx_documents_job_id"),
        ]
    )

    # Indexes for 'pages'
    await db["pages"].create_indexes(
        [
            IndexModel(
                [("document_id", ASCENDING), ("page_number", ASCENDING)],
                unique=True,
                name="idx_pages_document_page_unique",
            ),
            IndexModel([("job_id", ASCENDING)], name="idx_pages_job_id"),
        ]
    )

    # Indexes for 'entities'
    await db["entities"].create_indexes(
        [
            IndexModel(
                [
                    ("document_id", ASCENDING),
                    ("name", ASCENDING),
                    ("entity_type", ASCENDING),
                ],
                unique=True,
                name="idx_entities_doc_name_type_unique",
            ),
        ]
    )

    # Indexes for 'occurrences'
    await db["occurrences"].create_indexes(
        [
            IndexModel([("entity_id", ASCENDING)], name="idx_occurrences_entity_id"),
            IndexModel(
                [("document_id", ASCENDING), ("page_number", ASCENDING)],
                name="idx_occurrences_doc_page",
            ),
        ]
    )
    logger.debug("MongoDB indexes initialized successfully.")


def close_db() -> None:
    """Close the active AsyncIOMotorClient connection."""
    global _client
    if _client is not None:
        _client.close()
        _client = None
