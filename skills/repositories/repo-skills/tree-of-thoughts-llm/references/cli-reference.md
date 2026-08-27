# CLI Reference

The bundled runner is `scripts/run_tot.py`. It mirrors the repository runner
interface and writes JSON logs under `./logs/` relative to the launch location.

## Core flags

| Flag | Meaning | Default / choices |
| --- | --- | --- |
| `--backend` | OpenAI chat backend used by `tot.models.gpt` | `gpt-4`, `gpt-3.5-turbo`, or `gpt-4o`; default `gpt-4` |
| `--temperature` | Sampling temperature for completions | default `0.7` |
| `--task` | Task factory key | required; `game24`, `text`, or `crosswords` |
| `--task_start_index` | First dataset index to run | default `900` |
| `--task_end_index` | End index, exclusive | default `1000` |
| `--naive_run` | Use naive sampling instead of BFS | off by default |
| `--prompt_sample` | Prompt family used by the naive path or sample mode | `standard` or `cot` |
| `--method_generate` | Thought generation strategy for BFS | `sample` or `propose` |
| `--method_evaluate` | Candidate scoring strategy for BFS | `value` or `vote` |
| `--method_select` | Frontier selection strategy | `sample` or `greedy`; default `greedy` |
| `--n_generate_sample` | Number of generated continuations | default `1` |
| `--n_evaluate_sample` | Number of score or vote prompts | default `1` |
| `--n_select_sample` | Frontier width after selection | default `1` |

## Common command patterns

### Install and smoke-check

```bash
pip install -e .
python scripts/check_install.py
```

### Run the shared BFS path

```bash
python scripts/run_tot.py   --task game24   --method_generate propose   --method_evaluate value   --method_select greedy   --n_evaluate_sample 3   --n_select_sample 5
```

### Run a naive baseline

```bash
python scripts/run_tot.py   --task text   --naive_run   --prompt_sample cot   --n_generate_sample 10   --temperature 1.0
```

## Output layout

The runner writes one JSON file per invocation under:

```text
./logs/<task>/<backend>_<temperature>_..._start<start>_end<end>.json
```

The file contains the step-by-step frontier, generated candidates, selected
states, and the per-example task info returned by `test_output`.

## Notes for task selection

- `game24` uses `propose` + `value` for the paper-style BFS path.
- `text` uses `sample` + `vote` for BFS and `standard`/`cot` for naive runs.
- `crosswords` uses `sample` + `vote` for BFS, but the repo also ships a
  DFS-specific helper in `sub-skills/crosswords/scripts/dfs_search.py`.
