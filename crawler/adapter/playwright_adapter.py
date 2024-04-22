import asyncio
from asyncio import Semaphore
from typing import Optional, List, Tuple

import async_timeout
from playwright.async_api import async_playwright, Request, Route, Browser, BrowserContext, Playwright
from playwright_stealth import stealth_async

from crawler.abstract_crawler_adapter import AbstractPageCrawlerAdapter
from crawler.utils import async_timeit
from logger import logger


class PlaywrightCrawlerAdapter(AbstractPageCrawlerAdapter):
    """
    Crawler adapter for Playwright.
    """

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

    async def _create_browser(self, index: int = None) -> None:
        browser = await self.playwright.chromium.launch(headless=self.headless,
                                                        executable_path=self.executable_path)
        browser_ctx = await browser.new_context(ignore_https_errors=True, bypass_csp=True)
        if index is None:
            self._context_list.append((browser, browser_ctx, Semaphore(self.page_count)))
        else:
            browser_old, browser_ctx_old, _ = self._context_list[index]
            await browser_ctx_old.close()
            await browser_old.close()
            self._context_list[index] = (browser, browser_ctx, Semaphore(self.page_count))

    async def initialize(self) -> None:
        if len(self._context_list) == 0:
            self.playwright = await async_playwright().start()
            for idx in range(self.browser_count):
                await self._create_browser()

    @async_timeit
    async def _crawler(self, url: str) -> Tuple[str, Optional[str], Optional[str]]:
        current_idx = self._index % self.browser_count
        self._index += 1
        browser, browser_ctx, semaphore = self._context_list[current_idx]

        async with semaphore:
            try:
                page = await browser_ctx.new_page()
            except Exception as e:
                logger.error(f"Exception while creating page : {url} : {e}")
                await self._create_browser(current_idx)
                _, browser_ctx, _ = self._context_list[current_idx]
                page = await browser_ctx.new_page()

            try:
                await stealth_async(page)
                async with async_timeout.timeout(self.timeout / 1000):
                    # enable intercept
                    await page.route("**/*",
                                     lambda route, request: asyncio.create_task(self._intercept(route, request)))
                    await page.goto(url, timeout=self.timeout, wait_until="domcontentloaded")
                    return url, await page.content(), None
            except asyncio.TimeoutError as e:
                logger.error(f"Crawl timeout with adapter [playwright] : {url}")
                return url, None, "timeout"
            except Exception as e:
                logger.error(f"Crawl error with adapter [playwright] : {e} : {url}")
                return url, None, str()
            finally:
                await page.close()

    @classmethod
    async def _intercept(cls, route: Route, request: Request):
        resource_type = request.resource_type
        if resource_type in ['document', 'script']:
            await route.continue_()
        else:
            await route.abort()
