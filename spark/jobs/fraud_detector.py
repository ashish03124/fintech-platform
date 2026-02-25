# spark/jobs/fraud_detector.py
from pyspark.ml import Pipeline
from pyspark.ml.classification import RandomForestClassifier
from pyspark.ml.feature import VectorAssembler, StringIndexer, OneHotEncoder
from pyspark.ml.evaluation import BinaryClassificationEvaluator
from pyspark.sql.functions import *
import pickle

class FraudDetectionModel:
    def __init__(self, spark):
        self.spark = spark
        self.model = None
        
    def create_features(self, transactions_df):
        """Create features for fraud detection"""
        
        # Time-based features
        features = transactions_df \
            .withColumn("hour_of_day", hour(col("timestamp"))) \
            .withColumn("day_of_week", dayofweek(col("timestamp"))) \
            .withColumn("is_weekend", when(col("day_of_week").isin([1, 7]), 1).otherwise(0)) \
            .withColumn("is_night", when((col("hour_of_day") >= 22) | (col("hour_of_day") <= 6), 1).otherwise(0))
        
        # Transaction amount features
        features = features \
            .withColumn("amount_log", log(col("amount") + 1)) \
            .withColumn("amount_squared", pow(col("amount"), 2)) \
            .withColumn("is_high_value", when(col("amount") > 500, 1).otherwise(0))
        
        # Historical features using window functions
        window_spec = Window.partitionBy("user_id").orderBy("timestamp").rowsBetween(-10, -1)
        
        features = features \
            .withColumn("avg_last_10", avg(col("amount")).over(window_spec)) \
            .withColumn("std_last_10", stddev(col("amount")).over(window_spec)) \
            .withColumn("count_last_hour", count("*").over(
                Window.partitionBy("user_id")
                .orderBy(col("timestamp").cast("long"))
                .rangeBetween(-3600, 0)
            ))
        
        # Location velocity (simplified)
        features = features.withColumn("location_change", lit(0))  # Would use actual location data
        
        return features
    
    def train_model(self, training_data_path):
        """Train Random Forest fraud detection model"""
        
        # Load training data
        df = self.spark.read.parquet(training_data_path)
        
        # Create features
        features_df = self.create_features(df)
        
        # Prepare features for ML
        categorical_cols = ["category", "device_id"]
        numerical_cols = ["amount", "hour_of_day", "day_of_week", "amount_log", 
                         "avg_last_10", "std_last_10", "count_last_hour"]
        
        # String index categorical columns
        indexers = [StringIndexer(inputCol=col, outputCol=col+"_index", handleInvalid="keep") 
                   for col in categorical_cols]
        
        # One-hot encode
        encoders = [OneHotEncoder(inputCol=col+"_index", outputCol=col+"_encoded") 
                   for col in categorical_cols]
        
        # Assemble features
        feature_cols = [col+"_encoded" for col in categorical_cols] + numerical_cols
        assembler = VectorAssembler(inputCols=feature_cols, outputCol="features")
        
        # Create Random Forest model
        rf = RandomForestClassifier(
            labelCol="is_fraud",
            featuresCol="features",
            numTrees=100,
            maxDepth=10,
            seed=42,
            featureSubsetStrategy="auto",
            impurity="gini"
        )
        
        # Build pipeline
        pipeline = Pipeline(stages=indexers + encoders + [assembler, rf])
        
        # Split data
        train_df, test_df = features_df.randomSplit([0.8, 0.2], seed=42)
        
        # Train model
        model = pipeline.fit(train_df)
        
        # Evaluate
        predictions = model.transform(test_df)
        evaluator = BinaryClassificationEvaluator(labelCol="is_fraud")
        auc = evaluator.evaluate(predictions)
        
        print(f"Model trained. AUC: {auc}")
        
        # Save model
        model.save("/models/fraud_detection_model")
        self.model = model
        
        return model
    
    def predict_streaming(self, transactions_stream):
        """Apply fraud detection to streaming data"""
        
        if not self.model:
            # Load pre-trained model
            self.model = PipelineModel.load("/models/fraud_detection_model")
        
        # Create features
        features_stream = self.create_features(transactions_stream)
        
        # Make predictions
        predictions = self.model.transform(features_stream)
        
        # Extract fraud probabilities
        fraud_predictions = predictions.select(
            "transaction_id",
            "user_id",
            "amount",
            "merchant",
            "prediction",
            col("probability").getItem(1).alias("fraud_probability"),
            current_timestamp().alias("prediction_time")
        ).filter(col("prediction") == 1)
        
        return fraud_predictions