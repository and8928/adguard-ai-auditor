<div align="center">

# 🛡️ AdGuard AI Auditor

**AI-powered DNS log auditor for AdGuard Home - finds missed trackers & ads and detects false-positive blocks using LLMs.**
*FastAPI backend | Glassmorphism dashboard | Google Gemini / Vertex AI*

[![Python 3.13+](https://img.shields.io/badge/Python-3.13%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Pydantic v2](https://img.shields.io/badge/Pydantic-v2-E92063?logo=pydantic&logoColor=white)](https://docs.pydantic.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**English** · [Русский](readme.ru.md)

</div>

---

## 🎯 What is this

**AdGuard AI Auditor** is an intelligent tool built on FastAPI that connects to your AdGuard Home server, collects DNS request logs, and uses Large Language Models (Google Gemini, Vertex AI, and DeepSeek) to audit them.

![main finish audit.png](photo/main%20finish%20audit.png)

It automates history network traffic analysis: it finds missed trackers and ads, identifies false positives (where blocking breaks legitimate apps), and suggests recommendations for your filter configuration.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🔌 **AdGuard Home integration** | Automatic retrieval of request history (with pagination support). |
| 🧹 **Data cleaning** | Deduplication and splitting of requests into *Allowed* and *Blocked*. |
| 🛑 **Blocking recommendations** | Finds telemetry, trackers, and ads that slipped past the filter. |
| 🟢 **Unblocking recommendations** | Detects false positives (CDN, API) where blocking might break a service. |
| ⚠️ **Requires verification** | Surfaces ambiguous domains for manual testing. |
| 🤖 **Multiple LLM support** | Google Gemini, Google Cloud Vertex AI, and DeepSeek; with planned OpenAI ChatGPT and Qwen/local models. |
| 📦 **Structured output** | The AI returns strict JSON with a `reason` and a `confidence` level for every recommendation. |
| 🎨 **Interactive dashboard** | Glassmorphism UI with a dark theme and EN/RU localization. |
| 🚀 **Real-time progress** | Audit progress streamed live via Server-Sent Events (SSE). |
| 🔢 **Token accounting** | Shows the estimated tokens sent to the AI (on the clean/cache step) and the actual usage after analysis: input/output and total token count.<br/>![tokens info.png](photo/tokens%20info.png) |
| 📝 **Custom prompt rules** | CRUD management for custom prompt rules and AI overrides.<br/>![ai rules.png](photo/ai%20rules.png) |
| ⚡ **Quick actions** | Apply recommended blocks/unblocks.<br/>![auto update rules.png](photo/auto%20update%20rules.png) |
| 🗂️ **Filter rule manager** | Browse current AdGuard user rules with live search and type filtering; switch a rule's type (block ↔ allow) or delete it right from the dashboard — no analysis run required.<br/>![current rules.png](photo/current%20rules.png) |
| ⚙️ **Runtime settings** | Edit AdGuard URL/port/login/password, fetch step, and LLM API keys from the web UI without a restart. Changes persist to `data/state.env`; secrets stay write-only and can be verified with **Test connection** / **Test login**. |

---

## ⚙️ Settings panel

Open the **⚙️ Settings** dialog from the top bar to configure the app at runtime — no `.env` edit or restart required. Changes are persisted to `data/state.env` and applied to the running process immediately.

![settings panel](photo/settings.png)

**How saving works**

- **Secrets are write-only.** Password and API-key fields show a `••• set` placeholder and are never returned by the API — leave a field empty to keep the current value, or type a new one to replace it.
- **URL / Port changes** rebuild the AdGuard endpoints on the fly.
- **URL / Port / Login / Password changes** invalidate the current session, forcing a fresh login on the next request.
- **Test connection** checks whether the current `AGH_SESSION` is still valid; **Test login** performs a full re-login with the saved credentials.

---

## 🛠 Technology Stack

| Layer | Stack |
|---|---|
| **Backend** | Python 3.13+, FastAPI, Pydantic v2 |
| **Project management** | Poetry |
| **AI integration** | `google-genai` (planned: `openai`, `httpx`, `qwen`) |
| **Frontend** | Vanilla HTML5, CSS (Glassmorphism, custom animations) and JavaScript served via Jinja2 templates - no heavy Node.js build required |
| **Logging** | Custom logger with console output |

---

## 🚀 Installation & Running

The recommended way to install and run the project is using **Poetry**.

### 1. Clone the repository
```bash
git clone https://github.com/and8928/adguard-ai-auditor.git
cd adguard-ai-auditor
```

### 2. Install dependencies with Poetry
Configure Poetry to create the virtual environment inside the project folder:
```bash
poetry config virtualenvs.in-project true
poetry install
```

### 3. Environment configuration
Create a `.env` file in the project root. You can copy the template from `.env.example`:
```ini
# AdGuard Settings
# ADGUARD_BASE_URL defaults to http://host.docker.internal (the Docker host).
# When running outside Docker, set it to your AdGuard address, e.g. http://192.168.1.1
ADGUARD_BASE_URL="http://192.168.1.1"
ADGUARD_PORT=3333
ADGUARD_USER="your_user"
ADGUARD_PASSWORD="your_password"
ADGUARD_STEP_REQ=100
# Note: AGH_SESSION is issued automatically after login and stored in data/state.env - no need to set it manually.

# Google Gemini Settings (optional)
# List of models as a JSON string array (parsed by Pydantic). They are tried in order.
GEMINI_MODELS_NAME='["gemini-3-pro-preview","gemini-3-flash-preview", "gemini-3.1-pro-preview"]'
GEMINI_API_KEY = "gemini_key"

# Vertex AI Settings (optional)
VERTEX_AI_MODELS_NAME='[]'
VERTEX_AI_API_KEY = ""

# OpenAI Settings (not working yet)
OPENAI_MODEL_NAME="gpt-5-mini"
OPENAI_API_KEY = "openai_key"

# DeepSeek Settings (optional)
DEEPSEEK_MODELS_NAME='["deepseek-v4-flash","deepseek-v4-pro"]'
DEEPSEEK_API_KEY = "deepseek_key"
DEEPSEEK_REASONING_EFFORT = high #low,medium,high
DEEPSEEK_THINKING_ENABLED = True

# Set to True for verbose debug logging
DEBUG_MOD = False
```

> [!NOTE]
> **Runtime Settings.** Most of these values (language, AdGuard URL/port, login/password,
> fetch step, LLM API keys) can also be edited at runtime from the **⚙️ Settings** panel
> in the web UI. Changes are persisted to `data/state.env` and applied without a restart —
> the `.env` file only provides the initial defaults.

> [!WARNING]
> **Secrets are stored in plaintext** in `.env` and `data/state.env` (AdGuard password and
> LLM API keys). This is intentional for a **locally-accessible** service: the same value has
> to be available to the process anyway, so on-disk encryption would only add a false sense of
> security. Keep the deployment local, ensure `data/` is **not** committed to git (it is in
> `.gitignore`) and **not** baked into the Docker image (it is in `.dockerignore`), and restrict
> filesystem access on the host if the machine is shared.

### 4. Run the application
```bash
poetry run uvicorn src.adguard_auditor.main:app --reload
```

The application will be available at: `http://localhost:8000`
API documentation (Swagger): `http://localhost:8000/docs`

### 5. Testing
The project includes a test suite covering the core logic, API endpoints, and LLM integrations:
```bash
poetry run pytest tests/ -v
```

> [!TIP]
> All external calls (AdGuard Home, LLM APIs) are mocked, so the tests run without active instances or API keys.

---

## 🐳 Running with Docker

A `Dockerfile` and a `docker-compose.yml` are included for containerized deployment.

> ### ⚡ Quick start - one command, zero setup
> Paste this into your terminal. It downloads the project, asks a few questions (AdGuard host / port / login / password and **which AI provider you use** - the API keys are saved automatically), then builds and launches everything:
>
> ```bash
> bash <(curl -fsSL https://raw.githubusercontent.com/and8928/adguard-ai-auditor/main/install.sh)
> ```
>
> When it finishes, open **`http://<server-ip>:3334`** and you're done. 🎉
> Re-run the same command anytime to rebuild and restart - it won't ask again unless you delete `.env`.

Already cloned the repo? Just run it locally instead:
```bash
chmod +x install.sh
./install.sh
```

Prefer to configure everything by hand? Follow the manual steps below.

### 1. Prepare the environment
Create your `.env` file as described above. The `data/` directory (mounted as a volume) holds runtime state such as the auto-issued `AGH_SESSION` and your prompt rules, so it persists across restarts.

### 2. Build and start
```bash
docker compose up -d --build
```

The dashboard will be available at `http://<server-ip>:3334` (mapped to the container's internal port `8000`).

> [!NOTE]
> `ADGUARD_BASE_URL` defaults to `http://host.docker.internal`, which resolves to the Docker host machine - the compose file already maps `host.docker.internal` to the host gateway. If AdGuard Home runs on the same host, no change is needed; point it elsewhere if AdGuard lives on another machine.

---

## 📡 API Endpoints

The key endpoints in the `/api/v1` namespace (see Swagger at `/docs` for the full list):

- `GET /` - Serves the interactive Web Dashboard (the root `/` automatically redirects here).
- `GET /get-raw-request-log?limit=100` - Get raw query logs from the AdGuard Home server.
- `GET /get-response-log?limit=100` - Get cleaned and grouped logs (Allowed / Blocked).
- `POST /ai-analis-data` - Run LLM analysis on the supplied data; the model is chosen via the `model_services` parameter.
- `POST /auto-analis` - Fetch logs from AdGuard, clean them, and run them through the LLM in a single call (non-SSE equivalent of the full audit).
- `GET /audit/stream` - SSE endpoint streaming real-time audit progress and results. Supports `action=full|fetch|analyze`; also returns the estimated input tokens (`est_tokens`) and the model's actual usage (`usage`: input/output/total).
- `GET /audit/cache`, `POST /audit/cache/clear` - Inspect or clear the cached fetched/cleaned data.
- `POST /to_block`, `POST /to_unblock`, `POST /to_delete` - Apply block/unblock decisions or delete user rules directly in AdGuard Home filters.
- `GET /get_actual_filter` - Retrieve the current, optimized user filter rules from AdGuard Home (powers the interactive Filter rule manager).
- `GET /prompt-rules`, `POST /prompt-rules`, `GET /prompt-rules/{id}`, `PATCH /prompt-rules/{id}`, `DELETE /prompt-rules/{id}` - CRUD endpoints to manage custom prompt rules and guidelines for the AI.
- `GET /prompt-rules/{id}/test` - Preview the prompt block that a rule will inject into the AI's system instructions.
- `GET /settings`, `PUT /settings` - Read or update runtime settings (AdGuard URL/port/login/password, fetch step, LLM API keys). Secrets are never returned by `GET` (only `*_set` booleans) and an empty secret in `PUT` keeps the current value.
- `POST /settings/test_connection` - Check whether the current `AGH_SESSION` is still valid.
- `POST /settings/test_login` - Try to log in to AdGuard Home with the currently saved credentials.

---

## 📂 Project Structure

```text
src/
├── adguard_auditor/
│   ├── main.py                 # FastAPI application entry point
│   ├── core/
│   │   ├── config.py           # Configuration loading via Pydantic Settings
│   │   ├── endpoints.py        # AdGuard Home URL builder
│   │   ├── prompts.py          # AI system prompts and templates
│   │   └── logger.py           # Logging setup
│   ├── api/
│   │   └── v1/
│   │       └── endpoints/
│   │           ├── audit.py    # Main audit and SSE endpoints
│   │           ├── prompt_rules.py # CRUD endpoints for rules
│   │           └── settings.py # Runtime settings & connection-test endpoints
│   ├── services/
│   │   ├── adguard_client.py   # Client for AdGuard Home HTTP API
│   │   ├── analysis_service.py # Log parsing, cleaning, and rule generation
│   │   ├── cache.py            # In-memory cache for fetched/cleaned data
│   │   ├── controller.py       # Main data flow controller
│   │   ├── prompt_rules_service.py # Prompt rule storage management
│   │   └── settings_service.py # Runtime settings read/apply logic
│   ├── schemas/
│   │   ├── adguard_models.py   # Pydantic schemas for AdGuard structures
│   │   ├── audit.py            # API request/response models
│   │   ├── prompt_rules.py     # Prompt rule schemas
│   │   ├── settings.py         # Runtime settings read/update schemas
│   │   └── storage.py          # Storage model schemas
│   └── frontend/
│       ├── static/
│       │   ├── style.css       # Premium Dark theme CSS with Glassmorphism
│       │   ├── i18n.js         # EN/RU localization
│       │   └── app.js          # SPA logic & SSE listener
│       └── templates/
│           └── index.html      # Dashboard template
├── gemini/
│   └── init.py                 # Google Gemini client and API wrapper
├── vertex_ai/
│   └── init.py                 # Google Cloud Vertex AI client and API wrapper
├── deepseek/
│   └── init.py                 # DeepSeek client and API wrapper (built on the OpenAI library)
└── openai/
    └── init.py                 # OpenAI client (planned)
```

---

## 📝 Roadmap (Future Plans)

### 🛠 Backend & Infrastructure
- [x] **Docker support**: `Dockerfile` and `docker-compose.yml` for containerized deployment (with `host.docker.internal` host access).
- [ ] **Switch to `httpx`**: Replace `requests` with `httpx` for better async support and performance.

### 🤖 AI & Prompt Engineering
- [x] **Custom prompt rules**: Enhance system prompts with user-specific rules (e.g., override "Windows system widgets" as ads instead of required content).
- [ ] **Local AI**: Add Unsloth integration.
- [ ] **API integrations**: Add OpenAI integration.

### 📊 Analysis & Filtering
- [ ] **Resource categorization**:
  - [ ] Resources that work poorly.
  - [ ] Resources that don't work.
  - [ ] Resources that work but shouldn't (false positives).
  - [ ] Resources that should be blocked (missed trackers/ads).
  - [ ] Ads detected on specific services.

### 🎨 Frontend
- [X] **Settings panel**: Move language and AdGuard login/password into a dedicated Settings section.
- [ ] **Interactive Test tab**: Send "requires verification" domains to block/unblock/ignore directly.
- [x] **Filter rule manager**: Always-available Current Rules card with live search, type filtering, inline type switching, and rule deletion.
- [x] **UI improvements**: Currently focusing on FastAPI backend functionality; the frontend interface is under active development.

### 🔐 Authentication
- [x] **Auto auth**: Automatic authorization in AdGuard Home (`_get_new_session`).

---

## 📄 License

This project is distributed under the **MIT License**. See the [LICENSE](LICENSE) file for details.
