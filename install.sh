#!/usr/bin/env bash
#
# AdGuard AI Auditor - one-command installer / launcher.
#
# Works both ways:
#   * inside a cloned repo:   ./install.sh
#   * straight from the web:  bash <(curl -fsSL https://raw.githubusercontent.com/and8928/adguard-ai-auditor/main/install.sh)
#
# Modes:
#   ./install.sh            Just bring the app up. On the first run it seeds a
#                           default .env (no questions) so you can finish the
#                           setup in the web UI's ⚙️ Settings panel.
#   ./install.sh config     Run the interactive wizard (AdGuard host/port/login/
#                           password + AI provider keys), then build & start.
#                           Use it for headless setups or to reconfigure later.
#   ./install.sh update     Pull the latest code, add any new .env keys, rebuild
#                           and restart. Your .env and ./data are kept as is.
#   ./install.sh help       Show this help.
#
set -euo pipefail

REPO_URL="https://github.com/and8928/adguard-ai-auditor.git"
REPO_DIR="adguard-ai-auditor"
CONTAINER_NAME="adguard-ai-auditor"   # must match container_name in docker-compose.yml
ENV_FILE=".env"
EXAMPLE_FILE=".env.example"

print_usage() {
  cat <<'USAGE'
AdGuard AI Auditor installer

Usage:
  ./install.sh            Build & start; seed a default .env on first run
                          (configure the rest in the web UI ⚙️ Settings).
  ./install.sh config     Interactive setup wizard, then build & start.
                          Aliases: configure, settings.
  ./install.sh update     Pull the latest code, add any new .env keys,
                          rebuild & restart. .env and ./data are preserved.
                          Aliases: upgrade.
  ./install.sh help       Show this help.
USAGE
}

# --- Parse mode -------------------------------------------------------------
ORIGINAL_ARGS=("$@")
MODE="up"
case "${1:-}" in
  ""|up|start|--up)            MODE="up" ;;
  config|configure|settings|--config|-c) MODE="config" ;;
  update|upgrade|--update|-u)  MODE="update" ;;
  help|-h|--help)              print_usage; exit 0 ;;
  *) echo "❌ Unknown argument '$1'." >&2; echo >&2; print_usage >&2; exit 1 ;;
esac

# Make interactive `read` work even under `curl ... | bash`.
# Never fatal: with no usable terminal (cron, CI) only `config` needs input.
if [[ ! -t 0 && -e /dev/tty ]]; then exec </dev/tty 2>/dev/null || true; fi

# --- 0. Locate the project (or clone it) -----------------------------------
# Ask Docker where the existing installation lives. Compose stamps the working
# directory onto the container, so this finds it no matter where the user is
# standing - which matters a lot for the `bash <(curl ...)` one-liner.
find_installed_dir() {
  command -v docker >/dev/null 2>&1 || return 1
  local dir
  dir="$(docker inspect "$CONTAINER_NAME" \
           --format '{{index .Config.Labels "com.docker.compose.project.working_dir"}}' \
           2>/dev/null)" || return 1
  [[ -n "$dir" && -f "$dir/docker-compose.yml" ]] || return 1
  printf '%s' "$dir"
}

