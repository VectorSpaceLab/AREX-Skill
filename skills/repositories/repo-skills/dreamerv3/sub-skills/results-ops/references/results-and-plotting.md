# Results And Plotting

Use this reference when a user provides a DreamerV3 run logdir, scalar JSONL files, Scope summaries, TensorBoard/WandB/Expa outputs, or gzipped benchmark score artifacts.

## Logger Outputs

DreamerV3 constructs a logger with terminal output always enabled. Additional outputs are selected by `logger.outputs`; the default output list is `jsonl` and `scope`.

| Output selector | Produced artifact or service | Contract |
| --- | --- | --- |
| terminal | Console lines filtered by the logger filter | Default filter includes score, length, FPS, ratio, selected train losses, and selected random metrics. |
| `jsonl` | `metrics.jsonl` and `scores.jsonl` in the run logdir | Appends scalar JSON records. `scores.jsonl` is filtered to records whose metric name matches `episode/score`. |
| `scope` | Scope summary files in the run logdir | View with `python -m scope.viewer --basedir <logdir-parent> --port 8000`. |
| `tensorboard` | TensorBoard event files in the run logdir | Requires TensorBoard support to be installed and the output enabled. |
| `wandb` | A WandB run named from trailing logdir components | Requires WandB installation, login, and network policy suitable for the host. |
| `expa` | Expa tracking run | Uses a project/run naming convention derived from the logdir. Treat as optional infrastructure-specific output. |

The logger multiplies steps by the environment action repeat for the selected suite when reporting summaries. For cross-suite comparisons, confirm whether you are comparing environment steps, agent steps, or repeated action steps.

## JSONL Metric Schema

`metrics.jsonl` and `scores.jsonl` are newline-delimited JSON objects. Each object has a numeric `step` plus zero or more scalar metrics:

```json
{"step": 12000, "episode/score": 17.5, "episode/length": 842.0}
```

Practical notes:

- `metrics.jsonl` can contain many slash-separated keys: training losses, replay stats, episode statistics, usage, timers, and FPS.
- `scores.jsonl` is intentionally sparse and score-focused; it can remain absent or empty until an episode score has been logged.
- JSONL files are append-only. A run interrupted during writing can leave a malformed final line. Robust readers should skip invalid trailing lines rather than discard the file.
- If a requested key is missing, list available keys first instead of guessing.

Use the bundled standard-library summarizer:

```sh
python scripts/metrics_summary.py --input <logdir>/metrics.jsonl --list-keys
python scripts/metrics_summary.py --input <logdir>/scores.jsonl --key episode/score --last 10
python scripts/metrics_summary.py --input <logdir>/metrics.jsonl --key episode/length --last 10
```

The same script can scan a directory; it will look for `metrics.jsonl`, `scores.jsonl`, and `*.json.gz` files below that directory.

## Scope Viewer

Default DreamerV3 logs include Scope summaries. To view them:

```sh
python -m pip install -U scope
python -m scope.viewer --basedir <logdir-parent> --port 8000
```

Point `--basedir` at the directory that contains run subdirectories, not necessarily at a single run. If the viewer cannot start due to package, port, or browser restrictions, preserve the logdir and fall back to JSONL summarization.

## TensorBoard, WandB, And Expa

These outputs are optional and only appear if enabled in `logger.outputs`:

- TensorBoard: run `tensorboard --logdir <logdir-parent>` after confirming event files exist.
- WandB: confirm `wandb` is installed, credentials are configured, and outbound network is permitted.
- Expa: expect infrastructure-specific credentials/project naming; use JSONL and Scope as portable fallbacks.

Do not claim a run failed only because one optional viewer/tracker is absent. The portable artifacts are `metrics.jsonl`, `scores.jsonl`, Scope summaries, checkpoints, and replay/logdir contents.

## Gzipped Benchmark Score Records

DreamerV3 benchmark score artifacts use gzip-compressed JSON arrays. Each record has this schema:

