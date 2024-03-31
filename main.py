import math
import multiprocessing
import re
from contextlib import asynccontextmanager
from typing import List

import uvicorn
from fastapi import FastAPI
from parsel import Selector

from adapter import RequestCrawler, PyppeteerCrawler, PlaywrightCrawler
from models import CrawlerRequest, CrawlerResult


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    for crawler in ENABLE_CRAWLER:
        await crawler.close()


app = FastAPI(lifespan=lifespan,
              openapi_prefix="",
              openapi_url=None,
              docs_url=None,
              redoc_url=None)

core_count = multiprocessing.cpu_count()

playwright_count = math.ceil(core_count * 0.8)

request_crawler = RequestCrawler(timeout=5)
pyppeteer_crawler = PyppeteerCrawler(browser_count=core_count - playwright_count)
playwright_crawler = PlaywrightCrawler(browser_count=playwright_count)

ENABLE_CRAWLER = [
    request_crawler,
    pyppeteer_crawler,
    playwright_crawler
]

verify_keyword_list = ["验证", "verify", "robot", "captcha"]

verify_regex = re.compile('/authenticate/|/security/|/captcha/|/verify/', flags=re.IGNORECASE)

chinese_and_word_regex = re.compile('[\u4e00-\u9fa5]|[a-z-]+', flags=re.IGNORECASE)


def is_verification_page(title: str, html: str) -> bool:
    for verify in verify_keyword_list:
        if verify in title:
            return True
    selector: Selector = Selector(html)
    form_action_or_captcha_image_list: List[str] = selector.xpath('.//form/@action | .//img/@src').getall()
    for form_action_or_captcha_image in form_action_or_captcha_image_list:
        if verify_regex.findall(form_action_or_captcha_image):
            return True

    context = " ".join(selector.xpath('.//body//text()').getall())
    if len(chinese_and_word_regex.findall(context)) < 100:
        return True
    return False


@app.post("/extract")
async def extract(item: CrawlerRequest) -> CrawlerResult:
    request_result = await request_crawler.crawl(item)

    if request_result.success and not is_verification_page(title=request_result.title, html=request_result.html):
        return request_result

    if item.xhr:
        return await pyppeteer_crawler.crawl(item)
    else:
        return await playwright_crawler.crawl(item)


if __name__ == '__main__':
    uvicorn.run(app='main:app', workers=core_count)
