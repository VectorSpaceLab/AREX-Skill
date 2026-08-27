# Data and Checkpoints

This reference bundles the installation, data-layout, checkpoint, and storage facts needed by the setup-and-data router.

## Quick start install stack

The project README's base install sequence is:

```bash
export VLA_ADAPTER_REPO_ROOT=/abs/path/to/VLA-Adapter
cd "$VLA_ADAPTER_REPO_ROOT"
conda create -n vla-adapter python=3.10.16 -y
conda activate vla-adapter
pip install torch==2.2.0 torchvision==0.17.0 torchaudio==2.2.0
python -m pip install -e "$VLA_ADAPTER_REPO_ROOT"
```

Notes:

- Install PyTorch first, then the editable package install, then FlashAttention.
- `ninja --version` is used as a quick compile-tool sanity check.
- The repository's published environment snapshot matches the README pins for the core stack.
### External LIBERO installation

LIBERO is not a VLA-Adapter package extra. The repository's `pyproject.toml` has no
`libero` optional-dependency group, so `pip install -e ".[libero]"` is not a
supported installation command. From the VLA-Adapter repository root, clone the
upstream simulator package, install it editable, and then install the exact
benchmark requirements file:

```bash
cd "$VLA_ADAPTER_REPO_ROOT"
git clone https://github.com/Lifelong-Robot-Learning/LIBERO.git
pip install -e LIBERO
pip install -r experiments/robot/libero/libero_requirements.txt
```

`experiments/robot/libero/libero_requirements.txt` currently contains exactly:

```text
imageio[ffmpeg]
robosuite==1.4.1
bddl
easydict
cloudpickle
gym
```

These commands install packages only; they do not fetch LIBERO task assets,
initial states, or RLDS data. Keep those external assets and their paths separate
from the base package installation.

### External CALVIN installation and requirements

CALVIN is likewise external and is not represented by a VLA-Adapter extra. The
upstream checkout uses submodules and its own install script; run the install
from the checkout rather than assuming that the editable VLA-Adapter install
provides `calvin_agent` or `calvin_env`:

```bash
cd "$VLA_ADAPTER_REPO_ROOT"
git clone --recurse-submodules https://github.com/mees/calvin.git
export CALVIN_ROOT="$VLA_ADAPTER_REPO_ROOT/calvin"
cd "$CALVIN_ROOT"
sh install.sh
```

The upstream `install.sh` installs `wheel` and `cmake==3.18.4`, then installs
`calvin_env/tacto`, `calvin_env`, and `calvin_models` editable. Its two package
requirement files are the source of the remaining CALVIN Python dependencies:

