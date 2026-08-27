# TurboT2AV Setup and Inference Planning

TurboT2AV is a text-to-audio-video extension distilled from LTX-2 19B. Treat it as a separate workflow from core Wan T2V/I2V TurboDiffusion: it has a separate LTX/Pixi environment, separate checkpoints, a Gemma text encoder dependency, and a different acceleration stack.

## When to use this guidance

Use this reference for:

- planning TurboT2AV student or LTX-2 teacher audio-video inference commands;
- checking whether the user has the required LTX-2 base checkpoint, Gemma directory, TurboT2AV student checkpoint, prompt file, and output directory;
- explaining why the TurboT2AV Pixi/LTX workspace should stay separate from the core TurboDiffusion Wan environment;
- choosing TurboT2AV-specific acceleration flags such as `--attention_type sagesla`, `--sla_topk 0.3`, `--fast_norm`, `--trim_text_context`, and `--quant_linear_backend tilelang_postscale`.

Do not use this reference to replace the LTX-2 project documentation or to maintain its install script. Keep full LTX internals reference-only.

## Environment separation

TurboT2AV uses an LTX-2 Pixi workspace with CUDA 12.8 PyTorch and LTX package editables. Keep that environment separate from any core TurboDiffusion Wan inference/training environment because the dependency set includes LTX-specific packages plus SageAttention, SpargeAttn, and TileLang versions selected for the TurboT2AV path.

Public setup shape, performed by the user in their LTX-2 workspace:

```bash
pixi install
pixi run install-acceleration
```

The `install-acceleration` task installs local LTX packages, CUDA 12.8 PyTorch, SageAttention, SpargeAttn, and TileLang. It may compile or download packages; the bundled skill script does not run it.

### Source-layout import quirk

TurboT2AV acceleration imports TurboDiffusion acceleration symbols for SageSLA/FastNorm and one W8A8 backend. In an installed package environment, normal package imports may be enough. In a source-layout run, make sure the Python process can import both the LTX packages and the TurboDiffusion package/source layout.

Use public placeholders in user-facing commands rather than checkout-specific paths, for example:

```bash
PYTHONPATH=<TURBODIFFUSION_PROJECT>:<TURBODIFFUSION_SOURCE_PACKAGE>:$PYTHONPATH
```

When using the bundled command renderer, pass one or more `--pythonpath <ENTRY>` values if the run needs source-layout imports.

## Required external assets

TurboT2AV inference does not fetch weights automatically. Before rendering a runnable command, confirm these user-supplied assets:

| Asset | Required for | How it is supplied to inference |
| --- | --- | --- |
| LTX-2 19B base checkpoint, commonly `ltx-2-19b-dev.safetensors` | student and teacher | environment variable `TURBO_CHECKPOINT_PATH` |
| Gemma-3-12B-IT-QAT-Q4_0 directory | student and teacher text encoding | environment variable `TURBO_GEMMA_PATH` |
| TurboT2AV student checkpoint, commonly `model.pth` under the TurboT2AV weights | student only | `--student_checkpoint` |
| Bidirectional rCM config | student and teacher | `--config_path` |
| Prompts file | student and teacher | `--prompts_file` |
| Output directory | student and teacher | `--output_dir` |

Gemma is a gated Hugging Face model. The user must accept the model terms and use an authorized Hugging Face token when downloading it. Do not embed tokens in generated commands. If the Gemma directory already exists locally, runtime usually needs the directory path, not the token.

## Prompt file formats

`--prompts_file` accepts either:

- a plain text file with one non-empty prompt per line; or
- a CSV file with a `prompt`, `caption`, or `text` column.

A headerless CSV-like file is treated as one prompt per line, so a line containing a comma is still one prompt unless the first row contains a recognized prompt column.

Useful controls:

- `--num_prompts N` limits the number of prompts loaded from the file.
- `--num_seeds N` renders multiple seeds per selected prompt.
- `--same_seed_for_all_prompts` makes the same seed sequence repeat for every prompt.
- `--num_shards` and `--shard_id` split prompts by index modulo shard count.

## Command construction

Prefer the bundled renderer:

```bash
python <THIS_SUB_SKILL_DIR>/scripts/build_turbot2av_command.py --help
```

The renderer prints a shell command or JSON argv/env description and never executes inference.

