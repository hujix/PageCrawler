import asyncio
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from adapter import RequestCrawler, PyppeteerCrawler, PlaywrightCrawler
from models import CrawlerRequest


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    for crawler in ENABLE_CRAWLER:
        await crawler.close()


app = FastAPI(lifespan=lifespan)

request_crawler = RequestCrawler(timeout=5)
pyppeteer_crawler = PyppeteerCrawler()
playwright_crawler = PlaywrightCrawler()

ENABLE_CRAWLER = [
    # request_crawler,
    pyppeteer_crawler,
    playwright_crawler
]


@app.post("/extract", response_model_exclude={'adapter'})
async def extract(item: CrawlerRequest):
    tasks = [asyncio.create_task(crawler.crawl(item)) for crawler in ENABLE_CRAWLER]
    results = await asyncio.gather(*tasks)

    return results


if __name__ == '__main__':
    uvicorn.run(app='main:app', workers=1)
