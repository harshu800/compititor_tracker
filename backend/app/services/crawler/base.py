from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class FetchResult:
    url: str                  # final URL after redirects
    status_code: Optional[int]
    html: Optional[str]
    error: Optional[str] = None
    truncated: bool = False


class BaseCrawler(ABC):
    @abstractmethod
    async def fetch(self, url: str) -> FetchResult:
        ...
