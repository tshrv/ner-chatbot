"""Ingestion pipeline coordinator managing end-to-end extraction and entity recognition."""

from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from src.database import (
    get_documents_collection,
    get_entities_collection,
    get_jobs_collection,
    get_occurrences_collection,
    get_pages_collection,
    init_db,
)
from src.models.document import Document, DocumentPage, DocumentStatus, ExtractionStatus, NerStatus
from src.models.entity import EntityOccurrence, RecognizedEntity
from src.models.job import IngestionJob, JobStatus
from src.services.extraction import ExtractionError, XbergExtractionService
from src.services.ner import GlinerNerService
from src.utils.logging import logger


class IngestionPipelineCoordinator:
    """Coordinates execution lifecycle across document ingestion, OCR, and NER."""

    def __init__(
        self,
        extraction_service: Optional[XbergExtractionService] = None,
        ner_service: Optional[GlinerNerService] = None,
    ) -> None:
        self.extraction_service = extraction_service or XbergExtractionService()
        self.ner_service = ner_service or GlinerNerService()
        self.active_job_id: Optional[str] = None

    async def run(
        self,
        file_path: Path,
        labels: Optional[List[str]] = None,
        threshold: Optional[float] = None,
    ) -> IngestionJob:
        """
        Execute end-to-end ingestion pipeline for a target PDF document.

        Returns:
            Completed or partially completed IngestionJob model.
        """
        await init_db()

        # Step 1: Register Job record immediately for complete auditability
        job = IngestionJob(
            file_path=str(file_path),
            status=JobStatus.IN_PROGRESS,
            started_at=datetime.now(timezone.utc),
        )
        self.active_job_id = job.id
        jobs_col = get_jobs_collection()
        await jobs_col.insert_one(job.model_dump(by_alias=True))

        log = logger.bind(job_id=job.id)
        log.info("Initialized ingestion job for: {}", file_path.name)

        # Validate file existence and format
        if not file_path.exists() or not file_path.is_file():
            err_msg = f"Target file does not exist or is not a file: {file_path}"
            log.error(err_msg)
            job.status = JobStatus.FAILED
            job.error_message = err_msg
            job.completed_at = datetime.now(timezone.utc)
            await jobs_col.update_one(
                {"_id": job.id},
                {
                    "$set": {
                        "status": getattr(job.status, "value", job.status),
                        "error_message": job.error_message,
                        "completed_at": job.completed_at,
                    }
                },
            )
            raise ValueError(err_msg)

        if file_path.suffix.lower() != ".pdf":
            err_msg = (
                f"Invalid file format: target must be a PDF document (.pdf), "
                f"got '{file_path.suffix}'"
            )
            log.error(err_msg)
            job.status = JobStatus.FAILED
            job.error_message = err_msg
            job.completed_at = datetime.now(timezone.utc)
            await jobs_col.update_one(
                {"_id": job.id},
                {
                    "$set": {
                        "status": getattr(job.status, "value", job.status),
                        "error_message": job.error_message,
                        "completed_at": job.completed_at,
                    }
                },
            )
            raise ValueError(err_msg)

        resolved_path = file_path.resolve()
        file_size = resolved_path.stat().st_size
        if file_size == 0:
            err_msg = "Invalid PDF: file is 0 bytes in size"
            log.error(err_msg)
            job.status = JobStatus.FAILED
            job.error_message = err_msg
            job.completed_at = datetime.now(timezone.utc)
            await jobs_col.update_one(
                {"_id": job.id},
                {
                    "$set": {
                        "status": getattr(job.status, "value", job.status),
                        "error_message": job.error_message,
                        "completed_at": job.completed_at,
                    }
                },
            )
            raise ValueError(err_msg)

        # Step 2: Register Document
        document = Document(
            job_id=job.id,
            name=resolved_path.name,
            file_path=str(resolved_path),
            file_size_bytes=file_size,
            status=DocumentStatus.IN_PROGRESS,
        )
        docs_col = get_documents_collection()
        await docs_col.insert_one(document.model_dump(by_alias=True))

        job.document_id = document.id
        await jobs_col.update_one(
            {"_id": job.id},
            {"$set": {"document_id": document.id}},
        )

        log = logger.bind(job_id=job.id, document_id=document.id)
        log.info("Registered document. Dispatching OCR extraction to Xberg...")

        # Step 3: OCR Content Extraction via Xberg API
        try:
            total_pages, extracted_pages = await self.extraction_service.extract_pdf(resolved_path)
        except ExtractionError as e:
            log.error("Content extraction failed: {}", e)
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.now(timezone.utc)
            document.status = DocumentStatus.FAILED
            document.error_message = str(e)

            await jobs_col.update_one(
                {"_id": job.id},
                {
                    "$set": {
                        "status": getattr(job.status, "value", job.status),
                        "error_message": job.error_message,
                        "completed_at": job.completed_at,
                    }
                },
            )
            await docs_col.update_one(
                {"_id": document.id},
                {
                    "$set": {
                        "status": getattr(document.status, "value", document.status),
                        "error_message": document.error_message,
                    }
                },
            )
            raise

        # Update document & job with total page count
        job.total_pages = total_pages
        document.total_pages = total_pages
        await jobs_col.update_one({"_id": job.id}, {"$set": {"total_pages": total_pages}})
        await docs_col.update_one({"_id": document.id}, {"$set": {"total_pages": total_pages}})

        log.info("Xberg extraction completed: {} pages discovered", len(extracted_pages))

        # Step 4: Persist Document Pages into MongoDB
        pages_col = get_pages_collection()
        page_records: List[DocumentPage] = []
        for pg_num, pg_content in extracted_pages:
            page_obj = DocumentPage(
                document_id=document.id,
                job_id=job.id,
                page_number=pg_num,
                content=pg_content,
                char_count=len(pg_content),
                extraction_status=ExtractionStatus.COMPLETED,
                ner_status=NerStatus.PENDING,
            )
            await pages_col.insert_one(page_obj.model_dump(by_alias=True))
            page_records.append(page_obj)

        job.pages_extracted = len(page_records)
        await jobs_col.update_one(
            {"_id": job.id},
            {"$set": {"pages_extracted": job.pages_extracted}},
        )

        # Step 5: Named Entity Recognition across pages
        entities_col = get_entities_collection()
        occurrences_col = get_occurrences_collection()

        # In-memory document-scoped entity registry: (name.lower(), entity_type) -> RecognizedEntity
        entity_cache: Dict[Tuple[str, str], RecognizedEntity] = {}

        has_partial_failure = False
        partial_error_messages: List[str] = []

        for page in page_records:
            page_log = logger.bind(
                job_id=job.id, document_id=document.id, page_number=page.page_number
            )

            if not page.content.strip():
                page_log.debug("Page is blank; skipping NER.")
                page.ner_status = NerStatus.COMPLETED
                await pages_col.update_one(
                    {"_id": page.id},
                    {
                        "$set": {
                            "ner_status": getattr(NerStatus.COMPLETED, "value", NerStatus.COMPLETED)
                        }
                    },
                )
                job.pages_ner_completed += 1
                continue

            page_log.info("Running GLiNER entity recognition on page {}...", page.page_number)

            try:
                raw_entities = await self.ner_service.extract_entities(
                    text=page.content,
                    labels=labels,
                    threshold=threshold,
                )
            except Exception as e:
                page_log.error("Entity recognition failed on page {}: {}", page.page_number, e)
                has_partial_failure = True
                err_msg = f"Page {page.page_number} NER error: {e}"
                partial_error_messages.append(err_msg)

                page.ner_status = NerStatus.FAILED
                page.error_message = str(e)
                await pages_col.update_one(
                    {"_id": page.id},
                    {
                        "$set": {
                            "ner_status": getattr(NerStatus.FAILED, "value", NerStatus.FAILED),
                            "error_message": str(e),
                        }
                    },
                )
                continue

            # Process discovered entities and occurrences
            for raw_ent in raw_entities:
                ent_text = raw_ent.get("text", "").strip()
                ent_type = raw_ent.get("label", "Unknown").strip()
                start_offset = int(raw_ent.get("start", 0))
                end_offset = int(raw_ent.get("end", 0))
                confidence = float(raw_ent.get("score", 1.0))

                if not ent_text:
                    continue

                cache_key = (ent_text.lower(), ent_type.lower())
                if cache_key in entity_cache:
                    existing_entity = entity_cache[cache_key]
                    existing_entity.total_occurrences += 1
                    await entities_col.update_one(
                        {"_id": existing_entity.id},
                        {"$inc": {"total_occurrences": 1}},
                    )
                    active_entity_id = existing_entity.id
                else:
                    new_entity = RecognizedEntity(
                        document_id=document.id,
                        name=ent_text,
                        entity_type=ent_type,
                        total_occurrences=1,
                    )
                    await entities_col.insert_one(new_entity.model_dump(by_alias=True))
                    entity_cache[cache_key] = new_entity
                    active_entity_id = new_entity.id

                # Save occurrence
                occurrence = EntityOccurrence(
                    entity_id=active_entity_id,
                    document_id=document.id,
                    page_number=page.page_number,
                    start_offset=start_offset,
                    end_offset=end_offset,
                    surface_text=ent_text,
                    confidence=confidence,
                )
                await occurrences_col.insert_one(occurrence.model_dump(by_alias=True))
                job.total_occurrences_found += 1

            page.ner_status = NerStatus.COMPLETED
            await pages_col.update_one(
                {"_id": page.id},
                {
                    "$set": {
                        "ner_status": getattr(NerStatus.COMPLETED, "value", NerStatus.COMPLETED)
                    }
                },
            )
            job.pages_ner_completed += 1
            page_log.info(
                "Page {} NER complete: {} entity mentions found",
                page.page_number,
                len(raw_entities),
            )

        job.total_entities_found = len(entity_cache)
        job.completed_at = datetime.now(timezone.utc)

        if has_partial_failure:
            job.status = JobStatus.PARTIALLY_COMPLETED
            job.error_message = "; ".join(partial_error_messages)
            document.status = DocumentStatus.COMPLETED
            log.warning("Pipeline completed with partial page failures: {}", job.error_message)
        else:
            job.status = JobStatus.COMPLETED
            document.status = DocumentStatus.COMPLETED
            log.info("Pipeline completed successfully without errors.")

        await jobs_col.update_one(
            {"_id": job.id},
            {
                "$set": {
                    "status": getattr(job.status, "value", job.status),
                    "pages_ner_completed": job.pages_ner_completed,
                    "total_entities_found": job.total_entities_found,
                    "total_occurrences_found": job.total_occurrences_found,
                    "error_message": job.error_message,
                    "completed_at": job.completed_at,
                }
            },
        )
        await docs_col.update_one(
            {"_id": document.id},
            {"$set": {"status": getattr(document.status, "value", document.status)}},
        )

        return job