locate_project() {
  # Already sitting in the repo?
  if [[ -f docker-compose.yml && -f Dockerfile ]]; then return; fi

  # Script lives next to the repo files?
  local sd
  sd="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" 2>/dev/null && pwd)" || sd=""
  if [[ -n "$sd" && -f "$sd/docker-compose.yml" ]]; then cd "$sd"; return; fi

  # A container is already running somewhere - reuse THAT copy, so we never
  # clone a second one and clobber the user's .env with a blank template.
  local installed
  if installed="$(find_installed_dir)"; then
    if cd "$installed" 2>/dev/null; then
      echo "📍 Found the existing installation at: $installed"
      return
    fi
    echo "⚠️  A container is registered at '$installed', but that path is not"
    echo "   reachable from here. Continuing with the local copy instead."
  fi

  # Nothing installed yet - fetch it.
  if ! command -v git >/dev/null 2>&1; then
    echo "❌ git is required to download the project. Install git and retry." >&2
    exit 1
  fi
  if [[ -d "$REPO_DIR/.git" ]]; then
    echo "📥 Using the existing checkout in ./$REPO_DIR ..."
    cd "$REPO_DIR"
    # In update mode pull_latest handles this properly (dirty-tree checks etc).
    if [[ "$MODE" != "update" ]]; then
      git pull --ff-only || echo "⚠️  Could not fast-forward; using local copy."
    fi
  elif [[ "$MODE" == "update" ]]; then
    echo "❌ No existing installation found to update." >&2
    echo "   Nothing is running, and there is no ./$REPO_DIR checkout here." >&2
    echo "   If you installed it elsewhere, cd into that folder and re-run:" >&2
    echo "     ./install.sh update" >&2
    echo "   Or install fresh by running this without the 'update' argument." >&2
    exit 1
  else
    echo "📥 Cloning $REPO_URL ..."
    git clone --depth 1 "$REPO_URL" "$REPO_DIR"
    cd "$REPO_DIR"
  fi
}
locate_project

# --- 0b. Pull the latest code (update mode) ---------------------------------
pull_latest() {
  if [[ ! -d .git ]]; then
    echo "⚠️  This copy is not a git checkout - skipping code update."
    echo "   Re-install with: git clone $REPO_URL && cd $REPO_DIR && ./install.sh"
    return
  fi
  if ! command -v git >/dev/null 2>&1; then
    echo "❌ git is required to update. Install git and retry." >&2
    exit 1
  fi
  if ! git remote get-url origin >/dev/null 2>&1; then
    echo "⚠️  This checkout has no 'origin' remote - skipping the code update."
    echo "   Add one with: git remote add origin $REPO_URL"
    return
  fi

  local before after
  before="$(git rev-parse --short HEAD 2>/dev/null || echo '?')"

  if [[ -n "$(git status --porcelain --untracked-files=no)" ]]; then
    echo "❌ You have local changes to tracked files - refusing to overwrite them." >&2
    echo "   Commit or stash them, then re-run './install.sh update'." >&2
    exit 1
  fi

  echo "📥 Fetching the latest code..."
  # Keep shallow clones shallow, but never truncate a full clone's history.
  local depth=()
  [[ "$(git rev-parse --is-shallow-repository 2>/dev/null)" == "true" ]] && depth=(--depth 1)

  local target
  if git rev-parse --abbrev-ref '@{u}' >/dev/null 2>&1; then
    git fetch "${depth[@]}" origin
    target='@{u}'
  else
    # Detached HEAD or no tracking branch (e.g. a --depth 1 clone of a tag).
    git fetch "${depth[@]}" origin HEAD
    target=FETCH_HEAD
  fi

  if ! git merge --ff-only "$target"; then
    echo "❌ Cannot fast-forward to the latest revision (diverged history)." >&2
    echo "   Resolve it manually with git, then re-run './install.sh update'." >&2
    exit 1
  fi

  after="$(git rev-parse --short HEAD 2>/dev/null || echo '?')"
  if [[ "$before" == "$after" ]]; then
    echo "✅ Already on the latest revision ($after) - rebuilding anyway."
    return
  fi
  echo "✅ Updated $before → $after"

  # Bash reads this file lazily, so a rewritten install.sh would corrupt the
  # rest of this run. Hand over to the new version exactly once.
  local self
  self="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" 2>/dev/null && pwd)/$(basename "${BASH_SOURCE[0]:-$0}")"
  if [[ -f "$self" && -z "${AUDITOR_INSTALLER_REEXEC:-}" ]] \
     && ! git diff --quiet "$before" "$after" -- "$(basename "$self")"; then
    echo "🔄 The installer itself changed - restarting with the new version..."
    export AUDITOR_INSTALLER_REEXEC=1
    exec bash "$self" "${ORIGINAL_ARGS[@]}"
  fi
}

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

