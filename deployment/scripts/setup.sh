#!/bin/bash
# Complete setup script for Trading Platform deployment on AWS

set -e

# Configuration
PROJECT_NAME="trading-platform"
AWS_REGION=${AWS_REGION:-us-east-1}
TERRAFORM_DIR="../../terraform"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

print_banner() {
    echo -e "${BLUE}"
    cat << 'EOF'
╔══════════════════════════════════════════════════════════════╗
║                    Trading Platform Setup                    ║
║              Complete AWS Deployment Automation             ║
╚══════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
}

print_step() {
    echo -e "\n${PURPLE}▶ $1${NC}"
    echo -e "${YELLOW}$2${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    print_step "Step 1: Checking Prerequisites" "Verifying required tools and permissions"
    
    local missing_tools=()
    
    # Check required tools
    command -v aws >/dev/null 2>&1 || missing_tools+=("aws-cli")
    command -v terraform >/dev/null 2>&1 || missing_tools+=("terraform")
    command -v docker >/dev/null 2>&1 || missing_tools+=("docker")
    command -v git >/dev/null 2>&1 || missing_tools+=("git")
    
    if [ ${#missing_tools[@]} -ne 0 ]; then
        print_error "Missing required tools: ${missing_tools[*]}"
        echo "Please install the missing tools and run this script again."
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity >/dev/null 2>&1; then
        print_error "AWS credentials not configured"
        echo "Run 'aws configure' to set up your credentials"
        exit 1
    fi
    
    # Check Docker is running
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker is not running"
        echo "Please start Docker and run this script again"
        exit 1
    fi
    
    AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    AWS_USER=$(aws sts get-caller-identity --query Arn --output text | cut -d'/' -f2)
    
    print_success "All prerequisites satisfied"
    echo "  AWS Account: $AWS_ACCOUNT_ID"
    echo "  AWS User: $AWS_USER"
    echo "  AWS Region: $AWS_REGION"
}

# Generate SSH key pair
generate_ssh_key() {
    print_step "Step 2: SSH Key Setup" "Generating SSH key pair for EC2 access"
    
    SSH_KEY_PATH="$HOME/.ssh/$PROJECT_NAME"
    
    if [ -f "$SSH_KEY_PATH" ]; then
        print_success "Using existing SSH key at $SSH_KEY_PATH"
        return
    fi
    
    echo "Generating new SSH key pair..."
    ssh-keygen -t rsa -b 4096 -f "$SSH_KEY_PATH" -N "" -C "$PROJECT_NAME-$(date +%Y%m%d)"
    
    if [ -f "$SSH_KEY_PATH" ]; then
        chmod 600 "$SSH_KEY_PATH"
        chmod 644 "$SSH_KEY_PATH.pub"
        ssh-add "$SSH_KEY_PATH" 2>/dev/null || true
        print_success "SSH key pair generated successfully"
        echo "  Private key: $SSH_KEY_PATH"
        echo "  Public key: $SSH_KEY_PATH.pub"
    else
        print_error "Failed to generate SSH key pair"
        exit 1
    fi
}

# Collect configuration
collect_configuration() {
    print_step "Step 3: Configuration Setup" "Collecting deployment configuration"
    
    # Check if terraform.tfvars already exists and load values
    if [ -f "$TERRAFORM_DIR/terraform.tfvars" ]; then
        print_success "Loading existing configuration from terraform.tfvars"
        DOMAIN_NAME=$(grep '^domain_name' "$TERRAFORM_DIR/terraform.tfvars" | cut -d'"' -f2)
        INSTANCE_TYPE=$(grep '^instance_type' "$TERRAFORM_DIR/terraform.tfvars" | cut -d'"' -f2)
        CREATE_ROUTE53_ZONE=$(grep '^create_route53_zone' "$TERRAFORM_DIR/terraform.tfvars" | cut -d'=' -f2 | tr -d ' ')
        
        print_success "Using existing configuration:"
        echo "  Domain: $DOMAIN_NAME"
        echo "  Instance Type: $INSTANCE_TYPE"
        echo "  Manage DNS: $CREATE_ROUTE53_ZONE"
        return
    fi
    
    # Domain name
    echo "Enter your domain name (e.g., trading-platform.com):"
    read -p "Domain: " DOMAIN_NAME
    if [ -z "$DOMAIN_NAME" ]; then
        DOMAIN_NAME="trading-platform.local"
        print_warning "Using default domain: $DOMAIN_NAME"
    fi
    
    # Route53 management
    echo "Do you want Terraform to manage your Route53 DNS? (y/n)"
    read -p "Manage DNS: " -n 1 -r MANAGE_DNS
    echo
    CREATE_ROUTE53_ZONE="false"
    if [[ $MANAGE_DNS =~ ^[Yy]$ ]]; then
        CREATE_ROUTE53_ZONE="true"
    fi
    
    # Instance type
    echo "Select EC2 instance type:"
    echo "1) t3.micro (1 vCPU, 1GB RAM) - ~$8.50/month - Good for development"
    echo "2) t3.small (2 vCPU, 2GB RAM) - ~$16.79/month - Good for light production"
    echo "3) t3.medium (2 vCPU, 4GB RAM) - ~$33.58/month - Good for production"
    read -p "Choice (1-3): " -n 1 -r INSTANCE_CHOICE
    echo
    
    case $INSTANCE_CHOICE in
        1) INSTANCE_TYPE="t3.micro" ;;
        2) INSTANCE_TYPE="t3.small" ;;
        3) INSTANCE_TYPE="t3.medium" ;;
        *) INSTANCE_TYPE="t3.micro"
           print_warning "Invalid choice, using t3.micro"
           ;;
    esac
    
    # API Keys (optional)
    echo "Enter API keys (optional, press Enter to skip):"
    read -p "News API Key: " NEWS_API_KEY
    read -p "Alpha Vantage API Key: " ALPHA_VANTAGE_KEY
    
    # Generate secret key
    SECRET_KEY=$(openssl rand -base64 32 2>/dev/null || date +%s | sha256sum | base64 | head -c 32)
    
    # SSH allowed IPs
    CURRENT_IP=$(curl -s https://ipinfo.io/ip 2>/dev/null || echo "0.0.0.0")
    echo "Current IP address detected: $CURRENT_IP"
    read -p "Enter allowed IP addresses for SSH (comma-separated, or press Enter for current IP only): " SSH_IPS
    if [ -z "$SSH_IPS" ]; then
        SSH_ALLOWED_IPS="[\"$CURRENT_IP/32\"]"
    else
        # Convert comma-separated IPs to JSON array
        SSH_ALLOWED_IPS="[\"$(echo "$SSH_IPS" | sed 's/,/","/g')\"]"
    fi
    
    print_success "Configuration collected"
    echo "  Domain: $DOMAIN_NAME"
    echo "  Instance Type: $INSTANCE_TYPE"
    echo "  Manage DNS: $CREATE_ROUTE53_ZONE"
    echo "  SSH Access: $SSH_ALLOWED_IPS"
}

