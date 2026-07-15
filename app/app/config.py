"""
Configuration loader.

In production (ECS), these environment variables are injected by the task
definition from AWS Secrets Manager -- see terraform/secrets.tf and
terraform/ecs.tf. Locally, they come from docker-compose.yml / a .env file.
Nothing sensitive is ever hardcoded or committed to the repo.
"""

import os


def get_database_url() -> str:
    user = os.environ.get("DB_USER", "postgres")
    password = os.environ.get("DB_PASSWORD", "postgres")
    host = os.environ.get("DB_HOST", "localhost")
    port = os.environ.get("DB_PORT", "5432")
    name = os.environ.get("DB_NAME", "job_tracker")
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{name}"
