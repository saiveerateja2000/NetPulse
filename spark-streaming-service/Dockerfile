FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends default-jre-headless && rm -rf /var/lib/apt/lists/*
ENV JAVA_HOME=/usr/lib/jvm/default-java
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Pre-download Spark JARs at build time so the service starts without needing Maven Central at runtime
RUN python -c "\
from pyspark.sql import SparkSession; \
spark = SparkSession.builder.master('local[1]') \
    .config('spark.jars.packages', 'org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.3,org.postgresql:postgresql:42.7.4') \
    .getOrCreate(); \
spark.stop() \
"
COPY app ./app
CMD ["python", "app/main.py"]