# Setup Terraform configuration
setup_terraform() {
    print_step "Step 4: Terraform Setup" "Configuring infrastructure as code"
    
    # Store deployment directory as absolute path before changing directories
    DEPLOYMENT_DIR="$(pwd)"
    
    cd $TERRAFORM_DIR
    
    # Check if terraform.tfvars already exists
    if [ -f "terraform.tfvars" ]; then
        print_success "Terraform configuration already exists, skipping setup"
        cd - >/dev/null
        return
    fi
    
    # Create terraform.tfvars
    cat > terraform.tfvars << EOF
# Trading Platform Terraform Configuration
# Generated by setup script on $(date)

aws_region = "$AWS_REGION"
environment = "production"
project_name = "$PROJECT_NAME"
domain_name = "$DOMAIN_NAME"
create_route53_zone = $CREATE_ROUTE53_ZONE
instance_type = "$INSTANCE_TYPE"
root_volume_size = 20
ec2_public_key = "$(cat $HOME/.ssh/$PROJECT_NAME.pub)"
ssh_allowed_ips = $SSH_ALLOWED_IPS
secret_key = "$SECRET_KEY"
news_api_key = "$NEWS_API_KEY"
alpha_vantage_key = "$ALPHA_VANTAGE_KEY"
enable_detailed_monitoring = false
backup_retention_days = 7

additional_tags = {
  ManagedBy = "terraform"
  SetupScript = "automated"
  CreatedDate = "$(date +%Y-%m-%d)"
}
EOF
    
    print_success "Terraform configuration created"
    echo "  Configuration file: terraform/terraform.tfvars"
    
    cd - >/dev/null
}

