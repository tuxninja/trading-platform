#!/bin/bash
# Deploy Trading Platform to EC2 instance

set -e

# Configuration
EC2_HOST=${EC2_HOST:-}
EC2_USER=${EC2_USER:-ec2-user}
SSH_KEY_PATH=${SSH_KEY_PATH:-~/.ssh/trading-platform}
AWS_REGION=${AWS_REGION:-us-east-1}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}============================================${NC}"
    echo -e "${BLUE} Trading Platform Deployment Script${NC}"
    echo -e "${BLUE}============================================${NC}"
}

print_status() {
    echo -e "${YELLOW}📋 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    if [ -z "$EC2_HOST" ]; then
        print_error "EC2_HOST environment variable is not set"
        echo "Set it with: export EC2_HOST=your-ec2-ip-address"
        exit 1
    fi
    
    if [ ! -f "$SSH_KEY_PATH" ]; then
        print_error "SSH key not found at $SSH_KEY_PATH"
        exit 1
    fi
    
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI is not installed"
        exit 1
    fi
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        exit 1
    fi
    
    print_success "Prerequisites check passed"
}

# Test SSH connection
test_ssh_connection() {
    print_status "Testing SSH connection to $EC2_HOST..."
    
    if ssh -i $SSH_KEY_PATH -o StrictHostKeyChecking=no -o ConnectTimeout=10 $EC2_USER@$EC2_HOST "echo 'SSH connection successful'" >/dev/null 2>&1; then
        print_success "SSH connection successful"
    else
        print_error "Failed to connect to $EC2_HOST"
        exit 1
    fi
}

# Get latest image tags
get_latest_images() {
    print_status "Getting latest image information..."
    
    if [ -f "../../deployment/latest-images.env" ]; then
        source ../../deployment/latest-images.env
        print_success "Using images from latest build:"
        echo "  Backend: $BACKEND_IMAGE"
        echo "  Frontend: $FRONTEND_IMAGE"
    else
        # Use latest tags from ECR
        AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
        BACKEND_IMAGE="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/trading-platform-backend:latest"
        FRONTEND_IMAGE="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/trading-platform-frontend:latest"
        print_success "Using latest images from ECR"
    fi
}

# Create deployment package
create_deployment_package() {
    print_status "Creating deployment package..."
    
    # Create temporary deployment directory
    DEPLOY_DIR="/tmp/trading-platform-deploy-$(date +%s)"
    mkdir -p $DEPLOY_DIR
    
    # Copy docker-compose file
    cp ../../docker-compose.prod.yml $DEPLOY_DIR/
    
    # Update image references in docker-compose file
    sed -i "s|backend:.*|image: $BACKEND_IMAGE|g" $DEPLOY_DIR/docker-compose.prod.yml
    sed -i "s|frontend:.*|image: $FRONTEND_IMAGE|g" $DEPLOY_DIR/docker-compose.prod.yml
    
    # Remove build contexts since we're using pre-built images
    sed -i '/build:/,+2d' $DEPLOY_DIR/docker-compose.prod.yml
    
    print_success "Deployment package created at $DEPLOY_DIR"
}

# Deploy to EC2
deploy_to_ec2() {
    print_status "Deploying to EC2 instance..."
    
    # Copy deployment files
    print_status "Copying deployment files..."
    scp -i $SSH_KEY_PATH -o StrictHostKeyChecking=no \
        $DEPLOY_DIR/docker-compose.prod.yml \
        $EC2_USER@$EC2_HOST:/opt/trading/
    
    # Execute deployment on remote server
    print_status "Executing deployment on remote server..."
    ssh -i $SSH_KEY_PATH -o StrictHostKeyChecking=no $EC2_USER@$EC2_HOST << EOF
        set -e
        cd /opt/trading
        
        echo "🔐 Logging into ECR..."
        aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin \$(aws sts get-caller-identity --query Account --output text).dkr.ecr.$AWS_REGION.amazonaws.com
        
        echo "📋 Current container status:"
        docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
        
        echo "💾 Creating backup..."
        ./backup.sh
        
        echo "🛑 Stopping current services..."
        docker-compose -f docker-compose.prod.yml down || true
        
        echo "📥 Pulling latest images..."
        docker pull $BACKEND_IMAGE
        docker pull $FRONTEND_IMAGE
        
        echo "🚀 Starting new services..."
        docker-compose -f docker-compose.prod.yml up -d
        
        echo "⏳ Waiting for services to start..."
        sleep 30
        
        echo "📋 New container status:"
        docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
        
        echo "🧹 Cleaning up old images..."
        docker image prune -f
        
        echo "✅ Deployment completed!"
EOF
    
    print_success "Deployment executed successfully"
}

# Health check
perform_health_check() {
    print_status "Performing health check..."
    
    # Wait a bit more for services to fully start
    sleep 15
    
    # Check application health
    for i in {1..5}; do
        if curl -f -s "http://$EC2_HOST/health" >/dev/null 2>&1; then
            print_success "Frontend health check passed"
            break
        else
            print_status "Waiting for frontend to be ready... (attempt $i/5)"
            sleep 10
        fi
    done
    
    # Check API health
    for i in {1..5}; do
        if curl -f -s "http://$EC2_HOST:8000/" >/dev/null 2>&1; then
            print_success "Backend health check passed"
            break
        else
            print_status "Waiting for backend to be ready... (attempt $i/5)"
            sleep 10
        fi
    done
    
    # Final status check
    ssh -i $SSH_KEY_PATH -o StrictHostKeyChecking=no $EC2_USER@$EC2_HOST << 'EOF'
        echo "🔍 Final status check:"
        echo "Container status:"
        docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
        echo ""
        echo "Health check script result:"
        /opt/trading/health-check.sh
EOF
}

# Cleanup
cleanup() {
    print_status "Cleaning up temporary files..."
    if [ -n "$DEPLOY_DIR" ] && [ -d "$DEPLOY_DIR" ]; then
        rm -rf $DEPLOY_DIR
    fi
    print_success "Cleanup completed"
}

# Main deployment process
main() {
    print_header
    
    check_prerequisites
    test_ssh_connection
    get_latest_images
    create_deployment_package
    deploy_to_ec2
    perform_health_check
    cleanup
    
    echo ""
    print_success "🎉 Deployment completed successfully!"
    echo ""
    echo -e "${GREEN}📊 Application URLs:${NC}"
    echo "  Frontend: http://$EC2_HOST"
    echo "  Backend API: http://$EC2_HOST:8000"
    echo "  Health Check: http://$EC2_HOST/health"
    echo ""
    echo -e "${YELLOW}📋 Next steps:${NC}"
    echo "  1. Test the application in your browser"
    echo "  2. Check logs: ssh -i $SSH_KEY_PATH $EC2_USER@$EC2_HOST 'cd /opt/trading && docker-compose logs -f'"
    echo "  3. Monitor performance: ssh -i $SSH_KEY_PATH $EC2_USER@$EC2_HOST 'htop'"
    echo ""
}

# Handle script interruption
trap cleanup EXIT

# Run main function
main "$@"