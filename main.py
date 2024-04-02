import math
import multiprocessing
import re
from typing import List

import uvicorn
from fastapi import FastAPI
from parsel import Selector

from crawler import CrawlerExecutor
from crawler.models import CrawlerResult, CrawlerRequest, CrawlerAdapter
from logger import logger

app = FastAPI(openapi_prefix="",
              openapi_url=None,
              docs_url=None,
              redoc_url=None)

verify_keyword_list = ["验证", "verify", "robot", "captcha"]

verify_regex = re.compile('/authenticate/|/security/|/captcha/|/verify/', flags=re.IGNORECASE)

chinese_and_word_regex = re.compile('[\u4e00-\u9fa5]|[a-z-]+', flags=re.IGNORECASE)


def verify_is_available(title: str, html: str) -> bool:
    if len(title) == 0:
        return False
    for verify in verify_keyword_list:
        if verify in title:
            return False
    selector: Selector = Selector(html)
    form_action_or_captcha_image_list: List[str] = selector.xpath('.//form/@action | .//img/@src').getall()
    for form_action_or_captcha_image in form_action_or_captcha_image_list:
        if verify_regex.findall(form_action_or_captcha_image):
            return False

    context = " ".join(selector.xpath('.//body//text()').getall())
    if len(chinese_and_word_regex.findall(context)) < 100:
        return False
    return True


core_count = multiprocessing.cpu_count()

playwright_count = math.floor(core_count * 0.8)

logger.info(f"Lazy loading : playwright:{playwright_count} pyppeteer:{core_count - playwright_count}")

crawler_executor = CrawlerExecutor()


@app.post("/extract")
async def extract(item: CrawlerRequest) -> CrawlerResult:
    logger.info(f"Received new request : {item.model_dump()}")

    if item.xhr:
        return await crawler_executor.crawl_with_adapter(CrawlerAdapter.pyppeteer, item)

    request_result = await crawler_executor.crawl_with_adapter(CrawlerAdapter.request, item)

    if request_result.success and verify_is_available(title=request_result.title, html=request_result.html):
        return request_result

    return await crawler_executor.crawl_with_adapter(CrawlerAdapter.playwright, item)


if __name__ == '__main__':
    uvicorn.run(app='main:app', host="0.0.0.0", port=8000)
