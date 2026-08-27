# CloudFormation templates

This directory bundles the Raster Vision CloudFormation assets needed by agents that are preparing AWS Batch resources without reopening a source checkout.

- `batch-environment-template.yml` creates the Batch service role, spot fleet role, instance role/profile, security group, CPU/GPU compute environments, queues, optional ECR repository, and hosted/custom CPU/GPU job definitions.
- `job-definition-template.yml` creates project- or user-scoped CPU and GPU Batch job definitions that point at an ECR repository/tag.

Use these templates only after confirming the AWS account, region, VPC, subnet IDs, EC2 key pair, IAM permissions, and instance quotas. Creating a stack mutates cloud infrastructure and can incur costs.
