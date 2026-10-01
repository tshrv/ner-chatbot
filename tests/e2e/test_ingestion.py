from pathlib import Path

import pytest

from src.database import (
    get_documents_collection,
    get_entities_collection,
    get_occurrences_collection,
    get_pages_collection,
)
from src.models.job import JobStatus
from src.services.ingestion import IngestionPipelineCoordinator

PDF_PATH = Path("data/assessment-of-the-threat-from-russia.pdf")


@pytest.mark.asyncio
async def test_document_ingestion_e2e():
    """Ingest document and verify database persistence and page metadata."""
    coordinator = IngestionPipelineCoordinator()
    job = await coordinator.run(file_path=PDF_PATH)

    # verify Job model status and page counters
    assert job.status == JobStatus.COMPLETED
    assert job.total_pages == 3
    assert job.pages_extracted == 3
    assert job.pages_ner_completed == 3
    assert job.total_entities_found > 0
    assert job.total_occurrences_found > 0

    # verify database records
    docs_col = get_documents_collection()
    doc = await docs_col.find_one({"_id": job.document_id})
    assert doc is not None
    assert doc["name"] == PDF_PATH.name
    assert doc["status"] == "completed"

    pages_col = get_pages_collection()
    pages_count = await pages_col.count_documents({"document_id": job.document_id})
    assert pages_count == 3

    entities_col = get_entities_collection()
    unique_entities = await entities_col.count_documents({"document_id": job.document_id})
    assert unique_entities == job.total_entities_found

    occurrences_col = get_occurrences_collection()
    occurrences_count = await occurrences_col.count_documents({"document_id": job.document_id})
    assert occurrences_count == job.total_occurrences_found
