#!/bin/bash

# Setup script for automatic GitHub secret updates
# This configures Terraform to automatically update EC2_HOST secret when IP changes

set -e

echo "🔧 Setting up automatic GitHub secret updates..."

# Check if running in terraform directory
if [ ! -f "main.tf" ]; then
    echo "❌ Please run this script from the terraform directory"
    exit 1
fi

# Get GitHub repository name
echo "📝 Please provide your GitHub repository name (format: username/repository-name):"
read -p "Repository: " GITHUB_REPO

if [ -z "$GITHUB_REPO" ]; then
    echo "❌ Repository name is required"
    exit 1
fi

# Get GitHub token (will be hidden)
echo "🔑 Please provide your GitHub Personal Access Token:"
echo "   (Create one at: https://github.com/settings/personal-access-tokens/new)"
echo "   Required scopes: repo (for private repos) or public_repo (for public repos)"
read -s -p "Token: " GITHUB_TOKEN
echo

if [ -z "$GITHUB_TOKEN" ]; then
    echo "❌ GitHub token is required"
    exit 1
fi

# Extract owner from repo name
GITHUB_OWNER=$(echo "$GITHUB_REPO" | cut -d'/' -f1)
REPO_NAME=$(echo "$GITHUB_REPO" | cut -d'/' -f2)

# Create terraform.tfvars entry
echo "📄 Updating terraform.tfvars..."
if ! grep -q "github_repository" terraform.tfvars 2>/dev/null; then
    echo "github_repository = \"$GITHUB_REPO\"" >> terraform.tfvars
    echo "auto_update_github_secrets = true" >> terraform.tfvars
else
    echo "✅ GitHub configuration already exists in terraform.tfvars"
fi

# Set environment variables for current session
export GITHUB_TOKEN="$GITHUB_TOKEN"
export GITHUB_OWNER="$GITHUB_OWNER"

# Create .env file for future use
echo "💾 Creating .env file for GitHub credentials..."
cat > .env << EOF
# GitHub configuration for Terraform
export GITHUB_TOKEN="$GITHUB_TOKEN"
export GITHUB_OWNER="$GITHUB_OWNER"

# Usage: source .env before running terraform commands
EOF

# Make .env file secure
chmod 600 .env

# Initialize terraform with new provider
echo "🔄 Initializing Terraform with GitHub provider..."
terraform init

echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Source the environment: source .env"
echo "2. Run terraform plan to see changes"
echo "3. Run terraform apply to enable auto-updates"
echo ""
echo "⚠️  Important:"
echo "- Keep .env file secure and never commit it to git"
echo "- The GitHub token needs 'repo' or 'public_repo' scope"
echo "- EC2_HOST secret will be automatically updated when IP changes"
echo ""
echo "🎉 Your GitHub Actions will now automatically get the latest EC2 IP!"