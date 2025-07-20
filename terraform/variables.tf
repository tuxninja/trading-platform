# Trading Platform Terraform Variables

variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "trading-platform"
}

variable "domain_name" {
  description = "Domain name for the application"
  type        = string
  default     = "trading-platform.com"
}

variable "create_route53_zone" {
  description = "Whether to create Route53 hosted zone"
  type        = bool
  default     = false
}

# Networking
variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidr" {
  description = "CIDR block for public subnet"
  type        = string
  default     = "10.0.1.0/24"
}

# EC2 Configuration
variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.micro"
  
  validation {
    condition = contains([
      "t3.micro", "t3.small", "t3.medium",
      "t2.micro", "t2.small", "t2.medium"
    ], var.instance_type)
    error_message = "Instance type must be a valid cost-effective option."
  }
}

variable "root_volume_size" {
  description = "Size of root EBS volume in GB"
  type        = number
  default     = 20
}

variable "ec2_public_key" {
  description = "Public key for EC2 access (SSH)"
  type        = string
  sensitive   = true
}

variable "ssh_allowed_ips" {
  description = "List of IP addresses allowed SSH access"
  type        = list(string)
  default     = ["0.0.0.0/0"]  # Restrict this in production
}

# Application Configuration
variable "secret_key" {
  description = "Secret key for the application"
  type        = string
  sensitive   = true
  default     = ""
}

variable "news_api_key" {
  description = "News API key for sentiment analysis"
  type        = string
  sensitive   = true
  default     = ""
}

variable "alpha_vantage_key" {
  description = "Alpha Vantage API key"
  type        = string
  sensitive   = true
  default     = ""
}

# Cost Controls
variable "enable_detailed_monitoring" {
  description = "Enable detailed CloudWatch monitoring (additional cost)"
  type        = bool
  default     = false
}

variable "backup_retention_days" {
  description = "Number of days to retain automated backups"
  type        = number
  default     = 7
}

# Tags
variable "additional_tags" {
  description = "Additional tags to apply to resources"
  type        = map(string)
  default     = {}
}

# GitHub Configuration
variable "github_token" {
  description = "GitHub Personal Access Token"
  type        = string
  sensitive   = true
  default     = ""
}

variable "github_owner" {
  description = "GitHub repository owner (username or organization)"
  type        = string
  default     = ""
}

variable "github_repository" {
  description = "GitHub repository name (just the repo name, not owner/repo)"
  type        = string
  default     = ""
}

variable "auto_update_github_secrets" {
  description = "Automatically update GitHub secrets with new EC2 IP"
  type        = bool
  default     = true
}