FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    default-jre-headless \
    ca-certificates \
    ca-certificates-java \
    procps \
    openssl \
    curl \
    && mkdir -p /etc/ssl/certs/java \
    && update-ca-certificates \
    && /var/lib/dpkg/info/ca-certificates-java.postinst configure \
    && rm -rf /var/lib/apt/lists/*
ENV JAVA_HOME=/usr/lib/jvm/default-java
RUN mkdir -p /opt/spark-jars && \
    curl -fsSL -o /opt/spark-jars/spark-sql-kafka-0-10_2.12-3.5.3.jar \
      https://repo1.maven.org/maven2/org/apache/spark/spark-sql-kafka-0-10_2.12/3.5.3/spark-sql-kafka-0-10_2.12-3.5.3.jar && \
    curl -fsSL -o /opt/spark-jars/spark-token-provider-kafka-0-10_2.12-3.5.3.jar \
      https://repo1.maven.org/maven2/org/apache/spark/spark-token-provider-kafka-0-10_2.12/3.5.3/spark-token-provider-kafka-0-10_2.12-3.5.3.jar && \
    curl -fsSL -o /opt/spark-jars/kafka-clients-3.4.1.jar \
      https://repo1.maven.org/maven2/org/apache/kafka/kafka-clients/3.4.1/kafka-clients-3.4.1.jar && \
    curl -fsSL -o /opt/spark-jars/commons-pool2-2.11.1.jar \
      https://repo1.maven.org/maven2/org/apache/commons/commons-pool2/2.11.1/commons-pool2-2.11.1.jar && \
    curl -fsSL -o /opt/spark-jars/jsr305-3.0.0.jar \
      https://repo1.maven.org/maven2/com/google/code/findbugs/jsr305/3.0.0/jsr305-3.0.0.jar && \
    curl -fsSL -o /opt/spark-jars/spark-tags_2.12-3.5.3.jar \
      https://repo1.maven.org/maven2/org/apache/spark/spark-tags_2.12/3.5.3/spark-tags_2.12-3.5.3.jar && \
    curl -fsSL -o /opt/spark-jars/postgresql-42.7.4.jar \
      https://repo1.maven.org/maven2/org/postgresql/postgresql/42.7.4/postgresql-42.7.4.jar
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
CMD ["python", "app/main.py"]
