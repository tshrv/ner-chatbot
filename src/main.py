"""Typer CLI entrypoint for the Ingestion Pipeline."""

import asyncio
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

import typer

from src.agent import create_entity_agent
from src.config import settings
from src.database import close_db, get_jobs_collection, init_db
from src.models.job import IngestionJob, JobStatus
from src.services.extraction import ExtractionError
from src.services.ingestion import IngestionPipelineCoordinator
from src.utils.logging import logger, setup_logging

app = typer.Typer(
    name="ner-chatbot",
    help="Content extraction and named entity recognition ingestion pipeline CLI.",
    add_completion=False,
)


@app.callback()
def callback() -> None:
    """Ingestion pipeline CLI."""
    pass


def format_summary_table(job_record: IngestionJob, elapsed: float) -> str:
    """Format console execution summary according to CLI contract."""
    status_str = job_record.status.value.upper()
    lines = [
        "=" * 60,
        "              INGESTION PIPELINE SUMMARY",
        "=" * 60,
        f"Job ID:             {job_record.id}",
        f"Document ID:        {job_record.document_id or 'N/A'}",
        f"Document Name:      {Path(job_record.file_path).name}",
        f"File Path:          {job_record.file_path}",
        f"Status:             {status_str}",
        f"Total Pages:        {job_record.total_pages}",
        f"Pages Extracted:    {job_record.pages_extracted}",
        f"Pages Analyzed:     {job_record.pages_ner_completed}",
        (
            f"Entities Discovered: {job_record.total_occurrences_found} "
            f"(unique: {job_record.total_entities_found})"
        ),
        f"Elapsed Time:       {elapsed:.1f}s",
    ]
    if job_record.status == JobStatus.PARTIALLY_COMPLETED and job_record.error_message:
        lines.append(f"Warning: {job_record.error_message}")
    lines.append("=" * 60)
    return "\n".join(lines)


@app.command(name="ingest")
def ingest(
    file_path: Path = typer.Argument(
        ...,
        help="Local filesystem path to the target PDF document.",
    ),
    labels: Optional[str] = typer.Option(
        None,
        "--labels",
        "-l",
        help="Comma-separated list of target entity labels for GLiNER.",
    ),
    threshold: float = typer.Option(
        settings.ner_threshold,
        "--threshold",
        "-t",
        min=0.0,
        max=1.0,
        help="Confidence threshold for named entity recognition (0.0 to 1.0).",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable detailed debug logs to stderr.",
    ),
) -> None:
    """Trigger the document ingestion pipeline for a local PDF file."""
    setup_logging(verbose=verbose)

    # Parse labels
    parsed_labels: Optional[List[str]] = None
    if labels:
        parsed_labels = [label.strip() for label in labels.split(",") if label.strip()]

    start_time = time.perf_counter()
    coordinator = IngestionPipelineCoordinator()

    try:
        job = asyncio.run(
            coordinator.run(file_path=file_path, labels=parsed_labels, threshold=threshold)
        )
    except ValueError as e:
        logger.error("Input validation failed: {}", e)
        sys.stderr.write(f"Validation Error: {e}\n")
        raise typer.Exit(code=1)
    except KeyboardInterrupt:
        logger.warning("Pipeline execution interrupted by user (SIGINT / Ctrl+C).")
        sys.stderr.write("\nExecution interrupted by user.\n")
        # Record interruption to active job in MongoDB
        if coordinator.active_job_id:
            try:

                async def _mark_interrupted():
                    col = get_jobs_collection()
                    await col.update_one(
                        {"_id": coordinator.active_job_id},
                        {
                            "$set": {
                                "status": getattr(JobStatus.FAILED, "value", JobStatus.FAILED),
                                "error_message": "Execution interrupted by user (SIGINT)",
                                "completed_at": datetime.now(timezone.utc),
                            }
                        },
                    )

                asyncio.run(_mark_interrupted())
            except Exception as cleanup_err:
                logger.debug("Could not record interruption to database: {}", cleanup_err)
        raise typer.Exit(code=130)
    except ExtractionError as e:
        logger.error("Pipeline extraction error: {}", e)
        sys.stderr.write(f"Extraction Error: {e}\n")
        raise typer.Exit(code=2)
    except Exception as e:
        logger.exception("Unexpected pipeline failure: {}", e)
        sys.stderr.write(f"Fatal Error: {e}\n")
        raise typer.Exit(code=1)
    finally:
        close_db()

    elapsed = time.perf_counter() - start_time
    summary_text = format_summary_table(job, elapsed)
    sys.stdout.write(summary_text + "\n")


@app.command(name="chat")
def chat(
    model: Optional[str] = typer.Option(
        None,
        "--model",
        "-m",
        help="Gemini LLM model identifier (default: gemini-3.8-flash).",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable detailed debug logs to stderr.",
    ),
) -> None:
    """Launch an interactive natural language chat session to query entity intelligence."""
    setup_logging(verbose=verbose)

    banner = [
        "=" * 60,
        "              ENTITY INTELLIGENCE CHAT AGENT",
        "=" * 60,
        "Ask questions about entities, types, and occurrences.",
        "Type 'exit' or 'quit' to end the session.",
        "=" * 60,
    ]
    sys.stdout.write("\n".join(banner) + "\n\n")

    try:
        agent = create_entity_agent(model_name=model)
    except ValueError as e:
        logger.error("Configuration error: {}", e)
        sys.stderr.write(f"Configuration Error: {e}\n")
        raise typer.Exit(code=1)

    async def _chat_loop() -> None:
        await init_db()
        max_retries = settings.agent_max_retries

        while True:
            try:
                user_prompt = input("You: ").strip()
            except (KeyboardInterrupt, EOFError):
                sys.stdout.write("\nGoodbye!\n")
                break

            if not user_prompt:
                continue

            if user_prompt.lower() in ("exit", "quit", "q"):
                sys.stdout.write("Goodbye!\n")
                break

            # Execute single-turn query with retry mechanism
            for attempt in range(1, max_retries + 1):
                try:
                    result = await agent.run(user_prompt)
                    sys.stdout.write(f"\nAgent: {result.output}\n\n")
                    break
                except Exception as err:
                    logger.warning(
                        "Agent execution attempt {}/{} failed: {}",
                        attempt,
                        max_retries,
                        err,
                    )
                    if attempt < max_retries:
                        await asyncio.sleep(1.0)
                    else:
                        sys.stdout.write(
                            f"\nAgent: I encountered an unexpected error after "
                            f"{max_retries} attempts: {err}\n\n"
                        )

    try:
        asyncio.run(_chat_loop())
    except KeyboardInterrupt:
        sys.stdout.write("\nGoodbye!\n")
    finally:
        close_db()


def main() -> None:
    """CLI application main runner."""
    app()


if __name__ == "__main__":
    main()
