#!/bin/bash

# Script to update EC2 security group with GitHub Actions IP ranges
# Usage: ./update_security_group.sh <security-group-id>

SECURITY_GROUP_ID="$1"

if [ -z "$SECURITY_GROUP_ID" ]; then
    echo "Usage: $0 <security-group-id>"
    echo "Example: $0 sg-1234567890abcdef0"
    exit 1
fi

echo "🔄 Updating security group $SECURITY_GROUP_ID with GitHub Actions IP ranges..."

# Get GitHub's IP ranges
GITHUB_IPS=$(curl -s https://api.github.com/meta | jq -r '.actions[]')

# Add each IP range to the security group
for ip_range in $GITHUB_IPS; do
    echo "Adding IP range: $ip_range"
    aws ec2 authorize-security-group-ingress \
        --group-id "$SECURITY_GROUP_ID" \
        --protocol tcp \
        --port 22 \
        --cidr "$ip_range" \
        --description "GitHub Actions SSH - $ip_range" \
        2>/dev/null || echo "  (already exists or failed)"
done

echo "✅ Security group update completed"
echo "🔍 Current SSH rules:"
aws ec2 describe-security-groups \
    --group-ids "$SECURITY_GROUP_ID" \
    --query 'SecurityGroups[0].IpPermissions[?FromPort==`22`]' \
    --output table