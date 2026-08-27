# Evaluation workflows

This reference names native evaluation entrypoints for an external checkout;
the bundled builder only renders commands and never launches evaluation. Set
the absolute source root and use it for every native command:

```bash
export VLA_ADAPTER_REPO_ROOT=/abs/path/to/VLA-Adapter
cd "$VLA_ADAPTER_REPO_ROOT"
```

## Command-builder first

Use the skill-local helper by absolute skill path and pass the external root:

```bash
python "$VLA_ADAPTER_SKILL_ROOT/sub-skills/evaluation/scripts/build_eval_command.py" \
  --repo-root "$VLA_ADAPTER_REPO_ROOT" \
  --benchmark libero \
  --suite libero_spatial \
  --checkpoint outputs/LIBERO-Spatial-Pro \
  --gpu 0 \
  --log-file eval_logs/Spatial--chkpt.log \
  --use-pro-version \
  --num-trials-per-task 50
```

For CALVIN:

```bash
python "$VLA_ADAPTER_SKILL_ROOT/sub-skills/evaluation/scripts/build_eval_command.py" \
  --repo-root "$VLA_ADAPTER_REPO_ROOT" \
  --benchmark calvin \
  --suite calvin_abc \
  --checkpoint outputs/CALVIN-ABC-Pro \
  --gpu 0 \
  --log-file eval_logs/CALVIN--ABC.log \
  --use-pro-version
```

The helper prints an auditable shell command only; it does not create
directories, download checkpoints, or start rollouts. Review the printed
command, ensure the external prerequisites and log directory exist, and run
the native command only from its emitted `cd <absolute-repo-root>` guard.
## LIBERO workflow

Runnable entry point label: `experiments/robot/libero/run_libero_eval.py`.

### Required inputs

- A checkpoint directory or supported model id for the selected suite.
- The external LIBERO simulator stack and its Python packages.
- LIBERO task assets and initial-state data available to the installed LIBERO package.
- CUDA-capable PyTorch for real policy inference.
- Optional but recommended: a writable `eval_logs/` directory for stdout/stderr capture.

### Suite selection

Use these suite names with `--task_suite_name`:

- `libero_spatial`
- `libero_object`
- `libero_goal`
- `libero_10` for LIBERO-Long / LIBERO-10

Do not pass the RLDS training dataset suffix as the task suite name. For example, a checkpoint trained with `libero_10_no_noops` statistics is evaluated with `--task_suite_name libero_10`; the evaluation code can fall back to the `_no_noops` normalization key if it exists in checkpoint statistics.

### Core command shape

The README evaluation snippets reduce to this command shape:

```bash
cd <absolute-repo-root> && CUDA_VISIBLE_DEVICES=0 python experiments/robot/libero/run_libero_eval.py \
  --use_proprio True \
  --num_images_in_input 2 \
  --use_film False \
  --pretrained_checkpoint outputs/LIBERO-Spatial-Pro \
  --task_suite_name libero_spatial \
  --use_pro_version True \
  --num_trials_per_task 50 \
  > eval_logs/Spatial--chkpt.log 2>&1
```

Change the checkpoint, suite, GPU, log file, and Pro flag together. Append `&` only when the user explicitly wants a background run and has a plan for monitoring the log.

### Important `run_libero_eval` defaults

The evaluation dataclass defaults are important because many are not visible in the README command:

- `model_family="openvla"`
- `use_l1_regression=True`
- `use_minivlm=True`
- `use_proprio=True`
- `num_images_in_input=2`
- `use_film=False`
- `center_crop=True`
- `num_open_loop_steps=8`
- `num_steps_wait=10`
- `num_trials_per_task=50`
- `initial_states_path="DEFAULT"`
- `env_img_res=256`
- `use_wandb=False`
- `seed=7`
- `save_version="vla-adapter"`
- `use_pro_version=True`
- `phase="Inference"`

