#!/bin/bash
# Trading Platform EC2 User Data Script
# Installs Docker, Docker Compose, and sets up the application

set -e

# Variables from Terraform
DOMAIN_NAME="${domain_name}"
ECR_REPOSITORY_URL="${ecr_repository_url}"
AWS_REGION="${aws_region}"
SECRET_KEY="${secret_key}"
NEWS_API_KEY="${news_api_key}"
ALPHA_VANTAGE_KEY="${alpha_vantage_key}"

# Log everything
exec > >(tee /var/log/user-data.log)
exec 2>&1

echo "Starting Trading Platform setup at $(date)"

# Update system
yum update -y

# Install required packages
yum install -y \
    docker \
    git \
    htop \
    curl \
    wget \
    unzip \
    jq \
    aws-cli

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose

# Start and enable Docker
systemctl start docker
systemctl enable docker

# Add ec2-user to docker group
usermod -aG docker ec2-user

# Create application directories
mkdir -p /opt/trading/{data,logs,nginx_logs,backups}
chown -R ec2-user:ec2-user /opt/trading

# Create environment file
cat > /opt/trading/.env << EOF
DOMAIN_NAME=$DOMAIN_NAME
SECRET_KEY=$SECRET_KEY
NEWS_API_KEY=$NEWS_API_KEY
ALPHA_VANTAGE_KEY=$ALPHA_VANTAGE_KEY
ENVIRONMENT=production
DATABASE_URL=sqlite:///data/trading.db
CORS_ORIGINS=http://localhost,https://$DOMAIN_NAME
LOG_LEVEL=INFO
INITIAL_BALANCE=100000.0
MAX_POSITION_SIZE=0.05
ENABLE_SCHEDULER=true
GOOGLE_CLIENT_ID=${google_client_id}
EOF

chown ec2-user:ec2-user /opt/trading/.env
chmod 600 /opt/trading/.env

# Configure Docker daemon
cat > /etc/docker/daemon.json << EOF
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "storage-driver": "overlay2"
}
EOF

# Restart Docker with new configuration
systemctl restart docker

# Configure ECR login helper
mkdir -p /home/ec2-user/.docker
cat > /home/ec2-user/.docker/config.json << EOF
{
  "credHelpers": {
    "$ECR_REPOSITORY_URL": "ecr-login"
  }
}
EOF
chown -R ec2-user:ec2-user /home/ec2-user/.docker

# Install Amazon ECR Docker Credential Helper
curl -L "https://amazon-ecr-credential-helper-releases.s3.us-east-2.amazonaws.com/0.7.1/linux-amd64/docker-credential-ecr-login" -o /usr/local/bin/docker-credential-ecr-login
chmod +x /usr/local/bin/docker-credential-ecr-login

# Create systemd service for the application
cat > /etc/systemd/system/trading-platform.service << EOF
[Unit]
Description=Trading Platform Application
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/trading
EnvironmentFile=/opt/trading/.env
ExecStart=/usr/local/bin/docker-compose -f docker-compose.prod.yml up -d
ExecStop=/usr/local/bin/docker-compose -f docker-compose.prod.yml down
TimeoutStartSec=600
User=ec2-user
Group=ec2-user

[Install]
WantedBy=multi-user.target
EOF

# Create backup script
cat > /opt/trading/backup.sh << 'EOF'
#!/bin/bash
# Trading Platform Backup Script

BACKUP_DIR="/opt/trading/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="trading_backup_$DATE.tar.gz"

# Create backup
cd /opt/trading
tar -czf "$BACKUP_DIR/$BACKUP_FILE" \
    --exclude='backups' \
    --exclude='logs/*.log' \
    data/ docker-compose.prod.yml .env

# Keep only last 7 days of backups
find "$BACKUP_DIR" -name "trading_backup_*.tar.gz" -mtime +7 -delete

echo "Backup created: $BACKUP_FILE"
EOF

chmod +x /opt/trading/backup.sh
chown ec2-user:ec2-user /opt/trading/backup.sh

# Setup cron for backups
echo "0 2 * * * /opt/trading/backup.sh >> /var/log/backup.log 2>&1" | crontab -u ec2-user -

# Create log rotation configuration
cat > /etc/logrotate.d/trading-platform << EOF
/opt/trading/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
    su ec2-user ec2-user
}
EOF

# Configure CloudWatch agent (optional)
if command -v amazon-cloudwatch-agent-ctl &> /dev/null; then
    cat > /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json << EOF
{
    "logs": {
        "logs_collected": {
            "files": {
                "collect_list": [
                    {
                        "file_path": "/opt/trading/logs/*.log",
                        "log_group_name": "trading-platform",
                        "log_stream_name": "{instance_id}/application"
                    },
                    {
                        "file_path": "/var/log/user-data.log",
                        "log_group_name": "trading-platform",
                        "log_stream_name": "{instance_id}/user-data"
                    }
                ]
            }
        }
    }
}
EOF
fi

