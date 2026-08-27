# Classic API and CLI Reference

## Installed package facts

The `classic` Poetry project is `autogpt-classic` version `0.5.0`. Package roots are:

| Package | Source root | Purpose |
| --- | --- | --- |
| `autogpt` | `original_autogpt/autogpt` | Legacy autonomous agent CLI and server |
| `forge` | `forge/forge` | Agent framework and server implementation |
| `direct_benchmark` | `direct_benchmark/direct_benchmark` | Direct benchmark harness |

Poetry scripts are:

| Script | Entry point |
| --- | --- |
| `autogpt` | `autogpt.app.cli:cli` |
| `serve` | `autogpt.app.cli:serve` |
| `direct-benchmark` | `direct_benchmark.__main__:main` |

Safe help checks:

```bash
poetry run autogpt --help
poetry run autogpt run --help
poetry run autogpt serve --help
poetry run serve --help
poetry run direct-benchmark --help
```

Observed `autogpt` command groups include `config`, `run`, and `serve`.

## Direct benchmark commands

The benchmark CLI exposes:

- `run`
- `state`
- `list-benchmarks`
- `list-challenges`
- `list-models`
- `list-strategies`

Primary `run` options include strategy/model selection, categories, tests, attempts, parallel workers, timeout/cutoff, max steps, maintain/improve/explore filtering, dependency override, workspace, challenges directory, reports directory, kept answers, quiet/verbose/JSON output, CI mode, fresh/retry behavior, reset by strategy/model/challenge, debug, and external benchmark loading.

## Strategies and model presets

Strategies include:

- `one_shot`
- `rewoo`
- `plan_execute`
- `reflexion`
- `tree_of_thoughts`
- `lats`
- `multi_agent_debate`

Model presets include Claude, OpenAI, GPT-5, O-series reasoning, and extended-thinking variants such as `claude-thinking-10k`, `claude-thinking-25k`, `claude-thinking-50k`, `o1-low`, `o3-high`, and `gpt5-medium`. If `--models` is omitted, the harness chooses a default from available API key env vars in Claude, OpenAI, then Groq order, falling back to OpenAI. Do not rely on that fallback when cost/provider choice matters.

## Test locations

- Forge permission and provider tests: `forge/tests/`.
- Original AutoGPT unit tests: `original_autogpt/tests/`.
- Direct benchmark core modules: `direct_benchmark/direct_benchmark/`.
- Challenge data and challenge README: `direct_benchmark/challenges/`.

## Report helpers

`direct_benchmark/analyze_reports.py` and `analyze_failures.py` inspect generated benchmark reports. Use them only on user-approved report directories; report files may contain prompts, model outputs, provider names, and local paths.
