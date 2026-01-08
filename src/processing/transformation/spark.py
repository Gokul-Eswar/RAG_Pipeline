"""Spark data transformation pipeline."""

import logging
from typing import Any, Optional

from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, StructField, StringType, MapType

from src.utils.config import Config

logger = logging.getLogger(__name__)


class SparkTransformer:
    """Spark-based data transformation pipeline.
    
    Responsible for large-scale distributed data processing,
    specifically transforming raw events into structured data for RAG.
    """
    
    def __init__(self, app_name: Optional[str] = None, master: Optional[str] = None):
        """Initialize Spark transformer.
        
        Args:
            app_name: Name of the Spark application
            master: Spark master URL
        """
        self.app_name = app_name or Config.SPARK_APP_NAME
        self.master = master or Config.SPARK_MASTER
        self.spark = self._get_spark_session()
        
    def _get_spark_session(self) -> SparkSession:
        """Create or get an existing SparkSession."""
        try:
            return SparkSession.builder \
                .appName(self.app_name) \
                .master(self.master) \
                .config("spark.sql.streaming.checkpointLocation", "/tmp/spark-checkpoints") \
                .get_or_create()
        except Exception as e:
            logger.error(f"Failed to create Spark session: {e}")
            # Fallback to local if master is not reachable
            logger.info("Falling back to local Spark session")
            return SparkSession.builder \
                .appName(f"{self.app_name}-local") \
                .master("local[*]") \
                .get_or_create()

    def transform(self, df):
        """Apply basic transformations to the DataFrame.
        
        Args:
            df: Input Spark DataFrame
            
        Returns:
            Transformed DataFrame
        """
        # Example transformation: Ensure required fields exist
        if "text" not in df.columns:
            logger.warning("Input DataFrame missing 'text' column")
            
        return df.filter(col("text").isNotNull())

    def read_from_kafka(self, broker: str, topic: str):
        """Read stream from Kafka.
        
        Args:
            broker: Kafka broker address
            topic: Kafka topic to subscribe to
            
        Returns:
            Spark DataFrame (streaming)
        """
        schema = StructType([
            StructField("id", StringType(), True),
            StructField("text", StringType(), True),
            StructField("metadata", MapType(StringType(), StringType()), True)
        ])
        
        return self.spark \
            .readStream \
            .format("kafka") \
            .option("kafka.bootstrap.servers", broker) \
            .option("subscribe", topic) \
            .load() \
            .selectExpr("CAST(value AS STRING)") \
            .select(from_json(col("value"), schema).alias("data")) \
            .select("data.*")

    def stop(self):
        """Stop the SparkSession."""
        if self.spark:
            self.spark.stop()
