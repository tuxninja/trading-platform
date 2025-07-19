#!/bin/bash
# Build and push Docker images to ECR

set -e

# Configuration
AWS_REGION=${AWS_REGION:-us-east-1}
PROJECT_NAME=${PROJECT_NAME:-trading-platform}
ECR_REPOSITORY_BACKEND=${ECR_REPOSITORY_BACKEND:-trading-platform-backend}
ECR_REPOSITORY_FRONTEND=${ECR_REPOSITORY_FRONTEND:-trading-platform-frontend}
IMAGE_TAG=${IMAGE_TAG:-latest}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Building and pushing Trading Platform images${NC}"

# Check prerequisites
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI is not installed${NC}"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed${NC}"
    exit 1
fi

# Get AWS account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
if [ -z "$AWS_ACCOUNT_ID" ]; then
    echo -e "${RED}❌ Unable to get AWS account ID. Check your AWS credentials.${NC}"
    exit 1
fi

echo -e "${YELLOW}📋 Configuration:${NC}"
echo "  AWS Region: $AWS_REGION"
echo "  AWS Account: $AWS_ACCOUNT_ID"
echo "  Backend Repository: $ECR_REPOSITORY_BACKEND"
echo "  Frontend Repository: $ECR_REPOSITORY_FRONTEND"
echo "  Image Tag: $IMAGE_TAG"

# ECR URLs
ECR_BACKEND_URL="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY_BACKEND"
ECR_FRONTEND_URL="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY_FRONTEND"

# Create ECR repositories if they don't exist
echo -e "${YELLOW}🔧 Ensuring ECR repositories exist...${NC}"
aws ecr describe-repositories --repository-names $ECR_REPOSITORY_BACKEND --region $AWS_REGION >/dev/null 2>&1 || \
    aws ecr create-repository --repository-name $ECR_REPOSITORY_BACKEND --region $AWS_REGION >/dev/null

aws ecr describe-repositories --repository-names $ECR_REPOSITORY_FRONTEND --region $AWS_REGION >/dev/null 2>&1 || \
    aws ecr create-repository --repository-name $ECR_REPOSITORY_FRONTEND --region $AWS_REGION >/dev/null

# Login to ECR
echo -e "${YELLOW}🔐 Logging into ECR...${NC}"
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Build backend image
echo -e "${YELLOW}🏗️  Building backend image...${NC}"
cd ../../backend
docker build --platform linux/amd64 -t $ECR_BACKEND_URL:$IMAGE_TAG .
docker tag $ECR_BACKEND_URL:$IMAGE_TAG $ECR_BACKEND_URL:latest

# Build frontend image
echo -e "${YELLOW}🏗️  Building frontend image...${NC}"
cd ../frontend
docker build --platform linux/amd64 -t $ECR_FRONTEND_URL:$IMAGE_TAG .
docker tag $ECR_FRONTEND_URL:$IMAGE_TAG $ECR_FRONTEND_URL:latest

# Push images
echo -e "${YELLOW}📤 Pushing backend image...${NC}"
docker push $ECR_BACKEND_URL:$IMAGE_TAG
docker push $ECR_BACKEND_URL:latest

echo -e "${YELLOW}📤 Pushing frontend image...${NC}"
docker push $ECR_FRONTEND_URL:$IMAGE_TAG
docker push $ECR_FRONTEND_URL:latest

# Clean up local images to save space
echo -e "${YELLOW}🧹 Cleaning up local images...${NC}"
docker image prune -f

echo -e "${GREEN}✅ Build and push completed successfully!${NC}"
echo -e "${GREEN}📦 Images pushed:${NC}"
echo "  Backend: $ECR_BACKEND_URL:$IMAGE_TAG"
echo "  Frontend: $ECR_FRONTEND_URL:$IMAGE_TAG"

# Output for use in other scripts
echo "BACKEND_IMAGE=$ECR_BACKEND_URL:$IMAGE_TAG" > ../deployment/latest-images.env
echo "FRONTEND_IMAGE=$ECR_FRONTEND_URL:$IMAGE_TAG" >> ../deployment/latest-images.env

echo -e "${GREEN}🎉 Build and push process completed!${NC}"