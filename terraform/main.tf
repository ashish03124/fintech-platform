# terraform/main.tf
terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
    
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# EKS Cluster
resource "aws_eks_cluster" "fintech_cluster" {
  name     = "fintech-eks-cluster"
  role_arn = aws_iam_role.eks_cluster.arn
  
  vpc_config {
    subnet_ids = var.subnet_ids
  }
  
  tags = {
    Environment = "production"
    Application = "fintech-platform"
  }
}

# RDS PostgreSQL
resource "aws_db_instance" "postgres" {
  identifier           = "fintech-postgres"
  engine              = "postgres"
  engine_version      = "15.3"
  instance_class      = "db.r6g.2xlarge"
  allocated_storage   = 500
  storage_encrypted   = true
  kms_key_id          = aws_kms_key.database.arn
  
  db_name  = "fintech"
  username = var.db_username
  password = var.db_password
  
  vpc_security_group_ids = [aws_security_group.database.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name
  
  backup_retention_period = 30
  backup_window           = "03:00-04:00"
  maintenance_window      = "sun:04:00-sun:05:00"
  
  tags = {
    Environment = "production"
  }
}

# MSK Kafka Cluster
resource "aws_msk_cluster" "kafka" {
  cluster_name           = "fintech-kafka"
  kafka_version         = "3.4.0"
  number_of_broker_nodes = 3
  
  broker_node_group_info {
    instance_type   = "kafka.m5.2xlarge"
    ebs_volume_size = 1000
    
    client_subnets = var.subnet_ids
    security_groups = [aws_security_group.kafka.id]
  }
  
  encryption_info {
    encryption_at_rest_kms_key_arn = aws_kms_key.kafka.arn
    encryption_in_transit {
      client_broker = "TLS"
      in_cluster    = true
    }
  }
  
  tags = {
    Environment = "production"
  }
}

# ECR Repositories
resource "aws_ecr_repository" "services" {
  for_each = toset(["api-service", "ai-service", "spark-jobs", "data-generator"])
  
  name = "fintech/${each.key}"
  
  image_tag_mutability = "MUTABLE"
  
  image_scanning_configuration {
    scan_on_push = true
  }
}