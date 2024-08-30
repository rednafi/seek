import argparse
import asyncio
import logging
from contextlib import AsyncExitStack
from pathlib import Path
from typing import AsyncIterator

import httpx

# Configure logging to remove the default `__main__` logger name
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger()


async def fetch_index(api_url: str) -> AsyncIterator[bytes]:
    async with AsyncExitStack() as stack:
        client = await stack.enter_async_context(httpx.AsyncClient())
        response = await stack.enter_async_context(client.stream("GET", api_url))
        response.raise_for_status()
        total_size = int(response.headers.get("Content-Length", 0))
        downloaded_size = 0

        async for chunk in response.aiter_bytes():
            downloaded_size += len(chunk)
            logger.info(
                f"Downloaded {downloaded_size} of {total_size} bytes ({downloaded_size / total_size:.2%})"
            )
            yield chunk

        total_size_mb = downloaded_size / (1024 * 1024)
        logger.info(f"Download complete. Total size: {total_size_mb:.2f} MB.")


async def write_to_json(iterator: AsyncIterator[bytes], output_file: Path) -> None:
    if output_file.suffix != ".json":
        raise ValueError("Output file must be a JSON file")

    with output_file.open("wb") as f:
        async for chunk in iterator:
            f.write(chunk)


async def main(api_url: str, output_file: Path) -> None:
    blog_iterator = fetch_index(api_url)
    await write_to_json(blog_iterator, output_file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Fetch blog index and save to a JSON file."
    )
    parser.add_argument(
        "--url", type=str, help="The API URL to fetch the blog index from."
    )
    parser.add_argument(
        "--output", type=Path, help="The output JSON file path to save the blogs to."
    )

    args = parser.parse_args()

    asyncio.run(main(args.url, args.output))
