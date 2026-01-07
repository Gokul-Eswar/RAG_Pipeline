"""Ingestion package."""

from .producer import EventProducer, publish_event

__all__ = ["EventProducer", "publish_event"]
