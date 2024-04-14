import asyncio
from typing import Dict, List

from crawler.abstract_crawler_adapter import AbstractPageCrawlerAdapter
from crawler.adapter import RequestCrawlerAdapter, PlaywrightCrawlerAdapter, PuppeteerCrawlerAdapter
from crawler.models import CrawlerRequest, CrawlerResult, CrawlerAdapter
from logger import logger


class CrawlerExecutor:
    """
    Crawler Executor
    """

    def __init__(self, **kwargs):
        self.adapters: Dict["CrawlerAdapter", "AbstractPageCrawlerAdapter"] = {
            CrawlerAdapter.request: RequestCrawlerAdapter(timeout=kwargs.get("request_timeout", 5)),
            CrawlerAdapter.playwright: PlaywrightCrawlerAdapter(
                browser_count=kwargs.get("playwright_browser_count", 1),
                page_count=kwargs.get("playwright_page_count", 1),
                timeout=kwargs.get("browser_timeout", 5),
                headless=kwargs.get("headless", True),
                executable_path=kwargs.get("playwright_executable_path", None)),
            CrawlerAdapter.puppeteer: PuppeteerCrawlerAdapter(
                browser_count=kwargs.get("puppeteer_browser_count", 1),
                page_count=kwargs.get("puppeteer_page_count", 1),
                timeout=kwargs.get("browser_timeout", 5),
                headless=kwargs.get("headless", True),
                executable_path=kwargs.get("puppeteer_executable_path", None)),
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
