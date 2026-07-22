from hoophub.crawler.client import SportsReferenceClient
import pandas as pd
from requests import Response
from typing import Any, Callable

from hoophub.crawler.rate_limit import wait_for_rate_limit

_client = SportsReferenceClient()
DEFAULT_PAGE_LIMIT = 15


def fetch_raw_response(
    url: str,
    raise_for_status: bool = True,
    page_limit: int = DEFAULT_PAGE_LIMIT,
    progress_writer: Callable[[str], None] | None = None,
) -> Response:
    wait_for_rate_limit(page_limit, progress_writer=progress_writer)
    return _client.get_raw_response(url, raise_for_status=raise_for_status)

def fetch_raw_response_parts(
    url: str,
    raise_for_status: bool = True,
    include : str | list[str] = "all",
    page_limit: int = DEFAULT_PAGE_LIMIT,
    progress_writer: Callable[[str], None] | None = None,
) -> Response | dict[str, Any]:
    wait_for_rate_limit(page_limit, progress_writer=progress_writer)
    return _client.get_raw_response_parts(url, raise_for_status=raise_for_status, include=include)
        
def fetch_response_text(
    url: str,
    page_limit: int = DEFAULT_PAGE_LIMIT,
    progress_writer: Callable[[str], None] | None = None,
) -> str:
    wait_for_rate_limit(page_limit, progress_writer=progress_writer)
    return _client.get_reponse_text(url)

def fetch_response_content(
    url: str,
    page_limit: int = DEFAULT_PAGE_LIMIT,
    progress_writer: Callable[[str], None] | None = None,
) -> bytes:
    wait_for_rate_limit(page_limit, progress_writer=progress_writer)
    return _client.get_response_content(url)

def fetch_response_status_code(
    url: str,
    raise_for_status: bool = False,
    page_limit: int = DEFAULT_PAGE_LIMIT,
    progress_writer: Callable[[str], None] | None = None,
) -> int:
    wait_for_rate_limit(page_limit, progress_writer=progress_writer)
    return _client.get_response_status_code(url, raise_for_status=raise_for_status)

def read_html(
    url: str,
    page_limit: int = DEFAULT_PAGE_LIMIT,
    progress_writer: Callable[[str], None] | None = None,
    **kwargs,
):
    html = fetch_response_text(url, page_limit=page_limit, progress_writer=progress_writer)
    return pd.read_html(html, **kwargs)
