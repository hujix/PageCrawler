import time
from typing import List

from fastapi import FastAPI

from crawler import CrawlerExecutor
from crawler.models import CrawlerRequest, CrawlerResult
from logger import logger
from models import ResponseData

app = FastAPI(openapi_prefix="",
              openapi_url=None,
              docs_url=None,
              redoc_url=None)

crawler_executor = CrawlerExecutor()


@app.get("/")
async def index() -> dict:
    return {"ping": "pong"}


@app.post("/extract")
async def extract(item: CrawlerRequest) -> ResponseData:
    logger.info(f"Received new request : {item.model_dump()}")
    crawl_start = time.time()
    result: List[CrawlerResult] = await crawler_executor.crawl_page(item)
    return ResponseData(time=round(time.time() - crawl_start, 2), msg="success", data=result)
