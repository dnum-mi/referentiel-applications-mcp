from __future__ import annotations

import os
from urllib.parse import urlparse

import httpx
import yaml
from fastmcp import FastMCP
from fastmcp.server.dependencies import get_http_headers

DEFAULT_SWAGGER_URL = "http://host.docker.internal:3000/openapi/swagger.yaml"
REFAPP_API_TOKEN_HEADER = "x-refapp-token"


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


_OPENAPI_OPERATION_KEYS = {"get", "put", "post", "delete", "options", "head", "patch", "trace"}


def _keep_get_operations_only(spec: dict) -> dict:
    """Ne conserve que les operations GET de chaque path (les autres verbs HTTP sont exclus)."""
    paths = spec.get("paths")
    if not isinstance(paths, dict):
        return spec
    filtered = dict(spec)
    filtered["paths"] = {
        path: {
            key: value
            for key, value in item.items()
            if key.lower() not in _OPENAPI_OPERATION_KEYS or key.lower() == "get"
        }
        for path, item in paths.items()
        if isinstance(item, dict)
    }
    return filtered


REFAPP_ME_PATH = "/api/v2/users/me"


class _TokenAwareClient(httpx.AsyncClient):
    """httpx client that validates then forwards incoming auth context to RefApp."""

    def __init__(self, base_url: str):
        super().__init__(base_url=base_url)
        self._validated_tokens: set[str] = set()

    async def _is_token_valid(self, token: str) -> bool:
        if token in self._validated_tokens:
            return True
        me_url = str(self.base_url).rstrip("/") + REFAPP_ME_PATH
        request = httpx.Request("GET", me_url, headers={REFAPP_API_TOKEN_HEADER: token})
        response = await super().send(request)
        await response.aclose()
        if 200 <= response.status_code < 300:
            self._validated_tokens.add(token)
            return True
        return False

    async def send(self, request: httpx.Request, *args, **kwargs) -> httpx.Response:
        headers = get_http_headers(include={REFAPP_API_TOKEN_HEADER})
        token = headers.get(REFAPP_API_TOKEN_HEADER, "").strip()
        if token:
            if not await self._is_token_valid(token):
                return httpx.Response(
                    401,
                    json={"detail": "Invalid or expired RefApp token"},
                    request=request,
                )
            request.headers[REFAPP_API_TOKEN_HEADER] = token
        return await super().send(request, *args, **kwargs)


_swagger_url = os.getenv("SWAGGER_URL", DEFAULT_SWAGGER_URL)
openapi_spec = _keep_get_operations_only(_load_openapi_spec(_swagger_url))
api_base_url = _default_api_base_url(_swagger_url)

mcp = FastMCP.from_openapi(
    openapi_spec=openapi_spec,
    client=_TokenAwareClient(api_base_url),
    name="refapp-openapi-mcp",
)


if __name__ == "__main__":
    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "9000")),
    )
