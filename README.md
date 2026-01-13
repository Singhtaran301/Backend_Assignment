# Amrutam Telemedicine Backend

## Executive Summary
This repository contains a production-grade backend implementation for Amrutam’s telemedicine platform.  
The system is designed with **correctness under concurrency**, **security**, **idempotency**, and **auditability** as first-class concerns.

The application is currently deployed on a **single AWS EC2 instance using Docker Compose**.  
While not a highly available deployment, the architecture is intentionally **stateless and horizontally scalable**, and production-grade cloud mappings are documented.

---

## Core Features Implemented

### User Lifecycle & Security
- User registration and login
- JWT-based authentication (access + refresh tokens)
- Refresh token rotation and logout revocation
- Role-Based Access Control (patient / doctor / admin)
- Admin bootstrap via internal script (not public API)
- Inactive user blocking
- Audit logging for role and lifecycle changes

### Doctor Availability & Booking
- Doctor-managed availability slots
- Slot overlap prevention
- Slot locking using pessimistic DB locking
- Idempotent booking creation
- ACID transaction guarantees
- Guaranteed prevention of double booking under concurrency

### Payments & Saga Pattern
- Booking lifecycle with explicit states (PENDING, CONFIRMED, CANCELLED)
- Asynchronous payment flow using webhook callbacks
- Saga-style compensation:
  - Payment failure → slot released
  - Timeout → booking cancelled
- Webhook idempotency and replay safety
- Full audit trail for payment events

### Consultations & Clinical Data
- One prescription per booking
- Medical data encrypted at rest (symmetric encryption)
- Prescription immutability enforced at service layer
- Access restricted to patient and assigned doctor
- Prescription creation and access audited

### Search, Filtering & Performance
- Doctor search by name and specialization
- Pagination enforced on all list endpoints
- Read-heavy endpoints cached using Redis
- TTL-based cache invalidation
- SQL joins used to prevent N+1 query issues

### Admin & Analytics
- Admin-only analytics endpoints
- Revenue summary
- Consultation volume
- Doctor utilization metrics
- Aggregations executed at the database level
- No PII exposed

---

## Infrastructure & Deployment

### Current Deployment (Implemented)
- Single AWS EC2 instance
- Docker Compose services:
  - FastAPI application
  - PostgreSQL
  - Redis
- Docker volumes for persistence

This setup is sufficient to validate correctness, concurrency handling, and system behavior, but **does not claim high availability**.

### Cloud Readiness (Documented)
| Component | Current | Production Mapping |
|--------|--------|-------------------|
| API | EC2 + Docker | ECS / GKE |
| Database | Local Postgres | RDS / CloudSQL |
| Cache | Redis container | ElastiCache |
| Secrets | `.env` | Secrets Manager |

Migration requires infrastructure changes only; no application code changes.

---

## Data Model
Core tables:
- users
- profiles
- doctors
- availability_slots
- bookings
- payments
- prescriptions
- audit_logs

Design principles:
- UUID primary keys
- UTC, timezone-aware timestamps
- Foreign key constraints enforced
- High-growth tables identified for partitioning (documented)

---

## Idempotency (Critical)
- Idempotency-Key required for all write operations
- Redis-backed idempotency store
- Duplicate requests return the original response
- 24-hour expiration window
- Applied to bookings, payments, and write-heavy endpoints

---

## Audit Logging
- Append-only audit log table
- Logs written inside the same DB transaction as business actions
- Covers bookings, payments, prescriptions, and automated timeouts
- Admin-only visibility
- Immutable via API

---

## Background Jobs
- Asynchronous cleanup worker
- Cancels stale unpaid bookings
- Releases locked availability slots
- Retry-safe with exponential backoff
- Failures logged for inspection

---

## Security Hardening
- Password hashing using bcrypt
- JWT authentication
- RBAC enforced at middleware
- Rate limiting on login endpoints
- CORS restrictions
- Static security scanning (Bandit)
- No secrets logged or committed

**Note:** MFA, TLS termination, and managed secrets are documented but not implemented due to scope constraints.

---

## Observability
- Structured JSON logs
- Request correlation via request IDs
- Audit logs for sensitive actions
- Load testing used to validate latency and stability

**Metrics Export:** Not integrated with Prometheus; performance validated via load testing instead.

---

## Testing & Validation
- Integration tests for authentication, booking, and idempotency
- End-to-end flow validation
- Concurrency safety tested
- Load testing using Locust:
  - Stress test: 500 concurrent users
  - Stability test: 50 concurrent users

Observed locally (Docker):
- Median read latency: ~4ms
- Median write latency: ~61ms
- p95 read latency: <200ms
- p95 write latency: <500ms
- No 500-level errors observed

> Local load tests validate trends, not production throughput.

---

## Known Limitations
- Single-node EC2 deployment
- No managed database or HA setup
- Metrics not scraped by Prometheus
- MFA documented but not implemented

---

## Demo Instructions
- Access FastAPI documentation at `/docs`
- Demonstrate:
  - Login
  - Booking with Idempotency-Key
  - Payment saga (success/failure)
  - Audit log verification
