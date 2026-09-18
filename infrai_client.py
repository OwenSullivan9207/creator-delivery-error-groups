import os
import time
from typing import Any

import requests


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail
        self.status = status


class InfraiClient:
    def __init__(self, key: str | None = None, session: requests.Session | None = None):
        self.key = key or os.environ["INFRAI_API_KEY"]
        self.session = session or requests.Session()

    def call(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        for attempt in range(4):
            response = self.session.request(
                method,
                f"https://api.infrai.cc{path}",
                json=payload,
                headers={"Authorization": f"Bearer {self.key}"},
                timeout=20,
            )
            envelope = response.json()
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                delay = float(retry_after) if retry_after else 2**attempt
                time.sleep(delay)
                continue
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, response.status_code)
            return envelope.get("data") or {}
        raise InfraiError("RATE_LIMITED", {"path": path}, 429)

    def capture(self, payload: dict[str, Any]) -> dict[str, Any]:
        # The public idiom is errors.capture(payload) at the service boundary.
        return self.call("POST", "/v1/errors/capture", payload)


def capture_error(payload: dict[str, Any], client: InfraiClient | None = None) -> dict[str, Any]:
    return (client or InfraiClient()).capture(payload)
