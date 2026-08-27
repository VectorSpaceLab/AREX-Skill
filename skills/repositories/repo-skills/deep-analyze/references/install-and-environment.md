# DeepAnalyze install and environment notes

DeepAnalyze is a source checkout plus a set of runtime workflows, not a single installable top-level distribution. For repository inspection, keep one small CPU environment for API/client/UI checks and separate GPU-oriented environments only when you need real serving or training.

## Recommended default

Use Conda when available:

```bash
conda create --yes --prefix "<deep-analyze-inspection>" "python=3.12" pip
conda run --prefix "<deep-analyze-inspection>" python -m pip install \
  requests fastapi uvicorn openai pydantic python-multipart rich \
  pandas numpy matplotlib openpyxl scikit-learn seaborn statsmodels plotly \
  httpx python-dotenv aiohttp nbformat
```

That CPU inspection set is enough for:
- `scripts/check_deepanalyze_environment.py`
- API/client imports and TestClient checks
- WebUI v2 backend/settings checks
- CLI and Jupyter source compilation

## Optional add-ons by workflow

| Workflow | Add-ons | Why |
| --- | --- | --- |
| Model serving | `torch`, `transformers`, `vllm`, `bitsandbytes` | Needed for real vLLM launch, quantization, and tokenizer mutation. |
| Jupyter frontend | `uv`, `fastmcp`, `mcp`, `jupyterlab`, `notebook`, Node.js, npm | Needed for the notebook/MCP runtime and browser UI. |
| WebUI PDF export | `pypandoc`, `pandoc`, `xelatex` | Needed for PDF output beyond Markdown fallback. |
| Training / RL | `torch`, `deepspeed`, `flash-attn`, `liger-kernel`, `ray`, `ms-swift`, `SkyRL` | Needed for the official SFT/RL recipes. |

## Quick read-only checks

After preparing the environment, run the bundled checker from a DeepAnalyze checkout:

```bash
python skills/disco/deep-analyze/scripts/check_deepanalyze_environment.py --repo-root <deep-analyze-checkout>
```

The checker verifies:
- required Python modules for the CPU inspection path;
- syntax compilation for the selected source files;
- the `DeepAnalyzeVLLM` import and local `execute_code()` path;
- API and WebUI v2 TestClient smoke routes.

## What not to do by default

- Do not install `vllm` into the CPU inspection prefix unless you are explicitly validating real model serving.
- Do not install all training extras in the inspection prefix; keep the SFT/RL environments separate.
- Do not assume the repo root is a packaged wheel. If import paths are awkward, use the checkout plus the bundled checker.
