#!/bin/bash
# Production diagnostics runner
# This script will deploy and run the troubleshooting script on the production server

echo "🔍 Deploying production diagnostics to EC2..."

# Check if we have the required secrets/environment variables
if [ -z "$EC2_HOST" ] || [ -z "$EC2_SSH_PRIVATE_KEY" ]; then
    echo "❌ Missing required environment variables:"
    echo "   EC2_HOST - The production server IP/hostname"
    echo "   EC2_SSH_PRIVATE_KEY - SSH private key for EC2 access"
    echo ""
    echo "To run diagnostics on production server:"
    echo "1. Set environment variables:"
    echo "   export EC2_HOST='your-ec2-ip'"
    echo "   export EC2_SSH_PRIVATE_KEY='your-private-key'"
    echo "2. Run this script again"
    echo ""
    echo "Or manually run on the production server:"
    echo "   scp troubleshoot_production.sh ec2-user@your-ec2-ip:~/"
    echo "   ssh ec2-user@your-ec2-ip 'chmod +x ~/troubleshoot_production.sh && ~/troubleshoot_production.sh'"
    exit 1
fi

# Create private key file
echo "$EC2_SSH_PRIVATE_KEY" > private_key.pem
chmod 600 private_key.pem

# Test SSH connectivity
echo "🔐 Testing SSH connectivity to $EC2_HOST..."
if ! ssh -i private_key.pem -o StrictHostKeyChecking=no -o ConnectTimeout=10 -o BatchMode=yes ec2-user@$EC2_HOST "echo 'SSH connection successful'"; then
    echo "❌ Cannot connect to production server"
    rm private_key.pem
    exit 1
fi

echo "✅ SSH connection verified"

# Transfer troubleshooting script
echo "📄 Transferring troubleshooting script..."
if scp -i private_key.pem -o StrictHostKeyChecking=no troubleshoot_production.sh ec2-user@$EC2_HOST:~/; then
    echo "✅ Script transferred successfully"
else
    echo "❌ Failed to transfer script"
    rm private_key.pem
    exit 1
fi

# Run diagnostics on production server
echo "🚀 Running production diagnostics..."
ssh -i private_key.pem -o StrictHostKeyChecking=no ec2-user@$EC2_HOST << 'EOF'
echo "🔍 Starting production diagnostics on $(hostname)..."
chmod +x ~/troubleshoot_production.sh
~/troubleshoot_production.sh
echo ""
echo "🔍 Diagnostics complete. Check the output above for issues."
EOF

# Cleanup
rm private_key.pem

echo ""
echo "✅ Production diagnostics completed"
echo "Review the output above to identify the root cause of 502/504 errors"