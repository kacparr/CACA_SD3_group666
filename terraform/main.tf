terraform {
  required_version = ">= 1.5.0"
  required_providers {
    render = {
      source  = "render-oss/render"
      version = "1.9.1"
    }
  }
}

variable "render_api_key" {
  type        = string
  sensitive   = true
}
variable "render_user_id" {
  type        = string
  sensitive   = true
}
variable "postgres_dbname" {
  type        = string
  sensitive   = true 
}
variable "postgres_username" {
  type        = string
  sensitive   = true
}


provider "render" {
  api_key = var.render_api_key
  owner_id = var.render_user_id
}

resource "render_postgres" "db" {
  name    = "example-postgres"
  plan    = "free"
  region  = "frankfurt"
  version = "18"

  database_name = var.postgres_dbname
  database_user = var.postgres_username

  high_availability_enabled = false
}

resource "render_web_service" "app" {
  name               = "task2-app"
  plan               = "free"
  region             = "frankfurt"

  runtime_source = {
    image =  {
      image_url = "ghcr.io/kacparr/caca_sd3_group666"
      tag = "latest"
    }
  }


  env_vars = {
    # SQLAlchemy + psycopg2-binary==2.9.9
    DATABASE_URL = {
      value = replace(
        render_postgres.db.connection_info.internal_connection_string,
        "/^postgres(ql)?:/",
        "postgresql+psycopg2:"
      )
    }
    PORT = {
      value = "5000"
    }
  }
}


output "service_id" {
  description = "Render Web Service ID - GitHub Actions"
  value       = render_web_service.app.id
}

output "service_url" {
  description = "Public application URL"
  value       = render_web_service.app.url
}

output "database_internal_url" {
  description = "Internal PostgreSQL URL"
  value       = render_postgres.db.connection_info.internal_connection_string
  sensitive   = true
}

output "database_external_url" {
  description = "External PostgreSQL URL"
  value       = render_postgres.db.connection_info.external_connection_string
  sensitive   = true
}
