"""Asynchronous read-only database query tools for entity inspection."""

import re
from typing import Dict, List, Optional

from src.agent.schemas import (
    EntityCountResult,
    EntityExistenceResult,
    EntityItem,
    EntityListResult,
    EntityTypeCountResult,
    OccurrenceDetail,
    OccurrenceQueryResult,
)
from src.database import (
    get_documents_collection,
    get_entities_collection,
    get_occurrences_collection,
)
from src.utils.logging import logger


async def count_entity_types() -> EntityTypeCountResult:
    """Count total and unique entity classification types present in the database."""
    logger.debug("Tool executing: count_entity_types")
    col = get_entities_collection()
    unique_types = await col.distinct("entity_type")
    unique_types_sorted = sorted([str(t) for t in unique_types if t])
    total_types = await col.count_documents({})
    return EntityTypeCountResult(
        total_types_count=total_types,
        unique_types_count=len(unique_types_sorted),
        types=unique_types_sorted,
    )


async def list_entity_types() -> List[str]:
    """List all unique entity classification types recorded in the database."""
    logger.debug("Tool executing: list_entity_types")
    col = get_entities_collection()
    unique_types = await col.distinct("entity_type")
    return sorted([str(t) for t in unique_types if t])


async def check_entity_type_exists(type_name: str) -> EntityExistenceResult:
    """Check case-insensitively if a specific entity classification type exists."""
    logger.debug("Tool executing: check_entity_type_exists with '{}'", type_name)
    col = get_entities_collection()
    cleaned = type_name.strip()
    pattern = re.compile(f"^{re.escape(cleaned)}$", re.IGNORECASE)
    doc = await col.find_one({"entity_type": pattern})
    if doc:
        return EntityExistenceResult(
            exists=True,
            query_term=cleaned,
            canonical_name=doc.get("entity_type"),
            entity_type=doc.get("entity_type"),
        )
    return EntityExistenceResult(
        exists=False,
        query_term=cleaned,
        canonical_name=None,
        entity_type=None,
    )


async def count_entities() -> EntityCountResult:
    """Count total entity records and unique entity names stored across all documents."""
    logger.debug("Tool executing: count_entities")
    col = get_entities_collection()
    total_count = await col.count_documents({})
    unique_names = await col.distinct("name")
    return EntityCountResult(
        total_entities_count=total_count,
        unique_entities_count=len(unique_names),
    )


async def list_entities(
    type_name: Optional[str] = None,
    limit: int = 50,
) -> EntityListResult:
    """List stored entities, optionally filtered by classification type (case-insensitive)."""
    logger.debug("Tool executing: list_entities with type_name='{}', limit={}", type_name, limit)
    col = get_entities_collection()
    query = {}
    if type_name and type_name.strip():
        query["entity_type"] = re.compile(f"^{re.escape(type_name.strip())}$", re.IGNORECASE)

    cursor = col.find(query).limit(limit)
    items: List[EntityItem] = []
    async for doc in cursor:
        items.append(
            EntityItem(
                name=doc.get("name", ""),
                entity_type=doc.get("entity_type", ""),
                total_occurrences=doc.get("total_occurrences", 1),
            )
        )
    total_unique = len(await col.distinct("name"))
    return EntityListResult(
        entities=items,
        total_returned=len(items),
        total_unique_entities=total_unique,
    )


async def check_entity_exists(entity_name: str) -> EntityExistenceResult:
    """Check case-insensitively if a specific entity exists in the database."""
    logger.debug("Tool executing: check_entity_exists with '{}'", entity_name)
    col = get_entities_collection()
    cleaned = entity_name.strip()
    pattern = re.compile(f"^{re.escape(cleaned)}$", re.IGNORECASE)
    doc = await col.find_one({"name": pattern})
    if doc:
        return EntityExistenceResult(
            exists=True,
            query_term=cleaned,
            canonical_name=doc.get("name"),
            entity_type=doc.get("entity_type"),
        )
    return EntityExistenceResult(
        exists=False,
        query_term=cleaned,
        canonical_name=None,
        entity_type=None,
    )


