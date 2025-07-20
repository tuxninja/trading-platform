# Trading Platform Terraform Outputs

output "instance_id" {
  description = "ID of the EC2 instance"
  value       = aws_instance.main.id
}

output "public_ip" {
  description = "Public IP address of the EC2 instance"
  value       = aws_eip.main.public_ip
}

output "public_dns" {
  description = "Public DNS name of the EC2 instance"
  value       = aws_instance.main.public_dns
}

output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.main.id
}

output "subnet_id" {
  description = "ID of the public subnet"
  value       = aws_subnet.public.id
}

output "security_group_id" {
  description = "ID of the web security group"
  value       = aws_security_group.web.id
}

output "ecr_repository_url_backend" {
  description = "URL of the backend ECR repository"
  value       = aws_ecr_repository.backend.repository_url
}

output "ecr_repository_url_frontend" {
  description = "URL of the frontend ECR repository"
  value       = aws_ecr_repository.frontend.repository_url
}

output "ecr_repository_url_main" {
  description = "URL of the main ECR repository"
  value       = aws_ecr_repository.main.repository_url
}

output "route53_zone_id" {
  description = "ID of the Route53 hosted zone"
  value       = var.create_route53_zone ? aws_route53_zone.main[0].zone_id : null
}

output "route53_name_servers" {
  description = "Name servers for the Route53 hosted zone"
  value       = var.create_route53_zone ? aws_route53_zone.main[0].name_servers : null
}

output "application_url" {
  description = "URL to access the application"
  value       = var.create_route53_zone ? "https://${var.domain_name}" : "http://${aws_eip.main.public_ip}"
}

output "api_url" {
  description = "URL to access the API"
  value       = var.create_route53_zone ? "https://api.${var.domain_name}" : "http://${aws_eip.main.public_ip}:8000"
}

output "ssh_command" {
  description = "SSH command to connect to the instance"
  value       = "ssh -i ~/.ssh/${var.project_name} ec2-user@${aws_eip.main.public_ip}"
}

output "github_actions_cidrs_count" {
  description = "Number of GitHub Actions CIDR ranges allowed SSH access"
  value       = length(local.github_actions_friendly_cidrs)
}

output "all_ssh_allowed_cidrs" {
  description = "All SSH allowed CIDR ranges"
  value       = local.all_ssh_allowed_ipv4
}

# Cost Estimation Output
output "estimated_monthly_cost" {
  description = "Estimated monthly cost breakdown"
  value = {
    ec2_instance     = var.instance_type == "t3.micro" ? "$8.50" : var.instance_type == "t3.small" ? "$16.79" : "varies"
    ebs_storage      = "$${var.root_volume_size * 0.08}"
    elastic_ip       = "$0.00 (while attached)"
    route53_zone     = var.create_route53_zone ? "$0.50" : "$0.00"
    data_transfer    = "$0.00 - $2.00 (estimated)"
    ecr_storage      = "$0.00 - $0.50 (under 500MB free)"
    total_estimated  = var.instance_type == "t3.micro" ? "$10-12" : "$18-22"
  }
}