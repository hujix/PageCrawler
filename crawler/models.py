from enum import Enum
from typing import Union, List

from pydantic import BaseModel


class CrawlerAdapter(Enum):
    request: str = "request"
    pyppeteer: str = "pyppeteer"
    playwright: str = "playwright"


class CleanNode(BaseModel):
    style: bool = True
    script: bool = False


class CrawlerRequest(BaseModel):
    url: str
    clean: Union[CleanNode] = CleanNode()
    xhr: bool = False


class CrawlerResult(BaseModel):
    url: str
    title: str = ""
    keywords: List[str] = []
    description: str = ""
    html: str = ""
    success: bool = True
    reason: str = ""
    adapter: str = "not found"
