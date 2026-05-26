import os
import logging

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, to_timestamp
from pyspark.sql.types import DoubleType, IntegerType, StringType, StructField, StructType

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("spark-streaming")

SPARK_EXTRA_JARS = os.getenv(
    "SPARK_EXTRA_JARS",
    ",".join(
        [
            "/opt/spark-jars/spark-sql-kafka-0-10_2.12-3.5.3.jar",
            "/opt/spark-jars/spark-token-provider-kafka-0-10_2.12-3.5.3.jar",
            "/opt/spark-jars/kafka-clients-3.4.1.jar",
            "/opt/spark-jars/commons-pool2-2.11.1.jar",
            "/opt/spark-jars/jsr305-3.0.0.jar",
            "/opt/spark-jars/spark-tags_2.12-3.5.3.jar",
            "/opt/spark-jars/postgresql-42.7.4.jar",
        ]
    ),
)


def write_to_postgres(batch_df, batch_id):
    if batch_df.isEmpty():
        logger.debug(f"Batch {batch_id} is empty, skipping...")
        return

    try:
        logger.info(f"Writing batch {batch_id} with {batch_df.count()} records to PostgreSQL...")
        # Rename 'timestamp' column to 'ts' and cast to TIMESTAMPTZ to match the postgres schema
        batch_df = batch_df.withColumn("ts", to_timestamp(col("timestamp"))).drop("timestamp")

        props = {
            "user": os.getenv("POSTGRES_USER", "netpulse"),
            "password": os.getenv("POSTGRES_PASSWORD", "netpulse"),
            "driver": "org.postgresql.Driver",
        }
        jdbc_url = (
            f"jdbc:postgresql://{os.getenv('POSTGRES_HOST', 'postgres')}:{os.getenv('POSTGRES_PORT', '5432')}"
            f"/{os.getenv('POSTGRES_DB', 'netpulse')}"
        )

        batch_df.write.mode("append").jdbc(url=jdbc_url, table="telemetry_metrics", properties=props)
        logger.info(f"Successfully wrote batch {batch_id} to PostgreSQL")
    except Exception as e:
        logger.error(f"Failed to write batch {batch_id} to PostgreSQL: {e}", exc_info=True)
        raise


def main():
    logger.info("Starting Spark Streaming service...")
    logger.info(f"Kafka Bootstrap Servers: {os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:29092')}")
    logger.info(f"Kafka Topic: {os.getenv('KAFKA_TOPIC', 'netpulse.telemetry')}")
    logger.info(f"PostgreSQL Host: {os.getenv('POSTGRES_HOST', 'postgres')}")
    
    schema = StructType(
        [
            StructField("target", StringType()),
            StructField("latency_ms", DoubleType()),
            StructField("packet_loss", DoubleType()),
            StructField("jitter", DoubleType()),
            StructField("dns_lookup_time", DoubleType()),
            StructField("cpu_usage", DoubleType()),
            StructField("memory_usage", DoubleType()),
            StructField("bandwidth_usage", DoubleType()),
            StructField("active_connections", IntegerType()),
            StructField("traceroute_hops", StringType()),
            StructField("timestamp", StringType()),
        ]
    )

    try:
        logger.info("Creating Spark session...")
        spark = (
            SparkSession.builder.appName("NetPulseStreaming")
            .master("local[1]")
            .config("spark.sql.shuffle.partitions", "1")
            .config("spark.jars", SPARK_EXTRA_JARS)
            .getOrCreate()
        )
        spark.sparkContext.setLogLevel("WARN")
        logger.info("Spark session created successfully")

        logger.info("Connecting to Kafka topic...")
        raw_stream = (
            spark.readStream.format("kafka")
            .option("kafka.bootstrap.servers", os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092"))
            .option("subscribe", os.getenv("KAFKA_TOPIC", "netpulse.telemetry"))
            .option("startingOffsets", "latest")
            .load()
        )
        logger.info("Successfully connected to Kafka")

        parsed = raw_stream.select(from_json(col("value").cast("string"), schema).alias("m")).select("m.*")

        logger.info("Starting streaming query...")
        query = (
            parsed.writeStream.outputMode("append")
            .foreachBatch(write_to_postgres)
            .option("checkpointLocation", "/tmp/netpulse-checkpoint")
            .start()
        )
        
        logger.info("Spark Streaming service is running...")
        query.awaitTermination()
    except Exception as e:
        logger.error(f"Fatal error in Spark Streaming service: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
