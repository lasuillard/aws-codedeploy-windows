import json as json_
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

from selenium.webdriver import Remote
from structlog import BoundLogger, get_logger

logger: BoundLogger = get_logger(__name__)

_FETCH_JS = (Path(__file__).parent / "fetch.js").read_text()


class FetchResponse:
    """Fetch response object."""

    def __init__(self, *, headers: dict[str, str], text: str) -> None:
        """
        Initialize FetchResponse.

        Args:
            headers: Response headers.
            text: Response text.

        """
        self.headers = headers
        self.text = text

    def json(self) -> Any:
        """Parse response text as JSON."""
        return json_.loads(self.text)


def fetch(
    webdriver: Remote,
    *,
    method: str = "GET",
    url: str,
    params: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
    body: Any = None,
    data: Any = None,
    json: Any = None,
    encoding: str = "utf-8",
) -> FetchResponse:
    """
    Invoke HTTP request using browser built-in fetch API.

    Args:
        webdriver: Remote webdriver instance.
        method: HTTP method. Defaults to `"GET"`.
        url: URL to request.
        params: Query params.
        headers: Request headers.
        body: Request body.
        data: Request form data.
        json: Request JSON data.
        encoding: Encoding to use for decoding response.

    Returns:
        Response object.

    """
    logger.debug("Invoking web request via browser fetch API (%s %s)", method, url)
    if params:
        query = urlencode(params)
        url = f"{url}?{query}"

    if headers and json:
        headers.setdefault("Content-Type", "application/json")

    raw_response: dict[str, Any] = webdriver.execute_async_script(
        _FETCH_JS,
        method,
        url,
        headers or {},
        body,
        data,
        json,
        encoding,
    )
    return FetchResponse(headers=raw_response["headers"], text=raw_response["text"])
