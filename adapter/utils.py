import re
import time
from typing import List

from parsel import Selector

from logger import logger
from models import CleanNode


def async_timeit(func):
    """
    耗时统计装饰器
    """

    async def wrapper(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)
        execution_time = time.time() - start_time
        logger.info(f"Function [{func.__qualname__}] executed in {execution_time:.2f}s")
        return result

    return wrapper


def parse_title(html: str) -> str:
    selector: Selector = Selector(text=html)
    title = selector.css("title::text").get()
    if title is None:
        title = ""
    return title.strip()


def parse_keywords(html: str) -> List[str]:
    selector: Selector = Selector(text=html)
    keywords_str = selector.xpath('.//head/meta[@name="keywords"]/@content').get()

    if keywords_str is None:
        return []

    return [_.strip() for _ in keywords_str.split(",") if len(_.strip()) > 0]


def parse_description(html: str) -> str:
    selector: Selector = Selector(text=html)
    description_str = selector.xpath('.//head/meta[@name="description"]/@content').get()

    if description_str is None:
        return ""

    return description_str.strip()


style_regex = re.compile(r"<style.*?>.*?</style>", flags=re.DOTALL)


def clean_style(html: str) -> str:
    return style_regex.sub("", html)


script_regex = re.compile(r"<script.*?>.*?</script>", flags=re.DOTALL)


def clean_script(html: str) -> str:
    return script_regex.sub("", html)


def clean_html(html: str, clean: CleanNode) -> str:
    if clean.style:
        html = clean_style(html)
    if clean.script:
        html = clean_script(html)
    return html
