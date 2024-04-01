import asyncio
from asyncio import Semaphore
from typing import List, Tuple, Optional

from playwright.async_api import async_playwright
from pyppeteer import launch
from pyppeteer.browser import Browser
from pyppeteer.network_manager import Request

from adapter.base_adapter import BaseCrawler
from adapter.utils import async_timeit, clean_html, parse_meta
from logger import logger
from models import CrawlerResult, CrawlerRequest


class PyppeteerCrawler(BaseCrawler):
    adapter = "Pyppeteer"

    def __init__(self, browser_count: int = 1, page_count: int = 10, timeout: int = 5000,
                 headless: bool = True, executable_path: Optional[str] = None) -> None:
        super().__init__()
        self._context_list: List[Tuple[Browser, Semaphore]] = []
        self._index = 0

        self.timeout = timeout
        self.headless = headless
        self.browser_count = browser_count
        self.page_count = page_count
        self.executable_path = executable_path

    async def close(self):
        if len(self._context_list) > 0:
            for browser, _ in self._context_list:
                await browser.close()

    async def create_browser(self) -> None:
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
            await self.create_browser()

        browser, semaphore = self._context_list[self._index % self.browser_count]
        self._index += 1
        async with semaphore:
            page = await browser.newPage()
            try:
                await page.evaluateOnNewDocument('()=>{Object.defineProperties(navigator,{webdriver:{get:()=>false}});')
                # 开启请求拦截
                await page.setRequestInterception(True)
                page.on('request', lambda req: asyncio.ensure_future(self._intercept(req)))
                page.on("dialog", lambda x: asyncio.ensure_future(self._close_dialog(x)))

                wait_util = "domcontentloaded" if not item.xhr else "networkidle2"
                await page.goto(item.url, timeout=self.timeout, waitUntil=wait_util)

                title = await page.title()
                content = await page.content()
                html = clean_html(content, item.clean)

                _, keywords, description = parse_meta(html)

                return CrawlerResult(url=item.url, title=title, keywords=keywords, html=html,
                                     description=description, adapter=self.adapter)
            except ConnectionError as e:
                if page is not None:
                    await page.close()

                await self.create_browser()
                return await self.crawl(item)
            except Exception as e:
                logger.error(f"Crawl error with [{__name__}] adapter: {e}")
                return CrawlerResult(url=item.url, success=False, reason=str(e), adapter=self.adapter)
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