# --- helper: seed .env from the template (no prompts) -----------------------
seed_env() {
  if [[ -f "$EXAMPLE_FILE" ]]; then cp "$EXAMPLE_FILE" "$ENV_FILE"; else : > "$ENV_FILE"; fi
  sed -i 's/\r$//' "$ENV_FILE"
  [[ -s "$ENV_FILE" && -n "$(tail -c1 "$ENV_FILE")" ]] && printf '\n' >> "$ENV_FILE"
}

# --- helper: add keys that exist in the template but not in .env ------------
# Existing values are never touched - only genuinely new keys are appended.
merge_env_template() {
  [[ -f "$EXAMPLE_FILE" && -f "$ENV_FILE" ]] || return 0

  local added=0 line key value
  while IFS= read -r line || [[ -n "$line" ]]; do
    line="${line%$'\r'}"
    [[ "$line" =~ ^[[:space:]]*# ]] && continue
    [[ "$line" =~ ^[[:space:]]*([A-Za-z_][A-Za-z0-9_]*)[[:space:]]*=(.*)$ ]] || continue
    key="${BASH_REMATCH[1]}"
    value="${BASH_REMATCH[2]}"
    value="${value#"${value%%[![:space:]]*}"}"   # trim leading spaces

    if ! grep -qE "^[[:space:]]*${key}[[:space:]]*=" "$ENV_FILE"; then
      set_env "$key" "$value"
      echo "   + $key (new setting, default applied)"
      added=$((added + 1))
    fi
  done < "$EXAMPLE_FILE"

  if [[ "$added" -eq 0 ]]; then
    echo "✅ No new settings in this release - $ENV_FILE left untouched."
  else
    echo "ℹ️  Added $added new setting(s) with template defaults."
    echo "   Review them in the web UI ⚙️ Settings or in $ENV_FILE."
  fi
}

# --- helper: interactive configuration wizard -------------------------------
configure_interactive() {
  echo
  echo "🛠  Interactive setup"
  echo

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
    echo "ℹ️  No AI key was set. Add at least one provider key here or in the UI ⚙️ Settings before running an audit."
  fi
  echo
}

# --- 2. Configuration -------------------------------------------------------
SEEDED=0
if [[ ! -f "$ENV_FILE" ]]; then
  seed_env
  SEEDED=1
fi

if [[ "$MODE" == "update" ]]; then
  pull_latest
  echo
  echo "🔎 Checking $ENV_FILE for new settings..."
  if [[ "$SEEDED" -eq 1 ]]; then
    echo "   No $ENV_FILE found - seeded a fresh one from the template."
  else
    merge_env_template
  fi
  echo
elif [[ "$MODE" == "config" ]]; then
  configure_interactive
elif [[ "$SEEDED" -eq 1 ]]; then
  echo
  echo "🌱 Seeded a default $ENV_FILE from the template."
  echo "   Finish the setup in the web UI ⚙️ Settings after it starts,"
  echo "   or re-run './install.sh config' for the terminal wizard."
  echo
else
  echo "ℹ️  $ENV_FILE already exists - leaving it as is."
  echo "   (Run './install.sh config' to reconfigure from the terminal.)"
  echo
fi

# --- 3. Build & start -------------------------------------------------------
mkdir -p data   # holds state.env (auto session) and prompt_rules.json

if [[ "$MODE" == "update" ]]; then
  echo "🐳 Rebuilding and restarting the container..."
else
  echo "🐳 Building and starting the container..."
fi
$COMPOSE up -d --build

if [[ "$MODE" == "update" ]]; then
  # The previous image is now dangling; drop it so updates don't pile up.
  docker image prune -f --filter "label=com.docker.compose.project" >/dev/null 2>&1 || true
fi

echo
if [[ "$MODE" == "update" ]]; then
  echo "✅ AdGuard AI Auditor updated and running."
else
  echo "✅ AdGuard AI Auditor is running."
fi
echo "   Dashboard : http://localhost:3334   (or http://<server-ip>:3334)"
if [[ "$MODE" != "config" && "$SEEDED" -eq 1 ]]; then
  echo "   Configure : open the dashboard → ⚙️ Settings (AdGuard host/login + AI key)"
fi
echo "   Logs      : $COMPOSE logs -f"
echo "   Stop      : $COMPOSE down"
