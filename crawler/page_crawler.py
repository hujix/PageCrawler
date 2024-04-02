from typing import Dict

from crawler.abstract_crawler_adapter import AbstractPageCrawlerAdapter
from crawler.adapter import RequestCrawlerAdapter, PlaywrightCrawlerAdapter, PyppeteerCrawlerAdapter
from crawler.models import CrawlerRequest, CrawlerResult, CrawlerAdapter


class CrawlerExecutor:
    def __init__(self, **kwargs):
        self.adapters: Dict["CrawlerAdapter", "AbstractPageCrawlerAdapter"] = {
            CrawlerAdapter.request: RequestCrawlerAdapter(timeout=kwargs.get("request_timeout", 5)),
            CrawlerAdapter.playwright: PlaywrightCrawlerAdapter(browser_count=1),
            CrawlerAdapter.pyppeteer: PyppeteerCrawlerAdapter(browser_count=1)
        }

    async def crawl_with_adapter(self, adapter: CrawlerAdapter, item: CrawlerRequest) -> CrawlerResult:
        # 调用模板方法进行爬取
        result: CrawlerResult = await self.adapters.get(adapter).crawl(item)
        result.adapter = adapter.value.title()
        return result
