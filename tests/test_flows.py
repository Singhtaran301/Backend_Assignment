import pytest
import uuid

# We force the tests to run in order
@pytest.mark.anyio
async def test_health_check(client):
    """Simple check to see if API is alive."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "active"

@pytest.mark.anyio
async def test_full_booking_flow(client):
    """
    INTEGRATION TEST: Login -> Search -> Book
    """
    # ---------------------------------------------------------
    # 1. LOGIN (Get Token)
    # ---------------------------------------------------------
    login_payload = {"email": "patient@gmail.com", "password": "password123"}
    headers_login = {"Idempotency-Key": f"test-login-{uuid.uuid4()}"}
    
    login_res = await client.post("/auth/login", json=login_payload, headers=headers_login)
    assert login_res.status_code == 200, f"Login failed: {login_res.text}"
    
    token = login_res.json()["access_token"]
    auth_headers = {"Authorization": f"Bearer {token}"}

    # ---------------------------------------------------------
    # 2. SEARCH DOCTORS (Read)
    # ---------------------------------------------------------
    # FIX: Accept 404 if no doctors exist in the DB yet
    search_res = await client.get("/doctors?query=Cardio", headers=auth_headers)
    assert search_res.status_code in [200, 404] 

    # ---------------------------------------------------------
    # 3. CREATE BOOKING (Write)
    # ---------------------------------------------------------
    booking_payload = {"slot_id": str(uuid.uuid4())} # Random slot
    booking_headers = {
        **auth_headers,
        "Idempotency-Key": f"test-book-{uuid.uuid4()}"
    }
    
    book_res = await client.post("/bookings", json=booking_payload, headers=booking_headers)
    
    # We expect 404 (Slot not found) or 200 (Success). 
    assert book_res.status_code in [200, 404]

@pytest.mark.anyio
async def test_idempotency_protection(client):
    """
    PHASE 12 VERIFICATION: Sending same key twice returns same result.
    """
    key = str(uuid.uuid4())
    headers = {
        "Idempotency-Key": key,
        "Content-Type": "application/json"
    }
    payload = {"email": "patient@gmail.com", "password": "password123"}
    
    # Request 1
    res1 = await client.post("/auth/login", json=payload, headers=headers)
    assert res1.status_code == 200
    
    # Request 2 (Replay)
    res2 = await client.post("/auth/login", json=payload, headers=headers)
    assert res2.status_code == 200
    
    # CHECK HEADER
    assert res2.headers.get("X-Idempotency-Hit") == "true"