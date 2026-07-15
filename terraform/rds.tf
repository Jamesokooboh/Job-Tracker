resource "aws_db_subnet_group" "main" {
  name       = "${var.project_name}-db-subnets"
  subnet_ids = aws_subnet.private[*].id
  tags       = { Name = "${var.project_name}-db-subnets" }
}

resource "random_password" "db_password" {
  length  = 24
  special = false # keep it simple to avoid connection-string escaping issues
}

resource "aws_db_instance" "main" {
  identifier     = "${var.project_name}-db"
  engine         = "postgres"
  engine_version = "16.4"
  instance_class = var.db_instance_class

  allocated_storage     = 20
  max_allocated_storage = 100 # enables storage autoscaling instead of over-provisioning up front
  storage_type          = "gp3"
  storage_encrypted     = true

  db_name  = var.db_name
  username = var.db_username
  password = random_password.db_password.result

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  publicly_accessible    = false

  multi_az                  = false # set true for prod HA; kept off here to control cost
  backup_retention_period   = 7
  auto_minor_version_upgrade = true
  deletion_protection       = false # flip to true once this is a real prod DB
  skip_final_snapshot       = true  # flip to false + set final_snapshot_identifier for prod

  tags = { Name = "${var.project_name}-db" }
}
