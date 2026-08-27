# Evaluation And Hyperparameter-Search Workflows

Use these workflows after tracker result files already exist. If the user needs to create result files first, route to `../../tracking-inference/`.

## Safe preflight: validate result layout

Run the bundled helper before invoking full metrics:

```bash
python scripts/validate_results_layout.py \
  --tracker-path results \
  --dataset OTB100 \
  --tracker-prefix siamrpn
```

The helper checks only the result tree:

- `<tracker_path>/<dataset>/` exists.
- At least one tracker directory matches `<tracker_prefix*>`.
- Family-specific files exist under selected tracker directories.
- A command skeleton is printed for datasets supported by the stock evaluation CLI.

It does not require benchmark images, JSON sidecars, PySOT imports, CUDA, or snapshots.

## Full evaluation command

Canonical command:

```bash
python tools/eval.py \
  --tracker_path results \
  --dataset OTB100 \
  --tracker_prefix siamrpn \
  --num 4 \
  --show_video_level
```

Short options are also accepted:

```bash
python tools/eval.py -p results -d OTB100 -t siamrpn -n 4 -s
```

Flag semantics:

| Flag | Meaning | Notes |
| --- | --- | --- |
| `--tracker_path`, `-p` | Root that contains `<dataset>/<tracker_name>/...` | Usually `results` for standard PySOT tracking output. |
| `--dataset`, `-d` | Dataset name selecting adapter and metric branch | See [datasets-and-results.md](datasets-and-results.md). |
| `--tracker_prefix`, `-t` | Prefix used to glob tracker directories | Empty string selects all trackers. `siamrpn` matches `siamrpn`, `siamrpn_alex`, etc. |
| `--num`, `-n` | Multiprocessing worker count | The script clamps this to the number of selected trackers; use `1` when debugging. |
| `--show_video_level`, `-s` | Print per-video detail for small tracker sets | Useful for finding broken videos, but noisy for leaderboards. |

Full evaluation prerequisites:

- Benchmark data and `<dataset>.json` sidecar under `testing_dataset/<dataset>/`.
- Tracker results under `<tracker_path>/<dataset>/<tracker_name>/...`.
- Python can import `toolkit` and, for VOT-family metrics, `toolkit.utils.region`.
- OPE metrics can run on CPU; no snapshot or CUDA is needed once result files already exist.

## Dataset-to-metric workflow map

| Dataset family | Evaluation branch | Metrics shown |
| --- | --- | --- |
| OTB, UAV, NFS | OPE | Success and precision. |
| LaSOT | OPE | Success, precision, and normalized precision. |
| VOT2016/2017/2018/2019 | VOT short-term | Accuracy, robustness, lost number, and EAO. |
| VOT2018-LT | VOT long-term | Precision, recall, and F1. |
| GOT-10k, TrackingNet | Server-oriented | Not handled by the stock Python `eval` branches. Validate files locally, then use benchmark server packaging. |

## Hyperparameter search

The hyperparameter-search workflow sweeps tracker runtime parameters, reruns tracking, and writes one tracker result directory per parameter combination. It is not a safe default check because it loads the model snapshot with CUDA, reads benchmark frames, and can run many tracker passes.

Command template:

```bash
python tools/hp_search.py \
  --snapshot path/to/model.pth \
  --config path/to/config.yaml \
  --dataset VOT2018 \
  --penalty-k 0.05,0.5,0.05 \
  --lr 0.35,0.5,0.05 \
  --window-influence 0.1,0.8,0.05 \
  --search-region 255,256,8
```

Range syntax:

- `--penalty-k`, `--lr`, and `--window-influence` parse comma triples as `numpy.arange(start, stop, step)` floats. The stop value is exclusive.
- `--search-region` parses comma triples as `numpy.arange(start, stop, step)` integers.
- Total runs are the product of all four range lengths. Estimate this before launching.

Default ranges from the source workflow:

| Flag | Default | Interpretation |
| --- | --- | --- |
| `--penalty-k` | `0.05,0.5,0.05` | Motion/scale penalty sweep. |
| `--lr` | `0.35,0.5,0.05` | Tracking update learning-rate sweep. |
| `--window-influence` | `0.1,0.8,0.05` | Cosine/window influence sweep. |
| `--search-region` | `255,256,8` | Instance/search size sweep; default produces only `255`. |

Output naming:

```text
hp_search_result/<dataset>/<snapshot_base>_r<region>_pk-<penalty>_wi-<window>_lr-<lr>/...
```

The inner files follow the same dataset family layouts as normal tracking results. Evaluate a selected parameter directory by passing the hp-search root as `--tracker_path` and using `--tracker_prefix` to select the parameterized tracker names.

Example after a sweep:

```bash
python scripts/validate_results_layout.py \
  --tracker-path hp_search_result \
  --dataset VOT2018 \
  --tracker-prefix model_r255_pk-0.050

python tools/eval.py \
  --tracker_path hp_search_result \
  --dataset VOT2018 \
  --tracker_prefix model_r255_pk-0.050 \
  --num 1
```

## VOT integration notes

PySOT includes Python VOT-style result writing and Python AR/EAO/F1 evaluation. Optional official VOT toolkit or MATLAB integration is separate from the minimum Python workflow.

Use official VOT tooling when:

- A benchmark submission requires official workspace packaging.
- The user asks for official challenge protocol, reports, or VOT toolkit integration.
- Python toolkit scores disagree with an official evaluation server and the server is authoritative.

Keep the two workflows distinct: PySOT’s Python evaluator consumes `results/<dataset>/<tracker>/baseline/...` or `longterm/...`; official toolkits may require different workspace configuration and runner wrappers.

## Server benchmark notes

GOT-10k and TrackingNet are server-oriented in this repo’s toolkit scope:

- Tracking can produce server-style text files.
- The stock Python evaluation CLI does not compute leaderboard scores for them.
- Validate the local result file shapes, then follow the benchmark server’s packaging requirements supplied by the user or benchmark docs.

## Minimal verification snippets

Use these only as environment checks, not as benchmark proof:

```bash
python tools/eval.py --help
python tools/hp_search.py --help
python - <<'PY'
from toolkit.evaluation import OPEBenchmark, AccuracyRobustnessBenchmark, EAOBenchmark, F1Benchmark
from toolkit.utils.region import vot_overlap
print(vot_overlap([0, 0, 10, 10], [0, 0, 10, 10], (20, 20)))
PY
```

Expected signal: help text is printed, benchmark classes import, and identical boxes overlap at `1.0`. Full tracking/evaluation still requires user assets.
