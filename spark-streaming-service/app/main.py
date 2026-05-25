import os

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, to_timestamp
from pyspark.sql.types import DoubleType, IntegerType, StringType, StructField, StructType

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
        return

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


def main():
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

    spark = (
        SparkSession.builder.appName("NetPulseStreaming")
        .master("local[1]")
        .config("spark.sql.shuffle.partitions", "1")
        .config("spark.jars", SPARK_EXTRA_JARS)
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")

    raw_stream = (
        spark.readStream.format("kafka")
        .option("kafka.bootstrap.servers", os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"))
        .option("subscribe", os.getenv("KAFKA_TOPIC", "netpulse.telemetry"))
        .option("startingOffsets", "latest")
        .load()
    )

    parsed = raw_stream.select(from_json(col("value").cast("string"), schema).alias("m")).select("m.*")

    query = (
        parsed.writeStream.outputMode("append")
        .foreachBatch(write_to_postgres)
        .option("checkpointLocation", "/tmp/netpulse-checkpoint")
        .start()
    )

    query.awaitTermination()


if __name__ == "__main__":
    main()
