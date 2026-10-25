
import logging
import random
import time
import uuid

import httpx

from app.config import (
    SEAT_SERVICE_URL,
    PAYMENT_SERVICE_URL,
    NOTIFICATION_SERVICE_URL,
    SERVICE_TIMEOUT_SECONDS,
)

logger = logging.getLogger("booking_service")


def _post_with_retry(url: str, payload: dict, request_id: str) -> dict:
    """POST to another service with bounded retries for transient failures."""

    max_attempts = 3

    for attempt in range(max_attempts):
        try:
            with httpx.Client(timeout=SERVICE_TIMEOUT_SECONDS) as client:
                response = client.post(
                    url,
                    json=payload,
                    headers={"X-Request-ID": request_id},
                )

            if response.status_code in (400, 404, 409, 422):
                raise ValueError(
                    response.json().get("detail", "Request rejected")
                )

            response.raise_for_status()
            return response.json()

        except ValueError:
            raise

        except (
            httpx.TimeoutException,
            httpx.NetworkError,
            httpx.HTTPStatusError,
        ) as exc:
            if attempt == max_attempts - 1:
                logger.warning(
                    "Service call failed after %s attempts: %s",
                    max_attempts,
                    type(exc).__name__,
                )
                raise RuntimeError(
                    "A downstream service is currently unavailable"
                ) from exc

            delay = 0.2 * (2 ** attempt) + random.uniform(0, 0.1)
            time.sleep(delay)

    raise RuntimeError("Service call failed")


def reserve_seat(trip_id: int, request_id: str | None = None) -> dict:
    return _post_with_retry(
        f"{SEAT_SERVICE_URL}/api/v1/trips/{trip_id}/reservations",
        {},
        request_id or str(uuid.uuid4()),
    )


def process_payment(
    booking_id: int,
    amount: int,
    request_id: str | None = None,
) -> dict:
    return _post_with_retry(
        f"{PAYMENT_SERVICE_URL}/api/v1/payments",
        {"booking_id": booking_id, "amount": amount},
        request_id or str(uuid.uuid4()),
    )


def send_notification(
    booking_id: int,
    recipient: str,
    message: str,
    request_id: str | None = None,
) -> dict:
    return _post_with_retry(
        f"{NOTIFICATION_SERVICE_URL}/api/v1/notifications",
        {
            "booking_id": booking_id,
            "recipient": recipient,
            "message": message,
        },
        request_id or str(uuid.uuid4()),
    )
