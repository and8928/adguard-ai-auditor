<div align="center">

# 🛡️ AdGuard AI Auditor

**AI-powered DNS log auditor for AdGuard Home — finds missed trackers & ads and detects false-positive blocks using LLMs.**
*FastAPI backend | Glassmorphism dashboard | Google Gemini / Vertex AI*

[![Python 3.13+](https://img.shields.io/badge/Python-3.13%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Pydantic v2](https://img.shields.io/badge/Pydantic-v2-E92063?logo=pydantic&logoColor=white)](https://docs.pydantic.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**English** · [Русский](readme.ru.md)

</div>

---

## 🎯 What is this

**AdGuard AI Auditor** is an intelligent tool built on FastAPI that connects to your AdGuard Home server, collects DNS request logs, and uses Large Language Models (Google Gemini, Vertex AI; OpenAI / Qwen planned) to audit them.

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
| 🤖 **Multiple LLM support** | Google Gemini and Google Cloud Vertex AI, with planned OpenAI ChatGPT and Qwen/local models. |
| 📦 **Structured output** | The AI returns strict JSON with a `reason` and a `confidence` level for every recommendation. |
| 🎨 **Interactive dashboard** | Glassmorphism UI with a dark theme and EN/RU localization. |
| 🚀 **Real-time progress** | Audit progress streamed live via Server-Sent Events (SSE). |
| 📝 **Custom prompt rules** | CRUD management for custom prompt rules and AI overrides. |
| ⚡ **Quick actions** | Apply recommended blocks/unblocks directly to AdGuard Home, and inspect active filter rules. |

---

## 🛠 Technology Stack

| Layer | Stack |
|---|---|
| **Backend** | Python 3.13+, FastAPI, Pydantic v2 |
| **Project management** | Poetry |
| **AI integration** | `google-genai` (planned: `openai`, `httpx`, `qwen`) |
| **Frontend** | Vanilla HTML5, CSS (Glassmorphism, custom animations) and JavaScript served via Jinja2 templates — no heavy Node.js build required |
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
ADGUARD_BASE_URL="http://192.168.1.1"
ADGUARD_PORT=3333
ADGUARD_USER="your_user"
ADGUARD_PASSWORD="your_password"
AGH_SESSION="your_session"
ADGUARD_STEP_REQ=100

# Google Gemini Settings
# List of models as a JSON string array (parsed by Pydantic). They are tried in order.
GEMINI_MODELS_NAME='["gemini-3-pro-preview","gemini-3-flash-preview", "gemini-3.1-pro-preview"]'
GEMINI_API_KEY = "gemini_key"

# Vertex AI Settings (optional, leave empty if unused)
VERTEX_AI_MODELS_NAME='[]'
VERTEX_AI_API_KEY = ""

# OpenAI Settings
OPENAI_MODEL_NAME="gpt-5-mini"
OPENAI_API_KEY = "openai_key"

# Set to True for verbose debug logging
DEBUG_MOD = False
```

> [!NOTE]
> Automatic session retrieval is still under development, so for now you must manually specify the `AGH_SESSION` cookie from your browser.

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

## 📡 API Endpoints

The key endpoints in the `/api/v1` namespace (see Swagger at `/docs` for the full list):

- `GET /` — Serves the interactive Web Dashboard (the root `/` automatically redirects here).
- `GET /get-raw-request-log?limit=100` — Get raw query logs from the AdGuard Home server.
- `GET /get-response-log?limit=100` — Get cleaned and grouped logs (Allowed / Blocked).
- `GET /audit/stream` — SSE endpoint streaming real-time audit progress and results. Supports `action=full|fetch|analyze`.
- `GET /audit/cache`, `POST /audit/cache/clear` — Inspect or clear the cached fetched/cleaned data.
- `POST /to_block`, `POST /to_unblock` — Apply block/unblock decisions directly to AdGuard Home user filters.
- `GET /get_actual_filter` — Retrieve the current, optimized user filter rules from AdGuard Home.
- `GET /prompt-rules`, `POST /prompt-rules`, `GET /prompt-rules/{id}`, `PATCH /prompt-rules/{id}`, `DELETE /prompt-rules/{id}` — CRUD endpoints to manage custom prompt rules and guidelines for the AI.

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
│   │           └── prompt_rules.py # CRUD endpoints for rules
│   ├── services/
│   │   ├── adguard_client.py   # Client for AdGuard Home HTTP API
│   │   ├── analysis_service.py # Log parsing, cleaning, and rule generation
│   │   ├── cache.py            # In-memory cache for fetched/cleaned data
│   │   ├── controller.py       # Main data flow controller
│   │   └── prompt_rules_service.py # Prompt rule storage management
│   ├── schemas/
│   │   ├── adguard_models.py   # Pydantic schemas for AdGuard structures
│   │   ├── audit.py            # API request/response models
│   │   ├── prompt_rules.py     # Prompt rule schemas
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
└── openai/
    └── init.py                 # OpenAI client (planned)
```

---

## 📝 Roadmap (Future Plans)

### 🛠 Backend & Infrastructure
- [ ] **Switch to `httpx`**: Replace `requests` with `httpx` for better async support and performance.

### 🤖 AI & Prompt Engineering
- [x] **Custom prompt rules**: Enhance system prompts with user-specific rules (e.g., override "Windows system widgets" as ads instead of required content).
  - *Example*: AI suggests `{ "domain": "assets.msn.com", "reason": "Required for Windows widgets", "confidence": "MEDIUM" }`, but the user wants to block it.
- [ ] **Local AI**: Add support for running local LLM models (e.g., via Ollama or LM Studio).
- [ ] **API integrations**: Integrate the Qwen API and improve OpenAI integration stability.

### 📊 Analysis & Filtering
- [ ] **Resource categorization**:
  - [ ] Resources that work poorly.
  - [ ] Resources that don't work.
  - [ ] Resources that work but shouldn't (false positives).
  - [ ] Resources that should be blocked (missed trackers/ads).
  - [ ] Ads detected on specific services.
- [x] **Filter management**: Add reading of current user filters (`get_actual_filter`).

### 🔐 Authentication
- [ ] **Auto auth**: Implement automatic authorization in AdGuard Home (`_get_new_session`).

### 🎨 Frontend
- [ ] **UI improvements**: Currently focusing on FastAPI backend functionality; the frontend interface is under active development.

---

## 📄 License

This project is distributed under the **MIT License**. See the [LICENSE](LICENSE) file for details.
