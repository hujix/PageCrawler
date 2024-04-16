import asyncio
from typing import Dict, List

from crawler.abstract_crawler_adapter import AbstractPageCrawlerAdapter
from crawler.adapter import RequestCrawlerAdapter, PlaywrightCrawlerAdapter, PyppeteerCrawlerAdapter
from crawler.models import CrawlerRequest, CrawlerResult, CrawlerAdapter
from logger import logger


class CrawlerExecutor:
    """
    Crawler Executor
    """

    def __init__(self, **kwargs):
        self.adapters: Dict["CrawlerAdapter", "AbstractPageCrawlerAdapter"] = {
            CrawlerAdapter.REQUEST: RequestCrawlerAdapter(
                timeout=kwargs.get("request_timeout", 5)),
            CrawlerAdapter.PLAYWRIGHT: PlaywrightCrawlerAdapter(
                browser_count=kwargs.get("playwright_browser_count", 1),
                page_count=kwargs.get("playwright_page_count", 5),
                timeout=kwargs.get("browser_timeout", 5),
                headless=kwargs.get("headless", True),
                executable_path=kwargs.get("playwright_executable_path", None)),
            CrawlerAdapter.PYPPETEER: PyppeteerCrawlerAdapter(
                browser_count=kwargs.get("pyppeteer_browser_count", 1),
                page_count=kwargs.get("pyppeteer_page_count", 5),
                timeout=kwargs.get("browser_timeout", 5),
                headless=kwargs.get("headless", True),
                executable_path=kwargs.get("pyppeteer_executable_path", None)),
        }

    async def crawl_page(self, item: CrawlerRequest) -> List[CrawlerResult]:
        crawler_tasks = []
        for adapter in item.adapters:
            if adapter not in self.adapters:
                logger.error(f"Crawler adapter {adapter} not found")
                raise ValueError(f"Crawler adapter {adapter} not found")
            crawler_tasks.append(self.adapters.get(adapter).crawl(adapter, item.urls))

        result_item_list: List[CrawlerResult] = [CrawlerResult(url=url) for url in item.urls]
        url_dict = {url: idx for idx, url in enumerate(item.urls)}
        for crawler_task in asyncio.as_completed(crawler_tasks):
            results = await crawler_task
            for result in results:
                result_item = max(result, result_item_list[url_dict[result.url]],
                                  key=lambda x: len(x.title + x.html + x.reason))
                result_item_list[url_dict[result.url]] = result_item

        return result_item_list
