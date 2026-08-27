# Vizro environment and backend guidance

This reference is for future work with the Vizro skill. It summarizes the verified construction environment and safe setup patterns.

## Verified construction environment

The skill was constructed against commit `99634b8e837d371f0d25c53692278b39236594e6` using a private conda inspection prefix. Use your own `<env-prefix>` when recreating the environment.

Critical installed versions:

- Python `3.11.15`
- `vizro==0.1.61.dev0`
- `vizro-dash-components==0.3.1.dev0`
- `vizro_ai==0.4.3.dev0`
- `vizro-mcp==0.1.5.dev0`
- `vizro-experimental==0.1.1.dev0`
- `dash==4.4.1`
- `dash_mantine_components==2.8.0`, `dash_ag_grid==35.3.0`, `dash-bootstrap-components==2.0.4`
- `pandas==3.0.5`, `numpy==2.4.6`, `plotly==6.9.0`, `pydantic==2.13.4`
- `mcp==1.29.0`, `pydantic-ai-slim==2.31.0`, `dash-extensions==2.0.6`
- `pytest==9.1.1`, `selenium==4.2.0`, `chromedriver-autoinstaller==0.6.4`, `playwright==1.62.0`

Host facts at construction:

- Linux x86_64.
- Node `v24.16.0`, npm `11.13.0`.
- A100 GPUs present but not needed for Vizro CPU/Dash package checks.
- No Chrome/Chromium binary detected; browser-backed native tests were not required gates.

## Create a similar inspection environment

Use a private prefix; do not mutate user-provided environments unless asked.

```bash
export VIZRO_ENV_PREFIX="<env-prefix>"
conda create --yes --prefix "$VIZRO_ENV_PREFIX" "python=3.11" pip
conda run --prefix "$VIZRO_ENV_PREFIX" \
  python -m pip install -U "dash[dev,testing]>=4,<5" \
  pytest pytest-mock pytest-rerunfailures freezegun pyhamcrest \
  "selenium>=4.2.0" "chromedriver-autoinstaller>=0.6.4" playwright \
  pyyaml openpyxl requests toml
```

Then install local packages. Build `vizro-dash-components` first if installing from a source checkout without generated wrappers:

```bash
export VIZRO_REPO_ROOT="<repo-root>"
cd "$VIZRO_REPO_ROOT/vizro-dash-components"
npm install --legacy-peer-deps
npm run build:js
conda run --prefix "$VIZRO_ENV_PREFIX" bash -lc \
  'cd "$VIZRO_REPO_ROOT/vizro-dash-components" && \
   dash-generate-components ./src/ts/components vizro_dash_components -p package-info.json --ignore \\.test\\.'

conda run --prefix "$VIZRO_ENV_PREFIX" python -m pip install "$VIZRO_REPO_ROOT/vizro-dash-components"
conda run --prefix "$VIZRO_ENV_PREFIX" python -m pip install "$VIZRO_REPO_ROOT/vizro-core"
conda run --prefix "$VIZRO_ENV_PREFIX" python -m pip install \
  "$VIZRO_REPO_ROOT/vizro-ai" "$VIZRO_REPO_ROOT/vizro-mcp" "$VIZRO_REPO_ROOT/vizro-experimental"
```

Why `--legacy-peer-deps` may be needed: npm 11 strict peer resolution can reject `react-markdown@4.3.1` with React 18. The legacy peer mode matches the practical repo build route used during verification.

## Environment probe

From this skill directory:

```bash
conda run --prefix "$VIZRO_ENV_PREFIX" python scripts/probe_vizro_environment.py
```

The probe is CPU-only. It imports all five package families, builds a minimal Vizro dashboard, instantiates generated Dash components, checks the deprecated chart agent import, and checks experimental popup lazy exports.

## Browser backend

Browser-backed tests include Dash `dash_duo`, Selenium, and package e2e/integration tests. They require a real Chrome/Chromium binary plus compatible driver wiring.

Before treating browser tests as required, check:

```bash
command -v google-chrome || command -v chromium || command -v chromium-browser
```

If absent, either install a browser intentionally or document browser tests as skipped/blocked. Do not fail a CPU package skill verification solely because browser backend is unavailable unless the user explicitly asked for browser/e2e verification.

## LLM/provider backend

`vizro-ai` and experimental popup dashboard-agent flows may use pydantic-ai/provider-backed calls. Do not run live provider calls without user authorization, API keys, and network permission.

Credential-free alternatives:

- Import/inspect `vizro_ai.agents._chart_agent.chart_agent` and response models.
- Unit-test instruction helpers with small pandas DataFrames.
- Use `add_chat_popup(generate_response=...)` with a deterministic local callback.
- Validate dashboards through Vizro-MCP server helpers without calling a remote LLM.

## Hatch/package working directories

Vizro uses Hatch as the project development tool, but commands must be run from the relevant package directory:

```bash
cd vizro-core && hatch run test-unit
cd vizro-mcp && hatch run test-unit
```

Do not run Hatch commands from `vizro-e2e-flow`; that package is a Claude Code plugin with reference skills and its local instructions say no Hatch commands.
