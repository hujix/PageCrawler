from abc import ABC, abstractmethod

from crawler.models import CrawlerResult, CrawlerRequest
from crawler.utils import clean_html, parse_meta


class AbstractPageCrawlerAdapter(ABC):

    def __init__(self):
        pass

    @abstractmethod
    async def crawl(self, item: CrawlerRequest) -> CrawlerResult:
        """
        爬取网页内容
        """
        raise NotImplementedError

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

    @classmethod
    async def _post_process_browser_result(cls, page, item: CrawlerRequest) -> CrawlerResult:
        title = await page.title()
        html = await page.content()

        html = clean_html(html, item.clean)

        _, keywords, description = parse_meta(html)
        return CrawlerResult(url=item.url, title=title, keywords=keywords, html=html, description=description)
