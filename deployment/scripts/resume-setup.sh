#!/bin/bash
# Resume setup script from after Terraform deployment

set -e

# Configuration from your previous run
PROJECT_NAME="trading-platform"
AWS_REGION="us-east-1"
EC2_HOST="35.153.246.131"  # From your terraform output
DOMAIN_NAME="divestifi.com"
INSTANCE_TYPE="t3.small"
CREATE_ROUTE53_ZONE="false"
SSH_KEY_PATH="$HOME/.ssh/trading-platform"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

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

# Store deployment directory
DEPLOYMENT_DIR="$(pwd)"

# Wait for instance to be ready
wait_for_instance() {
    print_step "Step 6: Instance Preparation" "Waiting for EC2 instance to be ready"
    
    echo "Waiting for instance to boot and run user-data script..."
    
    for i in {1..20}; do
        echo "  Attempt $i/20..."
        if ssh -i "$SSH_KEY_PATH" -o StrictHostKeyChecking=no -o ConnectTimeout=10 ec2-user@$EC2_HOST "docker --version" >/dev/null 2>&1; then
            print_success "Instance is ready"
            break
        fi
        
        if [ $i -eq 20 ]; then
            print_error "Instance not ready after 20 attempts"
            print_warning "The instance might still be setting up. You can check manually:"
            echo "  ssh -i $SSH_KEY_PATH ec2-user@$EC2_HOST"
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
    export SSH_KEY_PATH
    
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
    
    SECRET_KEY=$(openssl rand -base64 32 2>/dev/null || date +%s | sha256sum | base64 | head -c 32)
    
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
    
    SECRET_KEY=$(openssl rand -base64 32)
    
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
    echo "  NEWS_API_KEY: (your news api key)"
    echo "  ALPHA_VANTAGE_KEY: (your alpha vantage key)"
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
    echo -e "${BLUE}💰 Estimated Monthly Cost: \$15-20${NC}"
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
    echo -e "${BLUE}🚀 Resuming Trading Platform Setup${NC}"
    echo -e "${YELLOW}Infrastructure already deployed, continuing from application deployment...${NC}"
    echo ""
    
    wait_for_instance
    build_and_deploy
    verify_deployment
    generate_documentation
    setup_github_actions_info
    print_summary
}

# Run main function
main "$@"