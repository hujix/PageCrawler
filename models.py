from pydantic import BaseModel

from crawler.models import CrawlerResult


class ResponseData(BaseModel):
    time: float
    msg: str
    data: CrawlerResult
