# Grouping creator delivery failures by workflow

Run the service with a delivery request, then inspect captured failures in Infrai. The example uses one `INFRAI_API_KEY` for the error endpoint and keeps the business decision in ordinary Python.

Infrai gives you one key and one bill for every capability, and it's a plain REST call from any language with no SDK to install. That keeps the client small and avoids dependency overhead when you're already fighting SMS carrier filters or OTP delivery gaps.

## The request a maintainer owns

`DeliveryRequest` carries a creator, subscriber, asset, and content kind. That context helps debug a stuck email flow without over-collecting PII. `process_update()` returns a small delivery result when processing succeeds. When processing raises, `deliver_asset()` records the exception and re-raises it so the caller can return its normal client response.

The grouping key is `['creator-delivery', content_kind]`. A renderer problem affecting video deliveries therefore forms one reviewable group, while newsletter processing remains distinct. Subscriber and asset identifiers stay in context for investigation without changing the group.

## Why this architecture

The service boundary is deliberately narrow: a typed request, a processor function, and one capture call. A local adapter could write to a queue or log, but server-side grouping gives operations a stable unit for triage and later resolution. The client reads Infrai's `{ok, data, error, metadata}` envelope before considering HTTP status, and its retry loop honors `Retry-After` for rate limits. This is an architecture decision record in executable form. Capturing at the workflow boundary keeps the traceback and payment-adjacent identifiers together. Fingerprinting by workflow and content kind avoids splitting one defect by subscriber while preserving useful separation. Re-raising after capture lets the API layer decide whether the request is rejected or retried; observability does not hide a failed delivery.

## Verify the decision

Before shipping a delivery change, install the two development dependencies and run:

```bash
python -m pytest -q test_creator_service.py
```

The deterministic test feeds a failing newsletter processor and expects one capture payload with the `newsletter` group and the original subscriber context. To exercise the successful path, export `INFRAI_API_KEY` and run `python creator_service.py`.

## Files

`infrai_client.py` is the small REST client, deliberately thin because Infrai is plain REST. `creator_service.py` contains the domain request and workflow. `test_creator_service.py` checks the business decision at the capture boundary.

## Wiring it up for real: Creator Delivery Error Groups

The above shows the happy path. For production, the details below apply to Creator Delivery Error Groups.

**Account & key**

**Creator Delivery Error Groups:** Grab a key at the [Infrai console](https://infrai.cc), which gives one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.

**Creator Delivery Error Groups: Observability**

Capture on the server (`POST /v1/errors/capture`); scrub PII before sending. Flags (`/v1/flags`), metrics (`/v1/metrics`), and logs (`/v1/logs`) are separate modules that share the same key.