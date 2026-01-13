"""Spark Batch Job for RAG."""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, window
import os
import sys

def run_job():
    """Run a batch processing job."""
    app_name = "RAG_Batch_Processor"
    master = os.getenv("SPARK_MASTER", "spark://spark-master:7077")
    
    print(f"Starting Spark Job: {app_name} on {master}")
    
    spark = SparkSession.builder \
        .appName(app_name) \
        .master(master) \
        .get_or_create()

    # Create a simple DataFrame (Simulating reading from a batch source like S3/HDFS/DB)
    # In a real scenario, this would read historical events from a data lake
    data = [
        ("event1", "ingest", "2023-10-01 10:00:00"),
        ("event2", "process", "2023-10-01 10:05:00"),
        ("event3", "ingest", "2023-10-01 10:10:00"),
        ("event4", "error", "2023-10-01 10:15:00"),
        ("event5", "ingest", "2023-10-01 10:20:00"),
    ]
    columns = ["id", "type", "timestamp"]
    
    df = spark.createDataFrame(data, columns)
    
    print("Processing Data...")
    
    # Simple Transformation: Count events by type
    result = df.groupBy("type").agg(count("id").alias("count"))
    
    print("Results:")
    result.show()
    
    # Write results (Simulated)
    # result.write.mode("overwrite").parquet("/opt/spark-data/results")
    
    spark.stop()
    print("Job Completed Successfully")

if __name__ == "__main__":
    run_job()
