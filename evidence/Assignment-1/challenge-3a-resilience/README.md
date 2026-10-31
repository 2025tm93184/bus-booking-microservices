# Challenge 3A: Resilience to Downstream Service Failure

## Objective

Verify that the Booking Service handles an unavailable downstream Seat Service gracefully rather than leaving the client waiting indefinitely.

## Test Setup

The Booking Service was configured temporarily to use an unavailable Seat Service URL:

`http://127.0.0.1:8999`

The Seat Service itself was not running at that address.

## Evidence

| File | What it demonstrates |
|---|---|
| `seat-service-unavailable-503.png` | The booking request receives HTTP 503 when the Seat Service is unavailable. |

## Implementation

The Booking Service uses HTTPX to communicate with downstream services. Its service-client logic includes request timeouts, retries, exponential backoff, and jitter. When the Seat Service remains unavailable, the Booking Service returns an error to the client.

## Expected Result

The booking request should fail gracefully with HTTP 503 when the Seat Service cannot be reached. The service should remain available to answer health checks after the correct configuration is restored.

## Test Procedure

1. Temporarily configure `SEAT_SERVICE_URL` to point to an unavailable address.
2. Restart the Booking Service.
3. Submit a booking request.
4. Confirm the HTTP 503 response.
5. Restore the Seat Service URL to `http://127.0.0.1:8002`.
6. Restart the Booking Service and confirm that it is healthy.

## Conclusion

The evidence demonstrates graceful handling of an unavailable downstream service. The retry and timeout configuration is implemented in the Booking Service client logic.