
import concurrent.futures
import threading
import httpx

BASE_URL = "http://127.0.0.1:8002"
TRIP_ID = 5
TOTAL_REQUESTS = 20

start_event = threading.Event()


def reserve_seat(request_number):
    # Make all worker threads begin as close together as possible.
    start_event.wait()

    try:
        response = httpx.post(
            f"{BASE_URL}/api/v1/trips/{TRIP_ID}/reservations",
            json={},
            timeout=15.0,
        )

        return {
            "request": request_number,
            "status_code": response.status_code,
            "body": response.text,
        }
    except httpx.HTTPError as exc:
        return {
            "request": request_number,
            "status_code": 0,
            "body": str(exc),
        }


def main():
    with concurrent.futures.ThreadPoolExecutor(
        max_workers=TOTAL_REQUESTS
    ) as executor:
        futures = [
            executor.submit(reserve_seat, number)
            for number in range(1, TOTAL_REQUESTS + 1)
        ]

        # Release all workers together to create contention.
        start_event.set()
        results = [future.result() for future in futures]

    successes = [r for r in results if r["status_code"] in (200, 201)]
    rejected = [r for r in results if r["status_code"] == 409]
    unexpected = [
        r for r in results
        if r["status_code"] not in (200, 201, 409)
    ]

    print(f"Trip ID: {TRIP_ID}")
    print(f"Total requests: {TOTAL_REQUESTS}")
    print(f"Successful reservations: {len(successes)}")
    print(f"Capacity rejections (409): {len(rejected)}")
    print(f"Unexpected responses: {len(unexpected)}")

    for result in unexpected:
        print("Unexpected:", result)

    if len(successes) == 5 and len(rejected) == 15 and not unexpected:
        print("PASS: exactly 5 seats were reserved.")
    else:
        print("CHECK: results differ from the expected 5 successes and 15 rejections.")


if __name__ == "__main__":
    main()
