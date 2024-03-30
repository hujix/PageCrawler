import re
import time

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
