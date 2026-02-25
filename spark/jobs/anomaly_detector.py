# spark/jobs/anomaly_detector.py
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
from pyspark.sql.window import Window
from pyspark.ml.feature import VectorAssembler, StandardScaler
from pyspark.ml.clustering import KMeans
from pyspark.ml.evaluation import ClusteringEvaluator
import numpy as np
import json

class AnomalyDetector:
    def __init__(self, spark_session):
        self.spark = spark_session
        self.model_path = "/models/anomaly_detection"
        
    def detect_transaction_anomalies(self, transactions_df):
        """Detect anomalous transactions"""
        
        # Feature engineering
        features_df = self._create_features(transactions_df)
        
        # Train or load model
        model = self._get_anomaly_model(features_df)
        
        # Make predictions
        predictions = model.transform(features_df)
        
        # Extract anomalies
        anomalies = predictions.filter(col("prediction") == 1) \
            .select(
                "transaction_id",
                "user_id",
                "amount",
                "merchant",
                "category",
                "timestamp",
                col("features").alias("anomaly_features"),
                col("cluster").alias("anomaly_type"),
                current_timestamp().alias("detected_at")
            )
        
        return anomalies
    
    def _create_features(self, df):
        """Create features for anomaly detection"""
        
        # Basic features
        features = df.withColumn("hour", hour(col("timestamp"))) \
                    .withColumn("day_of_week", dayofweek(col("timestamp"))) \
                    .withColumn("is_weekend", when(col("day_of_week").isin([1, 7]), 1).otherwise(0)) \
                    .withColumn("is_night", when((col("hour") >= 22) | (col("hour") <= 6), 1).otherwise(0))
        
        # User behavior features using window functions
        user_window = Window.partitionBy("user_id").orderBy("timestamp")
        time_window = Window.partitionBy("user_id") \
                          .orderBy(col("timestamp").cast("long")) \
                          .rangeBetween(-3600, 0)  # 1 hour window
        
        features = features \
            .withColumn("amount_zscore", 
                       (col("amount") - mean("amount").over(user_window)) / 
                       stddev("amount").over(user_window)) \
            .withColumn("time_since_last", 
                       col("timestamp").cast("long") - 
                       lag("timestamp", 1).over(user_window).cast("long")) \
            .withColumn("transactions_last_hour", 
                       count("*").over(time_window)) \
            .withColumn("avg_amount_last_hour", 
                       avg("amount").over(time_window)) \
            .withColumn("amount_ratio", 
                       col("amount") / col("avg_amount_last_hour"))
        
        # Merchant features
        merchant_window = Window.partitionBy("user_id", "merchant")
        features = features \
            .withColumn("merchant_frequency", 
                       count("*").over(merchant_window)) \
            .withColumn("avg_merchant_amount", 
                       avg("amount").over(merchant_window))
        
        # Fill nulls
        features = features.fillna({
            "time_since_last": 3600,  # 1 hour default
            "amount_zscore": 0,
            "amount_ratio": 1,
            "merchant_frequency": 1,
            "avg_merchant_amount": col("amount")
        })
        
        return features
    
    def _get_anomaly_model(self, features_df):
        """Get anomaly detection model"""
        
        try:
            # Try to load existing model
            from pyspark.ml.clustering import KMeansModel
            model = KMeansModel.load(self.model_path)
            print("Loaded existing anomaly detection model")
            
        except:
            # Train new model
            print("Training new anomaly detection model")
            
            # Prepare features for clustering
            feature_cols = [
                "amount_zscore", 
                "time_since_last",
                "transactions_last_hour",
                "amount_ratio",
                "merchant_frequency"
            ]
            
            # Remove outliers for training
            train_df = features_df.filter(
                (col("amount_zscore").between(-3, 3)) &
                (col("time_since_last") < 86400) &  # < 1 day
                (col("transactions_last_hour") < 100) &
                (col("amount_ratio").between(0.1, 10))
            )
            
            # Assemble features
            assembler = VectorAssembler(inputCols=feature_cols, outputCol="features")
            feature_vectors = assembler.transform(train_df)
            
            # Scale features
            scaler = StandardScaler(
                inputCol="features",
                outputCol="scaled_features",
                withStd=True,
                withMean=True
            )
            scaler_model = scaler.fit(feature_vectors)
            scaled_data = scaler_model.transform(feature_vectors)
            
            # Train KMeans
            kmeans = KMeans(
                k=5,  # 5 clusters for different types of transactions
                seed=42,
                featuresCol="scaled_features",
                predictionCol="cluster"
            )
            model = kmeans.fit(scaled_data)
            
            # Evaluate model
            evaluator = ClusteringEvaluator(
                featuresCol="scaled_features",
                predictionCol="cluster"
            )
            silhouette = evaluator.evaluate(model.transform(scaled_data))
            print(f"Model trained with silhouette score: {silhouette}")
            
            # Save model
            model.save(self.model_path)
            
            # Determine which clusters are anomalous
            clusters = model.transform(scaled_data)
            cluster_stats = clusters.groupBy("cluster").agg(
                count("*").alias("count"),
                avg("amount").alias("avg_amount"),
                stddev("amount").alias("std_amount"),
                avg("amount_zscore").alias("avg_zscore")
            ).collect()
            
            # Identify anomalous clusters (small clusters with high amounts)
            anomalous_clusters = []
            total_count = clusters.count()
            
            for row in cluster_stats:
                cluster_size_pct = row["count"] / total_count
                avg_zscore = abs(row["avg_zscore"])
                
                if cluster_size_pct < 0.05 and avg_zscore > 1.5:
                    anomalous_clusters.append(row["cluster"])
            
            print(f"Anomalous clusters: {anomalous_clusters}")
            
            # Add anomaly prediction
            model.broadcast_anomalous_clusters = anomalous_clusters
        
        return model
    
    def detect_user_behavior_anomalies(self, user_aggregates_df):
        """Detect anomalies in user behavior patterns"""
        
        # Calculate baseline for each user
        user_baseline = user_aggregates_df.groupBy("user_id").agg(
            avg("total_amount").alias("avg_daily_spend"),
            stddev("total_amount").alias("std_daily_spend"),
            avg("transaction_count").alias("avg_daily_transactions"),
            stddev("transaction_count").alias("std_daily_transactions"),
            collect_set("category").alias("common_categories")
        )
        
        # Join with current aggregates
        current_aggregates = user_aggregates_df.filter(
            col("window_end") > current_timestamp() - expr("INTERVAL 1 HOUR")
        )
        
        anomalies = current_aggregates.join(user_baseline, "user_id") \
            .withColumn("spend_zscore", 
                       (col("total_amount") - col("avg_daily_spend")) / 
                       col("std_daily_spend")) \
            .withColumn("transaction_zscore",
                       (col("transaction_count") - col("avg_daily_transactions")) /
                       col("std_daily_transactions")) \
            .withColumn("unusual_category",
                       when(~array_contains(col("common_categories"), col("category")), 1)
                       .otherwise(0)) \
            .filter(
                (col("spend_zscore") > 3) |
                (col("transaction_zscore") > 3) |
                (col("unusual_category") == 1)
            ) \
            .select(
                "user_id",
                "category",
                "total_amount",
                "transaction_count",
                "spend_zscore",
                "transaction_zscore",
                "unusual_category",
                current_timestamp().alias("detected_at")
            )
        
        return anomalies
    
    def generate_anomaly_alerts(self, anomalies_df):
        """Generate alerts from detected anomalies"""
        
        alerts = anomalies_df.withColumn("alert_id", expr("uuid()")) \
            .withColumn("alert_type", 
                       when(col("unusual_category") == 1, "UNUSUAL_CATEGORY")
                       .when(col("spend_zscore") > 5, "HIGH_SPENDING")
                       .when(col("transaction_zscore") > 5, "HIGH_FREQUENCY")
                       .otherwise("SUSPICIOUS_PATTERN")) \
            .withColumn("severity",
                       when(col("spend_zscore") > 5, "HIGH")
                       .when(col("transaction_zscore") > 5, "HIGH")
                       .when(col("unusual_category") == 1, "MEDIUM")
                       .otherwise("LOW")) \
            .withColumn("message",
                       concat(
                           lit("Anomaly detected: "),
                           col("alert_type"),
                           lit(". User: "),
                           col("user_id"),
                           lit(". Details: "),
                           when(col("alert_type") == "HIGH_SPENDING",
                                concat(lit("Spent $"), col("total_amount"), 
                                      lit(" which is "), round(col("spend_zscore"), 1),
                                      lit(" standard deviations above average")))
                           .when(col("alert_type") == "HIGH_FREQUENCY",
                                concat(lit("Made "), col("transaction_count"),
                                      lit(" transactions which is "), 
                                      round(col("transaction_zscore"), 1),
                                      lit(" standard deviations above average")))
                           .when(col("alert_type") == "UNUSUAL_CATEGORY",
                                concat(lit("Transaction in unusual category: "),
                                      col("category")))
                           .otherwise(lit("Suspicious pattern detected"))
                       )) \
            .select(
                "alert_id",
                "user_id",
                "alert_type",
                "severity",
                "message",
                col("total_amount").alias("alert_data_amount"),
                col("transaction_count").alias("alert_data_count"),
                col("category").alias("alert_data_category"),
                current_timestamp().alias("created_at")
            )
        
        return alerts