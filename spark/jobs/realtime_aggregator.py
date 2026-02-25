# spark/jobs/realtime_aggregator.py
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
from pyspark.sql.window import Window
import json

class RealtimeAggregator:
    def __init__(self, spark_session):
        self.spark = spark_session
        
    def process_transaction_stream(self, kafka_bootstrap_servers, topic):
        """Process real-time transaction stream"""
        
        # Read from Kafka
        df = self.spark.readStream \
            .format("kafka") \
            .option("kafka.bootstrap.servers", kafka_bootstrap_servers) \
            .option("subscribe", topic) \
            .option("startingOffsets", "latest") \
            .option("failOnDataLoss", "false") \
            .load()
        
        # Parse JSON
        schema = StructType([
            StructField("transaction_id", StringType()),
            StructField("user_id", StringType()),
            StructField("amount", DoubleType()),
            StructField("currency", StringType()),
            StructField("merchant", StringType()),
            StructField("category", StringType()),
            StructField("timestamp", LongType()),
            StructField("location", StringType()),
            StructField("device_id", StringType()),
            StructField("ip_address", StringType()),
            StructField("status", StringType())
        ])
        
        transactions = df.select(
            from_json(col("value").cast("string"), schema).alias("data")
        ).select("data.*")
        
        # Add processing timestamp
        processed = transactions.withColumn(
            "processing_time", current_timestamp()
        )
        
        # Multiple aggregation windows
        aggregations = self._create_aggregations(processed)
        
        # Write to multiple sinks
        query = self._write_aggregations(aggregations)
        
        return query
    
    def _create_aggregations(self, df):
        """Create multiple aggregation windows"""
        
        # 1-minute tumbling window
        one_min_agg = df \
            .withWatermark("timestamp", "5 minutes") \
            .groupBy(
                window(col("timestamp"), "1 minute"),
                col("user_id")
            ) \
            .agg(
                count("*").alias("transaction_count_1min"),
                sum("amount").alias("total_amount_1min"),
                avg("amount").alias("avg_amount_1min"),
                collect_list(struct("amount", "merchant", "category")).alias("recent_transactions")
            )
        
        # 5-minute sliding window (every minute)
        five_min_agg = df \
            .withWatermark("timestamp", "10 minutes") \
            .groupBy(
                window(col("timestamp"), "5 minutes", "1 minute"),
                col("user_id"),
                col("category")
            ) \
            .agg(
                count("*").alias("transaction_count_5min"),
                sum("amount").alias("total_amount_5min"),
                avg("amount").alias("avg_amount_5min"),
                stddev("amount").alias("std_amount_5min")
            )
        
        # Hourly aggregation with state
        hourly_agg = df \
            .withWatermark("timestamp", "2 hours") \
            .groupBy(
                window(col("timestamp"), "1 hour"),
                col("user_id")
            ) \
            .agg(
                count("*").alias("transaction_count_hourly"),
                sum("amount").alias("total_amount_hourly"),
                approx_count_distinct("merchant").alias("unique_merchants"),
                approx_count_distinct("category").alias("unique_categories"),
                collect_set("device_id").alias("devices_used"),
                sum(when(col("category") == "FOOD", col("amount")).otherwise(0))
                    .alias("food_spending"),
                sum(when(col("category") == "SHOPPING", col("amount")).otherwise(0))
                    .alias("shopping_spending"),
                sum(when(col("category") == "ENTERTAINMENT", col("amount")).otherwise(0))
                    .alias("entertainment_spending")
            )
        
        # Session-based aggregation (transactions within 30 minutes of inactivity)
        session_window = Window.partitionBy("user_id") \
            .orderBy(col("timestamp").cast("long")) \
            .rangeBetween(-1800, 0)  # 30 minutes in seconds
        
        session_agg = df \
            .withColumn("session_id",
                       sum(when(col("timestamp").cast("long") - 
                               lag("timestamp", 1).over(Window.partitionBy("user_id")
                               .orderBy("timestamp")).cast("long") > 1800, 1)
                           .otherwise(0))
                       .over(Window.partitionBy("user_id").orderBy("timestamp"))) \
            .groupBy("user_id", "session_id") \
            .agg(
                count("*").alias("session_transaction_count"),
                sum("amount").alias("session_total_amount"),
                min("timestamp").alias("session_start"),
                max("timestamp").alias("session_end"),
                collect_list(struct("amount", "merchant", "category", "timestamp"))
                    .alias("session_transactions")
            )
        
        return {
            "one_minute": one_min_agg,
            "five_minute": five_min_agg,
            "hourly": hourly_agg,
            "session": session_agg
        }
    
    def _write_aggregations(self, aggregations):
        """Write aggregations to various sinks"""
        
        queries = []
        
        # Write to ClickHouse
        for agg_name, agg_df in aggregations.items():
            if agg_name == "hourly":
                query = agg_df.writeStream \
                    .foreachBatch(self._write_to_clickhouse) \
                    .outputMode("update") \
                    .trigger(processingTime="5 minutes") \
                    .start()
                queries.append(query)
        
        # Write to Kafka for downstream consumption
        for agg_name, agg_df in aggregations.items():
            if agg_name in ["one_minute", "five_minute"]:
                kafka_df = agg_df.select(
                    to_json(struct("*")).alias("value")
                )
                
                query = kafka_df.writeStream \
                    .format("kafka") \
                    .option("kafka.bootstrap.servers", "kafka:29092") \
                    .option("topic", f"aggregations_{agg_name}") \
                    .option("checkpointLocation", f"/tmp/checkpoints/{agg_name}") \
                    .outputMode("update") \
                    .trigger(processingTime="1 minute") \
                    .start()
                queries.append(query)
        
        # Write to console for debugging (remove in production)
        debug_query = aggregations["one_minute"].writeStream \
            .outputMode("update") \
            .format("console") \
            .option("truncate", False) \
            .trigger(processingTime="30 seconds") \
            .start()
        queries.append(debug_query)
        
        return queries
    
    def _write_to_clickhouse(self, batch_df, batch_id):
        """Write batch to ClickHouse"""
        
        # Convert to Pandas for easier handling
        pandas_df = batch_df.toPandas()
        
        if not pandas_df.empty:
            # Write to ClickHouse
            # This is simplified - in production, use proper ClickHouse connector
            print(f"Writing batch {batch_id} with {len(pandas_df)} rows to ClickHouse")
            
            # Example: Write to CSV and load (production would use JDBC)
            pandas_df.to_csv(f"/tmp/clickhouse_batch_{batch_id}.csv", index=False)
    
    def calculate_user_metrics(self, transactions_df):
        """Calculate comprehensive user metrics"""
        
        # Time-based metrics
        time_metrics = transactions_df \
            .withColumn("hour", hour(col("timestamp"))) \
            .withColumn("day_of_week", dayofweek(col("timestamp"))) \
            .groupBy("user_id") \
            .agg(
                # Spending patterns
                avg("amount").alias("avg_transaction_amount"),
                stddev("amount").alias("std_transaction_amount"),
                
                # Time patterns
                avg("hour").alias("avg_transaction_hour"),
                collect_set("day_of_week").alias("active_days"),
                
                # Merchant patterns
                approx_count_distinct("merchant").alias("total_unique_merchants"),
                approx_count_distinct("category").alias("total_unique_categories"),
                
                # Location patterns (simplified)
                approx_count_distinct("location").alias("total_unique_locations"),
                
                # Device patterns
                approx_count_distinct("device_id").alias("total_devices_used")
            )
        
        # Category spending distribution
        category_metrics = transactions_df \
            .groupBy("user_id", "category") \
            .agg(
                sum("amount").alias("category_total"),
                count("*").alias("category_count")
            ) \
            .groupBy("user_id") \
            .pivot("category") \
            .agg(
                first("category_total").alias("total"),
                first("category_count").alias("count")
            )
        
        # Velocity metrics (spending over time)
        window_1h = Window.partitionBy("user_id") \
            .orderBy(col("timestamp").cast("long")) \
            .rangeBetween(-3600, 0)
        
        window_24h = Window.partitionBy("user_id") \
            .orderBy(col("timestamp").cast("long")) \
            .rangeBetween(-86400, 0)
        
        velocity_metrics = transactions_df \
            .withColumn("hourly_spending", sum("amount").over(window_1h)) \
            .withColumn("daily_spending", sum("amount").over(window_24h)) \
            .groupBy("user_id") \
            .agg(
                max("hourly_spending").alias("max_hourly_spending"),
                avg("hourly_spending").alias("avg_hourly_spending"),
                max("daily_spending").alias("max_daily_spending"),
                avg("daily_spending").alias("avg_daily_spending"),
                stddev("hourly_spending").alias("std_hourly_spending"),
                stddev("daily_spending").alias("std_daily_spending")
            )
        
        # Join all metrics
        user_metrics = time_metrics \
            .join(category_metrics, "user_id", "left") \
            .join(velocity_metrics, "user_id", "left") \
            .withColumn("calculated_at", current_timestamp())
        
        return user_metrics
    
    def generate_recommendations(self, user_metrics_df):
        """Generate recommendations based on user metrics"""
        
        recommendations = user_metrics_df \
            .withColumn("recommendations", 
                       array(
                           # Budgeting recommendation
                           when(col("avg_daily_spending") > 1000,
                                lit("Consider setting a daily spending limit"))
                           .otherwise(lit("Your spending patterns look healthy")),
                           
                           # Category recommendation
                           when(col("FOOD_total") / col("total_spending") > 0.4,
                                lit("High food spending. Consider meal planning"))
                           .otherwise(lit("")),
                           
                           # Time recommendation
                           when(col("avg_transaction_hour") > 22,
                                lit("Late night spending detected. Consider setting limits"))
                           .otherwise(lit("")),
                           
                           # Device recommendation
                           when(col("total_devices_used") > 3,
                                lit("Multiple devices used. Ensure all are secure"))
                           .otherwise(lit(""))
                       )) \
            .withColumn("recommendations", 
                       expr("filter(recommendations, x -> x != '')")) \
            .select(
                "user_id",
                "recommendations",
                col("calculated_at").alias("generated_at")
            )
        
        return recommendations