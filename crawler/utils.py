import time
from typing import Tuple, List

from parsel import Selector

from logger import logger


def async_timeit(func):
    """
    A decorator that runs the function asynchronously and returns the result.
    """

    async def wrapper(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)
        execution_time = time.time() - start_time
        logger.info(f"CrawlerAdapter [{func.__qualname__}:{args[1].url}] executed in {execution_time:.2f}s.")
        return result

    return wrapper


def parse_meta(html: str) -> Tuple[str, List[str], str]:
    """
    Parse meta tags from HTML and extract relevant information.
    """
    selector: Selector = Selector(text=html)
    title = selector.css("title::text").get()
    if title is None:
        title = ""

    keywords_str = selector.xpath('.//head/meta[@name="keywords"]/@content').get()
    if keywords_str is None:
        keywords = []
    else:
        keywords = [_.strip() for _ in keywords_str.split(",") if len(_.strip()) > 0]

    description = selector.xpath('.//head/meta[@name="description"]/@content').get()
    if description is None:
        description = ""

    return title.strip(), keywords, description.strip()
