from locust import HttpUser, task, between
import os
import time
import uuid

AUTH_URL = os.getenv("AUTH_URL", "https://auth-service-adaezel-dev.apps.rm2.thpm.p1.openshiftapps.com")
USERNAME = os.getenv("LOCUST_USER", "adaezel")
PASSWORD = os.getenv("LOCUST_PASS", "adaezel")

MAX_CREATES_PER_USER = int(os.getenv("MAX_CREATES_PER_USER", "3"))

class TaskUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        r = self.client.post(
            f"{AUTH_URL}/login",
            json={"username": USERNAME, "password": PASSWORD},
            name="/login (auth)"
        )
        if r.status_code != 200:
            
            r.failure(f"Login failed: {r.status_code} {r.text}")
            self.stop(True)
            return

        token = r.json()["access_token"]
        self.client.headers.update({"Authorization": f"Bearer {token}"})

        self.created = 0

    @task(6)
    def health(self):
        self.client.get("/healthz")

    @task(10)
    def list_tasks(self):
        self.client.get("/tasks")

    @task(1)
    def create_task_limited(self):
        # DB şişmesin diye kullanıcı başına limit
        if self.created >= MAX_CREATES_PER_USER:
            return

        payload = {
            "title": f"Locust-{uuid.uuid4().hex[:8]}",
            "description": "performance test",
            "status": "todo"
        }
        r = self.client.post("/tasks", json=payload)
        if r.status_code in (200, 201):
            self.created += 1