# Deploy infrastructure
deploy_infrastructure() {
    print_step "Step 5: Infrastructure Deployment" "Creating AWS resources with Terraform"
    
    cd $TERRAFORM_DIR
    
    # Check if infrastructure already exists
    if terraform show >/dev/null 2>&1; then
        print_success "Infrastructure already deployed, checking status..."
        
        # Get existing outputs
        if terraform output public_ip >/dev/null 2>&1; then
            EC2_HOST=$(terraform output -raw public_ip)
            APPLICATION_URL=$(terraform output -raw application_url)
            
            print_success "Using existing infrastructure"
            echo "  EC2 Instance IP: $EC2_HOST"
            echo "  Application URL: $APPLICATION_URL"
            
            # Save outputs for later use
            terraform output -json > "$DEPLOYMENT_DIR/terraform-outputs.json"
            
            cd - >/dev/null
            export EC2_HOST
            return
        fi
    fi
    
    # Initialize Terraform
    echo "Initializing Terraform..."
    terraform init
    
    # Plan infrastructure
    echo "Planning infrastructure changes..."
    terraform plan -out=tfplan
    
    echo ""
    print_warning "About to create AWS infrastructure. Estimated monthly cost: $8-35 depending on instance type."
    read -p "Continue with deployment? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_error "Deployment cancelled by user"
        exit 1
    fi
    
    # Apply infrastructure
    echo "Applying infrastructure changes..."
    terraform apply tfplan
    
    # Get outputs
    EC2_HOST=$(terraform output -raw public_ip)
    APPLICATION_URL=$(terraform output -raw application_url)
    
    # Save outputs for later use
    terraform output -json > "$DEPLOYMENT_DIR/terraform-outputs.json"
    
    print_success "Infrastructure deployed successfully"
    echo "  EC2 Instance IP: $EC2_HOST"
    echo "  Application URL: $APPLICATION_URL"
    
    cd - >/dev/null
    
    # Export for use in next steps
    export EC2_HOST
}

# Wait for instance to be ready
wait_for_instance() {
    print_step "Step 6: Instance Preparation" "Waiting for EC2 instance to be ready"
    
    echo "Waiting for instance to boot and run user-data script..."
    
    for i in {1..20}; do
        echo "  Attempt $i/20..."
        if ssh -i "$HOME/.ssh/$PROJECT_NAME" -o StrictHostKeyChecking=no -o ConnectTimeout=10 ec2-user@$EC2_HOST "docker --version" >/dev/null 2>&1; then
            print_success "Instance is ready"
            break
        fi
        
        if [ $i -eq 20 ]; then
            print_error "Instance not ready after 20 attempts"
            print_warning "The instance might still be setting up. You can check manually:"
            echo "  ssh -i $HOME/.ssh/$PROJECT_NAME ec2-user@$EC2_HOST"
            exit 1
        fi
        
        sleep 30
    done
}

# Build and deploy application
build_and_deploy() {
    print_step "Step 7: Application Deployment" "Building and deploying containers"
    
    # Set environment variables for the build script
    export AWS_REGION
    export EC2_HOST
    export SSH_KEY_PATH="$HOME/.ssh/$PROJECT_NAME"
    
    # Build and push images
    echo "Building and pushing Docker images..."
    ./build-and-push.sh
    
    # Deploy to EC2
    echo "Deploying application to EC2..."
    ./deploy.sh
    
    print_success "Application deployed successfully"
}

