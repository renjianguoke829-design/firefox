#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="$ROOT_DIR/docker/docker-compose.yml"

command_exists() {
  command -v "$1" >/dev/null 2>&1
}

install_docker() {
  if command_exists docker; then
    echo "Docker already installed"
    return
  fi

  echo "Installing Docker..."
  curl -fsSL https://get.docker.com | sh
  sudo usermod -aG docker "$USER" || true
}

install_compose() {
  if docker compose version >/dev/null 2>&1; then
    echo "Docker Compose already installed"
    return
  fi

  echo "Installing Docker Compose plugin..."
  sudo apt-get update
  sudo apt-get install -y docker-compose-plugin
}

create_directories() {
  echo "Creating local directories..."
  mkdir -p "$ROOT_DIR/docker/data/postgres"
  mkdir -p "$ROOT_DIR/docker/data/qinglong"
}

start_services() {
  echo "Starting services..."
  docker compose -f "$COMPOSE_FILE" up -d
}

print_endpoints() {
  local host="localhost"
  echo "Services are running:"
  echo "- PostgreSQL: postgresql://postgres:${POSTGRES_PASSWORD:-password}@${host}:5432/production"
  echo "- pgAdmin: http://${host}:5050 (admin@admin.com / admin)"
  echo "- QingLong: http://${host}:5700"
  echo "- ttyd Terminal: http://${host}:7681"
}

main() {
  install_docker
  install_compose
  create_directories
  start_services
  print_endpoints
}

main "$@"
