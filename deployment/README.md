# Trading Platform Deployment Guide

This guide covers the complete deployment process for the Trading Platform on AWS using Docker, Terraform, and GitHub Actions.

## 📋 Table of Contents

- [Architecture Overview](#architecture-overview)
- [Prerequisites](#prerequisites)
- [Initial Setup](#initial-setup)
- [Infrastructure Deployment](#infrastructure-deployment)
- [Application Deployment](#application-deployment)
- [CI/CD Pipeline](#cicd-pipeline)
- [Monitoring & Maintenance](#monitoring--maintenance)
- [Cost Management](#cost-management)
- [Troubleshooting](#troubleshooting)

## 🏗️ Architecture Overview

### Cost-Optimized AWS Architecture
- **Monthly Cost**: ~$10-15 (well under $50 budget)
- **Infrastructure**: Single EC2 t3.micro instance
- **Containerization**: Docker Compose orchestration
- **SSL/CDN**: CloudFlare (free)
- **DNS**: Route 53 (~$0.50/month)
- **Container Registry**: ECR (500MB free tier)

### Services Architecture
```
┌─────────────────────────────────────────────────────────────────┐
│                        CloudFlare CDN/SSL                       │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                    Route 53 DNS                                │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                 EC2 t3.micro Instance                          │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐              │
│  │  Frontend   │ │   Backend   │ │  Scheduler  │              │
│  │ (Nginx+React)│ │  (FastAPI)  │ │   (Python)  │              │
│  └─────────────┘ └─────────────┘ └─────────────┘              │
│                        │                                        │
│                 ┌─────────────┐                                │
│                 │   SQLite    │                                │
│                 │  Database   │                                │
│                 └─────────────┘                                │
└─────────────────────────────────────────────────────────────────┘
```

## 🔧 Prerequisites

### Required Tools
- **AWS CLI** v2.0+ configured with appropriate permissions
- **Terraform** v1.0+
- **Docker** and Docker Compose
- **Git** with GitHub repository access
- **SSH key pair** for EC2 access

### Required AWS Permissions
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:*",
        "ecr:*",
        "iam:*",
        "route53:*",
        "vpc:*"
      ],
      "Resource": "*"
    }
  ]
}
```

### Cost Estimation
| Service | Monthly Cost | Notes |
|---------|--------------|--------|
| EC2 t3.micro | $8.50 | Free tier: 750 hours/month for 12 months |
| EBS 20GB | $1.60 | GP3 storage |
| Elastic IP | $0.00 | Free when attached to running instance |
| Route 53 | $0.50 | Hosted zone fee |
| Data Transfer | $0-2 | First 1GB free |
| ECR Storage | $0.00 | 500MB free tier |
| **Total** | **~$10-12** | Well under $50 budget |

## 🚀 Initial Setup

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/trading-platform.git
cd trading-platform
```

### 2. Generate SSH Key Pair
```bash
# Generate new SSH key pair for EC2 access
ssh-keygen -t rsa -b 4096 -f ~/.ssh/trading-platform
ssh-add ~/.ssh/trading-platform

# Get public key for Terraform
cat ~/.ssh/trading-platform.pub
```

### 3. Configure AWS Credentials
```bash
# Configure AWS CLI
aws configure

# Or export environment variables
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_DEFAULT_REGION="us-east-1"
```

### 4. Set Up GitHub Secrets
Navigate to your GitHub repository → Settings → Secrets and variables → Actions

**Required Secrets:**
```
AWS_ACCESS_KEY_ID: Your AWS access key
AWS_SECRET_ACCESS_KEY: Your AWS secret key
EC2_SSH_PRIVATE_KEY: Content of ~/.ssh/trading-platform (private key)
EC2_PUBLIC_KEY: Content of ~/.ssh/trading-platform.pub
SECRET_KEY: Random secret key for the application
DOMAIN_NAME: Your domain name (e.g., trading-platform.com)
TF_STATE_BUCKET: S3 bucket for Terraform state (optional)
```

**Optional Secrets:**
```
NEWS_API_KEY: News API key from newsapi.org
ALPHA_VANTAGE_KEY: Alpha Vantage API key
SLACK_WEBHOOK: Slack webhook URL for notifications
INSTANCE_TYPE: EC2 instance type (default: t3.micro)
CREATE_ROUTE53_ZONE: true/false for Route53 management
SSH_ALLOWED_IPS: JSON array of allowed IP addresses
```

## 🏗️ Infrastructure Deployment

### 1. Prepare Terraform Configuration
```bash
cd terraform

# Copy example variables file
cp terraform.tfvars.example terraform.tfvars

# Edit terraform.tfvars with your values
vim terraform.tfvars
```

### 2. Initialize Terraform
```bash
# Initialize Terraform (with remote state - optional)
terraform init

# Or with S3 backend
terraform init \
  -backend-config="bucket=your-terraform-state-bucket" \
  -backend-config="key=trading-platform/terraform.tfstate" \
  -backend-config="region=us-east-1"
```

### 3. Plan and Apply Infrastructure
```bash
# Plan infrastructure changes
terraform plan

# Apply infrastructure
terraform apply

# Save important outputs
terraform output > ../deployment/terraform-outputs.txt
```

### 4. Verify Infrastructure
```bash
# Get instance IP
INSTANCE_IP=$(terraform output -raw public_ip)

# Test SSH connection
ssh -i ~/.ssh/trading-platform ec2-user@$INSTANCE_IP

# Check instance setup
ssh -i ~/.ssh/trading-platform ec2-user@$INSTANCE_IP 'docker --version && docker-compose --version'
```

## 🚀 Application Deployment

### Option 1: Manual Deployment
```bash
# Build and push images manually
./deployment/scripts/build-and-push.sh

# Deploy to EC2
./deployment/scripts/deploy.sh
```

### Option 2: GitHub Actions (Recommended)
1. Push code to main branch
2. GitHub Actions automatically:
   - Runs tests
   - Builds Docker images
   - Pushes to ECR
   - Deploys to EC2
   - Verifies deployment

### Deployment Process
```bash
# The automated deployment:
# 1. Pulls latest images from ECR
# 2. Updates docker-compose.prod.yml
# 3. Stops current containers
# 4. Starts new containers
# 5. Runs health checks
# 6. Cleans up old images
```

## 🔄 CI/CD Pipeline

### GitHub Actions Workflows

#### 1. Application Deployment (`.github/workflows/deploy.yml`)
- **Trigger**: Push to main branch
- **Steps**:
  1. Run tests (backend & frontend)
  2. Build and push Docker images to ECR
  3. Deploy to EC2 instance
  4. Verify deployment health
  5. Send notifications

#### 2. Infrastructure Deployment (`.github/workflows/infrastructure.yml`)
- **Trigger**: Changes to `terraform/` directory
- **Steps**:
  1. Terraform plan/apply
  2. Update GitHub secrets with outputs
  3. Cost estimation (on PRs)
  4. Security scanning

### Manual CI/CD Commands
```bash
# Trigger infrastructure deployment
git push origin main  # If terraform/ files changed

# Trigger application deployment
git push origin main  # Any code changes

# Manual deployment trigger (if needed)
curl -X POST \
  -H "Accept: application/vnd.github.v3+json" \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/yourusername/trading-platform/actions/workflows/deploy.yml/dispatches \
  -d '{"ref":"main"}'
```

## 📊 Monitoring & Maintenance

### Health Checks
```bash
# Application health
curl http://your-domain.com/health

# Backend API health
curl http://your-domain.com/api/

# Container status
ssh ec2-user@your-server 'docker ps'
```

### Log Management
```bash
# View application logs
ssh ec2-user@your-server 'cd /opt/trading && docker-compose logs -f'

# View specific service logs
ssh ec2-user@your-server 'docker logs trading-backend -f'

# System logs
ssh ec2-user@your-server 'tail -f /var/log/user-data.log'
```

### Backup and Recovery
```bash
# Manual backup
ssh ec2-user@your-server '/opt/trading/backup.sh'

# Automated backups run daily at 2 AM
# Backups are stored in /opt/trading/backups/
# Retention: 7 days

# Restore from backup
ssh ec2-user@your-server << 'EOF'
  cd /opt/trading
  docker-compose down
  tar -xzf backups/trading_backup_YYYYMMDD_HHMMSS.tar.gz
  docker-compose up -d
EOF
```

### Updates and Maintenance
```bash
# Update system packages
ssh ec2-user@your-server 'sudo yum update -y'

# Update Docker images
git push origin main  # Triggers automatic deployment

# Manual container restart
ssh ec2-user@your-server 'cd /opt/trading && docker-compose restart'

# Database maintenance
ssh ec2-user@your-server 'cd /opt/trading && sqlite3 data/trading.db ".vacuum"'
```

## 💰 Cost Management

### Cost Monitoring
```bash
# Check current AWS costs
aws ce get-cost-and-usage \
  --time-period Start=2024-01-01,End=2024-01-31 \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --group-by Type=DIMENSION,Key=SERVICE

# Monitor instance usage
aws cloudwatch get-metric-statistics \
  --namespace AWS/EC2 \
  --metric-name CPUUtilization \
  --dimensions Name=InstanceId,Value=i-1234567890abcdef0 \
  --statistics Average \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-31T23:59:59Z \
  --period 86400
```

### Cost Optimization Tips
1. **Use t3.micro for development**, upgrade to t3.small only if needed
2. **Enable CloudFlare caching** to reduce bandwidth costs
3. **Monitor storage usage** and clean up old Docker images
4. **Use ECR lifecycle policies** to remove old container images
5. **Set up billing alerts** for budget monitoring

### Instance Sizing Guidelines
- **t3.micro** (1 vCPU, 1GB RAM): Development/Light production (~$8.50/month)
- **t3.small** (2 vCPU, 2GB RAM): Production with moderate load (~$16.79/month)
- **t3.medium** (2 vCPU, 4GB RAM): High-load production (~$33.58/month)

## 🔧 Troubleshooting

### Common Issues

#### 1. Deployment Failures
```bash
# Check deployment logs
ssh ec2-user@your-server 'journalctl -u trading-platform -f'

# Check container status
ssh ec2-user@your-server 'docker ps -a'

# Check container logs
ssh ec2-user@your-server 'docker-compose -f /opt/trading/docker-compose.prod.yml logs'
```

#### 2. Application Not Accessible
```bash
# Check security groups
aws ec2 describe-security-groups --group-ids sg-xxxxxxxxx

# Check nginx configuration
ssh ec2-user@your-server 'docker exec trading-frontend nginx -t'

# Check port accessibility
curl -I http://your-server-ip:80
```

#### 3. Database Issues
```bash
# Check database file
ssh ec2-user@your-server 'ls -la /opt/trading/data/'

# Database backup
ssh ec2-user@your-server 'cp /opt/trading/data/trading.db /opt/trading/backups/'

# Check database integrity
ssh ec2-user@your-server 'sqlite3 /opt/trading/data/trading.db "PRAGMA integrity_check;"'
```

#### 4. SSL/HTTPS Issues (with CloudFlare)
```bash
# Verify CloudFlare DNS settings
dig your-domain.com

# Check SSL certificate
curl -I https://your-domain.com

# Verify CloudFlare SSL mode is set to "Flexible" or "Full"
```

### Emergency Procedures

#### 1. Rollback Deployment
```bash
# SSH to server
ssh ec2-user@your-server

# Go to application directory
cd /opt/trading

# Stop current deployment
docker-compose -f docker-compose.prod.yml down

# Restore from backup
tar -xzf backups/trading_backup_$(ls backups/ | sort -r | head -1)

# Start previous version
docker-compose -f docker-compose.prod.yml up -d
```

#### 2. Scale Up Instance (if needed)
```bash
# In terraform/terraform.tfvars
instance_type = "t3.small"  # or t3.medium

# Apply changes
terraform plan
terraform apply
```

#### 3. Complete Infrastructure Rebuild
```bash
# Backup data first
./deployment/scripts/backup.sh

# Destroy infrastructure
terraform destroy

# Recreate infrastructure
terraform apply

# Restore data and redeploy
./deployment/scripts/restore.sh
```

### Performance Optimization

#### 1. Application Performance
```bash
# Monitor resource usage
ssh ec2-user@your-server 'htop'

# Check database performance
ssh ec2-user@your-server 'sqlite3 /opt/trading/data/trading.db ".schema"'

# Optimize Docker
ssh ec2-user@your-server 'docker system prune -f'
```

#### 2. Network Performance
- Enable CloudFlare caching for static assets
- Use CloudFlare's "Auto Minify" for CSS/JS/HTML
- Enable CloudFlare's "Rocket Loader" for faster JavaScript loading

## 📞 Support and Maintenance

### Regular Maintenance Tasks
- [ ] Weekly: Check application logs and health
- [ ] Monthly: Update system packages
- [ ] Monthly: Review AWS costs and usage
- [ ] Quarterly: Update Docker images and dependencies
- [ ] Quarterly: Review and rotate API keys

### Monitoring Checklist
- [ ] Application accessibility (HTTP 200 responses)
- [ ] Container health status
- [ ] Disk space usage (< 80%)
- [ ] Memory usage (< 80%)
- [ ] Database integrity
- [ ] Backup success
- [ ] SSL certificate validity

### Contact and Resources
- **Documentation**: This README and service-specific docs
- **Monitoring**: AWS CloudWatch, application health endpoints
- **Alerting**: GitHub Actions notifications, Slack webhooks
- **Support**: GitHub Issues, application logs

---

For additional help, refer to the main project documentation or create an issue in the GitHub repository.