import asyncio
from abc import ABC, abstractmethod
from typing import Tuple, Optional

from crawler.models import CrawlerResult, CrawlerRequest, CrawlerAdapter
from crawler.utils import parse_meta
from logger import logger


class AbstractPageCrawlerAdapter(ABC):

    def __init__(self):
        pass

    @abstractmethod
    async def initialize(self) -> None:
        """
        初始化
        """
        raise NotImplementedError

    @abstractmethod
    async def close(self) -> None:
        """
        关闭资源
        """
        raise NotImplementedError

    @abstractmethod
    async def _crawler(self, item: CrawlerRequest) -> Tuple[Optional[str], Optional[str]]:
        """
        爬取网页内容
        """
        raise NotImplementedError

    async def crawl(self, adapter: CrawlerAdapter, item: CrawlerRequest) -> CrawlerResult:
        """
        爬取网页内容
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
