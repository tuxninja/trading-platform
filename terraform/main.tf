# Trading Platform AWS Infrastructure
# Cost-optimized deployment using single EC2 instance with Docker Compose

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    http = {
      source  = "hashicorp/http"
      version = "~> 3.4"
    }
    github = {
      source  = "integrations/github"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "trading-platform"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

provider "github" {
  token = var.github_token
  owner = var.github_owner
}

# Data sources
data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }
}

# Fetch GitHub Actions IP ranges
data "http" "github_meta" {
  url = "https://api.github.com/meta"
}

locals {
  # For GitHub Actions, we'll allow SSH from the major cloud provider ranges
  # This is more manageable than 100+ individual ranges
  github_actions_friendly_cidrs = [
    "13.64.0.0/11",     # Microsoft Azure (GitHub uses Azure for Actions)
    "20.0.0.0/8",       # Microsoft Azure
    "4.148.0.0/14",     # GitHub Actions primary range
    "140.82.112.0/20",  # GitHub.com
    "143.55.64.0/20",   # GitHub.com
    "192.30.252.0/22",  # GitHub.com
    "185.199.108.0/22", # GitHub.com
  ]
  
  # Combine user-specified IPs with GitHub Actions friendly ranges
  all_ssh_allowed_ipv4 = concat(var.ssh_allowed_ips, local.github_actions_friendly_cidrs)
}

# VPC and Networking
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "${var.project_name}-vpc"
  }
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "${var.project_name}-igw"
  }
}

resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.public_subnet_cidr
  availability_zone       = data.aws_availability_zones.available.names[0]
  map_public_ip_on_launch = true

  tags = {
    Name = "${var.project_name}-public-subnet"
    Type = "Public"
  }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = {
    Name = "${var.project_name}-public-rt"
  }
}

resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

# Security Groups
resource "aws_security_group" "web" {
  name        = "${var.project_name}-web-sg"
  description = "Security group for web server"
  vpc_id      = aws_vpc.main.id

  # HTTP
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # HTTPS
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # SSH (restricted to specific IPs + GitHub Actions)
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = local.all_ssh_allowed_ipv4
    description = "SSH access for admins and GitHub Actions"
  }

  # Backend API (for internal communication)
  ingress {
    from_port = 8000
    to_port   = 8000
    protocol  = "tcp"
    self      = true
  }

  # All outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-web-sg"
  }
}

# Key Pair for EC2 Access
resource "aws_key_pair" "main" {
  key_name   = "${var.project_name}-keypair"
  public_key = var.ec2_public_key

  tags = {
    Name = "${var.project_name}-keypair"
  }
}

# IAM Role for EC2
resource "aws_iam_role" "ec2_role" {
  name = "${var.project_name}-ec2-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

# IAM Policy for ECR access
resource "aws_iam_policy" "ecr_policy" {
  name        = "${var.project_name}-ecr-policy"
  description = "Policy for ECR access"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ecr:GetAuthorizationToken",
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogStreams"
        ]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ec2_ecr_policy" {
  role       = aws_iam_role.ec2_role.name
  policy_arn = aws_iam_policy.ecr_policy.arn
}

# Instance Profile
resource "aws_iam_instance_profile" "ec2_profile" {
  name = "${var.project_name}-ec2-profile"
  role = aws_iam_role.ec2_role.name
}

# User Data Script for EC2
locals {
  user_data = base64encode(templatefile("${path.module}/user-data.sh", {
    domain_name         = var.domain_name
    ecr_repository_url  = aws_ecr_repository.main.repository_url
    aws_region         = var.aws_region
    secret_key         = var.secret_key
    news_api_key       = var.news_api_key
    alpha_vantage_key  = var.alpha_vantage_key
  }))
}

# EC2 Instance
resource "aws_instance" "main" {
  ami                     = data.aws_ami.amazon_linux.id
  instance_type           = var.instance_type
  key_name                = aws_key_pair.main.key_name
  vpc_security_group_ids  = [aws_security_group.web.id]
  subnet_id               = aws_subnet.public.id
  iam_instance_profile    = aws_iam_instance_profile.ec2_profile.name
  user_data               = local.user_data

  root_block_device {
    volume_type = "gp3"
    volume_size = var.root_volume_size
    encrypted   = true
  }

  tags = {
    Name = "${var.project_name}-server"
    Type = "WebServer"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Elastic IP
resource "aws_eip" "main" {
  instance = aws_instance.main.id
  domain   = "vpc"

  tags = {
    Name = "${var.project_name}-eip"
  }

  depends_on = [aws_internet_gateway.main]
}

# ECR Repository
resource "aws_ecr_repository" "main" {
  name                 = var.project_name
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name = "${var.project_name}-ecr"
  }
}

# ECR Repository for Frontend
resource "aws_ecr_repository" "frontend" {
  name                 = "${var.project_name}-frontend"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name = "${var.project_name}-frontend-ecr"
  }
}

# ECR Repository for Backend
resource "aws_ecr_repository" "backend" {
  name                 = "${var.project_name}-backend"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name = "${var.project_name}-backend-ecr"
  }
}

# Route 53 Hosted Zone (optional)
resource "aws_route53_zone" "main" {
  count = var.create_route53_zone ? 1 : 0
  name  = var.domain_name

  tags = {
    Name = "${var.project_name}-zone"
  }
}

# Route 53 A Record
resource "aws_route53_record" "main" {
  count   = var.create_route53_zone ? 1 : 0
  zone_id = aws_route53_zone.main[0].zone_id
  name    = var.domain_name
  type    = "A"
  ttl     = 300
  records = [aws_eip.main.public_ip]
}

# Route 53 CNAME for API subdomain
resource "aws_route53_record" "api" {
  count   = var.create_route53_zone ? 1 : 0
  zone_id = aws_route53_zone.main[0].zone_id
  name    = "api.${var.domain_name}"
  type    = "CNAME"
  ttl     = 300
  records = [var.domain_name]
}

# GitHub Actions Secret Management
resource "github_actions_secret" "ec2_host" {
  count           = var.auto_update_github_secrets && var.github_repository != "" && var.github_owner != "" ? 1 : 0
  repository      = var.github_repository
  secret_name     = "EC2_HOST"
  plaintext_value = aws_eip.main.public_ip
}