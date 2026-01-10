import sys
import pytest

# Skip this entire test module on Python 3.13 due to PySpark incompatibility
# PySpark 4.1.0 has issues with socketserver.UnixStreamServer which was removed in Python 3.13
if sys.version_info >= (3, 13):
    pytest.skip(
        "PySpark 4.1.0 is not compatible with Python 3.13+",
        allow_module_level=True
    )

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
    assert transformer.master == "local[*]"