import pytest
from pyspark.sql import SparkSession
from src.processing.transformation.spark import SparkTransformer

@pytest.fixture(scope="module")
def spark_session():
    """Fixture for creating a local Spark session for testing."""
    spark = SparkSession.builder \
        .master("local[*]") \
        .appName("TestSparkTransformer") \
        .get_or_create()
    yield spark
    spark.stop()

def test_spark_transformer_init():
    """Test SparkTransformer initialization."""
    transformer = SparkTransformer(app_name="TestApp", master="local[*]")
    assert transformer.app_name == "TestApp"
    assert transformer.master == "local[*]