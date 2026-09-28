"""HTTP REST client for OCR-enabled content extraction via Xberg API."""

import json
from pathlib import Path
from typing import List, Tuple

import aiofiles
import httpx

from src.config import settings
from src.utils.logging import logger


class ExtractionError(Exception):
    """Raised when Xberg content extraction fails."""

    pass


class XbergExtractionService:
    """Service client for calling the containerized Xberg OCR API server."""

    def __init__(
        self, base_url: str = settings.xberg_api_url, language: str = settings.xberg_ocr_language
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.language = language

    async def extract_pdf(
        self,
        file_path: Path,
        force_ocr: bool = True,
    ) -> Tuple[int, List[Tuple[int, str]]]:
        """
        Extract text from a target PDF document page-by-page using unconditional OCR.

        Returns:
            Tuple of (total_page_count, list of (1-based page_number, extracted_text))
        """
        if not file_path.exists() or not file_path.is_file():
            raise ExtractionError(f"Target file does not exist or is not a file: {file_path}")

        url = f"{self.base_url}/extract"
        logger.debug(
            "Dispatching extraction request to Xberg at {} for file: {}", url, file_path.name
        )

        async with aiofiles.open(file_path, "rb") as f:
            file_bytes = await f.read()

        config_payload = {
            "ocr": {
                "backend": "tesseract",
                "language": [self.language],
            },
            "force_ocr": force_ocr,
        }

        # Multi-page documents with OCR may take tens of seconds
        timeout = httpx.Timeout(connect=15.0, read=300.0, write=60.0, pool=15.0)

        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                response = await client.post(
                    url,
                    files={"files": (file_path.name, file_bytes, "application/pdf")},
                    data={"config": json.dumps(config_payload)},
                )
            except httpx.ConnectError as e:
                logger.error("Failed to connect to Xberg API server at {}: {}", self.base_url, e)
                raise ExtractionError(
                    f"Could not connect to Xberg API at {self.base_url}. "
                    "Ensure Docker container is running."
                ) from e
            except httpx.TimeoutException as e:
                logger.error("Xberg extraction timed out for file {}: {}", file_path.name, e)
                raise ExtractionError(
                    f"Extraction request timed out for file: {file_path.name}"
                ) from e
            except httpx.HTTPError as e:
                logger.error("HTTP error while calling Xberg API: {}", e)
                raise ExtractionError(f"Xberg API communication error: {e}") from e

        if response.status_code != 200:
            error_msg = f"Xberg API returned error {response.status_code}: {response.text}"
            logger.error(error_msg)
            raise ExtractionError(error_msg)

        data = response.json()
        results = data.get("results", [])
        if not results:
            errors = data.get("errors", [])
            err_desc = "; ".join(str(err) for err in errors) if errors else "No results returned"
            raise ExtractionError(f"Xberg extraction returned no content: {err_desc}")

        primary_result = results[0]
        metadata = primary_result.get("metadata", {}) or {}
        raw_pages = primary_result.get("pages", [])

        extracted_pages: List[Tuple[int, str]] = []

        if raw_pages:
            for page_entry in raw_pages:
                pg_num = page_entry.get("page_number", len(extracted_pages) + 1)
                pg_content = page_entry.get("content", "") or ""
                extracted_pages.append((int(pg_num), pg_content))
            extracted_pages.sort(key=lambda x: x[0])
        else:
            # Fallback if pages breakdown was omitted
            full_content = primary_result.get("content", "") or ""
            extracted_pages.append((1, full_content))

        # Total pages from metadata, fallback to extracted pages count
        total_pages = metadata.get("page_count", len(extracted_pages))
        if total_pages is None or total_pages < len(extracted_pages):
            total_pages = len(extracted_pages)

        logger.debug(
            "Xberg extraction parsed successfully for {}: {} pages detected",
            file_path.name,
            len(extracted_pages),
        )
        return int(total_pages), extracted_pages
