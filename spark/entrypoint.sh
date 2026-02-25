#!/bin/bash
# spark/entrypoint.sh
#!/bin/bash

set -e

echo "Starting Spark ${SPARK_MODE}..."

# Set Spark master URL
export SPARK_MASTER_URL="spark://${SPARK_MASTER}:7077"

# Configure Spark based on mode
if [ "$SPARK_MODE" = "master" ]; then
    echo "Starting Spark Master..."
    /opt/bitnami/spark/bin/spark-class org.apache.spark.deploy.master.Master \
        --host $SPARK_MASTER_HOST \
        --port $SPARK_MASTER_PORT \
        --webui-port $SPARK_MASTER_WEBUI_PORT
elif [ "$SPARK_MODE" = "worker" ]; then
    echo "Starting Spark Worker..."
    /opt/bitnami/spark/bin/spark-class org.apache.spark.deploy.worker.Worker \
        $SPARK_MASTER_URL \
        --cores $SPARK_WORKER_CORES \
        --memory $SPARK_WORKER_MEMORY \
        --webui-port $SPARK_WORKER_WEBUI_PORT
else
    echo "Starting Spark in client mode..."
    # Submit a job or start a shell
    if [ -f "/opt/spark-jobs/submit-job.sh" ]; then
        /opt/spark-jobs/submit-job.sh
    else
        echo "No job specified, starting Spark shell..."
        /opt/bitnami/spark/bin/pyspark
    fi
fi