The script's suite max-step limits are 220 for spatial, 280 for object, 300 for goal, and 520 for LIBERO-10.

### LIBERO output surfaces

- Shell redirection: use `eval_logs/*.log` for long-run stdout/stderr capture.
- Internal evaluation text logs: the entry point creates timestamped text logs under its configured local log directory.
- Videos: each episode video is written under `rollouts/vla-adapter/<date>/` with success and task information in the filename.
- Final metric: look for `Total episodes`, `Total successes`, and `Overall success rate` near the end of the log. Rich logging can split the numeric success-rate value onto the next line.

### LIBERO image and gripper cautions

Do not remove or bypass these source-coded transformations when debugging metrics:

- `get_libero_image` rotates `agentview_image` by 180 degrees using `img[::-1, ::-1]`.
- `get_libero_wrist_image` rotates `robot0_eye_in_hand_image` by 180 degrees using the same operation.
- The action postprocessor maps gripper values from `[0, 1]` to `[-1, +1]`, binarizes them, and for OpenVLA flips the sign back to the simulator convention where `-1` means open and `+1` means close.
- Image resizing uses the same JPEG encode/decode plus Lanczos resize path used for training-distribution matching.

If a custom evaluation wrapper skips any of these transformations, do not compare its success rate with the published logs.

## CALVIN workflow

Runnable entry point label: `vla-scripts/evaluate_calvin.py`.

### Required inputs

- A local CALVIN checkpoint directory, normally `outputs/CALVIN-ABC-Pro` for the published Pro run.
- The external CALVIN repository packages importable as `calvin_agent` and `calvin_env`.
- CALVIN ABC→D dataset assets in the layout expected by the evaluator: `calvin/dataset/task_ABC_D/validation` from the run directory.
- CALVIN model configuration assets under the expected `calvin/calvin_models/conf` layout.
- CUDA-capable PyTorch and a renderer configuration suitable for pybullet/EGL.
### CALVIN dependency provenance and stack check

The CALVIN evaluator imports `calvin_agent`, `calvin_env`, `moviepy.editor`,
`pytorch_lightning`, and `termcolor`; none of these are supplied by the
VLA-Adapter base package or a `.[calvin]` extra. Install CALVIN from its
upstream checkout with submodules, then use its own install script:

```bash
cd "$VLA_ADAPTER_REPO_ROOT"
git clone --recurse-submodules https://github.com/mees/calvin.git
export CALVIN_ROOT="$VLA_ADAPTER_REPO_ROOT/calvin"
cd "$CALVIN_ROOT"
sh install.sh
```

The upstream sources are the dependency authority:

