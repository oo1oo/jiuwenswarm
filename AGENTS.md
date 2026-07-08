# AGENTS.md

## Cursor Cloud specific instructions

JiuwenSwarm is a self-hosted multi-agent AI assistant (Python backend + React/Vite web
chat UI). This monorepo also contains the optional `jiuwenbox` sandbox and TUI clients.
The update script (run automatically on VM startup) installs `uv`, provisions Python 3.11,
runs `uv sync -p 3.11`, and installs the web frontend npm deps. Everything below is about
running/testing after that.

### Python version matters (use 3.11, not the system 3.12)
- The venv is intentionally created with **Python 3.11** (`uv sync -p 3.11`). Do not run the
  suite with the system Python 3.12: a transitive dep (`pysbd`) emits a `SyntaxWarning`
  for an invalid `\s` escape, and `pytest.ini` sets `filterwarnings = error`, which turns
  that into a collection error on 3.12 (~57 files fail to import). On 3.11 the same warning
  is a `DeprecationWarning`, which `pytest.ini` ignores. Always invoke tools via `.venv/bin/...`.

### Services and how to run (development)
- `.venv/bin/jiuwenswarm-start dev` is the full dev stack in one command: it starts the
  AgentServer (ws `18092`), Gateway (ws `19001`), the WebChannel (ws `19000/ws`), and the
  **Vite dev server on http://localhost:5173** (with HMR). Vite proxies `/ws` and `/api` to
  the WebChannel on `19000`, so no separate frontend build is needed for dev.
- Modes: `all` (backend + static server serving the built `dist`), `app` (backend only),
  `web` (static server only), `dev` (backend + Vite). See `jiuwenswarm/start_services.py`.
- `jiuwenswarm-start` needs `npm`/`node` on PATH for `dev` mode (it spawns `npm run dev`).

### First-run workspace init (one-off, required before starting)
- Startup reads the user workspace at `~/.jiuwenswarm`. If it does not exist, run
  `.venv/bin/jiuwenswarm-init` once (non-interactive; defaults language to `zh`). This
  creates `~/.jiuwenswarm/config/{config.yaml,.env,...}`.
- `config.yaml` pulls the model config from env vars in `~/.jiuwenswarm/config/.env`
  (`API_BASE`, `API_KEY`, `MODEL_NAME`, `MODEL_PROVIDER`). A sample (currently invalid)
  DeepSeek key lives in the repo's `llm_config.txt`. **A valid LLM API key is required for
  the agent to actually reply** — without it the UI loads and messages route through the
  full pipeline but the LLM call returns HTTP 401.
- The optional Playwright browser tool is on by default in the `.env` template
  (`BROWSER_RUNTIME_MCP_ENABLED=1`); set it to `0` to avoid `npx @playwright/mcp` download
  attempts if you don't need browser automation.

### Lint / test / build
- Python tests: `.venv/bin/python -m pytest tests/unit_tests` (also `./run_tests.sh`).
  Note `tests/unit_tests/gateway/test_cron_scheduler.py::...::test_file_modified_triggers_reload`
  is sensitive to filesystem mtime granularity and can fail on fast/coarse-mtime filesystems;
  it is unrelated to app correctness.
- Python lint: `.venv/bin/ruff check jiuwenswarm` (reports pre-existing findings).
- Web frontend (`jiuwenswarm/channels/web/frontend`): `npm run build` works; `npm run dev`
  runs the dev server. `npm run lint` currently fails because no ESLint config is committed
  (pre-existing repo issue).

### Optional components (not needed for the web product)
- `jiuwenbox` sandbox needs Linux + `bubblewrap` (not installed) and is off by default.
- Chat channels (Feishu/Telegram/Discord/WhatsApp/etc.) are all disabled by default and
  require per-channel tokens.
