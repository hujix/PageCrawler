import asyncio
from typing import Dict, List

from crawler.abstract_crawler_adapter import AbstractPageCrawlerAdapter
from crawler.adapter import RequestCrawlerAdapter, PlaywrightCrawlerAdapter, PyppeteerCrawlerAdapter
from crawler.models import CrawlerRequest, CrawlerResult, CrawlerAdapter
from logger import logger


class CrawlerExecutor:
    def __init__(self, **kwargs):
        self.adapters: Dict["CrawlerAdapter", "AbstractPageCrawlerAdapter"] = {
            CrawlerAdapter.request: RequestCrawlerAdapter(timeout=kwargs.get("request_timeout", 5)),
            CrawlerAdapter.playwright: PlaywrightCrawlerAdapter(browser_count=1),
            CrawlerAdapter.pyppeteer: PyppeteerCrawlerAdapter(browser_count=1)
        }

    async def crawl_page(self, item: CrawlerRequest) -> CrawlerResult:
        tasks = []
        for adapter in item.adapters:
            if adapter not in self.adapters:
                logger.error(f"Crawler adapter {adapter} not found")
                raise ValueError(f"Crawler adapter {adapter} not found")
            tasks.append(self.adapters.get(adapter).crawl(adapter, item))

        results: List[CrawlerResult] = list(await asyncio.gather(*tasks))

        return max(results, key=lambda x: len(x.title + x.html + x.reason))
