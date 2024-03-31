import asyncio
from asyncio import Semaphore
from typing import Optional

from pyppeteer import launch
from pyppeteer.browser import Browser
from pyppeteer.network_manager import Request

from adapter.base_adapter import BaseCrawler
from adapter.utils import async_timeit, clean_html, parse_keywords, parse_description
from logger import logger
from models import CrawlerResult, CrawlerRequest


class PyppeteerCrawler(BaseCrawler):
    adapter = "Pyppeteer"

    def __init__(self, page_count: int = 10) -> None:
        super().__init__()
        self.browser: Optional[Browser] = None
        self.semaphore: Semaphore = Semaphore(page_count)
        self.index = 0

        self._page_count = page_count

    async def close(self):
        if self.browser is not None:
            await self.browser.close()

    async def create_browser(self) -> None:
        self.browser = await launch(options={
            'headless': False,
            'ignoreHTTPSErrors': True,
            'dumpio': True,
            'autoClose': True,
            'userDataDir': r'C:/Users/Hu.Sir/Documents/PyCharmProjects/PageExtractor/tmp/pyppeteer',
            "args": [
                '--no-sandbox',
                '--window-size=1280,720',
                '--disable-infobars',
                '--disable-features=TranslateUI',
                '--disable-web-security',
                '--disable-popup-blocking'
            ],
            'ignoreDefaultArgs': ['--enable-automation'],
            'defaultViewport': {"width": 1280, "height": 720},
            "executablePath": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
        })

    @async_timeit
    async def crawl(self, item: CrawlerRequest) -> CrawlerResult:
        if self.browser is None:
            await self.create_browser()

        async with self.semaphore:
            page = await self.browser.newPage()
            try:
                await page.evaluateOnNewDocument('()=>{Object.defineProperties(navigator,{webdriver:{get:()=>false}});')
                # 开启请求拦截
                await page.setRequestInterception(True)
                page.on('request', lambda req: asyncio.ensure_future(self._intercept(req)))
                page.on("dialog", lambda x: asyncio.ensure_future(self._close_dialog(x)))

                wait_util = "domcontentloaded" if not item.xhr else "networkidle2"
                await page.goto(item.url, timeout=10000, waitUntil=wait_util)

                title = await page.title()
                content = await page.content()
                html = clean_html(content, item.clean)

                return CrawlerResult(url=item.url, title=title, keywords=parse_keywords(html), html=html,
                                     description=parse_description(html), adapter=self.adapter)
            except ConnectionError as e:
                if page is not None:
                    await page.close()
                if self.browser is not None:
                    await self.close()

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
