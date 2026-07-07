#!/usr/bin/env bash
#
# AdGuard AI Auditor - one-command installer / launcher.
#
# Works both ways:
#   * inside a cloned repo:   ./install.sh
#   * straight from the web:  bash <(curl -fsSL https://raw.githubusercontent.com/and8928/adguard-ai-auditor/main/install.sh)
#
# On the FIRST run (no .env yet) it asks for your AdGuard Home host/port/login/
# password and which AI provider(s) to use, saves everything into .env, then
# builds and starts the Docker container. Later runs just rebuild & restart.
#
set -euo pipefail

REPO_URL="https://github.com/and8928/adguard-ai-auditor.git"
REPO_DIR="adguard-ai-auditor"
ENV_FILE=".env"
EXAMPLE_FILE=".env.example"

# Make interactive `read` work even under `curl ... | bash`.
if [[ ! -t 0 && -e /dev/tty ]]; then exec </dev/tty; fi

# --- 0. Locate the project (or clone it) -----------------------------------
locate_project() {
  # Already sitting in the repo?
  if [[ -f docker-compose.yml && -f Dockerfile ]]; then return; fi

  # Script lives next to the repo files?
  local sd
  sd="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" 2>/dev/null && pwd)" || sd=""
  if [[ -n "$sd" && -f "$sd/docker-compose.yml" ]]; then cd "$sd"; return; fi

  # Otherwise fetch it.
  if ! command -v git >/dev/null 2>&1; then
    echo "❌ git is required to download the project. Install git and retry." >&2
    exit 1
  fi
  if [[ -d "$REPO_DIR/.git" ]]; then
    echo "📥 Updating existing checkout in ./$REPO_DIR ..."
    cd "$REPO_DIR"
    git pull --ff-only || echo "⚠️  Could not fast-forward; using local copy."
  else
    echo "📥 Cloning $REPO_URL ..."
    git clone --depth 1 "$REPO_URL" "$REPO_DIR"
    cd "$REPO_DIR"
  fi
}
locate_project

# --- 1. Sanity checks -------------------------------------------------------
if ! command -v docker >/dev/null 2>&1; then
  echo "❌ Docker is not installed. Install it first: https://docs.docker.com/get-docker/" >&2
  exit 1
fi

if docker compose version >/dev/null 2>&1; then
  COMPOSE="docker compose"
elif command -v docker-compose >/dev/null 2>&1; then
  COMPOSE="docker-compose"
else
  echo "❌ Docker Compose not found: https://docs.docker.com/compose/install/" >&2
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo "❌ The Docker daemon is not running (or you lack permission). Start Docker and retry." >&2
  exit 1
fi

# --- helper: set KEY=VALUE in .env (replace existing line or append) --------
set_env() {
  local key="$1" value="$2" esc
  esc=$(printf '%s' "$value" | sed -e 's/[&\\/]/\\&/g')   # escape & \ / for sed
  if grep -qE "^[[:space:]]*${key}[[:space:]]*=" "$ENV_FILE"; then
    sed -i.bak -E "s|^[[:space:]]*${key}[[:space:]]*=.*|${key}=${esc}|" "$ENV_FILE"
    rm -f "${ENV_FILE}.bak"
  else
    [[ -s "$ENV_FILE" && -n "$(tail -c1 "$ENV_FILE")" ]] && printf '\n' >> "$ENV_FILE"
    printf '%s=%s\n' "$key" "$value" >> "$ENV_FILE"
  fi
}

# --- 2. First-run configuration --------------------------------------------
if [[ ! -f "$ENV_FILE" ]]; then
  echo
  echo "🛠  First run detected - let's configure the app."
  echo

  if [[ -f "$EXAMPLE_FILE" ]]; then cp "$EXAMPLE_FILE" "$ENV_FILE"; else : > "$ENV_FILE"; fi
  sed -i 's/\r$//' "$ENV_FILE"
  [[ -s "$ENV_FILE" && -n "$(tail -c1 "$ENV_FILE")" ]] && printf '\n' >> "$ENV_FILE"

  echo "── AdGuard Home ──────────────────────────────────────────"
  read -rp "Host/URL [http://host.docker.internal]: " agh_url
  agh_url="${agh_url:-http://host.docker.internal}"

  read -rp "Port [3333]: " agh_port
  agh_port="${agh_port:-3333}"

  agh_user=""
  while [[ -z "$agh_user" ]]; do read -rp "Login: " agh_user; done

  agh_pass=""
  while [[ -z "$agh_pass" ]]; do read -rsp "Password: " agh_pass; echo; done

  set_env "ADGUARD_BASE_URL" "\"$agh_url\""
  set_env "ADGUARD_PORT"     "$agh_port"
  set_env "ADGUARD_USER"     "\"$agh_user\""
  set_env "ADGUARD_PASSWORD" "\"$agh_pass\""

  echo
  echo "── AI provider(s) ────────────────────────────────────────"
  echo "  1) Google Gemini"
  echo "  2) DeepSeek"
  echo "  3) Google Vertex AI"
  echo "  4) OpenAI             (experimental)"
  read -rp "Pick one or more, separated by space [1]: " ai_choices
  ai_choices="${ai_choices:-1}"

  configured_ai=0
  for c in $ai_choices; do
    case "$c" in
      1) read -rp "  Gemini API key: " k
         [[ -n "$k" ]] && { set_env "GEMINI_API_KEY" "\"$k\""; configured_ai=1; } ;;
      2) read -rp "  DeepSeek API key: " k
         [[ -n "$k" ]] && { set_env "DEEPSEEK_API_KEY" "\"$k\""; configured_ai=1; } ;;
      3) read -rp "  Vertex AI API key: " k
         read -rp "  Vertex AI models JSON, e.g. '[\"gemini-3-pro-preview\"]' [[]]: " m
         m="${m:-[]}"
         [[ -n "$k" ]] && { set_env "VERTEX_AI_API_KEY" "\"$k\""; configured_ai=1; }
         set_env "VERTEX_AI_MODELS_NAME" "'$m'" ;;
      4) read -rp "  OpenAI API key: " k
         [[ -n "$k" ]] && { set_env "OPENAI_API_KEY" "\"$k\""; configured_ai=1; } ;;
      *) echo "  (skipping unknown option '$c')" ;;
    esac
  done

  echo
  echo "✅ Configuration saved to $ENV_FILE"
  if [[ "$configured_ai" -eq 0 ]]; then
    echo "ℹ️  No AI key was set. Add at least one provider key to $ENV_FILE before running an audit."
  fi
  echo
else
  echo "ℹ️  $ENV_FILE already exists - skipping configuration."
  echo "   (Delete $ENV_FILE and re-run this script to reconfigure.)"
  echo
fi

# --- 3. Build & start -------------------------------------------------------
mkdir -p data   # holds state.env (auto session) and prompt_rules.json

echo "🐳 Building and starting the container..."
$COMPOSE up -d --build

echo
echo "✅ AdGuard AI Auditor is running."
echo "   Dashboard : http://localhost:3334   (or http://<server-ip>:3334)"
echo "   Logs      : $COMPOSE logs -f"
echo "   Stop      : $COMPOSE down"