# Create health check script
cat > /opt/trading/health-check.sh << 'EOF'
#!/bin/bash
# Trading Platform Health Check

BACKEND_URL="http://localhost:8000"
FRONTEND_URL="http://localhost:80"

# Check backend
if curl -f -s "$BACKEND_URL/" > /dev/null; then
    echo "Backend: OK"
    BACKEND_STATUS=0
else
    echo "Backend: FAIL"
    BACKEND_STATUS=1
fi

# Check frontend
if curl -f -s "$FRONTEND_URL/health" > /dev/null; then
    echo "Frontend: OK"
    FRONTEND_STATUS=0
else
    echo "Frontend: FAIL"
    FRONTEND_STATUS=1
fi

# Overall status
if [ $BACKEND_STATUS -eq 0 ] && [ $FRONTEND_STATUS -eq 0 ]; then
    echo "Overall: HEALTHY"
    exit 0
else
    echo "Overall: UNHEALTHY"
    exit 1
fi
EOF

chmod +x /opt/trading/health-check.sh
chown ec2-user:ec2-user /opt/trading/health-check.sh

# Create update script for CI/CD
cat > /opt/trading/update.sh << 'EOF'
#!/bin/bash
# Trading Platform Update Script for CI/CD

set -e

BACKEND_IMAGE="$1"
FRONTEND_IMAGE="$2"

if [ -z "$BACKEND_IMAGE" ] || [ -z "$FRONTEND_IMAGE" ]; then
    echo "Usage: $0 <backend_image> <frontend_image>"
    exit 1
fi

echo "Updating Trading Platform..."
echo "Backend Image: $BACKEND_IMAGE"
echo "Frontend Image: $FRONTEND_IMAGE"

# Update docker-compose with new images
cd /opt/trading

# Create backup before update
./backup.sh

# Pull new images
docker pull "$BACKEND_IMAGE"
docker pull "$FRONTEND_IMAGE"

# Update images in docker-compose file
sed -i "s|image: .*backend.*|image: $BACKEND_IMAGE|g" docker-compose.prod.yml
sed -i "s|image: .*frontend.*|image: $FRONTEND_IMAGE|g" docker-compose.prod.yml

# Restart services
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d

# Wait for services to be ready
sleep 30

# Simple container check instead of health checks
if docker-compose -f docker-compose.prod.yml ps | grep -q "Up"; then
    echo "Update completed successfully!"
    # Clean up old images
    docker image prune -f
else
    echo "Update failed! No containers running."
    exit 1
fi
EOF

chmod +x /opt/trading/update.sh
chown ec2-user:ec2-user /opt/trading/update.sh

# Install CloudWatch Agent (optional)
# wget https://s3.amazonaws.com/amazoncloudwatch-agent/amazon_linux/amd64/latest/amazon-cloudwatch-agent.rpm
# rpm -U ./amazon-cloudwatch-agent.rpm

# Setup fail2ban for SSH protection
yum install -y epel-release
yum install -y fail2ban

cat > /etc/fail2ban/jail.local << EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3

[sshd]
enabled = true
port = 22
logpath = /var/log/secure
EOF

systemctl enable fail2ban
systemctl start fail2ban

# Configure firewall
yum install -y firewalld
systemctl enable firewalld
systemctl start firewalld

firewall-cmd --permanent --add-port=80/tcp
firewall-cmd --permanent --add-port=443/tcp
firewall-cmd --permanent --add-service=ssh
firewall-cmd --reload

# Set up monitoring script
cat > /opt/trading/monitor.sh << 'EOF'
#!/bin/bash
# Basic monitoring script

echo "=== Trading Platform Status ==="
echo "Date: $(date)"
echo "Uptime: $(uptime)"
echo "Memory: $(free -h)"
echo "Disk: $(df -h /opt/trading)"
echo "Docker Status:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo "Recent Logs:"
tail -n 5 /opt/trading/logs/*.log 2>/dev/null || echo "No application logs yet"
EOF

chmod +x /opt/trading/monitor.sh
chown ec2-user:ec2-user /opt/trading/monitor.sh

# Add monitoring to cron (every 15 minutes)
echo "*/15 * * * * /opt/trading/monitor.sh >> /var/log/monitor.log 2>&1" | crontab -u ec2-user -

# Final setup
systemctl daemon-reload

echo "Trading Platform setup completed at $(date)"
echo "Next steps:"
echo "1. Deploy the application using CI/CD pipeline"
echo "2. Configure DNS to point to this server: $(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)"
echo "3. Monitor logs in /opt/trading/logs/"
echo "4. Access application health check: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)/health"

# Send completion notification to CloudWatch
if command -v aws &> /dev/null; then
    aws logs create-log-group --log-group-name trading-platform --region $AWS_REGION 2>/dev/null || true
    echo "User data script completed successfully" | aws logs create-log-stream --log-group-name trading-platform --log-stream-name "$(curl -s http://169.254.169.254/latest/meta-data/instance-id)/setup" --region $AWS_REGION 2>/dev/null || true
fi