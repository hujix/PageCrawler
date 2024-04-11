import asyncio
from asyncio import Semaphore
from typing import List, Tuple, Optional

import async_timeout
from pyppeteer import launch
from pyppeteer.browser import Browser
from pyppeteer.network_manager import Request

from crawler.abstract_crawler_adapter import AbstractPageCrawlerAdapter
from crawler.models import CrawlerRequest
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

    async def close(self):
        if len(self._context_list) > 0:
            for browser, _ in self._context_list:
                await browser.close()
            self._context_list.clear()

    async def initialize(self) -> None:
        if len(self._context_list) == 0:
            for idx in range(self.browser_count):
                browser = await launch(options={
                    'headless': self.headless,
                    'ignoreHTTPSErrors': True,
                    'dumpio': False,
                    'autoClose': False,
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
    async def _crawler(self, item: CrawlerRequest) -> Tuple[Optional[str], Optional[str]]:
        browser, semaphore = self._context_list[self._index % self.browser_count]
        self._index += 1
        async with semaphore:
            page = await browser.newPage()
            try:
                async with async_timeout.timeout(self.timeout / 1000):
                    await page.evaluateOnNewDocument(
                        '()=>{Object.defineProperties(navigator,{webdriver:{get:()=>false}});')
                    # 开启请求拦截
                    await page.setRequestInterception(True)
                    page.on('request', lambda req: asyncio.ensure_future(self._intercept(req)))
                    page.on("dialog", lambda x: asyncio.ensure_future(self._close_dialog(x)))

                    await page.goto(item.url, timeout=self.timeout, waitUntil="networkidle2")

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
