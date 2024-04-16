from enum import Enum
from typing import List

from pydantic import BaseModel, ConfigDict


class CrawlerAdapter(Enum):
    """
    Crawler adapter enum
    """
    REQUEST: str = "request"
    PYPPETEER: str = "pyppeteer"
    PLAYWRIGHT: str = "playwright"


class CrawlerRequest(BaseModel):
    """
    Crawler request model
    """
    model_config = ConfigDict(str_strip_whitespace=True)

    urls: List[str]
    adapters: List[CrawlerAdapter] = [CrawlerAdapter.REQUEST]

    def __init__(self, **data):
        adapters = data.get('adapters', [])
        if len(adapters) == 0:
            data['adapters'] = [CrawlerAdapter.REQUEST]
        super().__init__(**data)


class CrawlerResult(BaseModel):
    """
    Crawler result model
    """
    model_config = ConfigDict(str_strip_whitespace=True)

    url: str
    title: str = ""
    keywords: List[str] = []
    description: str = ""
    html: str = ""
    success: bool = True
    reason: str = ""
    adapter: str = "unknown"
