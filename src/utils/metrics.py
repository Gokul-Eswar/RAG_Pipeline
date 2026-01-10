"""Prometheus metrics configuration."""

from prometheus_client import Counter, Histogram

# API Metrics
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"]
)

REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"]
)

# Database Metrics
DB_OPERATION_LATENCY = Histogram(
    "db_operation_duration_seconds",
    "Database operation duration in seconds",
    ["database", "operation"]
)

# Event Metrics
EVENTS_INGESTED = Counter(
    "events_ingested_total",
    "Total events successfully ingested",
    ["topic"]
)
