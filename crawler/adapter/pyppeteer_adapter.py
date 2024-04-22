import asyncio
from asyncio import Semaphore
from typing import List, Tuple, Optional

import async_timeout
from pyppeteer import launch
from pyppeteer.browser import Browser
from pyppeteer.network_manager import Request
from pyppeteer_stealth import stealth

from crawler.abstract_crawler_adapter import AbstractPageCrawlerAdapter
from crawler.utils import async_timeit
from logger import logger


class PyppeteerCrawlerAdapter(AbstractPageCrawlerAdapter):
    """
    Crawler adapter for Pyppeteer.
    """

    def __init__(self, browser_count: int = 1, page_count: int = 2, timeout: int = 5,
                 headless: bool = True, executable_path: Optional[str] = None) -> None:
        super().__init__()
        self._context_list: List[Tuple[Browser, Semaphore]] = []
        self._index = 0

        self.timeout = timeout * 1000
        self.headless = headless
        self.browser_count = browser_count
        self.page_count = page_count
        self.executable_path = executable_path

    async def close(self):
        if len(self._context_list) > 0:
            for browser, _ in self._context_list:
                await browser.close()
            self._context_list.clear()

    async def _create_browser(self, index: int = None):
        browser = await launch(options={
            'headless': self.headless,
            'ignoreHTTPSErrors': True,
            'dumpio': False,
            'autoClose': False,
            "args": [
                '--no-sandbox',
                '--disable-gpu',
                '--disable-setuid-sandbox',
                '--disable-infobars',
                '--disable-accelerated-2d-canvas',
                '--disable-features=TranslateUI',
                '--disable-popup-blocking',
                '--disable-accelerated-mjpeg-decode',
                '--disable-accelerated-video-encode',
                '--disable-audio-input',
                '--disable-audio-output',
                '--disable-canvas-aa',
                '--disable-web-security',
                '--disable-dev-shm-usage',
                '--disable-extensions'
            ],
            'ignoreDefaultArgs': ['--enable-automation'],
            'executablePath': self.executable_path
        })
        if index is None:
            self._context_list.append((browser, Semaphore(self.page_count)))
        else:
            browser, _ = self._context_list[index]
            await browser.close()
            self._context_list[index] = (browser, Semaphore(self.page_count))

    async def initialize(self) -> None:
        if len(self._context_list) == 0:
            for idx in range(self.browser_count):
                await self._create_browser()

    @async_timeit
    async def _crawler(self, url: str) -> Tuple[str, Optional[str], Optional[str]]:
        current_idx = self._index % self.browser_count
        self._index += 1
        browser, semaphore = self._context_list[current_idx]

        async with semaphore:
            try:
                page = await browser.newPage()
            except ConnectionError as e:
                logger.error(f"ConnectionError while creating page : {e}")
                await self._create_browser(current_idx)
                browser, _ = self._context_list[current_idx]
                page = await browser.newPage()

            try:
                await stealth(page)
                async with async_timeout.timeout(self.timeout / 1000):
                    # enable intercept
                    await page.setRequestInterception(True)
                    page.on('request', lambda req: asyncio.ensure_future(self._intercept(req)))
                    page.on("dialog", lambda x: asyncio.ensure_future(self._close_dialog(x)))

                    await page.goto(url, timeout=self.timeout, waitUntil="networkidle2")
                    return url, await page.content(), None
            except asyncio.TimeoutError as e:
                logger.error(f"Crawl timeout with adapter [pyppeteer] : {url}")
                return url, None, "timeout"
            except Exception as e:
                logger.error(f"Crawl error with adapter [pyppeteer] : {e} : {url}")
                return url, None, str()
            finally:
                await page.close()

    @classmethod
    async def _intercept(cls, request: Request):
        resource_type = request.resourceType
        if resource_type in ['document', 'script', 'xhr', 'fetch']:
            await request.continue_()
        else:
            await request.abort()

    @classmethod
    async def _close_dialog(cls, dialog):
        await dialog.dismiss()
