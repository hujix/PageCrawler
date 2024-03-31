import asyncio
from asyncio import Semaphore
from typing import Optional

from playwright.async_api import async_playwright, Request, Route, Playwright, Browser, BrowserContext

from adapter.base_adapter import BaseCrawler
from adapter.utils import async_timeit, clean_html, parse_keywords, parse_description
from logger import logger
from models import CrawlerResult, CrawlerRequest


class PlaywrightCrawler(BaseCrawler):
    adapter = "Playwright"

    def __init__(self, page_count: int = 10):
        super().__init__()
        self.browser_ctx: Optional[BrowserContext] = None
        self._browser: Optional[Browser] = None
        self._playwright: Optional[Playwright] = None
        self.semaphore: Semaphore = Semaphore(page_count)

    async def close(self) -> None:
        if self.browser_ctx is not None:
            await self.browser_ctx.close()
        if self._browser is not None:
            await self._browser.close()
        if self._playwright is not None:
            await self._playwright.stop()

    async def create_browser(self) -> None:
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=False)
        self.browser_ctx = await self._browser.new_context(ignore_https_errors=True, bypass_csp=True)

    @async_timeit
    async def crawl(self, item: CrawlerRequest) -> CrawlerResult:
        if self.browser_ctx is None:
            await self.create_browser()
        async with self.semaphore:
            page = await self.browser_ctx.new_page()
            try:
                # 开启请求拦截
                await page.route("**/*", lambda route, request: asyncio.create_task(self._intercept(route, request)))
                await page.goto(item.url, wait_until="domcontentloaded")

                title = await page.title()
                content = await page.content()

                html = clean_html(content, item.clean)

                return CrawlerResult(url=item.url, title=title, keywords=parse_keywords(html), html=html,
                                     description=parse_description(html), adapter=self.adapter)
            except Exception as e:
                logger.error(f"Crawl error : {e}")
                return CrawlerResult(url=item.url, success=False, reason=str(e), adapter=self.adapter)
            finally:
                await page.close()

    @classmethod
    async def _intercept(cls, route: Route, request: Request):
        # 获取请求的资源类型
        resource_type = request.resource_type
        # 允许加载页面和 JavaScript
        if resource_type in ['document', 'script', 'xhr']:
            await route.continue_()
        else:
            await route.abort()
