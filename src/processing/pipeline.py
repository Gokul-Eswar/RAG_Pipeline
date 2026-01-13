"""Main processing pipeline entry point."""

import logging
import time
import sys
from typing import Optional

from src.infrastructure.messaging.consumer import KafkaEventConsumer
from src.processing.processor import DocumentProcessor
from src.utils.config import Config
from src.utils.logging import setup_logging

# Configure logging
setup_logging()
logger = logging.getLogger(__name__)


class RAGPipeline:
    """Continuous processing pipeline for RAG."""
    
    def __init__(self):
        self.consumer = KafkaEventConsumer()
        self.processor = DocumentProcessor()
        self.running = False

    def start(self, limit: Optional[int] = None):
        """Start the processing loop.
        
        Args:
            limit: Optional maximum number of events to process before exiting.
        """
        self.running = True
        logger.info(f"Starting RAG Pipeline (limit={limit})...")
        
        count = 0
        try:
            # Consumes indefinitely
            for event in self.consumer.consume():
                if not self.running:
                    break
                    
                self._process_event(event)
                count += 1
                
                if limit and count >= limit:
                    logger.info(f"Reached limit of {limit} events. Stopping.")
                    break
                    
        except KeyboardInterrupt:
            logger.info("Pipeline stopped by user")
        except Exception as e:
            logger.error(f"Pipeline crashed: {e}")
        finally:
            self.stop()

    def _process_event(self, event: dict):
        """Process a single event."""
        event_id = event.get("id")
        text = event.get("text")
        metadata = event.get("metadata", {})
        
        if not text:
            logger.warning(f"Skipping event {event_id}: No text content")
            return

        logger.info(f"Processing event {event_id}...")
        
        try:
            result = self.processor.process(
                doc_id=event_id,
                text=text,
                metadata=metadata
            )
            
            if result.get("errors"):
                logger.error(f"Completed with errors: {result['errors']}")
            else:
                logger.info(f"Successfully processed {event_id}")
                
        except Exception as e:
            logger.error(f"Failed to process {event_id}: {e}")

    def stop(self):
        """Stop the pipeline and clean up."""
        self.running = False
        if self.consumer:
            self.consumer.close()
        if self.processor:
            self.processor.close()
        logger.info("Pipeline stopped")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run RAG Pipeline")
    parser.add_argument("--limit", type=int, help="Number of events to process before exiting", default=None)
    args = parser.parse_args()
    
    pipeline = RAGPipeline()
    pipeline.start(limit=args.limit)
