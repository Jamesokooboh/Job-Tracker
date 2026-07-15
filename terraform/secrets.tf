# The ECS task pulls these values at container-start time via the
# "secrets" block in the task definition -- credentials are never
# baked into the image, the repo, or plain env vars.
resource "aws_secretsmanager_secret" "db_credentials" {
  name        = "${var.project_name}/db-credentials"
  description = "Postgres credentials for the job tracker API"
}

resource "aws_secretsmanager_secret_version" "db_credentials" {
  secret_id = aws_secretsmanager_secret.db_credentials.id
  secret_string = jsonencode({
    DB_USER     = var.db_username
    DB_PASSWORD = random_password.db_password.result
    DB_HOST     = aws_db_instance.main.address
    DB_PORT     = tostring(aws_db_instance.main.port)
    DB_NAME     = var.db_name
  })
}
