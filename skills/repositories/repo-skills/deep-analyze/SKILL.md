---
name: "deep-analyze"
description: "Router for DeepAnalyze agentic data-science workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# DeepAnalyze

DeepAnalyze is an agentic data-science repo built around a local reasoning loop, an OpenAI-compatible API server, browser and notebook frontends, model-serving helpers, and official training/evaluation recipes.

Use this router when the request names DeepAnalyze, DeepAnalyze-8B, the OpenAI-compatible API, the browser demo, the CLI, Jupyter, vLLM serving, quantization, tokenizer customization, SFT/RL recipes, or the bundled benchmark playgrounds.

If the checkout may be stale, consult [`references/repo-provenance.md`](./references/repo-provenance.md) before trusting any route or claim.

## Start here

1. If you are setting up or checking an environment, read [`references/install-and-environment.md`](./references/install-and-environment.md).
2. If something fails, read [`references/troubleshooting.md`](./references/troubleshooting.md).
3. For a read-only health check, run [`scripts/check_deepanalyze_environment.py`](./scripts/check_deepanalyze_environment.py) against a DeepAnalyze checkout.
4. Then route to the sub-skill that owns the task surface.

## Route map

| Task family | Read first | Why |
| --- | --- | --- |
| Programmatic agent loop, workspace execution, file-aware client flows | [`sub-skills/api-and-clients/SKILL.md`](./sub-skills/api-and-clients/SKILL.md) | Covers `DeepAnalyzeVLLM`, OpenAI-style clients, file/thread semantics, and API smoke scripts. |
| CLI, browser WebUI v2, or Jupyter frontend | [`sub-skills/interactive-frontends/SKILL.md`](./sub-skills/interactive-frontends/SKILL.md) | Covers the terminal client, workspace UI, Docker execution mode, and Jupyter MCP flow. |
| Model download, vLLM launch, quantization, or tokenizer tag extension | [`sub-skills/model-serving/SKILL.md`](./sub-skills/model-serving/SKILL.md) | Covers the memory table, dry-run vLLM commands, Docker deployment, and model customization. |
| SFT, RL, benchmark runs, or case-study contribution | [`sub-skills/training-and-evaluation/SKILL.md`](./sub-skills/training-and-evaluation/SKILL.md) | Covers the official DeepAnalyze training recipes and benchmark playgrounds. |

## What this router should answer

- How to call DeepAnalyze from Python or through an OpenAI-compatible client.
- How to upload files, keep a thread workspace, and interpret generated files.
- How to launch or preflight the browser and notebook experiences.
- How to choose a DeepAnalyze vLLM command from GPU memory and context requirements.
- How to plan tag-extension, quantization, SFT, RL, or benchmark commands without running placeholder-heavy jobs blindly.

## Minimal read-only check

If you need a quick confidence check without starting services, use the bundled checker:

```bash
python scripts/check_deepanalyze_environment.py --repo-root <DeepAnalyze checkout>
```

That checker verifies the core Python imports, selected source-file compilation, `DeepAnalyzeVLLM`, API TestClient behavior, and WebUI v2 TestClient behavior.

## Route away from this root when

- You already know the exact sub-skill and only need its detailed reference.
- The task is only about the older legacy browser demo, unless the user explicitly asks for it.
- The task is about a different package's agent framework, model server, or benchmark harness.

## Preferred mental model

- `api-and-clients` = "How do I use DeepAnalyze programmatically or test the API?"
- `interactive-frontends` = "How do I use the CLI, browser demo, or notebook UI?"
- `model-serving` = "How do I size, serve, or customize DeepAnalyze-8B?"
- `training-and-evaluation` = "How do I dry-run training, RL, or benchmark jobs?"

When a request spans multiple areas, pick the owner of the primary workflow first and then follow its cross-links.