```json
{
  "task": "atari_pong",
  "method": "dreamerv3",
  "seed": 0,
  "xs": [0, 100000, 200000],
  "ys": [null, -18.0, -12.5]
}
```

Contract:

- `task`: benchmark task id, commonly prefixed by suite (`atari_`, `dmc_`, `dmlab_`, `procgen_`, `minecraft_`).
- `method`: algorithm name such as `dreamerv3`, `ppo_fixhp`, or another baseline.
- `seed`: seed id.
- `xs`: budget/step values for the curve.
- `ys`: score values aligned to `xs`; `null` represents missing or undefined values.

Bundled score artifact naming follows `<benchmark>-<method>.json.gz`. Known benchmark families include `atari100k`, `atari57`, `dmc_proprio`, `dmc_vision`, `dmlab30`, `minecraft_diamond`, and `procgen`. Known methods represented by the score artifacts include `dreamerv3`, `ppo_fixhp`, `muzero`, `d4pg`, `ddpg`, `dmpo`, `mpo`, `curl`, `drqv2`, `sac`, `impala`, `r2d2`, `rainbow`, and `ppg`.

Use the summarizer on one or more gzip score files:

```sh
python scripts/metrics_summary.py --input scores.json.gz --key episode/score --last 5
python scripts/metrics_summary.py --input atari57-dreamerv3.json.gz --list-keys
```

For gzip score records, `episode/score`, `score`, and `ys` all refer to the `ys` curve; `step` and `xs` refer to `xs`.

## Plotting Workflow Concepts

DreamerV3's plotting workflow loads run curves from `scores.jsonl`, bins them by step/budget, computes per-task and aggregate statistics, and plots curves. It uses packages such as pandas, NumPy, Matplotlib, ruamel.yaml, tqdm, and elements. Use it as a conceptual workflow when those dependencies and the expected directory layout are available; otherwise prefer the bundled lightweight summarizer.

Key plotting concepts to preserve when adapting:

| Concept | Meaning |
| --- | --- |
| X keys | Plot readers look for `xs` in score-record JSON or `step` in JSONL. |
| Y keys | Plot readers look for `ys` in score-record JSON or `episode/score` in JSONL. |
| Binning | Curves are binned into a fixed number of step intervals or a supplied bin size before aggregation. |
| Seed/method/task grouping | Runs are grouped by task, method, and seed; comparisons should avoid mixing unrelated methods or tasks. |
| Threshold mode | A y-threshold can turn scores into binary success values before aggregation. |
| Auto stats | Atari uses gamer-normalized mean/median; DMC uses mean/median; DMLab uses normalized/capped mean; ProcGen uses hard-mode normalization. |
| Self-normalization | When no benchmark reference applies, min/max observed values can form a self-baseline, but this changes interpretation. |

## Baseline Normalization Concepts

The benchmark normalization table stores `(low, high)` reference scores. Normalized score is:

```text
normalized = (score - low) / (high - low)
```

Aggregate meanings:

- **Atari gamer mean/median**: normalize each Atari task by human-gamer reference ranges, then average or take median across tasks.
- **DMLab capped mean**: normalize DMLab tasks, then optionally cap scores at 1 before averaging.
- **ProcGen normalized mean**: normalize by hard-mode reference ranges.
- **Runs count**: count finite binned values per method to reveal missing seeds/tasks.

When presenting results, always state whether the numbers are raw scores, normalized scores, capped normalized scores, or self-normalized scores.

## Safe Result Summary Procedure

1. Confirm the path is a logdir, JSONL file, or gzip score-record file.
2. List keys first if the expected key is unknown:
   ```sh
   python scripts/metrics_summary.py --input <path> --list-keys
   ```
3. Summarize the intended scalar:
   ```sh
   python scripts/metrics_summary.py --input <path> --key episode/score --last 20
   ```
4. Report count, first/last step, latest value, recent mean, min, and max.
5. If results are from gzip score records, include task/method/seed in the report.
6. If files are malformed, skip only the invalid line/record and state how many parse errors were ignored.
7. Do not infer learning success from a single last value; compare recent mean, curve shape, and expected benchmark scale.
