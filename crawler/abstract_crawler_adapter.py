import asyncio
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple

from crawler.models import CrawlerResult, CrawlerAdapter
from crawler.utils import parse_meta


class AbstractPageCrawlerAdapter(ABC):
    """
    Abstract base class for page crawler adapters.
    """

    def __init__(self):
        pass

    @abstractmethod
    async def initialize(self) -> None:
        """
        initialize the page crawler adapter.
        """
        raise NotImplementedError

    @abstractmethod
    async def close(self) -> None:
        """
        close the page crawler adapter's resource.
        """
        raise NotImplementedError

    @abstractmethod
    async def _crawler(self, url: str) -> Tuple[str, Optional[str], Optional[str]]:
        """
        Crawl the given item.
        :param url: url to crawl
        :return: html,reason
        """
        raise NotImplementedError

    async def crawl(self, adapter: CrawlerAdapter, urls: List[str]) -> List[CrawlerResult]:
        """
        Crawl the given item by adapter.
        :param adapter: adapter to crawl
        :param urls: urls to crawl
        :return: result of crawl
        """
        await self.initialize()

        crawler_tasks = []
        for idx, url in enumerate(urls):
            crawler_tasks.append(self._crawler(url))

        result_item_list: List[CrawlerResult] = []
        for crawler_task in asyncio.as_completed(crawler_tasks):
            url, html, reason = await crawler_task
            title, keywords, description = "", [], ""
            if html is not None:
                title, keywords, description = parse_meta(html)

            result = CrawlerResult(url=url, title=title, keywords=keywords,
                                   html="" if html is None else html,
                                   reason="" if reason is None else reason,
                                   success=True if reason is None else False,
                                   description=description, adapter=adapter.value.title())
            result_item_list.append(result)

        return result_item_list
