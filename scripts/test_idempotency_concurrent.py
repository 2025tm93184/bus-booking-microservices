
import concurrent.futures
import threading
import httpx

BASE_URL = "http://127.0.0.1:8001"
TRIP_ID = 6
IDEMPOTENCY_KEY = "concurrent-idempotency-test-002"

payload = {
    "trip_id": TRIP_ID,
    "amount": 50000,
    "recipient": "concurrent-test@example.com",
}

start_event = threading.Event()


def send_booking():
    start_event.wait()

    try:
        response = httpx.post(
            f"{BASE_URL}/api/v1/bookings",
            json=payload,
            headers={"Idempotency-Key": IDEMPOTENCY_KEY},
            timeout=30.0,
        )

        return {
            "status_code": response.status_code,
            "body": response.json(),
        }
    except Exception as exc:
        return {
            "status_code": 0,
            "body": str(exc),
        }


def main():
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        first = executor.submit(send_booking)
        second = executor.submit(send_booking)

        start_event.set()

        results = [first.result(), second.result()]

    for number, result in enumerate(results, start=1):
        print(f"Request {number}: HTTP {result['status_code']}")
        print(result["body"])

    successful = [
        result for result in results
        if result["status_code"] in (200, 201)
        and isinstance(result["body"], dict)
        and "id" in result["body"]
    ]

    if len(successful) == 2:
        booking_ids = [result["body"]["id"] for result in successful]
        if booking_ids[0] == booking_ids[1]:
            print("PASS: both requests returned the same booking ID.")
        else:
            print("FAIL: the requests returned different booking IDs.")
    else:
        print("FAIL: both requests did not return a successful booking result.")


if __name__ == "__main__":
    main()
