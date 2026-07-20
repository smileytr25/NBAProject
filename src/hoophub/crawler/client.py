import requests
from typing import Any 
from requests import Response 

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
}

class SportsReferenceClient:
    def __init__(self, timeout: int = 20):
        self.timeout = timeout

        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)

    def get_raw_response(self, url: str, raise_for_status: bool = True):
        response = self.session.get(url, timeout=self.timeout)
        if raise_for_status:
            response.raise_for_status()
        return response

    def get_reponse_text(self, url: str) -> str:
        response = self.get_raw_response(url)
        return response.text
    
    def get_response_content(self, url: str) -> bytes:
        response = self.get_raw_response(url)
        return response.content
    
    def get_response_status_code(self, url: str, raise_for_status: bool = False) -> int:
        response = self.get_raw_response(url, raise_for_status=raise_for_status)
        return response.status_code

    def get_raw_response_parts(self, url: str, raise_for_status: bool = True, include : str | list[str] = "all") -> Response | dict[str, Any]:
        response = self.session.get(url, timeout=self.timeout)
        if raise_for_status:
            response.raise_for_status()

        if include == "all":
            return response 
        
        else:
            include_dict = {attr : getattr(response, attr) for attr in include}
            return include_dict 