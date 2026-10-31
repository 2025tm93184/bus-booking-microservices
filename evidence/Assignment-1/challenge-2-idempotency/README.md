# Challenge 2: Idempotent Booking Requests

## Objective

Verify that repeated booking requests using the same `Idempotency-Key` do not create duplicate bookings, and that simultaneous identical requests return the same result.

## Evidence

| File | What it demonstrates |
|---|---|
| `first-request.png` | The initial booking request succeeds and returns booking details. |
| `same-key-same-request.png` | Repeating the same request with the same key returns the saved booking result. |
| `same-key-different-payload.png` | Reusing a key with a different request payload is rejected with HTTP 409. |
| `idempotency-database-record.png` | The stored idempotency record and its completed status for the sequential test. |
| `concurrent-idempotency-test.png` | Two simultaneous requests return HTTP 201 with the same booking ID. |
| `concurrent-idempotency-database.png` | The concurrent test's saved idempotency record in the database. |
| `concurrent-idempotency-bookings.png` | The corresponding booking record in the database. |

## Test Script

The simultaneous-request test is implemented in `scripts/test_idempotency_concurrent.py`.

Run it from the project root:

```powershell id="8s3d2a"
python scripts\test_idempotency_concurrent.py
```

The script uses the same `Idempotency-Key` and request payload for two concurrent requests.

## Expected Result

Both simultaneous requests should return HTTP 201 with the same booking ID. The database should contain one corresponding booking, and the idempotency record should have status `COMPLETED`.

Reusing the same key with a different payload should return HTTP 409.

## Conclusion

The evidence demonstrates sequential replay, rejection of a changed payload, and successful handling of simultaneous identical booking requests.