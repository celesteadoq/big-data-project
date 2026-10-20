output "postgres_connection_string" {
  description = "String de conexão para carregar os CSVs processados no Postgres via Python/Pandas"
  value       = "postgresql://${var.db_user}:${var.db_password}@localhost:${var.db_port}/${var.db_name}"
  sensitive   = true
}

output "minio_api_endpoint" {
  description = "Endpoint S3 do MinIO"
  value       = "http://localhost:9000"
}

output "minio_console_url" {
  description = "Interface web do MinIO para gerenciamento de buckets"
  value       = "http://localhost:9001"
}