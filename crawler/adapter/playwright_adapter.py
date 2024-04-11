import asyncio
from asyncio import Semaphore
from typing import Optional, List, Tuple

import async_timeout
from playwright.async_api import async_playwright, Request, Route, Playwright, Browser, BrowserContext

from crawler.abstract_crawler_adapter import AbstractPageCrawlerAdapter
from crawler.models import CrawlerRequest
from crawler.utils import async_timeit
from logger import logger


class PlaywrightCrawlerAdapter(AbstractPageCrawlerAdapter):
    def __init__(self, browser_count: int = 1, page_count: int = 2, timeout: int = 5,
                 headless: bool = True, executable_path: Optional[str] = None) -> None:
        super().__init__()
        self._context_list: List[Tuple[Browser, BrowserContext, Semaphore]] = []
        self.playwright: Optional[Playwright] = None

        self._index = 0
        self.timeout = timeout * 1000
        self.headless = headless
        self.browser_count = browser_count
        self.page_count = page_count
        self.executable_path = executable_path

    async def close(self) -> None:
        if len(self._context_list) > 0:
            for browser, browser_ctx, _ in self._context_list:
                await browser.close()
                await browser_ctx.close()
            self._context_list.clear()
        if self.playwright is not None:
            await self.playwright.stop()

    async def initialize(self) -> None:
        if len(self._context_list) == 0:
            self.playwright = await async_playwright().start()

            for idx in range(self.browser_count):
                browser = await self.playwright.chromium.launch(headless=self.headless,
                                                                executable_path=self.executable_path)
                browser_ctx = await browser.new_context(ignore_https_errors=True, bypass_csp=True)
                self._context_list.append((browser, browser_ctx, Semaphore(self.page_count)))

    @async_timeit
    async def _crawler(self, item: CrawlerRequest) -> Tuple[Optional[str], Optional[str]]:
        _, browser_ctx, semaphore = self._context_list[self._index % self.browser_count]
        self._index += 1
        async with semaphore:
            page = await browser_ctx.new_page()
            try:
                async with async_timeout.timeout(self.timeout):
                    # 开启请求拦截
                    await page.route("**/*",
                                     lambda route, request: asyncio.create_task(self._intercept(route, request)))
                    await page.goto(item.url, timeout=self.timeout, wait_until="domcontentloaded")

                    return await page.content(), None
            except asyncio.TimeoutError as e:
                logger.error(f"Crawl timeout with adapter: {item.url}")
                return None, "timeout"
            except Exception as e:
                logger.error(f"Crawl error with adapter: {e} : {item.url}")
                return None, str(e)
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
