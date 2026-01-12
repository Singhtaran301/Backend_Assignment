import uuid
from locust import HttpUser, task, between

class TelemedicineUser(HttpUser):
    wait_time = between(1, 3) 
    token = None

    def on_start(self):
        """Login to get a valid token."""
        response = self.client.post("/auth/login", json={
            "email": "patient@gmail.com", # Using your valid patient
            "password": "password123"
        }, headers={"Idempotency-Key": f"load-login-{uuid.uuid4()}"})
        
        if response.status_code == 200:
            self.token = response.json()["access_token"]

    @task(3)
    def search_doctors(self):
        """READ: Search for doctors (Heavy Read)"""
        if self.token:
            self.client.get("/doctors?query=John", headers={
                "Authorization": f"Bearer {self.token}"
            })

    @task(1)
    def create_booking(self):
        """WRITE: Attempt to book a slot (Heavy Write)"""
        # We use a random UUID. API will check DB and return 404.
        # This stresses the DB connection and validation logic.
        if self.token:
            self.client.post("/bookings", json={
                "slot_id": str(uuid.uuid4())
            }, headers={
                "Authorization": f"Bearer {self.token}",
                "Idempotency-Key": f"load-book-{uuid.uuid4()}"
            })