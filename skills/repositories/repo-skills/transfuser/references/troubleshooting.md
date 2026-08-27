# Cross-Cutting Troubleshooting

## Installation and import

- **`ModuleNotFoundError: mmcv`, `mmdet`, `mmsegmentation`, `mmcls`, or
  `torch_scatter`:** install the version-matched packages from the historical
  CUDA/PyTorch matrix; do not satisfy the import with an unrelated latest
  wheel. Re-run the package and CUDA probes before loading `model.py`.
- **`undefined symbol`, missing operator, or import crash in `mmcv.ops` or
  `torch_scatter`:** the compiled extension does not match the installed
  PyTorch/CUDA/Python ABI. Recreate or repair an isolated environment with a
  matching wheel family; do not mix CPU and CUDA builds.
- **`No module named carla`:** the external CARLA Python API is not on the
  runtime `PYTHONPATH`. Install/use the documented CARLA 0.9.10.1 distribution
  and add its Python API plus ScenarioRunner/leaderboard roots only in the
  execution environment. This is an external-runtime block, not a reason to
  claim the package-only skill passed simulation.
- **`torch.cuda.is_available()` is false:** inspect the selected Python's torch
  build, driver visibility, `CUDA_VISIBLE_DEVICES`, and container GPU passthrough.
  A CPU torch wheel cannot validate the learned workflow.

## Data and configuration

- **Dataset validator reports no eligible frames:** check the
  `Scenario/Town/Route` hierarchy, all required modality directories, four
  future label frames, and the loader's intentional first/last-frame margins.
  Use `model-training`'s data-format reference and validator rather than
  changing the loader silently.
- **Missing `args.txt`, `.pth`, or derived optimizer checkpoint:** point
  `TEAM_CONFIG` at the directory containing `args.txt` and model files, not at
  the file itself. Resume training requires the matching
  `optimizer_<epoch>.pth` derived from the model checkpoint name.
- **Invalid route/scenario references:** validate XML/JSON independently and
  confirm town/scenario IDs and route IDs agree before starting CARLA.

## CLI and launch semantics

- **DDP `KeyError` for `RANK`, `LOCAL_RANK`, or `WORLD_SIZE`:** use
  `--parallel_training 0` with ordinary `python train.py` for one GPU, or start
  the script through `torchrun` with the documented process count. Do not set
  fake rank values inside the source.
- **CARLA evaluator cannot find files:** use absolute operator-supplied roots
  for `CARLA_ROOT`, `SCENARIO_RUNNER_ROOT`, `LEADERBOARD_ROOT`, `SCENARIOS`,
  `ROUTES`, `TEAM_AGENT`, and `TEAM_CONFIG`. Use the command builders to emit
  and inspect the final environment before execution.
- **Evaluation resumes an unexpected run:** inspect `CHECKPOINT_ENDPOINT` and
  `RESUME`; use a new result path for an independent run and retain the route
  and scenario files used to produce it.

## External operations

- **Training or inference runs out of memory:** reduce per-GPU batch size,
  worker count, image/model options, or use the documented disk cache only
  after checking its storage location. Do not assume a smaller CPU run proves
  CUDA behavior.
- **CARLA hangs, times out, or returns no sensor data:** confirm the server
  version/port, synchronous sensor timing, route assets, ScenarioRunner
  compatibility, and server logs. Stop before retrying if the server process
  or checkpoint is not known-good.
- **Docker or Alpha submission fails:** first run the submission-layout
  preflight and verify Docker/GPU privileges and checkpoint placement. Cloud
  login/submission needs credentials and network and is never a safe automatic
  recovery step.
- **Result parser aborts:** inspect stderr for failed route records, missing
  results, zero-start routes, or a route-count mismatch. Repair the input set;
  do not interpret a partial aggregate as a benchmark result.