async def get_entity_occurrences(entity_name: str) -> OccurrenceQueryResult:
    """
    Find all occurrences of a named entity (case-insensitive) across documents.
    Returns target document names, 1-based page numbers, and character offsets.
    """
    logger.debug("Tool executing: get_entity_occurrences for '{}'", entity_name)
    entities_col = get_entities_collection()
    occurrences_col = get_occurrences_collection()
    docs_col = get_documents_collection()

    cleaned = entity_name.strip()
    pattern = re.compile(f"^{re.escape(cleaned)}$", re.IGNORECASE)

    matching_entities = []
    async for ent in entities_col.find({"name": pattern}):
        matching_entities.append(ent)

    if not matching_entities:
        return OccurrenceQueryResult(
            target=cleaned,
            search_type="entity",
            total_occurrences=0,
            document_breakdown={},
            sample_occurrences=[],
            has_more=False,
        )

    entity_ids = [ent["_id"] for ent in matching_entities]

    # Map document IDs to document names
    doc_ids = list({ent["document_id"] for ent in matching_entities})
    doc_name_map: Dict[str, str] = {}
    async for d in docs_col.find({"_id": {"$in": doc_ids}}):
        doc_name_map[d["_id"]] = d.get("name", "Unknown Document")

    # Fetch occurrences
    total_occurrences = await occurrences_col.count_documents({"entity_id": {"$in": entity_ids}})

    breakdown: Dict[str, int] = {}
    sample_items: List[OccurrenceDetail] = []

    cursor = occurrences_col.find({"entity_id": {"$in": entity_ids}}).sort(
        [("document_id", 1), ("page_number", 1), ("start_offset", 1)]
    )

    async for occ in cursor:
        doc_name = doc_name_map.get(occ.get("document_id", ""), "Unknown Document")
        breakdown[doc_name] = breakdown.get(doc_name, 0) + 1

        if len(sample_items) < 10:
            sample_items.append(
                OccurrenceDetail(
                    document_name=doc_name,
                    page_number=occ.get("page_number", 1),
                    start_offset=occ.get("start_offset", 0),
                    end_offset=occ.get("end_offset", 0),
                    surface_text=occ.get("surface_text", ""),
                    confidence=occ.get("confidence", 1.0),
                )
            )

    return OccurrenceQueryResult(
        target=cleaned,
        search_type="entity",
        total_occurrences=total_occurrences,
        document_breakdown=breakdown,
        sample_occurrences=sample_items,
        has_more=total_occurrences > len(sample_items),
    )


async def get_entity_type_occurrences(type_name: str) -> OccurrenceQueryResult:
    """
    Find occurrences of all entities belonging to a specific entity type (case-insensitive).
    Returns target document names, 1-based page numbers, and character offsets.
    """
    logger.debug("Tool executing: get_entity_type_occurrences for '{}'", type_name)
    entities_col = get_entities_collection()
    occurrences_col = get_occurrences_collection()
    docs_col = get_documents_collection()

    cleaned = type_name.strip()
    pattern = re.compile(f"^{re.escape(cleaned)}$", re.IGNORECASE)

    matching_entities = []
    async for ent in entities_col.find({"entity_type": pattern}):
        matching_entities.append(ent)

    if not matching_entities:
        return OccurrenceQueryResult(
            target=cleaned,
            search_type="entity_type",
            total_occurrences=0,
            document_breakdown={},
            sample_occurrences=[],
            has_more=False,
        )

    entity_ids = [ent["_id"] for ent in matching_entities]

    doc_ids = list({ent["document_id"] for ent in matching_entities})
    doc_name_map: Dict[str, str] = {}
    async for d in docs_col.find({"_id": {"$in": doc_ids}}):
        doc_name_map[d["_id"]] = d.get("name", "Unknown Document")

    total_occurrences = await occurrences_col.count_documents({"entity_id": {"$in": entity_ids}})

    breakdown: Dict[str, int] = {}
    sample_items: List[OccurrenceDetail] = []

    cursor = occurrences_col.find({"entity_id": {"$in": entity_ids}}).sort(
        [("document_id", 1), ("page_number", 1), ("start_offset", 1)]
    )

    async for occ in cursor:
        doc_name = doc_name_map.get(occ.get("document_id", ""), "Unknown Document")
        breakdown[doc_name] = breakdown.get(doc_name, 0) + 1

        if len(sample_items) < 10:
            sample_items.append(
                OccurrenceDetail(
                    document_name=doc_name,
                    page_number=occ.get("page_number", 1),
                    start_offset=occ.get("start_offset", 0),
                    end_offset=occ.get("end_offset", 0),
                    surface_text=occ.get("surface_text", ""),
                    confidence=occ.get("confidence", 1.0),
                )
            )

    return OccurrenceQueryResult(
        target=cleaned,
        search_type="entity_type",
        total_occurrences=total_occurrences,
        document_breakdown=breakdown,
        sample_occurrences=sample_items,
        has_more=total_occurrences > len(sample_items),
    )
