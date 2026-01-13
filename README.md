# Amrutam Telemedicine Backend

## Executive Summary
This is the backend system for Amrutam's telemedicine platform, implementing a production-grade solution with a focus on **scalability, reliability, security**, and **observability**. The system is deployed on a single EC2 instance using Docker Compose with horizontal scalability in mind.

## Features Implemented

- **User Lifecycle**: Registration, login, refresh, logout, profile creation/update.
- **Role-Based Access Control (RBAC)**: Roles for patient, doctor, and admin, enforced via middleware.
- **Doctor Availability**: Slot management, slot locking, overlap prevention, and release upon failure.
- **Booking Flow**: Idempotent booking with ACID transaction guarantees.
- **Payment Flow**: Using the Saga pattern for asynchronous payments and ensuring idempotency.
- **Consultation Lifecycle**: One prescription per booking, encrypted medical data, access control.
- **Search & Filtering**: Doctor search by name, specialization with pagination and caching.
- **Audit Logging**: Complete compliance with immutable logs for all critical events.
- **Admin Analytics**: Revenue, consultation count, doctor utilization metrics.

## Infrastructure

- **EC2 Instance** running Docker Compose with:
  - API (FastAPI)
  - PostgreSQL
  - Redis
- **Cloud-Ready Design**: Easily deployable to ECS/GKE, RDS, ElastiCache with no code changes.

## Data Model

Key tables:
- `users`
- `profiles`
- `doctors`
- `availability_slots`
- `bookings`
- `payments`
- `prescriptions`
- `audit_logs`

## Authentication & Authorization

- **Passwords** hashed using bcrypt.
- **JWT Tokens** with short-lived access and long-lived refresh tokens.
- **RBAC**: Enforced for admin and doctor-only routes.

## Key Features

### 1. **Doctor Availability System**
- Doctors create availability slots.
- Overlap prevention and immutable booked slots.
- Slot release on booking/payment failure.

### 2. **Booking Flow**
- Idempotent booking creation with concurrency protection (`SELECT FOR UPDATE`).
- Transaction safety and audit logging.

### 3. **Payment & Saga Pattern**
- **Asynchronous Payment Handling** using webhooks for success/failure.
- Payment success updates booking state, failure releases slots.
- Webhook idempotency and full audit trail.

### 4. **Consultation & Clinical Data**
- Prescriptions encrypted with symmetric Fernet encryption.
- Immutable prescriptions after creation.
- Access restricted to patient and doctor only.

### 5. **Search & Filtering**
- Doctor search by name and specialization.
- Read-heavy endpoints cached using Redis.
- Query performance optimized with pagination and indexing.

### 6. **Admin Analytics**
- Admin-only access to revenue, consultation counts, and doctor utilization stats.
- Data aggregation directly via SQL for performance.

### 7. **Audit Logging**
- Immutable, append-only logs for critical actions (bookings, payments, prescriptions).
- Logged events include `PRESCRIPTION_VIEWED`, `PAYMENT_SUCCESS`, etc.

## Testing & CI/CD

- **Unit & Integration Tests** using `pytest`.
- **Load Testing** with Locust (500 concurrent users).
- **CI Pipeline** with linting, tests, and security scans.
- **Metrics**: p95 latency for reads and writes, error rates, rate limiter behavior.

## Security & Hardening

- **Rate Limiting** on login endpoints.
- **CORS** restrictions for frontend APIs.
- **OWASP Top 10** mitigations implemented.
- **Secrets Management** using environment variables, no secrets in code.

## Known Limitations

- Single-node EC2 deployment.
- No managed DB yet (PostgreSQL running on EC2).
- Metrics not exported to Prometheus.
- MFA is documented but not implemented.

## Demo Instructions

1. **Start the API** by running the Docker Compose setup on EC2.
2. **Navigate to FastAPI Docs** at `/docs` on the deployed API.
3. **Demonstrate the following:**
   - Login
   - Book a slot (with idempotency protection)
   - Payment saga
   - View audit logs
