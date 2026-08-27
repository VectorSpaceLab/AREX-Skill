"""Adapted, bounded APOD API Locust profile.

Set APOD_API_HOST or pass Locust's --host. The operator must also provide an
explicit finite users/spawn-rate/run-time; this file does not start a run.
"""

import os

from locust import HttpUser, between, task


class ApodUser(HttpUser):
    host = os.getenv("APOD_API_HOST", "")
    wait_time = between(1, 3)

    @task
    def get_apod(self):
        self.client.get("/v1/apod?date=2023-01-01", name="dated apod")

    @task(3)
    def get_thumbs_apod(self):
        self.client.get(
            "/v1/apod?date=2026-01-01&thumbs=true", name="thumbnail apod"
        )

    @task(5)
    def get_today_apod(self):
        self.client.get("/v1/apod", name="today apod")
