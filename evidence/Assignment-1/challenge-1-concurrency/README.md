# Challenge 1: Concurrent Seat Reservations

## Objective

Verify that concurrent seat reservation requests cannot exceed a trip's available capacity.

## Test Setup

- Trip ID: 5
- Seat capacity: 5
- Concurrent reservation requests: 20

## Evidence

| File | What it demonstrates |
|---|---|
| `concurrency-test-results.png` | Test output showing the number of successful reservations, capacity rejections, unexpected responses, and the final test result. |
| `concurrency-database-results.png` | Database evidence showing the reservations recorded for Trip ID 5. |

## Expected Result

Exactly 5 requests should succeed, 15 requests should be rejected with HTTP 409, and there should be no unexpected responses.

The database should contain no more than 5 reservations for this trip.

## Test Script

The test is implemented in `scripts/test_concurrency.py`.

Run it from the project root with:

```powershell
python scripts\test_concurrency.py
```

## Conclusion

The recorded test results demonstrate that the service enforces the trip's seat capacity during concurrent reservation requests.