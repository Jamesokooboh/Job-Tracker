# Job Application Tracker — Deployed on AWS ECS Fargate

A small FastAPI + Postgres API for tracking job applications (company, role,
status, notes), built primarily as a vehicle to demonstrate a real,
production-shaped DevOps pipeline: containerization → Infrastructure as Code
→ CI/CD → secrets management → monitoring.

**What this proves:** I can take a working application and get it into AWS
safely and repeatably — not just `docker run` on a laptop, but with locked-down
networking, no hardcoded secrets, automated testing gates, an approval step
before infra changes, and alerting when something breaks.

## Architecture

```
Internet
   │
   ▼
Application Load Balancer  (public subnet)
   │  :80 → :8000
   ▼
ECS Fargate Service        (private subnet, autoscales 1-3 tasks on CPU)
   │  reads secrets from Secrets Manager at container start
   ▼
RDS Postgres                (private subnet, only reachable from ECS tasks)
```

- **No public IPs** on the app or database — only the ALB is internet-facing.
- **Security groups** are chained: internet → ALB → ECS → RDS, each layer
  only accepts traffic from the layer in front of it.
- **Secrets** (DB credentials) live in AWS Secrets Manager and are injected
  into the container at start time — never in the image, repo, or env files
  that get committed.
- **CloudWatch alarms** watch for 5xx spikes, unhealthy targets, and
  sustained high CPU, and notify an SNS email topic.

## Repo structure

```
job-tracker/
├── app/                     FastAPI service
│   ├── app/                 application code
│   ├── tests/                pytest suite (runs against in-memory SQLite in CI)
│   ├── Dockerfile            multi-stage, non-root, small final image
│   └── requirements*.txt
├── terraform/                all AWS infrastructure
│   ├── backend.tf             S3 + DynamoDB remote state
│   ├── vpc.tf                 VPC, public/private subnets, NAT
│   ├── security_groups.tf     ALB -> ECS -> RDS traffic chaining
│   ├── ecr.tf                 image repository + lifecycle policy
│   ├── ecs.tf                 cluster, task definition, service, autoscaling
│   ├── alb.tf                 load balancer, target group, listener
│   ├── rds.tf                 Postgres instance
│   ├── secrets.tf             Secrets Manager entry for DB credentials
│   ├── iam.tf                 least-privilege execution/task roles
│   ├── monitoring.tf          CloudWatch alarms + SNS topic
│   ├── variables.tf / outputs.tf
├── .github/workflows/
│   ├── ci.yaml                 lint + test on every PR
│   └── deploy.yaml             build → push → terraform apply (approval-gated) → deploy
└── docker-compose.yml          local dev: app + postgres
```

## Running it locally

```bash
docker compose up --build
# API docs: http://localhost:8000/docs
# Health check: http://localhost:8000/health
```

## Deploying to AWS

**One-time setup (manual, before CI can run):**

1. Create the Terraform state backend:
   ```bash
   aws s3api create-bucket --bucket <your-unique-bucket-name> --region us-east-1
   aws dynamodb create-table --table-name job-tracker-tf-locks \
     --attribute-definitions AttributeName=LockID,AttributeType=S \
     --key-schema AttributeName=LockID,KeyType=HASH \
     --billing-mode PAY_PER_REQUEST
   ```
   Update the bucket name in `terraform/backend.tf`.

2. Create an IAM role for GitHub Actions to assume via OIDC (no long-lived
   AWS access keys stored in the repo), and add its ARN as the
   `AWS_DEPLOY_ROLE_ARN` repository secret.

3. In the repo's Settings → Environments, create a `production` environment
   and require a reviewer — this is the manual approval gate before any
   `terraform apply` runs.

4. Update `terraform/variables.tf` defaults: `alert_email`, and review
   `db_instance_class` / `task_cpu` / `task_memory` for your budget.

**After that, every push to `main`:**

1. `ci.yaml` runs lint + tests.
2. `deploy.yaml` builds the image, pushes it to ECR tagged with the commit
   SHA, waits for manual approval, then runs `terraform plan`/`apply` to
   roll the ECS service onto the new image, and waits for the service to
   stabilize.

## Cost notes

This is sized to be cheap to run for a portfolio demo (~$40–60/month):
single NAT gateway, `db.t4g.micro`, `256/512` Fargate task, single AZ RDS.
For a "real" production setup you'd want Multi-AZ RDS, a NAT gateway per AZ,
and `deletion_protection = true` — noted inline in `rds.tf` where those
tradeoffs are made, so it's clear these are intentional cost decisions for a
demo environment, not oversights.

## What I'd add next

- HTTPS on the ALB (ACM cert + Route 53 domain)
- A staging environment before production in the deploy workflow
- Terratest coverage for the Terraform modules
- A lightweight frontend