### Accelerated student plan

This is the recommended TurboT2AV path. It combines the four-step student checkpoint with SageSLA self-attention, text-context trimming, FastNorm, and TileLang W8A8 linear layers.

```bash
python <THIS_SUB_SKILL_DIR>/scripts/build_turbot2av_command.py \
  --model-kind student \
  --config-path <LTX2_CONFIG.yaml> \
  --prompts-file <PROMPTS.txt-or.csv> \
  --output-dir <STUDENT_OUTPUT_DIR> \
  --base-checkpoint <LTX2_BASE_CHECKPOINT.safetensors> \
  --gemma-path <GEMMA_DIRECTORY> \
  --student-checkpoint <TURBOT2AV_STUDENT_MODEL.pth> \
  --num-prompts 8 \
  --video-height 1024 \
  --video-width 1792
```

By default, the renderer's `auto` acceleration preset expands a student command with:

```text
--attention_type sagesla
--attention_scope self
--sla_topk 0.3
--trim_text_context
--fast_norm
--quant_linear
--quant_linear_scope all
--quant_linear_backend tilelang_postscale
```

### Teacher baseline plan

Use the teacher path when the user wants a 40-step LTX-2 baseline for comparison rather than the distilled student.

```bash
python <THIS_SUB_SKILL_DIR>/scripts/build_turbot2av_command.py \
  --model-kind teacher \
  --config-path <LTX2_CONFIG.yaml> \
  --prompts-file <PROMPTS.txt-or.csv> \
  --output-dir <TEACHER_OUTPUT_DIR> \
  --base-checkpoint <LTX2_BASE_CHECKPOINT.safetensors> \
  --gemma-path <GEMMA_DIRECTORY> \
  --teacher-mode native_rf \
  --teacher-steps 40 \
  --acceleration-preset none
```

Teacher commands do not require `--student_checkpoint`. They can be used for dense baselines or for controlled experiments with acceleration enabled explicitly.

## Main inference CLI options

The underlying module is:

```bash
python -m ltx_distillation.tools.run_av_inference_eval
```

Core options:

| Option | Meaning |
| --- | --- |
| `--config_path` | LTX/TurboT2AV config file. Environment variables can override checkpoint and output paths inside the loaded config. |
| `--prompts_file` | Prompt text or CSV file. |
| `--output_dir` | Directory where samples, prompt shard files, and optional timing JSON are written. |
| `--model_kind {student,teacher}` | Selects distilled student or LTX teacher generation. |
| `--student_checkpoint PATH` | Required for student. Accepts a regular checkpoint or FSDP-style directory with `sharded/` and `metadata.pth`. |
| `--student_param {auto,native_rf,rcm_trig}` | Student parameterization; `auto` follows the config's DMD style. |
| `--student_strict` | Enforce strict state-dict loading for the student checkpoint. |
| `--teacher_mode {native_rf,rcm_trig}` | Teacher sampling mode. |
| `--teacher_steps N` | Number of teacher scheduler steps; the public baseline uses 40. |
| `--skip_decode` | Benchmark generator latency only; skip VAE decode and sample writing. |
| `--timing_json PATH` | Write generator timing records. With `--skip_decode`, a timing file is created in the output directory if no path is supplied. |
| `--video_height`, `--video_width`, `--num_frames` | Override config dimensions. `num_frames` must satisfy the LTX temporal compression requirement used by the model. |

Output files for decoded samples are named like `sample_0000.mp4`, `sample_0000.wav`, and `sample_0000.json`. The separate WAV is written even when MP4 audio muxing succeeds because downstream audio-video evaluation expects it.

## Multi-shard and repeated runs

For multi-shard launches, the runner uses a model-initialization file lock by default so shards do not all initialize heavy models concurrently. Controls:

- `--num_shards` and `--shard_id` select the shard.
- `--init_lock_path PATH` chooses an explicit lock file.
- `--no_init_lock` disables the default lock.
- `AV_EVAL_INIT_LOCK_DIR` changes the default lock directory.
- `AV_EVAL_NO_INIT_LOCK=1` also disables the lock.

For repeated runs, `--overwrite` controls whether existing decoded MP4/WAV pairs are regenerated. Without `--overwrite`, existing complete samples are skipped.
