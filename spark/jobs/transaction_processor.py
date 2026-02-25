# spark/jobs/transaction_processor.py
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
from pyspark.sql.window import Window
import json

class TransactionProcessor:
    def __init__(self):
        self.spark = SparkSession.builder \
            .appName("RealTimeTransactionProcessor") \
            .config("spark.sql.streaming.checkpointLocation", "/tmp/checkpoints/transactions") \
            .config("spark.jars.packages", 
                   "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,"
                   "org.apache.spark:spark-avro_2.12:3.5.0") \
            .getOrCreate()
        
        # Define Avro schema for transactions
        self.transaction_schema = """
            {
                "type": "record",
                "name": "Transaction",
                "fields": [
                    {"name": "transaction_id", "type": "string"},
                    {"name": "user_id", "type": "string"},
                    {"name": "amount", "type": "double"},
                    {"name": "currency", "type": "string"},
                    {"name": "merchant", "type": ["null", "string"]},
                    {"name": "category", "type": {"type": "enum", "name": "Category", 
                                                  "symbols": ["FOOD", "TRANSPORT", "SHOPPING", 
                                                             "BILLS", "ENTERTAINMENT", "OTHER"]}},
                    {"name": "timestamp", "type": {"type": "long", "logicalType": "timestamp-millis"}},
                    {"name": "location", "type": ["null", "string"]},
                    {"name": "device_id", "type": ["null", "string"]},
                    {"name": "ip_address", "type": ["null", "string"]},
                    {"name": "status", "type": {"type": "enum", "name": "Status", 
                                               "symbols": ["PENDING", "COMPLETED", "FAILED", "FRAUD"]}}
                ]
            }
        """
    
    def create_transaction_stream(self):
        """Create streaming DataFrame from Kafka"""
        df = self.spark.readStream \
            .format("kafka") \
            .option("kafka.bootstrap.servers", "kafka:29092") \
            .option("subscribe", "transactions") \
            .option("startingOffsets", "latest") \
            .option("failOnDataLoss", "false") \
            .load()
        
        # Decode Avro data
        transactions = df.select(
            from_avro(col("value"), self.transaction_schema).alias("transaction")
        ).select("transaction.*")
        
        return transactions
    
    def process_transactions(self):
        """Main processing pipeline"""
        transactions = self.create_transaction_stream()
        
        # Add processing timestamp
        processed = transactions.withColumn(
            "processing_timestamp", current_timestamp()
        )
        
        # Real-time aggregations with watermark
        windowed_agg = processed \
            .withWatermark("timestamp", "10 minutes") \
            .groupBy(
                window(col("timestamp"), "5 minutes", "1 minute"),
                col("user_id"),
                col("category")
            ) \
            .agg(
                count("*").alias("transaction_count"),
                sum("amount").alias("total_amount"),
                avg("amount").alias("avg_amount"),
                stddev("amount").alias("std_amount"),
                collect_list(struct("transaction_id", "amount", "merchant")).alias("recent_transactions")
            ) \
            .withColumn("window_start", col("window.start")) \
            .withColumn("window_end", col("window.end")) \
            .drop("window")
        
        # Calculate spending velocity
        spending_velocity = windowed_agg \
            .withColumn("spending_velocity", 
                       col("total_amount") / 5)  # per minute
        
        # Write to multiple sinks
        query = spending_velocity.writeStream \
            .foreachBatch(self.write_to_sinks) \
            .outputMode("update") \
            .trigger(processingTime="1 minute") \
            .start()
        
        return query
    
    def write_to_sinks(self, batch_df, batch_id):
        """Write batch to multiple sinks"""
        
        # 1. Write to ClickHouse for analytics
        batch_df.write \
            .format("jdbc") \
            .option("url", "jdbc:clickhouse://clickhouse:8123/fintech") \
            .option("dbtable", "user_spending_aggregates") \
            .option("driver", "com.clickhouse.jdbc.ClickHouseDriver") \
            .mode("append") \
            .save()
        
        # 2. Write to Kafka for downstream consumers
        kafka_output = batch_df.select(
            to_json(struct("*")).alias("value")
        )
        
        kafka_output.write \
            .format("kafka") \
            .option("kafka.bootstrap.servers", "kafka:29092") \
            .option("topic", "user_aggregations") \
            .save()
        
        # 3. Write high-velocity alerts
        high_velocity = batch_df.filter(col("spending_velocity") > 1000)
        if high_velocity.count() > 0:
            alerts = high_velocity.select(
                lit("HIGH_SPENDING_VELOCITY").alias("alert_type"),
                col("user_id"),
                col("spending_velocity"),
                current_timestamp().alias("alert_time")
            )
            
            alerts.select(to_json(struct("*")).alias("value")) \
                .write \
                .format("kafka") \
                .option("kafka.bootstrap.servers", "kafka:29092") \
                .option("topic", "alerts") \
                .save()
        
        print(f"Batch {batch_id} processed. Records: {batch_df.count()}")

if __name__ == "__main__":
    processor = TransactionProcessor()
    query = processor.process_transactions()
    query.awaitTermination()