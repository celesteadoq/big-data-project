variable "db_name" {
  description = "Nome do banco de dados relacional para os dados de trânsito"
  type        = string
  default     = "db_transito_brasil"
}

variable "db_user" {
  description = "Usuário master do PostgreSQL"
  type        = string
  default     = "postgres"
}

variable "db_password" {
  description = "Senha de acesso ao banco PostgreSQL"
  type        = string
  sensitive   = true
}

variable "db_port" {
  description = "Porta de acesso ao PostgreSQL"
  type        = number
  default     = 5432
}

variable "minio_root_user" {
  description = "Usuário administrador do MinIO"
  type        = string
  default     = "minio_admin"
}

variable "minio_root_password" {
  description = "Senha do administrador do MinIO"
  type        = string
  sensitive   = true
}