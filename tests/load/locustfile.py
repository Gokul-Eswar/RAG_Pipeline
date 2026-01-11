"""Locust load test file."""

import random
import os
from locust import HttpUser, task, between


class BigDataRAGUser(HttpUser):
    wait_time = between(1, 3)
    api_key = None
    headers = {}

    def on_start(self):
        """Authenticate on start."""
        self.api_key = os.getenv("TEST_API_KEY", "test-api-key")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    @task(1)
    def health_check(self):
        """Test health endpoint."""
        self.client.get("/health/live")

    @task(5)
    def search_hybrid(self):
        """Test hybrid search (Vector + Graph)."""
        query_data = {
            "query_text": "test query content",
            "limit": 5
        }
        self.client.post("/memory/search/hybrid", json=query_data,
                         headers=self.headers)

    @task(2)
    def ingest_event(self):
        """Test event ingestion."""
        event_data = {
            "id": f"load_test_{random.randint(1, 100000)}",
            "text": f"This is a load test document {random.randint(1, 1000)}",
            "metadata": {
                "source": "locust",
                "timestamp": "2026-01-11T12:00:00Z"
            }
        }
        self.client.post("/ingest/", json=event_data, headers=self.headers)

    @task(3)
    def find_node(self):
        """Test graph node search."""
        search_data = {
            "label": "Document",
            "properties": {"source": "locust"}
        }
        self.client.post("/graph/node/find", json=search_data,
                         headers=self.headers)
