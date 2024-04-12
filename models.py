from pydantic import BaseModel

from crawler.models import CrawlerResult


class ResponseData(BaseModel):
    """
    Response data model
    """
    time: float
    msg: str
    data: CrawlerResult
