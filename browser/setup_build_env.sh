#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
MACH_DOWNLOAD_PATH="$SCRIPT_DIR/mach"
BOOTSTRAP_DOWNLOAD_PATH="$SCRIPT_DIR/mozboot_bootstrap.py"

log() {
  printf '[setup-build-env] %s\n' "$1"
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1
}

install_apt_packages() {
  local packages=(
    autoconf2.13
    build-essential
    ccache
    clang
    curl
    git
    llvm
    mercurial
    nasm
    nodejs
    npm
    pkg-config
    python3
    python3-dev
    python3-pip
    python3-venv
    wget
    yasm
    zip
    unzip
    libdbus-1-dev
    libdbus-glib-1-dev
    libgtk-3-dev
    libxt-dev
    libx11-xcb-dev
    libxtst-dev
    libasound2-dev
    libpulse-dev
  )

  log "Installing Firefox build dependencies via apt..."
  sudo apt-get update
  sudo apt-get install -y "${packages[@]}"
}

install_rustup() {
  if require_cmd rustup; then
    log "rustup already installed."
  else
    log "Installing rustup..."
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
  fi

  # shellcheck disable=SC1091
  source "$HOME/.cargo/env"
  rustup toolchain install stable
  rustup default stable
}

install_mach_tools() {
  log "Downloading mach launcher and bootstrap helper..."
  curl -fsSL https://hg.mozilla.org/mozilla-central/raw-file/tip/mach -o "$MACH_DOWNLOAD_PATH"
  chmod +x "$MACH_DOWNLOAD_PATH"
  curl -fsSL https://hg.mozilla.org/mozilla-central/raw-file/tip/python/mozboot/mozboot/bootstrap.py -o "$BOOTSTRAP_DOWNLOAD_PATH"
}

ensure_mozconfig() {
  if [[ -f "$SCRIPT_DIR/mozconfig" ]]; then
    log "Using existing $SCRIPT_DIR/mozconfig"
  else
    log "Creating base mozconfig at $SCRIPT_DIR/mozconfig"
    cat > "$SCRIPT_DIR/mozconfig" <<'EOF'
ac_add_options --enable-application=browser
ac_add_options --disable-debug
ac_add_options --enable-optimize
ac_add_options --disable-tests
mk_add_options MOZ_OBJDIR=@TOPSRCDIR@/obj-production
EOF
  fi
}

verify_with_mach_bootstrap() {
  local firefox_src="${FIREFOX_SRC:-}"

  if [[ -z "$firefox_src" ]]; then
    log "FIREFOX_SRC is not set. Skipping ./mach bootstrap verification."
    log "Set FIREFOX_SRC to your local Firefox source checkout and rerun this script."
    return
  fi

  if [[ ! -d "$firefox_src" ]]; then
    log "FIREFOX_SRC path does not exist: $firefox_src"
    exit 1
  fi

  if [[ ! -x "$firefox_src/mach" ]]; then
    log "No executable mach found in $firefox_src. Ensure Firefox source is present."
    exit 1
  fi

  log "Running ./mach bootstrap in $firefox_src"
  (
    cd "$firefox_src"
    ./mach bootstrap --application-choice browser --no-interactive
  )
}

main() {
  if ! require_cmd apt-get; then
    log "This script currently supports Debian/Ubuntu with apt-get."
    exit 1
  fi

  install_apt_packages
  install_rustup
  install_mach_tools
  ensure_mozconfig
  verify_with_mach_bootstrap

  log "Done."
  log "mach launcher downloaded to: $MACH_DOWNLOAD_PATH"
  log "bootstrap helper downloaded to: $BOOTSTRAP_DOWNLOAD_PATH"
  log "mozconfig path: $SCRIPT_DIR/mozconfig"
  log "Repository root: $REPO_ROOT"
}

main "$@"
