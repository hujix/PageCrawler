import asyncio
from asyncio import Semaphore
from typing import List, Tuple, Optional

import async_timeout
from playwright.async_api import async_playwright
from pyppeteer import launch
from pyppeteer.browser import Browser
from pyppeteer.network_manager import Request

from crawler.abstract_crawler_adapter import AbstractPageCrawlerAdapter
from crawler.models import CrawlerResult, CrawlerRequest
from crawler.utils import async_timeit
from logger import logger


class PyppeteerCrawlerAdapter(AbstractPageCrawlerAdapter):
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

    def __del__(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.close())

    async def close(self):
        if len(self._context_list) > 0:
            for browser, _ in self._context_list:
                await browser.close()

    async def initialize(self) -> None:
        await self.close()
        if self.executable_path is None:
            # 借助playwright的浏览器创建实例
            playwright = await async_playwright().start()
            self.executable_path = playwright.chromium.executable_path
            await playwright.stop()

        for idx in range(self.browser_count):
            browser = await launch(options={
                'headless': self.headless,
                'ignoreHTTPSErrors': True,
                'dumpio': True,
                'autoClose': True,
                "args": [
                    '--no-sandbox',
                    '--disable-infobars',
                    '--disable-features=TranslateUI',
                    '--disable-web-security',
                    '--disable-popup-blocking'
                ],
                'ignoreDefaultArgs': ['--enable-automation'],
                'executablePath': self.executable_path
            })
            self._context_list.append((browser, Semaphore(self.page_count)))

    @async_timeit
    async def crawl(self, item: CrawlerRequest) -> CrawlerResult:
        if len(self._context_list) == 0:
            await self.initialize()

        browser, semaphore = self._context_list[self._index % self.browser_count]
        self._index += 1
        async with semaphore:
            page = await browser.newPage()
            try:
                async with async_timeout.timeout(self.timeout):
                    await page.evaluateOnNewDocument(
                        '()=>{Object.defineProperties(navigator,{webdriver:{get:()=>false}});')
                    # 开启请求拦截
                    await page.setRequestInterception(True)
                    page.on('request', lambda req: asyncio.ensure_future(self._intercept(req)))
                    page.on("dialog", lambda x: asyncio.ensure_future(self._close_dialog(x)))

                    wait_util = "domcontentloaded" if not item.xhr else "networkidle2"
                    await page.goto(item.url, timeout=self.timeout, waitUntil=wait_util)

                    return await super()._post_process_browser_result(page, item)
            except asyncio.TimeoutError as e:
                logger.error(f"Crawl timeout with adapter: {item.url}")
                return CrawlerResult(url=item.url, success=False, reason="timeout")
            except Exception as e:
                logger.error(f"Crawl error with adapter: {e} : {item.url}")
                return CrawlerResult(url=item.url, success=False, reason=str(e))
            finally:
                await page.close()

    @classmethod
    async def _intercept(cls, request: Request):
        # 获取请求的资源类型
        resource_type = request.resourceType

        # 允许加载页面和 JavaScript
        if resource_type in ['document', 'script', 'xhr']:
            await request.continue_()
        else:
            # 其他资源类型，如图片、样式表、字体等，中止请求
            await request.abort()

    @classmethod
    async def _close_dialog(cls, dialog):
        await dialog.dismiss()
