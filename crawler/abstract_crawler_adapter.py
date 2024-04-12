import asyncio
from abc import ABC, abstractmethod
from typing import Tuple, Optional

from crawler.models import CrawlerResult, CrawlerRequest, CrawlerAdapter
from crawler.utils import parse_meta
from logger import logger


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
    async def _crawler(self, item: CrawlerRequest) -> Tuple[Optional[str], Optional[str]]:
        """
        Crawl the given item.
        :param item: item to crawl
        :return: html,reason
        """
        raise NotImplementedError

    async def crawl(self, adapter: CrawlerAdapter, item: CrawlerRequest) -> CrawlerResult:
        """
        Crawl the given item by adapter.
        :param adapter: adapter to crawl
        :param item: item to crawl
        :return: result of crawl
        """
        await self.initialize()

        try:
            html, reason = await self._crawler(item)
        except asyncio.TimeoutError as e:
            logger.error(f"Crawl timeout with adapter [{adapter.value}] : {item.url}")
            html, reason = None, "timeout"
        except Exception as e:
            logger.error(f"Crawl error with adapter [{adapter.value}] : {e} : {item.url}")
            html, reason = None, str(e)

        title, keywords, description = "", [], ""
        if html is not None:
            title, keywords, description = parse_meta(html)

        return CrawlerResult(url=item.url, title=title, keywords=keywords,
                             html="" if html is None else html,
                             reason="" if reason is None else reason,
                             success=True if reason is None else False,
                             description=description, adapter=adapter.value.title())
