from typing import Optional

import aiohttp
from aiohttp import ClientSession
from fake_useragent import UserAgent

from adapter.base_adapter import BaseCrawler
from adapter.utils import async_timeit, clean_html, parse_meta
from logger import logger
from models import CrawlerResult, CrawlerRequest


class RequestCrawler(BaseCrawler):
    adapter = "Request"

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
    async def crawl(self, item: CrawlerRequest) -> CrawlerResult:
        if self.session is None:
            await self.initialize()
        try:
            async with self.session.get(item.url, headers=await self._create_header(item.url)) as response:
                if response.status not in [200, 301, 302, 307, 401, 403]:
                    response.raise_for_status()
                html = await response.text()

                html = clean_html(html, item.clean)

                title, keywords, description = parse_meta(html)
                return CrawlerResult(url=item.url, title=title, keywords=keywords, html=html,
                                     description=description, adapter=self.adapter)
        except Exception as e:
            logger.error(f"Error while crawling {item.url}: {e}")
            return CrawlerResult(url=item.url, success=False, reason=f"{response.status}:{response.reason}",
                                 adapter=self.adapter)
