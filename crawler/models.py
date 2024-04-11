from enum import Enum
from typing import List

from pydantic import BaseModel


class CrawlerAdapter(Enum):
    request: str = "request"
    pyppeteer: str = "pyppeteer"
    playwright: str = "playwright"


class CrawlerRequest(BaseModel):
    url: str
    adapters: List[CrawlerAdapter] = [CrawlerAdapter.request]


class CrawlerResult(BaseModel):
    url: str
    title: str = ""
    keywords: List[str] = []
    description: str = ""
    html: str = ""
    success: bool = True
    reason: str = ""
    adapter: str = "unknown"
