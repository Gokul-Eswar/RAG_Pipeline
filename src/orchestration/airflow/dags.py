"""Airflow DAGs for RAG Pipeline."""

from datetime import timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago

from src.processing.pipeline import RAGPipeline

# Default arguments for DAGs
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email': ['admin@example.com'],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

def run_rag_batch():
    """Run the RAG pipeline in batch mode (process 100 items)."""
    pipeline = RAGPipeline()
    # Process up to 100 events then exit
    pipeline.start(limit=100)

with DAG(
    'rag_ingestion_pipeline',
    default_args=default_args,
    description='RAG Ingestion and Processing Pipeline',
    schedule_interval=timedelta(minutes=15),  # Run every 15 minutes
    start_date=days_ago(1),
    tags=['rag', 'ingestion'],
    catchup=False,
) as dag:

    # Task 1: Check System Health (Placeholder)
    check_health = BashOperator(
        task_id='check_api_health',
        bash_command='curl -f http://api:8000/health || exit 1',
    )

    # Task 2: Run Processing Pipeline (Python)
    # This runs the pipeline inside the Airflow worker
    process_events = PythonOperator(
        task_id='process_events_batch',
        python_callable=run_rag_batch,
    )

    # Task 3: Transformation (Spark Placeholder)
    # In a real setup, this might submit a Spark job
    spark_transform = BashOperator(
        task_id='spark_transform_job',
        bash_command='echo "Submitting Spark job..." && sleep 5',
    )

    check_health >> process_events >> spark_transform