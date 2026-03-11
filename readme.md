# 🛡️ AdGuard AI Auditor

**AdGuard AI Auditor** is an intelligent tool based on FastAPI that connects to your AdGuard Home server, collects DNS request logs, and uses artificial intelligence capabilities (LLM: Google Gemini, OpenAI ChatGPT, Qwen) to audit them.

The project helps automate network traffic analysis: it finds missed trackers and ads, identifies false blockings (when necessary apps break), and suggests recommendations for filter configuration.

## ✨ Features

- **Integration with AdGuard Home**: Automatic retrieval of request history (with pagination support).
- **Data Cleaning**: Filtering duplicates and splitting requests into "Allowed" and "Blocked".
- **Smart Analysis using AI**:
  - 🛑 **Blocking Recommendations**: Finds telemetry, trackers, and ads that passed the filter.
  - 🟢 **Unblocking Recommendations**: Identifies false positives (CDN, API) where blocking might break service functionality.
  - ⚠️ **Require Verification**: Finds ambiguous domains for manual testing.
- **Multiple LLM Support**: Integration with Google Gemini, OpenAI ChatGPT, and support for Qwen/Local models.
- **Structured Output**: AI returns answers in strict JSON format with reason (`reason`) and confidence level (`confidence`).

## 🛠 Technology Stack

- **Backend**: Python 3.10+, FastAPI, Pydantic
- **Project Management**: `pyproject.toml`
- **AI Integration**: `google-genai` (Planned:  `openai`, `httpx`, `qwen`)
- **Frontend**: HTML + JS, Jinja2 Templates (In Development)
- **Logging**: Custom logger with console output (and preparation for file writing).

## 🚀 Installation & Running

### 1. Clone the repository
```bash
git clone https://github.com/and8928/adguard-ai-auditor.git
cd adguard-ai-auditor
```

### 2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate  # For Linux/macOS
# or
venv\Scripts\activate  # For Windows
```

### 3. Install dependencies
The project uses `pyproject.toml` to define dependencies. To install them:

```bash
pip install .
```
*(Alternatively, for development, you can use `pip install -e .`)*

### 4. Environment Configuration
Create a `.env` file in the project root based on the configuration structure.
Example `.env` file:

```ini

# AdGuard Settings
ADGUARD_URL="http://192.168.1.1"
ADGUARD_PORT=3333
ADGUARD_USER="your_user"
ADGUARD_PASSWORD="your_password"
ADGUARD_REQ_BASE = "/control/querylog?&response_status=all&limit="
ADGUARD_STEP_REQ = 100
# Current session (cookies) for accessing AdGuard Home
AGH_SESSION="your_session"

# Google Gemini Settings
# List of models separated by comma (in JSON string format if parsed by Pydantic)
GEMINI_MODELS_NAME='["gemini-3-pro-preview","gemini-3-flash-preview", "gemini-3.1-pro-preview"]'
GEMINI_API_KEY = "gemini_key"

# OpenAI Settings
OPENAI_MODEL_NAME="gpt-5-mini"
OPENAI_API_KEY = "openai_key"
```

**Note:** At the moment, automatic session retrieval is under development, so you must manually specify the `AGH_SESSION` cookie from your browser.

### 5. Run the application
```bash
uvicorn src.adguard_auditor.main:app --reload
```

The application will be available at: `http://localhost:8000`
API Documentation (Swagger): `http://localhost:8000/docs`

## 📡 API Endpoints

Available methods in the `/api/v1` namespace:

- `GET /` — Main page with web interface.
- `GET /get-row-request-log?limit=100` — Get raw logs from the AdGuard server.
- `GET /get-response-log?limit=100` — Get cleaned and grouped logs (Allowed / Blocked).
- `POST /ai-analis-data` — Send custom data for analysis by the selected LLM.
- `POST /auto-analis` — Full cycle: collect logs from AdGuard, clean, and send to AI analysis (default uses Gemini).

## 📂 Project Structure

```text
src/
├──adguard_auditor
│   ├── main.py                 # Entry point (FastAPI app)
│   ├── core/
│   │   ├── config.py           # Loading .env variables
│   │   ├── prompts.py          # System prompts for AI
│   │   └── logger.py           # Logging configuration
│   ├── api/
│   │   └── v1/
│   │       └── endpoints/
│   │           └── audit.py    # API routes
│   ├── services/
│   │   ├── adguard_client.py   # AdGuard API logic
│   │   ├── analysis_service.py # Cleaning and preparing logs
│   │   └── controller.py       # Data controller
│   ├── schemas/
│   │   └── storage.py          # Pydantic models
│   ├── frontend/
│   │   ├── static/             # CSS, JS
│   │   └── templates/          # HTML templates
│   ├── gemini/                 # Gemini interaction logic
│   └── openai/                 # OpenAI interaction logic
├── .env                    # Configuration file (do not commit!)
├── .env.example            # Configuration example file
├── .gitignore              # 
├── poetry.lock             # 
├── readme.md               # This file)
└── pyproject.toml          # Project metadata and dependencies
```

## 📝 TODO (Future Plans)

### 🛠 Backend & Infrastructure
- [ ] **Switch to `httpx`**: Replace `requests` with `httpx` for better async support and performance.

### 🤖 AI & Prompt Engineering
- [ ] **Custom Prompt Rules**: Enhance system prompts with user-specific rules (e.g., override "Windows system widgets" as ads instead of required content).
  - *Example*: AI suggests `{ "domain": "assets.msn.com", "reason": "Required for Windows widgets", "confidence": "MEDIUM" }`, but user wants to block it.
- [ ] **Local AI**: Add support for running local LLM models (e.g., via Ollama or LM Studio).
- [ ] **API Integrations**: Integrate Qwen API and improve OpenAI integration stability.

### 📊 Analysis & Filtering
- [ ] **Resource Categorization**:
  - [ ] Resources that work poorly.
  - [ ] Resources that don't work.
  - [ ] Resources that work but shouldn't (false positives).
  - [ ] Resources that should be blocked (missed trackers/ads).
  - [ ] Ads detected on specific services.
- [ ] **Filter Management**: Add reading of current user filters (`get_actual_filter`).

### 🔐 Authentication
- [ ] **Auto Auth**: Implement automatic authorization in AdGuard Home (`_get_new_session`).

### 🎨 Frontend
- [ ] **UI Improvements**: Currently focusing on FastAPI backend functionality; frontend interface is under development.

## 📄 License

MIT License