# Final verification
verify_deployment() {
    print_step "Step 8: Deployment Verification" "Verifying the deployment"
    
    echo "Running health checks..."
    
    # Wait a bit for services to fully start
    sleep 30
    
    # Check services
    FRONTEND_STATUS="❌"
    BACKEND_STATUS="❌"
    
    if curl -f -s "http://$EC2_HOST/health" >/dev/null 2>&1; then
        FRONTEND_STATUS="✅"
    fi
    
    if curl -f -s "http://$EC2_HOST:8000/" >/dev/null 2>&1; then
        BACKEND_STATUS="✅"
    fi
    
    echo "  Frontend: $FRONTEND_STATUS"
    echo "  Backend:  $BACKEND_STATUS"
    
    if [[ "$FRONTEND_STATUS" == "✅" && "$BACKEND_STATUS" == "✅" ]]; then
        print_success "All services are healthy"
    else
        print_warning "Some services may need more time to start"
        echo "You can monitor the deployment with:"
        echo "  ./monitor.sh"
    fi
}

# Generate documentation
generate_documentation() {
    print_step "Step 9: Documentation Generation" "Creating deployment documentation"
    
    if [ -f "$DEPLOYMENT_DIR/deployment-info.md" ]; then
        print_success "Deployment documentation already exists, updating..."
    fi
    
    cat > "$DEPLOYMENT_DIR/deployment-info.md" << EOF
# Trading Platform Deployment Information

**Deployment Date:** $(date)
**Deployed By:** $(whoami)

## Infrastructure Details
- **AWS Region:** $AWS_REGION
- **EC2 Instance Type:** $INSTANCE_TYPE
- **Instance IP:** $EC2_HOST
- **Domain:** $DOMAIN_NAME
- **Route53 Managed:** $CREATE_ROUTE53_ZONE

## Access Information
- **Application URL:** http://$EC2_HOST
- **API URL:** http://$EC2_HOST:8000
- **SSH Access:** ssh -i ~/.ssh/$PROJECT_NAME ec2-user@$EC2_HOST

## Management Commands
\`\`\`bash
# Monitor deployment
./deployment/scripts/monitor.sh

# Deploy updates
./deployment/scripts/deploy.sh

# Build and push new images
./deployment/scripts/build-and-push.sh

# SSH into server
ssh -i ~/.ssh/$PROJECT_NAME ec2-user@$EC2_HOST
\`\`\`

## Configuration Files
- Terraform config: \`terraform/terraform.tfvars\`
- Docker Compose: \`docker-compose.prod.yml\`
- SSH Keys: \`~/.ssh/$PROJECT_NAME\`

## Estimated Monthly Costs
- EC2 Instance: \$8-35 (depending on instance type)
- EBS Storage: \$1-2
- Route53: \$0.50
- **Total:** \$10-40/month

## Next Steps
1. Configure your domain DNS to point to: $EC2_HOST
2. Set up CloudFlare for SSL/CDN (recommended)
3. Configure GitHub Actions secrets for CI/CD
4. Monitor the deployment using the provided scripts

## Troubleshooting
- Check logs: \`docker-compose -f /opt/trading/docker-compose.prod.yml logs\`
- Restart services: \`docker-compose -f /opt/trading/docker-compose.prod.yml restart\`
- Health check: \`/opt/trading/health-check.sh\`
EOF
    
    print_success "Documentation generated"
    echo "  File: deployment/deployment-info.md"
}

# Setup GitHub Actions secrets (informational)
setup_github_actions_info() {
    print_step "Step 10: CI/CD Setup Instructions" "GitHub Actions configuration"
    
    echo "To enable automated deployments, add these secrets to your GitHub repository:"
    echo ""
    echo -e "${YELLOW}GitHub Repository → Settings → Secrets and variables → Actions${NC}"
    echo ""
    echo "Required secrets:"
    echo "  AWS_ACCESS_KEY_ID: (your AWS access key)"
    echo "  AWS_SECRET_ACCESS_KEY: (your AWS secret key)"
    echo "  EC2_HOST: $EC2_HOST"
    echo "  EC2_SSH_PRIVATE_KEY: (content of ~/.ssh/$PROJECT_NAME)"
    echo "  SECRET_KEY: $SECRET_KEY"
    echo "  DOMAIN_NAME: $DOMAIN_NAME"
    echo ""
    echo "Optional secrets:"
    echo "  NEWS_API_KEY: $NEWS_API_KEY"
    echo "  ALPHA_VANTAGE_KEY: $ALPHA_VANTAGE_KEY"
    echo "  SLACK_WEBHOOK: (for deployment notifications)"
    echo ""
    
    # Save secrets to a file for reference
    cat > "$DEPLOYMENT_DIR/github-secrets.txt" << EOF
# GitHub Actions Secrets Configuration
# Add these to your GitHub repository secrets

AWS_ACCESS_KEY_ID=<your-aws-access-key>
AWS_SECRET_ACCESS_KEY=<your-aws-secret-key>
EC2_HOST=$EC2_HOST
EC2_SSH_PRIVATE_KEY=<content-of-ssh-private-key>
SECRET_KEY=$SECRET_KEY
DOMAIN_NAME=$DOMAIN_NAME
NEWS_API_KEY=$NEWS_API_KEY
ALPHA_VANTAGE_KEY=$ALPHA_VANTAGE_KEY

# Optional
SLACK_WEBHOOK=<your-slack-webhook-url>
TF_STATE_BUCKET=<your-terraform-state-bucket>
EOF
    
    print_success "GitHub Actions configuration saved to deployment/github-secrets.txt"
}

# Final summary
print_summary() {
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                    🎉 DEPLOYMENT COMPLETED! 🎉                 ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${BLUE}🌐 Application Access:${NC}"
    echo "   Frontend: http://$EC2_HOST"
    echo "   Backend:  http://$EC2_HOST:8000"
    echo "   Health:   http://$EC2_HOST/health"
    echo ""
    echo -e "${BLUE}🔧 Management Commands:${NC}"
    echo "   Monitor:  ./deployment/scripts/monitor.sh"
    echo "   Deploy:   ./deployment/scripts/deploy.sh"
    echo "   SSH:      ssh -i ~/.ssh/$PROJECT_NAME ec2-user@$EC2_HOST"
    echo ""
    echo -e "${BLUE}💰 Estimated Monthly Cost: \$10-40${NC}"
    echo ""
    echo -e "${YELLOW}📋 Next Steps:${NC}"
    echo "   1. Configure DNS to point to: $EC2_HOST"
    echo "   2. Set up CloudFlare for SSL/CDN"
    echo "   3. Configure GitHub Actions secrets (see deployment/github-secrets.txt)"
    echo "   4. Monitor your deployment with ./deployment/scripts/monitor.sh"
    echo ""
    echo -e "${GREEN}✨ Happy Trading! ✨${NC}"
}

# Main function
main() {
    print_banner
    
    echo -e "${YELLOW}This script will set up the complete Trading Platform on AWS.${NC}"
    echo -e "${YELLOW}Estimated time: 10-15 minutes${NC}"
    echo -e "${YELLOW}Estimated cost: \$10-40/month${NC}"
    echo ""
    read -p "Continue with setup? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Setup cancelled."
        exit 0
    fi
    
    check_prerequisites
    generate_ssh_key
    collect_configuration
    setup_terraform
    deploy_infrastructure
    wait_for_instance
    build_and_deploy
    verify_deployment
    generate_documentation
    setup_github_actions_info
    print_summary
}

# Handle script interruption
trap 'echo -e "\n${RED}Setup interrupted. You may need to clean up AWS resources manually.${NC}"' INT

# Run main function
main "$@"