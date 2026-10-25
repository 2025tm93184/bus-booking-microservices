# Bus Booking Microservices

## 1. Project Overview

This project implements a bus seat booking system using four independently runnable microservices. Each service has its own database and communicates with other services through REST APIs over HTTP.

The Booking Service coordinates the booking workflow by reserving a seat, processing a payment, and recording a notification.

## 2. Technology Stack

- Python 3.13
- FastAPI
- Uvicorn
- PostgreSQL
- SQLAlchemy
- Pydantic
- HTTPX
- Pytest

## 3. Architecture

| Service | Port | Responsibility | Database |
|---|---:|---|---|
| Booking Service | 8001 | Coordinates bookings and manages idempotency records | `bus_booking_db` |
| Seat Service | 8002 | Manages trips, seat availability, and reservations | `bus_seat_db` |
| Payment Service | 8003 | Records mock payments | `bus_payment_db` |
| Notification Service | 8004 | Records simulated booking notifications | `bus_notification_db` |

Each service owns its database. Services communicate through REST APIs rather than accessing another service's database directly.

## 4. Prerequisites

Install the following before running the project:

- Python 3.13 or a compatible Python version
- PostgreSQL installed on Windows
- Git, if cloning the repository

## 5. Database Setup

Create these four PostgreSQL databases:

- `bus_booking_db`
- `bus_seat_db`
- `bus_payment_db`
- `bus_notification_db`

Configure a separate database user and password for each service. Grant each user access only to its own database.

Set the `DATABASE_URL` environment variable separately in each service's terminal, using that service's own credentials.

Example format:

`postgresql+psycopg://USERNAME:PASSWORD@localhost:5432/DATABASE_NAME`

Replace the placeholders with the actual credentials and database name. Do not commit real passwords to the repository.

## 6. Python Environment Setup

Open PowerShell in the project root.

Create and activate a virtual environment if one does not already exist:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install the dependencies using the requirements file:

```powershell
python -m pip install -r services/booking/requirements.txt
```

All four services currently use the same dependencies. Install the shared requirements once in the project's virtual environment.

If the dependencies change, update the requirements files accordingly.

## 7. Environment Variables

Each service requires its own `DATABASE_URL`.

The Booking Service also supports these configuration variables:

| Variable | Purpose | Default |
|---|---|---|
| `SEAT_SERVICE_URL` | Seat Service base URL | `http://127.0.0.1:8002` |
| `PAYMENT_SERVICE_URL` | Payment Service base URL | `http://127.0.0.1:8003` |
| `NOTIFICATION_SERVICE_URL` | Notification Service base URL | `http://127.0.0.1:8004` |
| `SERVICE_TIMEOUT_SECONDS` | Downstream request timeout | `2.0` |

The service port is supplied through the `PORT` environment variable when launching Uvicorn.

## 8. Running the Services

Run each service in a separate PowerShell terminal from the project root. Activate the virtual environment and set that service's `DATABASE_URL` before starting it.

### Booking Service

```powershell
$env:PORT = "8001"
# Set DATABASE_URL to the Booking database connection string.
python -m uvicorn app.main:app --reload --port $env:PORT --app-dir services/booking
```

### Seat Service

```powershell
$env:PORT = "8002"
# Set DATABASE_URL to the Seat database connection string.
python -m uvicorn app.main:app --reload --port $env:PORT --app-dir services/seat
```

### Payment Service

```powershell
$env:PORT = "8003"
# Set DATABASE_URL to the Payment database connection string.
python -m uvicorn app.main:app --reload --port $env:PORT --app-dir services/payment
```

### Notification Service

```powershell
$env:PORT = "8004"
# Set DATABASE_URL to the Notification database connection string.
python -m uvicorn app.main:app --reload --port $env:PORT --app-dir services/notification
```

Replace each comment with the appropriate `$env:DATABASE_URL = "..."` command before starting the service. Use that service's own database credentials.

## 9. Health Checks and API Documentation

| Service | Health endpoint | Swagger UI |
|---|---|---|
| Booking | `http://127.0.0.1:8001/health` | `http://127.0.0.1:8001/docs` |
| Seat | `http://127.0.0.1:8002/health` | `http://127.0.0.1:8002/docs` |
| Payment | `http://127.0.0.1:8003/health` | `http://127.0.0.1:8003/docs` |
| Notification | `http://127.0.0.1:8004/health` | `http://127.0.0.1:8004/docs` |

Each health endpoint should return a healthy status when its service is running.

## 10. Testing

The project includes scripts for testing seat-capacity concurrency and simultaneous booking idempotency.

Run the seat concurrency test:

```powershell
python scripts\test_concurrency.py
```

Run the concurrent idempotency test:

```powershell
python scripts\test_idempotency_concurrent.py
```

The concurrency test checks that a trip with five available seats accepts exactly five reservations from twenty concurrent requests. The idempotency test checks that simultaneous requests with the same key and payload return the same booking result.

Validation tests are maintained in each service's `tests` directory. Run them from the relevant service context using the project's test setup.

### Validation Tests

Run the validation tests from the project root. Because each service has its own `app` package, run the tests separately from the corresponding service directory.

**Booking Service:**

```powershell
cd services/booking
python -m pytest tests/test_booking_validation.py -v
```

**Seat Service:**

```powershell
cd ../seat
python -m pytest tests/test_seat_validation.py -v
```

**Payment Service:**

```powershell
cd ../payment
python -m pytest tests/test_payment_validation.py -v
```

**Notification Service:**

```powershell
cd ../notification
python -m pytest tests/test_notification_validation.py -v
```

Each validation suite contains four tests. Run each suite separately to avoid import conflicts between the services' similarly named Python packages.

## 11. Evidence

The `evidence` directory contains screenshots and supporting files for the implemented tests and engineering challenges.

- `evidence/automated-tests/`
- `evidence/challenge-1-concurrency/`
- `evidence/challenge-2-idempotency/`
- `evidence/challenge-3a-resilience/`

Review the evidence files and their README descriptions, where present, to understand which requirement each item demonstrates.

## 12. Limitations

Payments and notifications are simulated for this assignment. The system is intended to demonstrate microservice decomposition, independent data ownership, REST communication, validation, idempotency, concurrency control, and resilience rather than production payment processing.