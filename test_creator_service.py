import pytest

from creator_service import DeliveryRequest, deliver_asset


class RecordingClient:
    def __init__(self):
        self.payloads = []

    def capture(self, payload):
        self.payloads.append(payload)
        return {"event_id": "evt-1"}


def test_processing_failure_is_captured_with_business_group():
    client = RecordingClient()
    request = DeliveryRequest("c1", "s1", "a1", "newsletter")

    def reject(_):
        raise ValueError("render queue rejected content")

    with pytest.raises(ValueError):
        deliver_asset(request, reject, client)

    payload = client.payloads[0]
    assert payload["fingerprint"] == ["creator-delivery", "newsletter"]
    assert payload["context"]["subscriber_id"] == "s1"
    assert "ValueError" in payload["exception"]
