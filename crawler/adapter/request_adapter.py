from typing import Optional, Tuple

import aiohttp
from aiohttp import ClientSession
from fake_useragent import UserAgent

from crawler.abstract_crawler_adapter import AbstractPageCrawlerAdapter
from crawler.models import CrawlerRequest
from crawler.utils import async_timeit


class RequestCrawlerAdapter(AbstractPageCrawlerAdapter):
    """
    Crawler adapter for requests using aiohttp.
    """

    def __init__(self, timeout: int = 5):
        super().__init__()
        self._base_header = {
            "Accept": "*/*",
            # "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "Cache-Control": "no-cache",
        }
        self.session: Optional[ClientSession] = None
        self._timeout = timeout

    async def close(self) -> None:
        if self.session is not None:
            await self.session.close()

    async def initialize(self) -> None:
        if self.session is None:
            connector = aiohttp.TCPConnector(verify_ssl=False)
            client_timeout = aiohttp.ClientTimeout(total=self._timeout)
            self.session = aiohttp.ClientSession(timeout=client_timeout, connector=connector)

    async def _create_header(self, url: str) -> dict:
        # parsed_url = urlparse(url)
        # host = parsed_url.netloc
        # scheme = parsed_url.scheme
        # if not parsed_url.path:
        #     homepage = f"{scheme}://{host}/"
        # else:
        #     homepage = f"{scheme}://{host}/"

        current_header = self._base_header.copy()
        current_header.update({
            # "Host": host,
            # "Referer": homepage,
            "User-Agent": UserAgent().random
        })
        return current_header

    @async_timeit
    async def _crawler(self, item: CrawlerRequest) -> Tuple[Optional[str], Optional[str]]:
        async with self.session.get(item.url, headers=await self._create_header(item.url)) as response:
            if response.status not in [200, 301, 302, 307, 401, 403]:
                response.raise_for_status()
            html = await response.text()
            return html, None
