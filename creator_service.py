from dataclasses import dataclass
import traceback
from typing import Callable

from infrai_client import InfraiClient


@dataclass(frozen=True)
class DeliveryRequest:
    creator_id: str
    subscriber_id: str
    asset_id: str
    content_kind: str


def deliver_asset(request: DeliveryRequest, processor: Callable[[DeliveryRequest], str], client: InfraiClient) -> str:
    """Process one paid delivery and group failures by workflow and asset kind."""
    try:
        return processor(request)
    except Exception as exc:
        client.capture({
            "title": "creator delivery failed",
            "message": f"{type(exc).__name__}: {exc}",
            "level": "error",
            "fingerprint": ["creator-delivery", request.content_kind],
            "exception": traceback.format_exc(),
            "context": {
                "creator_id": request.creator_id,
                "subscriber_id": request.subscriber_id,
                "asset_id": request.asset_id,
                "content_kind": request.content_kind,
            },
        })
        raise


def process_update(request: DeliveryRequest, processor: Callable[[DeliveryRequest], str], client: InfraiClient) -> dict[str, str]:
    result = deliver_asset(request, processor, client)
    return {"subscriber_id": request.subscriber_id, "asset_id": request.asset_id, "status": result}


if __name__ == "__main__":
    request = DeliveryRequest("creator-17", "subscriber-42", "asset-9", "video")
    print(process_update(request, lambda _: "delivered", InfraiClient()))
