"""Structured logging configuration utilizing loguru."""

import sys
from typing import Any, Dict

from loguru import logger


def format_record(record: Dict[str, Any]) -> str:
    """Format loguru records with contextual bound attributes if present."""
    extra = record["extra"]
    context_parts = []
    if "job_id" in extra:
        job_id = str(extra["job_id"])
        context_parts.append(f"job={job_id[:8] if len(job_id) >= 8 else job_id}")
    if "document_id" in extra:
        doc_id = str(extra["document_id"])
        context_parts.append(f"doc={doc_id[:8] if len(doc_id) >= 8 else doc_id}")
    if "page_number" in extra:
        context_parts.append(f"page={extra['page_number']}")

    context_str = f" [{', '.join(context_parts)}]" if context_parts else ""

    return (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan>"
        f"{context_str} - <level>{{message}}</level>\n{{exception}}"
    )


def setup_logging(verbose: bool = False) -> None:
    """Configure loguru logger routing diagnostic logs to stderr."""
    logger.remove()
    log_level = "DEBUG" if verbose else "INFO"
    logger.add(
        sys.stderr,
        format=format_record,
        level=log_level,
        colorize=True,
    )


__all__ = ["logger", "setup_logging"]
