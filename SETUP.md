# Amrutam Telemedicine Backend - Setup Guide

This guide will walk you through setting up the Amrutam Telemedicine Backend project on your local machine from scratch. Follow each step carefully to get a fully working environment for development and testing.

## Prerequisites

Before starting, ensure you have the following installed on your computer:

- **Git**: For cloning the repository.
  - Download from [https://git-scm.com/](https://git-scm.com/).
- **Docker**: For running the application in containers.
  - Download from [https://www.docker.com/](https://www.docker.com/).
- **Docker Compose**: Usually included with Docker Desktop.
  - Verify with `docker-compose --version`.

If you're on Windows, use PowerShell or Command Prompt. On macOS/Linux, use Terminal.

## Step 1: Clone the Repository

1. Open your terminal (Command Prompt, PowerShell, or Terminal).
2. Navigate to a folder where you want to store the project (e.g., `cd Desktop`).
3. Run the following command to clone the repository:

   ```
   git clone https://github.com/Singhtaran301/Backend_Assignment.git
   ```

4. Change into the project directory:

   ```
   cd Backend_Assignment
   ```

## Step 2: Set Up Environment Variables

1. The project uses a `.env` file for configuration. Create a `.env` file in the root folder (`Backend_Assignment/.env`) with the following variables. Set your own values:

   ```
   # Database Connection
   DATABASE_URL=postgresql+asyncpg://postgres:your_password@amrutam_db:5432/amrutam
   # Replace 'your_password' with a secure password for PostgreSQL.

   # Environment Mode
   ENVIRONMENT=development
   # Set to 'production' when deploying.

   # Security Keys
   SECRET_KEY=your_unique_secret_key_here
   # Generate a random string (e.g., 32 characters) for JWT signing. Never share this!

   ALGORITHM=HS256
   # JWT algorithm (leave as is).

   # Token Expiration Times
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   REFRESH_TOKEN_EXPIRE_DAYS=7
   ```

   **Notes:**
   - `DATABASE_URL`: Points to the PostgreSQL container. The password must match the one in `infra/docker-compose.yml` (default is `password`).
   - `SECRET_KEY`: Use a strong, random key (e.g., generate online or use `openssl rand -hex 32`).
   - Do not commit `.env` to Git—it's already in `.gitignore`.

## Step 3: Build and Start the Application

1. Navigate to the `infra` folder (where Docker Compose files are):

   ```
   cd infra
   ```

2. Build and start all services (API, Database, Redis). This may take 5-10 minutes the first time:

   ```
   docker-compose up --build
   ```

   - `--build` ensures images are built from scratch.
   - You'll see logs from PostgreSQL, Redis, and the API.

3. Wait for the services to fully start. Look for messages like:
   - "database system is ready to accept connections"
   - "INFO:     Uvicorn running on http://0.0.0.0:8000"

   The API will be available at `http://localhost:8000`.

## Step 4: Verify the Setup

1. Open a web browser and go to `http://localhost:8000/health`.
   - You should see: `{"status": "active"}`

2. Check the API documentation at `http://localhost:8000/docs`.
   - This is an interactive Swagger UI for testing endpoints.

3. (Optional) Check container status:

   ```
   docker-compose ps
   ```

   You should see `amrutam_api`, `amrutam_db`, and `amrutam_redis` running.

## Step 5: Create an Admin User

To access admin features, create an admin user:

1. In a new terminal window (keep the Docker containers running), run:

   ```
   docker exec -it amrutam_api python src/scripts/create_admin.py
   ```

2. Follow the prompts:
   - Enter email (e.g., `admin@example.com`)
   - Enter password (e.g., `securepassword123`)

3. You'll see a success message. Note the credentials for login.

## Step 6: Test All Endpoints

Use the Swagger UI at `http://localhost:8000/docs` to test endpoints. Here's a step-by-step guide to test the full flow:

### 6.1 Authentication
1. **Register a Patient:**
   - Go to `POST /auth/register`.
   - Body: `{"email": "patient@example.com", "password": "password123", "full_name": "John Doe", "phone_number": "1234567890", "role": "patient"}`
   - Execute. Note the response.

2. **Login as Patient:**
   - Go to `POST /auth/login`.
   - Body: `{"email": "patient@example.com", "password": "password123"}`
   - Execute. Copy the `access_token` from response.

3. **Authorize Requests:**
   - Click "Authorize" at the top, paste: `Bearer <access_token>`.

4. **Register/Login as Doctor:**
   - Repeat registration with `role: "doctor"`.
   - Login and get doctor token.

5. **Login as Admin:**
   - Use the admin credentials from Step 5.

### 6.2 Doctor Availability
1. **Create Slots (as Doctor):**
   - Use doctor token.
   - Go to `POST /availability/slots`.
   - Body: `{"start_time": "2026-01-15T10:00:00Z", "end_time": "2026-01-15T11:00:00Z"}`
   - Execute.

2. **List Slots:**
   - `GET /availability/slots` (as patient or doctor).

### 6.3 Bookings
1. **Book a Slot (as Patient):**
   - Use patient token.
   - Go to `POST /bookings`.
   - Header: `Idempotency-Key: unique-key-123`
   - Body: `{"slot_id": "<slot_id_from_above>"}`
   - Execute. Note the `booking_id`.

2. **Check Booking Status:**
   - `GET /bookings/{booking_id}`.

### 6.4 Payments
1. **Initiate Payment:**
   - `POST /payments/initiate`.
   - Body: `{"booking_id": "<booking_id>", "amount": 100}`

2. **Simulate Webhook (Success):**
   - `POST /payments/webhook`.
   - Header: `x-signature: valid_secret_key`
   - Body: `{"transaction_id": "<transaction_id_from_initiate>", "status": "SUCCESS"}`

3. **Check Booking Status:** Should now be "CONFIRMED".

### 6.5 Consultations & Prescriptions
1. **Create Prescription (as Doctor):**
   - Use doctor token.
   - `POST /consultations/prescription`.
   - Body: `{"booking_id": "<booking_id>", "content": "Take medicine twice daily."}`

2. **View Prescription (as Patient):**
   - Use patient token.
   - `GET /consultations/prescription/{booking_id}`.

### 6.6 Admin Analytics
1. **View Metrics (as Admin):**
   - Use admin token.
   - `GET /admin/analytics`.

### 6.7 Search & Other
- **Search Doctors:** `GET /doctors/search?name=Dr`.
- **Profile Updates:** `PUT /auth/profile`.
- **Logout:** `POST /auth/logout`.

## Step 7: Development Workflow

- **Stop Services:** Press `Ctrl+C` in the terminal running `docker-compose up`.
- **Restart:** Run `docker-compose up` (no `--build` needed unless code changes).
- **View Logs:** Run `docker-compose logs -f api` for real-time API logs.
- **Database Access:** Connect to PostgreSQL with:
  ```
  docker exec -it amrutam_db psql -U postgres -d amrutam
  ```
- **Make Changes:** Edit code in `src/`, then restart containers.
- **Run Tests:** `docker exec -it amrutam_api pytest`.
- **Metrics:** Visit `http://localhost:8000/metrics`.

## Troubleshooting

- **Port Conflicts:** If port 8000/5432/6379 is in use, stop other apps or change ports in `docker-compose.yml`.
- **Build Fails:** Ensure Docker has enough resources (RAM/CPU). Try `docker system prune` to clean up.
- **Database Issues:** If migrations fail, check logs with `docker-compose logs db`.
- **Permission Errors:** On Windows, run terminal as Administrator.
- **Slow Startup:** First run takes time due to building images.
- **Endpoint Errors:** Ensure correct tokens and data. Check logs for details.

## What's Included

- **API:** FastAPI with authentication, bookings, payments, consultations, admin analytics.
- **Database:** PostgreSQL with Alembic migrations.
- **Caching/Rate Limiting:** Redis.
- **Monitoring:** Prometheus metrics, request logging.
- **Background Jobs:** Automatic cleanup of stale bookings.
- **Testing:** Pytest setup for unit/integration tests.

## Next Steps

- Read the main `README.md` for project architecture and features.
- Explore the code in `src/`.
- For production, deploy to cloud (e.g., AWS ECS) with managed services.

If you encounter issues, check the logs or open an issue on GitHub.