- [`calvin_env/requirements.txt`](https://raw.githubusercontent.com/mees/calvin_env/main/requirements.txt)
  supplies `cloudpickle`, `gitpython`, `gym`, `hydra-core`, `hydra-colorlog`,
  `matplotlib`, `numba`, `numpy`, `numpy-quaternion`, `omegaconf`,
  `opencv-python`, `pandas`, `pybullet`, and `scipy`.
- [`calvin_models/requirements.txt`](https://raw.githubusercontent.com/mees/calvin/main/calvin_models/requirements.txt)
  supplies `pytorch-lightning==1.8.6`, `moviepy`, and `termcolor` (as well as
  the other model-side requirements). The import name `pytorch_lightning` maps
  to the distribution name `pytorch-lightning`.

If `pyhash` fails during the upstream install, the CALVIN README documents
`python -m pip install setuptools==57.5.0` before retrying; this is an upstream
compatibility workaround, not a VLA-Adapter pin. Downloaded ABC→D native assets
are also required; an RLDS snapshot is not a substitute for the evaluator's
native `calvin/dataset/task_ABC_D/validation` and model configuration layout.

The read-only environment checker can inspect the base stack, optional imports,
and CUDA without launching a benchmark:

```bash
python "$VLA_ADAPTER_SKILL_ROOT/scripts/check_vla_adapter_env.py" \
  --repo-root "$VLA_ADAPTER_REPO_ROOT" \
  --check-optional \
  --require-cuda
```

Treat a checker result as diagnostics only, not as benchmark readiness.

### Snapshot versus installation source

`our_envs.txt` is a record of one previously captured environment (including
`Calvin`, `calvin_env`, `moviepy`, `pytorch-lightning`, and `termcolor`). It is a
verification snapshot, **not** a requirements file, lockfile, or installation
source. Install the external stacks from their upstream checkout and requirement
files above; do not infer that a snapshot entry is supplied by the VLA-Adapter
base package.

The shared `experiments/robot/robot_utils.py` serialization path is lazy-loaded.
Therefore the base VLA-Adapter import surface does not require the ALOHA-only
MessagePack packages. For ALOHA workflows, install the explicit extras in
`experiments/robot/aloha/requirements_aloha.txt` (`msgpack`, `msgpack-numpy`,
`dm-env`, `ipython`, and optional `imageio[ffmpeg]`); ROS packages and robot
drivers remain outside pip.
 

### Dependency pins visible in `pyproject.toml`

| Area | Pins or constraints |
| --- | --- |
| Core VLA stack | `torch==2.2.0`, `torchvision==0.17.0`, `torchaudio==2.2.0`, `transformers==4.40.1`, `peft==0.11.1`, `timm==0.9.10`, `sentencepiece==0.1.99`, `draccus==0.8.0` |
| Data / TFDS | `tensorflow==2.15.0`, `tensorflow_datasets==4.9.3`, `tensorflow_graphics==2021.12.3`, `dlimp @ git+https://github.com/moojink/dlimp_openvla` |
| Utility stack | `accelerate>=0.25.0`, `rich`, `wandb`, `jsonlines`, `json-numpy`, `protobuf`, `imageio`, `uvicorn`, `fastapi` |

### Environment snapshot evidence

The shipped `our_envs.txt` confirms the expected stack was actually installed. The most relevant entries are:

- `torch 2.2.0`, `torchvision 0.17.0`, `torchaudio 2.2.0`
- `flash-attn 2.5.5`
- `tensorflow 2.15.0`, `tensorflow-datasets 4.9.3`, `tensorflow-graphics 2021.12.3`
- `transformers 4.40.1`, `peft 0.11.1`, `timm 0.9.10`, `sentencepiece 0.1.99`
- `libero 0.1.0`, `Calvin 0.0.1`, `calvin_env 0.0.1`, `tacto 0.0.3`

Treat that file as a verification snapshot, not as a lockfile.

### ALOHA-only extras

`experiments/robot/aloha/requirements_aloha.txt` adds only the robot-specific extras that are still needed after the base install:

- `msgpack`
- `msgpack-numpy`
- `dm-env`
- `ipython`
- `imageio[ffmpeg]`

ROS packages such as `rospy`, `cv_bridge`, `sensor_msgs`, `geometry_msgs`, and `interbotix_*` are outside pip and must come from the robot environment.

## Pretrained VLM and config bundle

The repository keeps the configuration bundle in `pretrained_models/configs/` and the large Prismatic VLM weights alongside it in `pretrained_models/prism-qwen25-extra-dinosiglip-224px-0_5b/`.

The config bundle is expected to contain at least:

- `config.json`
- `configuration_prismatic.py`
- `modeling_prismatic.py`
- `processing_prismatic.py`
- `processor_config.json`
- `preprocessor_config.json`
- `generation_config.json`
- tokenizer files such as `tokenizer.json`, `tokenizer_config.json`, `special_tokens_map.json`, `added_tokens.json`, `merges.txt`, and `vocab.json`

The checked-in `config.json` confirms the bundle is the OpenVLA/Prismatic remote-code package:

- `model_type = openvla`
- `auto_map` entries for `AutoConfig` and `AutoModelForVision2Seq`
- `llm_backbone_id = qwen25-0_5b-extra`
- `image_resize_strategy = resize-naive`
- `llm_max_length = 2048`
- embedded `norm_stats` for denormalization

## Checkpoint layout

Local VLA checkpoints are validated through the run directory, not just the `.pt` file.

Expected shape:

```text
<run-dir>/
  config.json
  dataset_statistics.json
  checkpoints/
    step-...pt
    latest-checkpoint.pt   # if the run keeps a rolling checkpoint
```

Rules to keep in mind:

- If you point the loader at a single `.pt`, it should live under `checkpoints/`.
- The parent run directory must still contain `config.json` and `dataset_statistics.json`.
- `dataset_statistics.json` is required for action denormalization during inference; missing it can surface as an absent `unnorm_key`.

## Benchmark data layouts

### LIBERO

The README places the benchmark data under `data/libero/` with one builder directory per suite:

```text
data/libero/
  libero_spatial_no_noops/1.0.0/
  libero_object_no_noops/1.0.0/
  libero_goal_no_noops/1.0.0/
  libero_10_no_noops/1.0.0/
```

Each `1.0.0` directory should contain TFDS metadata plus TFRecord shards. The modified Hugging Face archive is named `modified_libero_rlds`; the local path must match the unmodified benchmark names above.

Expected size is roughly 10 GB for the four modified RLDS suites together.

### CALVIN

The training layout in this repository uses the RLDS/TFDS dataset name `calvin_abc`.

Typical layout:

```text
calvin_abc/1.0.0/
```

The README describes the HF RLDS download as `calvin_abc_rlds`; the bundled checker accepts either label and reports which one it found. If you are wiring training commands, keep the dataset name expected by the config registry, not the archive alias.

The README estimates this RLDS archive at about 50 GB.

### ALOHA

ALOHA data must be converted from hdf5 into TFDS format before training. The default training script points at:

```text
${ROOT_DIR}/datasets/cobot_aloha/tfds
```

The root should contain one or more registered dataset directories, each with a `1.0.0/` TFDS version directory. `setup_training.sh` registers the dataset in the OXE config, mixture, and transform registries.

The ALOHA data path is intentionally more flexible than LIBERO/CALVIN, because the registered dataset names are user/task dependent. The bundled validator therefore looks for any TFDS-style dataset directory under the provided root.

### ALOHA offline model mirrors

If you enable local loading, `download_models.sh` mirrors the following repos under `ai_models/`:

- `timm/vit_large_patch14_reg4_dinov2.lvd142m`
- `timm/ViT-SO400M-14-SigLIP`
- `Qwen/Qwen2.5-0.5B`
- `Stanford-ILIAD/prism-qwen25-extra-dinosiglip-224px-0_5b`

`setup_training.sh --local-models` then rewrites the relevant source files to point at those local paths.

## Storage planning

Rule-of-thumb planning from the README and environment evidence:

| Artifact | Planning note |
| --- | --- |
| LIBERO RLDS | About 10 GB total for the modified suites |
| CALVIN RLDS | About 50 GB |
| ALOHA TFDS | Task-dependent; plan for a dedicated TFDS volume |
| Pretrained VLM weights | Keep the large Prismatic VLM bundle beside `pretrained_models/configs/` |
| Trained checkpoints | About 3 GB per model according to the README |
| Local model mirrors | Reserve extra room for Qwen and timm mirrors if using offline ALOHA setup |

Recommended layout:

- one volume for datasets
- one volume for `pretrained_models/` and mirrored HF assets
- one volume for `outputs/`
- one volume for logs and experiment metadata

## Safe validation example

The bundled checker is read-only and can validate data roots, configs, and checkpoints together:
```bash
python "$VLA_ADAPTER_SKILL_ROOT/sub-skills/setup-and-data/scripts/validate_data_layout.py" \
  --benchmark libero \
  --data-root "$VLA_ADAPTER_REPO_ROOT/data/libero" \
  --checkpoint "$VLA_ADAPTER_REPO_ROOT/outputs/LIBERO-Spatial-Pro" \
  --vlm-config-dir "$VLA_ADAPTER_REPO_ROOT/pretrained_models/configs" \
  --require-existing
```

