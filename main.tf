# Rede isolada para os serviços
resource "docker_network" "transito_network" {
  name = "rede_dados_transito"
}

# Volume persistente para o Banco de Dados
resource "docker_volume" "postgres_data" {
  name = "vol_postgres_transito"
}

# Volume persistente para o Data Lake MinIO
resource "docker_volume" "minio_data" {
  name = "vol_minio_transito"
}

# --- POSTGRESQL (Banco Relacional) ---
resource "docker_image" "postgres_image" {
  name         = "postgres:15-alpine"
  keep_locally = true
}

resource "docker_container" "postgres_db" {
  name  = "postgres_transito"
  image = docker_image.postgres_image.image_id

  networks_advanced {
    name = docker_network.transito_network.name
  }

  mounts {
    target = "/var/lib/postgresql/data"
    source = docker_volume.postgres_data.name
    type   = "volume"
  }

  ports {
    internal = 5432
    external = var.db_port
     ip       = "127.0.0.1"
  }

  env = [
    "POSTGRES_DB=${var.db_name}",
    "POSTGRES_USER=${var.db_user}",
    "POSTGRES_PASSWORD=${var.db_password}"
  ]
}

# --- MINIO (Data Lake S3 Local) ---
resource "docker_image" "minio_image" {
  name         = "coollabsio/minio:latest"
  keep_locally = true
}

resource "docker_container" "minio_s3" {
  name    = "minio_datalake"
  image   = docker_image.minio_image.image_id
  command = ["server", "/data", "--console-address", ":9001"]

  networks_advanced {
    name = docker_network.transito_network.name
  }

  mounts {
    target = "/data"
    source = docker_volume.minio_data.name
    type   = "volume"
  }

  ports {
    internal = 9000
    external = 9000
     ip       = "127.0.0.1"
  }

  ports {
    internal = 9001
    external = 9001
     ip       = "127.0.0.1"
  }

  env = [
    "MINIO_ROOT_USER=${var.minio_root_user}",
    "MINIO_ROOT_PASSWORD=${var.minio_root_password}"
  ]
}