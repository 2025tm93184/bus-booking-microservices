
import os

SEAT_SERVICE_URL = os.getenv(
    "SEAT_SERVICE_URL",
    "http://127.0.0.1:8002",
)

PAYMENT_SERVICE_URL = os.getenv(
    "PAYMENT_SERVICE_URL",
    "http://127.0.0.1:8003",
)

NOTIFICATION_SERVICE_URL = os.getenv(
    "NOTIFICATION_SERVICE_URL",
    "http://127.0.0.1:8004",
)

SERVICE_TIMEOUT_SECONDS = float(
    os.getenv("SERVICE_TIMEOUT_SECONDS", "2.0")
)
