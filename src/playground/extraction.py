import asyncio
import json
import time

import aiofiles
import httpx
from loguru import logger

RESPONSE_DIR_PATH = "/home/tushar/ner-chatbot/data/responses/extraction"

FILE_PATH = "/home/tushar/ner-chatbot/data/assessment-of-the-threat-from-russia.pdf"


async def main() -> None:
    uid = str(int(time.time()))
    logger.info(f"Request id: {uid}")
    try:
        async with httpx.AsyncClient() as client, aiofiles.open(FILE_PATH, "rb") as f:
            data = {"config": '{"ocr": {"language": "eng"}, "force_ocr": true}'}
            file_contents = await f.read()
            response = await client.post(
                "http://localhost:8000/extract",
                files={"files": file_contents},
                data=data,
            )
        data = response.json()
        resp_text = json.dumps(data, indent=2)

        logger.info(f"Response: {resp_text}")
        await save_response(uid, resp_text)
    except httpx.HTTPStatusError as e:
        error: dict = e.response.json()
        error_type: str = error.get("error_type", "Unknown")
        message: str = error.get("message", "No message")
        print(f"Error: {error_type}: {message}")


async def save_response(uid: str, data: str):
    resp_file_path = f"{RESPONSE_DIR_PATH}/{uid}.json"
    async with aiofiles.open(resp_file_path, "w") as f:
        await f.write(data)
    logger.info(f"Response written to: {resp_file_path}")


asyncio.run(main())
