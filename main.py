import math
import multiprocessing
import time

import uvicorn
from fastapi import FastAPI

from crawler import CrawlerExecutor
from crawler.models import CrawlerRequest, CrawlerAdapter, CrawlerResult
from logger import logger
from models import ResponseData

app = FastAPI(openapi_prefix="",
              openapi_url=None,
              docs_url=None,
              redoc_url=None)

core_count = multiprocessing.cpu_count()

playwright_count = math.floor(core_count * 0.8)

logger.info(f"Lazy loading : playwright:{playwright_count} pyppeteer:{core_count - playwright_count}")

crawler_executor = CrawlerExecutor()


@app.get("/")
async def index() -> dict:
    return {"ping": "pong"}


@app.post("/extract")
async def extract(item: CrawlerRequest) -> ResponseData:
    logger.info(f"Received new request : {item.model_dump()}")
    crawl_start = time.time()
    if len(item.adapters) == 0:
        item.adapters.append(CrawlerAdapter.request)

    result: CrawlerResult = await crawler_executor.crawl_page(item)

    return ResponseData(time=round(time.time() - crawl_start, 2), msg="success", data=result)


if __name__ == '__main__':
    uvicorn.run(app='main:app', host="0.0.0.0", port=8000)