- [`calvin_env/requirements.txt`](https://raw.githubusercontent.com/mees/calvin_env/main/requirements.txt)
  provides the environment package requirements.
- [`calvin_models/requirements.txt`](https://raw.githubusercontent.com/mees/calvin/main/calvin_models/requirements.txt)
  provides `pytorch-lightning==1.8.6`, `moviepy`, and `termcolor` (plus the
  model-side requirements). The pip distribution `pytorch-lightning` exposes
  the Python import `pytorch_lightning`.
- The upstream [`install.sh`](https://raw.githubusercontent.com/mees/calvin/main/install.sh)
  installs `wheel`, `cmake==3.18.4`, and editable `tacto`, `calvin_env`, and
  `calvin_models` packages.

Use the skill checker for a non-native import/CUDA diagnostic before any rollout:

```bash
python "$VLA_ADAPTER_SKILL_ROOT/scripts/check_vla_adapter_env.py" \
  --repo-root "$VLA_ADAPTER_REPO_ROOT" \
  --check-optional \
  --require-cuda
```

The checker is diagnostic only and does not establish evaluation readiness.

### Native assets, CUDA, and renderer limitations

- CALVIN evaluation needs the native ABC→D checkout assets at the relative
  `calvin/dataset/task_ABC_D/validation` path and the matching
  `calvin/calvin_models/conf` configuration tree. A `calvin_abc` RLDS snapshot
  is useful for training but is not a substitute for those native assets.
- LIBERO evaluation needs the installed LIBERO task assets and initial-state
  data in addition to its Python requirements. RLDS training data alone does
  not provide the simulator assets.
- Both evaluators are intended for CUDA-capable PyTorch; CPU-only execution is
  not a stated supported benchmark path and GPU memory must be checked for both
  policy inference and simulation.
- Headless operation depends on a working GPU driver and EGL/OpenGL/Mesa
  renderer. The documented Linux fallback packages are
  `libgl1-mesa-dev`, `libegl1-mesa-dev`, `libgles2-mesa-dev`, and `libglew-dev`;
  installing them does not guarantee that the host can create an EGL context.
- CALVIN writes static-camera and gripper-camera MP4s and therefore needs a
  working ffmpeg/MoviePy path plus substantial output storage. Native renderer,
  simulator, driver, and asset limitations remain host-specific.
 
 ### Core command shape


The README evaluation snippet reduces to this command shape:

```bash
cd <absolute-repo-root> && CUDA_VISIBLE_DEVICES=0 python vla-scripts/evaluate_calvin.py \
  --pretrained_checkpoint outputs/CALVIN-ABC-Pro \
  > eval_logs/CALVIN--ABC.log 2>&1
```

The bundled command builder validates `--suite calvin_abc` but does not pass a suite flag, because the evaluator is specialized to CALVIN ABC→D.

### Important `evaluate_calvin` defaults and hard-coded behavior

- `model_family="openvla"`
- `pretrained_checkpoint="../outputs/calvin-abc"` unless overridden.
- `use_l1_regression=True`
- `use_diffusion=False`
- `use_x0_prediction=False`
- `num_images_in_input=2`
- `use_proprio=True`
- `center_crop=False`
- `num_open_loop_steps=8`
- `with_depth=True`, `with_gripper=True`, `with_cfg=True`
- `enrich_lang=False`
- `seed=7`
- `save_version="Pro"`
- The evaluator constructs 1,000 five-instruction sequences and uses an episode length of 360 simulation steps.
- The evaluator sets its CALVIN root to the relative `calvin` directory internally, so do not assume an external environment variable overrides that path.

### CALVIN output surfaces

- Shell redirection: use `eval_logs/*.log` for stdout/stderr capture.
- Result directory: CALVIN writes to `evaluation_results/calvin/<timestamp>_<checkpoint-name>/`.
- Progress file: `success_rate.txt` is appended during evaluation with chain success-rate snapshots.
- Result file: `result.txt` stores the JSON summary written by the evaluator.
- Videos: both static-camera and gripper-camera MP4s are written per subtask and include success/failure in the filename.
- Final metric: the key paper number is `Average successful sequence length`, with chain success rates for 1, 2, 3, 4, and 5 instructions in a row.

## Dependency and runtime checklist

Before launching either benchmark, verify:

1. The checkpoint exists and contains model weights, `dataset_statistics.json`, and the expected component checkpoint files for proprio/action heads when loading locally.
2. The checkpoint suite matches the command suite and normalization key.
3. CUDA is available and the selected GPU has enough memory for the OpenVLA model plus simulator.
4. Base packages from the VLA-Adapter project are installed, including PyTorch, torchvision, transformers, tokenizers, timm, peft, TensorFlow, TFDS, draccus, and image/video foundations. Do not count `moviepy`, `termcolor`, or `pytorch_lightning` as base packages: CALVIN obtains them from its external `calvin_models/requirements.txt`.
5. LIBERO or CALVIN external stacks are installed only for the benchmark being run; their native requirements are not provided by the base package.
6. The renderer can create an EGL/OpenGL context in headless mode; package installation alone does not prove that native renderer assets or drivers work.
7. The log and video output locations have enough disk space; CALVIN especially writes many MP4s during a full 1,000-sequence run.
