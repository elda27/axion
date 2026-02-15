"""Low-level HTTP transport shared by all service classes."""

from __future__ import annotations

from typing import Any

import httpx


class AxionHTTPError(Exception):
    """Raised when the Axion API returns an error response."""

    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"HTTP {status_code}: {detail}")


class HttpTransport:
    """Thin wrapper around :class:`httpx.Client` for JSON API calls."""

    def __init__(self, client: httpx.Client) -> None:
        self._client = client

    # ── request helpers ───────────────────────────────────────

    def _check(self, resp: httpx.Response) -> dict[str, Any]:
        if resp.status_code >= 400:
            raise AxionHTTPError(resp.status_code, resp.text)
        return resp.json()

    def _check_no_content(self, resp: httpx.Response) -> None:
        if resp.status_code >= 400:
            raise AxionHTTPError(resp.status_code, resp.text)

    def get(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        resp = self._client.get(path, params=params)
        return self._check(resp)

    def post(
        self,
        path: str,
        *,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        resp = self._client.post(path, json=json)
        return self._check(resp)

    def patch(
        self,
        path: str,
        *,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        resp = self._client.patch(path, json=json)
        return self._check(resp)

    def delete(self, path: str) -> None:
        resp = self._client.delete(path)
        self._check_no_content(resp)
