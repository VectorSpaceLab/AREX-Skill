---
name: inference
description: "Builds and troubleshoots HunyuanVideo single-GPU text-to-video CLI
  and Python API inference workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# HunyuanVideo Inference

Use this sub-skill for single-GPU text-to-video generation with the canonical sampling entry point and the `HunyuanVideoSampler` API. Route setup/checkpoint problems to `../checkpoint-and-setup/SKILL.md`, FP8 or multi-GPU decisions to `../parallel-and-optimization/SKILL.md`, and browser UI tasks to `../web-demo/SKILL.md`.

## Read first

- `references/workflows.md` for practical single-GPU generation recipes.
- `references/cli-reference.md` for parser flags, defaults, and constraints.
- `references/api-reference.md` for verified Python signatures and return contracts.
- `references/troubleshooting.md` for common CLI/API failures.
- `scripts/build_sample_command.py` to construct a safe command without launching generation.

## Safe command construction

Generate a command for a prepared HunyuanVideo checkout:

```bash
python sub-skills/inference/scripts/build_sample_command.py \
  --prompt "A cat walks on the grass, realistic style." \
  --height 544 --width 960 --video-length 129 \
  --seed 42 --use-cpu-offload --save-path ./results
```

The helper validates positive dimensions and the default 3D VAE frame rule before printing the command. It does not load checkpoints or use CUDA.

## Core workflow

1. Validate dependencies and checkpoint layout using the root and setup helpers.
2. Choose height, width, and frame count. Common frame counts are 65 and 129; for the default VAE, use `4n+1`.
3. Include `--flow-reverse`; the repository examples use it.
4. Use `--use-cpu-offload` for single-GPU memory pressure, but do not use it for xDiT distributed mode.
5. Run the printed command only in an environment with downloaded checkpoints and enough CUDA memory.

## API reminder

The high-level Python path is:

```python
from pathlib import Path
from hyvideo.config import parse_args
from hyvideo.inference import HunyuanVideoSampler

args = parse_args()
sampler = HunyuanVideoSampler.from_pretrained(Path(args.model_base), args=args)
outputs = sampler.predict(prompt=args.prompt, height=args.video_size[0], width=args.video_size[1], video_length=args.video_length)
```

Read `references/api-reference.md` before writing nontrivial API code because prompt, seed, video length, and guidance handling have implementation-specific behavior.
