from pathlib import Path

import pytest

from src.agent import create_entity_agent
from src.services.agent_tools import get_entity_occurrences
from src.services.ingestion import IngestionPipelineCoordinator

PDF_PATH = Path("data/assessment-of-the-threat-from-russia.pdf")


@pytest.mark.asyncio
async def test_agent_entity_query_e2e():
    """Ingest document, query the agent for 'Putin', and verify occurrence count."""
    # ingest document
    coordinator = IngestionPipelineCoordinator()
    await coordinator.run(file_path=PDF_PATH)

    # ground truth check from database tool
    ground_truth = await get_entity_occurrences("Putin")
    expected_count = ground_truth.total_occurrences
    assert expected_count > 0, "Expected 'Putin' occurrences in test document"

    # query the conversational agent
    agent = create_entity_agent()
    response = await agent.run("How many occurrences of Putin are in the documents?")

    # verify agent response contains the correct count
    output = response.output
    assert str(expected_count) in output, (
        f"Expected agent response to state count {expected_count}. Response was: {output}"
    )
