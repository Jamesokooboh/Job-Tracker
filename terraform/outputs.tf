output "alb_dns_name" {
  description = "Public URL of the load balancer -- hit /health or /docs here"
  value       = aws_lb.main.dns_name
}

output "ecr_repository_url" {
  description = "Push images here from CI"
  value       = aws_ecr_repository.app.repository_url
}

output "ecs_cluster_name" {
  value = aws_ecs_cluster.main.name
}

output "ecs_service_name" {
  value = aws_ecs_service.app.name
}

output "rds_endpoint" {
  description = "Not publicly reachable -- for reference only"
  value       = aws_db_instance.main.address
}
