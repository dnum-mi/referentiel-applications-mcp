from __future__ import annotations

import os
from urllib.parse import urlparse

import httpx
import yaml
from fastmcp import FastMCP
from fastmcp.server.dependencies import get_access_token, get_http_headers

DEFAULT_SWAGGER_URL = "http://host.docker.internal:3000/openapi/swagger.yaml"


def _default_api_base_url(swagger_url: str) -> str:
    parsed = urlparse(swagger_url)
    if not parsed.scheme or not parsed.netloc:
        raise ValueError("SWAGGER_URL must be an absolute URL")
    return f"{parsed.scheme}://{parsed.netloc}"


def _load_openapi_spec(swagger_url: str) -> dict:
    response = httpx.get(swagger_url, timeout=30.0)
    response.raise_for_status()
    text = response.text
    try:
        return response.json()
    except ValueError:
        loaded = yaml.safe_load(text)
        if not isinstance(loaded, dict):
            raise ValueError("OpenAPI content must be a JSON/YAML object")
        return loaded


class _TokenAwareClient(httpx.AsyncClient):
    """httpx client that injects the current Bearer token before sending."""

    def __init__(self, base_url: str):
        super().__init__(base_url=base_url)

    @staticmethod
    def _resolve_bearer_token() -> str | None:
        access_token = get_access_token()
        if access_token and access_token.token:
            return access_token.token

        headers = get_http_headers(include={"authorization"})
        auth_header = headers.get("authorization", "")
        if auth_header.lower().startswith("bearer "):
            return auth_header.split(" ", 1)[1].strip() or None
        return None

    async def send(self, request: httpx.Request, *args, **kwargs) -> httpx.Response:
        token = self._resolve_bearer_token()
        if token and "Authorization" not in request.headers:
            request.headers["Authorization"] = f"Bearer {token}"
        return await super().send(request, *args, **kwargs)


_swagger_url = os.getenv("SWAGGER_URL", DEFAULT_SWAGGER_URL)
openapi_spec = _load_openapi_spec(_swagger_url)
api_base_url = _default_api_base_url(_swagger_url)

mcp = FastMCP.from_openapi(
    openapi_spec=openapi_spec,
    client=_TokenAwareClient(api_base_url),
    name="refapp-openapi-mcp",
)


if __name__ == "__main__":
    mcp.run(
        transport="http",
        host=os.getenv("MCP_HOST", "127.0.0.1"),
        port=int(os.getenv("MCP_PORT", "9000")),
    )
