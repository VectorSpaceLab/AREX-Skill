---
name: lm-evaluation-harness
description: "Use EleutherAI LM Evaluation Harness for language-model evaluation
  runs, YAML task authoring, model backend setup, result logging,
  decontamination hygiene, and maintainer workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# LM Evaluation Harness

Use this skill when a user asks for help with EleutherAI's `lm-evaluation-harness` / `lm_eval`: running evaluations, writing tasks, choosing model backends, interpreting results, or maintaining evaluation hygiene.

## First Checks

- Install the base package with Python `>=3.10`; model backends are optional extras and are not included in the base package.
- Verify the CLI with `lm-eval --help`; the current command surface is `run`, `ls`, and `validate`, with legacy no-subcommand usage mapped to `run`.
- Use `references/repo-provenance.md` before refreshing this skill against a checkout; changed commits, dirty paths, metadata, or entry points mean the skill may be stale.
- Use `references/troubleshooting.md` for cross-cutting install/import, optional dependency, credential, network, and unsafe-code issues.
- Run `scripts/check_lm_eval_install.py` for a local, safe package/CLI/registry check before deeper debugging.

## Route By User Intent

| User request | Use this route |
| --- | --- |
| Run an evaluation, build an `lm-eval run` command, use YAML config, call `simple_evaluate()`, debug seeds/cache/chat flags | `sub-skills/evaluation-runs/` |
| Create or repair YAML tasks, groups, tags, filters, metrics, Jinja prompts, `!function` helpers, external task dirs | `sub-skills/task-authoring/` |
| Choose/install/configure `hf`, `vllm`, API, local server, custom `LM`, chat-template, or thinking-token backends | `sub-skills/model-backends/` |
| Read result JSON, sample logs, schemas, W&B/Trackio/HF Hub args, local summaries, result comparisons | `sub-skills/result-logging/` |
| Review decontamination fields, request caches, clean-training-data safety, maintainer tests, advanced hygiene | `sub-skills/decontamination-maintenance/` |

## Minimal Patterns

```bash
lm-eval ls tasks
lm-eval validate --tasks hellaswag,arc_easy
lm-eval run --model hf --model_args pretrained=gpt2,dtype=float32 --tasks hellaswag --limit 10
```

```python
import lm_eval

results = lm_eval.simple_evaluate(
    model="hf",
    model_args="pretrained=gpt2,dtype=float32",
    tasks=["hellaswag"],
    limit=10,
)
```

## Important Boundaries

- Do not assume a base install can import every model backend; install the narrow extra for the chosen backend, such as `lm_eval[hf]`, `lm_eval[vllm]`, `lm_eval[api]`, or `lm_eval[litellm]`.
- Do not run model downloads, dataset downloads, API calls, service uploads, GPU-heavy evaluations, or multi-day decontamination scripts unless the user explicitly approves the cost and credentials/hardware are available.
- Do not copy or depend on original checkout docs, scripts, notebooks, or tests at runtime; this skill bundles distilled references and safe helper scripts.
- Treat native tests/examples named in references as maintainer guidance for a live checkout, not as required runtime dependencies of this exported skill.

## Repo-Level Files

- `references/repo-provenance.md` records the source snapshot and refresh criteria.
- `references/troubleshooting.md` covers cross-cutting failures before routing into sub-skills.
- `scripts/check_lm_eval_install.py` checks import metadata, CLI help, and lazy model registry behavior without importing heavy backend classes.
