---
name: optillm
description: "Use OptiLLM as an OpenAI-compatible optimizing inference proxy
  with approach routing, plugins, local inference, decoding, and safe
  troubleshooting guidance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# OptiLLM Repo Skill

Use this skill when a task involves OptiLLM: starting or configuring the proxy, routing OpenAI-compatible chat requests through inference-time optimization approaches, enabling plugins/tools, using built-in local model inference, or diagnosing OptiLLM API/config/runtime failures.

OptiLLM is a Python package and Flask service that exposes OpenAI-compatible endpoints while applying reasoning, search, voting, planning, plugin, and local decoding techniques at inference time.

## Fast route

1. If the task is about **starting the server, API compatibility, provider selection, auth, SSL, batching, streaming, `n`, Docker, `/health`, `/v1/models`, or `/v1/chat/completions`**, read [sub-skills/proxy-server/SKILL.md](sub-skills/proxy-server/SKILL.md).
2. If the task is about **choosing, combining, or tuning approach slugs** such as `moa`, `bon`, `mcts`, `cepo`, `mars`, `z3`, `re2`, or `cot_reflection`, read [sub-skills/optimization-approaches/SKILL.md](sub-skills/optimization-approaches/SKILL.md).
3. If the task is about **plugins or tool integrations** such as MCP, memory, privacy, JSON structured output, proxy load balancing, SPL, LongCePO, web search, code execution, or router, read [sub-skills/plugins-and-tools/SKILL.md](sub-skills/plugins-and-tools/SKILL.md).
4. If the task is about **built-in local HuggingFace/LoRA inference, `OPTILLM_API_KEY`, CUDA/MPS/MLX, logprobs, reasoning tokens, or decoding methods** such as `cot_decoding`, `entropy_decoding`, `thinkdeeper`, `deepconf`, or `autothink`, read [sub-skills/local-inference-decoding/SKILL.md](sub-skills/local-inference-decoding/SKILL.md).

For cross-cutting install/import/provider failures, read [references/troubleshooting.md](references/troubleshooting.md). For shared CLI/environment settings, read [references/configuration.md](references/configuration.md). For source/version staleness checks, read [references/repo-provenance.md](references/repo-provenance.md).

## Minimal setup and import check

For normal package use:

```bash
pip install optillm
optillm --version
```

For source checkout work:

```bash
python -m pip install -e .
python - <<'PY'
import optillm
from optillm import parse_combined_approach, known_approaches
print(optillm.__version__)
print(parse_combined_approach("moa-gpt-4o-mini", known_approaches, {}))
PY
```

A healthy import exposes `optillm.__version__`, server helpers such as `parse_combined_approach`, and approach slugs including `none`, `mcts`, `bon`, `moa`, `rto`, `z3`, `self_consistency`, `pvg`, `rstar`, `cot_reflection`, `plansearch`, `leap`, `re2`, `cepo`, and `mars`.

## Common operating patterns

### Drop-in OpenAI-compatible proxy

Start the server with a provider key or local inference key, then point any OpenAI client at `http://localhost:8000/v1`:

```bash
export OPENAI_API_KEY="..."
optillm --approach auto --model gpt-4o-mini
```

```python
from openai import OpenAI
client = OpenAI(base_url="http://localhost:8000/v1", api_key="...")
response = client.chat.completions.create(
    model="moa-gpt-4o-mini",
    messages=[{"role": "user", "content": "Solve the problem."}],
)
```

Read [sub-skills/proxy-server/SKILL.md](sub-skills/proxy-server/SKILL.md) before changing auth, SSL, host binding, batching, streaming, or provider fallback behavior.

### Approach selection and composition

OptiLLM can select approaches by model prefix (`moa-gpt-4o-mini`), request body (`optillm_approach`), or prompt tag (`<optillm_approach>re2</optillm_approach>`). Use `&` for pipeline composition and `|` for parallel alternatives. Read [sub-skills/optimization-approaches/SKILL.md](sub-skills/optimization-approaches/SKILL.md) before composing expensive multi-call methods.

### Plugins and tools

Plugins are discovered from `optillm/plugins` when the server loads them. Plugin slugs include `memory`, `privacy`, `mcp`, `json`, `proxy`, `spl`, `longcepo`, `deepthink`, `deep_research`, `web_search`, `executecode`, `compact`, `coc`, `genselect`, `majority_voting`, `readurls`, and `router`. Read [sub-skills/plugins-and-tools/SKILL.md](sub-skills/plugins-and-tools/SKILL.md) before enabling plugins with browser automation, code execution, external tools, or model downloads.

### Local inference and decoding

Setting `OPTILLM_API_KEY` enables the built-in local inference client. Model strings can include LoRAs separated by `+`, and `extra_body` can request decoding methods. Read [sub-skills/local-inference-decoding/SKILL.md](sub-skills/local-inference-decoding/SKILL.md) before relying on CUDA/MPS/MLX, HuggingFace cache, private models, bitsandbytes, PEFT adapters, logprobs, or reasoning token accounting.

## Bundled helpers

- Run `python scripts/inspect_optillm.py --help` to inspect an installed OptiLLM package, known approaches, plugin importability, and optional backend status without making provider calls.
- Run `bash scripts/run_safe_native_checks.sh --help` only when you are working in an OptiLLM source checkout and want a bounded set of safe native checks.

## Safety and scope notes

- Real provider calls require credentials; mock-client and dry-run helpers cover routing without secrets.
- Benchmark and training scripts are long-running or dataset/API-key dependent; treat them as evaluation references, not default smoke tests.
- Local model loading may download weights; use backend checks before requesting generation.
- Do not expose the server with `--host 0.0.0.0` unless auth and network boundaries are intentionally configured.
