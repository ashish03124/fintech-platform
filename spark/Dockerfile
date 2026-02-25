# spark/Dockerfile
# NOTE: bitnami/spark was removed from Docker Hub — using official Apache image
FROM apache/spark:3.5.0

USER root

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    python3-pip \
    python3-dev \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-setuptools \
    && rm -rf /var/lib/apt/lists/*

# Set Python 3 as default
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3 1

# Install Python dependencies
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt

# Download required JAR files
RUN mkdir -p /opt/spark/jars && \
    cd /opt/spark/jars && \
    wget -q https://repo1.maven.org/maven2/org/apache/spark/spark-sql-kafka-0-10_2.12/3.5.0/spark-sql-kafka-0-10_2.12-3.5.0.jar && \
    wget -q https://repo1.maven.org/maven2/org/apache/kafka/kafka-clients/3.4.0/kafka-clients-3.4.0.jar && \
    wget -q https://repo1.maven.org/maven2/org/apache/spark/spark-avro_2.12/3.5.0/spark-avro_2.12-3.5.0.jar && \
    wget -q https://repo1.maven.org/maven2/org/apache/spark/spark-streaming-kafka-0-10-assembly_2.12/3.5.0/spark-streaming-kafka-0-10-assembly_2.12-3.5.0.jar && \
    wget -q https://repo1.maven.org/maven2/com/databricks/spark-xml_2.12/0.16.0/spark-xml_2.12-0.16.0.jar && \
    wget -q https://repo1.maven.org/maven2/org/mongodb/spark/mongo-spark-connector_2.12/10.1.1/mongo-spark-connector_2.12-10.1.1.jar && \
    wget -q https://repo1.maven.org/maven2/mysql/mysql-connector-java/8.0.33/mysql-connector-java-8.0.33.jar && \
    wget -q https://repo1.maven.org/maven2/com/clickhouse/clickhouse-jdbc/0.4.6/clickhouse-jdbc-0.4.6-all.jar

# Copy Spark configuration (use official image path)
COPY spark-defaults.conf /opt/spark/conf/spark-defaults.conf

# Create directories
RUN mkdir -p /opt/spark-jobs /opt/spark-models /tmp/spark-events /tmp/checkpoints
RUN chmod 777 /tmp/spark-events /tmp/checkpoints

# Copy application code
COPY jobs/ /opt/spark-jobs/
COPY models/ /opt/spark-models/

# Set environment variables (official image keeps Spark at /opt/spark)
ENV SPARK_HOME=/opt/spark
ENV PYTHONPATH=/opt/spark-jobs:$PYTHONPATH
ENV PATH=$SPARK_HOME/bin:$PATH

# Set working directory
WORKDIR /opt/spark-jobs

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s \
    CMD curl -f http://localhost:4040/api/v1/applications || exit 1

# Expose ports
EXPOSE 4040 7077 8080

# Entrypoint script
COPY entrypoint.sh /opt/entrypoint.sh
RUN chmod +x /opt/entrypoint.sh

ENTRYPOINT ["/opt/entrypoint.sh"]