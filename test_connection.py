
import asyncio
import os

import aiohttp


API_BASE = os.getenv(
    "ECHOCHAT_API_URL",
    "http://127.0.0.1:8000",
).rstrip("/")


async def main():
    timeout = aiohttp.ClientTimeout(total=15)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        for path in ("/", "/health", "/docs"):
            url = f"{API_BASE}{path}"

            try:
                async with session.get(url) as response:
                    print(f"{path}: HTTP {response.status}")
                    print(await response.text())
            except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
                print(f"{path}: CONNECTION FAILED — {exc}")


if __name__ == "__main__":
    asyncio.run(main())
