from abc import ABC, abstractmethod

from models import CrawlerResult, CrawlerRequest


class BaseCrawler(ABC):

    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    async def crawl(self, item: CrawlerRequest) -> CrawlerResult:
        """
        爬取网页内容
        """
        raise NotImplementedError

    @abstractmethod
    async def close(self) -> None:
        """
        关闭资源
        """
        raise NotImplementedError
