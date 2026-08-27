# Local Inference Workflows

## Purpose

Read this for task-level generation recipes. Start with a dry run or preflight check, then run actual generation only when CUDA, model files/access, and license constraints are satisfied. The helper uses the bundled `runtime/pipelines/` implementation by default, so the original checkout is not required.

## Workflow 1: default identity-preserving portrait

1. Prepare an identity image with one clear, large, visible human face.
2. Prefer local model directories when working offline or on a cluster:
   - InfiniteYou model tree under `models/InfiniteYou`.
   - FLUX base model under `models/FLUX.1-dev`.
3. Review the plan:
   ```bash
   python scripts/run_infinite_you_flux.py --dry-run \
     --id-image path/to/id.jpg \
     --prompt "A person, portrait, cinematic" \
     --model-dir models/InfiniteYou \
     --base-model-path models/FLUX.1-dev \
     --out-results-dir path/to/results
   ```
4. Preflight:
   ```bash
   python scripts/run_infinite_you_flux.py --check-only \
     --id-image path/to/id.jpg \
     --prompt "A person, portrait, cinematic" \
     --model-dir models/InfiniteYou \
     --base-model-path models/FLUX.1-dev
   ```
5. Generate after preflight passes:
   ```bash
   python scripts/run_infinite_you_flux.py \
     --id-image path/to/id.jpg \
     --prompt "A person, portrait, cinematic" \
     --model-dir models/InfiniteYou \
     --base-model-path models/FLUX.1-dev \
     --out-results-dir path/to/results
   ```
6. Validate that a PNG appears in the output directory and that the seed in the output name matches the intended reproducibility mode.

## Workflow 2: low-memory CUDA generation

The repository documents approximate peak VRAM of 43 GB without memory flags, 30 GB with `--cpu-offload`, 24 GB with `--quantize-8bit`, and 16 GB with both. For constrained GPUs, start with both flags:

```bash
python scripts/run_infinite_you_flux.py \
  --id-image path/to/id.jpg \
  --prompt "A person, portrait, cinematic" \
  --model-dir models/InfiniteYou \
  --base-model-path models/FLUX.1-dev \
  --cpu-offload --quantize-8bit
```

If this still fails with CUDA OOM:

- reduce `--width` and `--height` if acceptable for the task
- reduce `--num-steps` when quality/latency trade-offs are acceptable
- choose a freer CUDA device with `--cuda-device`
- close other GPU processes or use a larger GPU
- do not expect CPU-only generation from `--cpu-offload`

## Workflow 3: choose a model variant

Use `aes_stage2` by default for text-image alignment and aesthetics:

```bash
python scripts/run_infinite_you_flux.py --model-version aes_stage2 ...
```

Use `sim_stage1` when the user prioritizes identity similarity:

```bash
python scripts/run_infinite_you_flux.py \
  --model-version sim_stage1 \
  --infusenet-guidance-start 0.1 \
  --id-image path/to/id.jpg \
  --prompt "A person, portrait, cinematic" \
  --model-dir models/InfiniteYou \
  --base-model-path models/FLUX.1-dev
```

If `sim_stage1` copies the face too strongly or prompt alignment is weak, try lowering `--infusenet-conditioning-scale` to about `0.9`. Make one change at a time and keep the seed fixed when comparing.

## Workflow 4: control-image keypoint guidance

Use a control image when the user wants face-pose/keypoint control in addition to identity preservation:

```bash
python scripts/run_infinite_you_flux.py \
  --id-image path/to/id.jpg \
  --control-image path/to/control-face.jpg \
  --prompt "A person, cinematic portrait" \
  --model-dir models/InfiniteYou \
  --base-model-path models/FLUX.1-dev \
  --cpu-offload --quantize-8bit
```

Control-image requirements:

- The control image must contain a detectable face.
- It is resized and padded to the requested canvas size before keypoints are drawn.
- A missing control image means the pipeline uses a black control image, not a pose-control source.
- A `No face detected in the control image` error is about the control image, not the identity image.

## Workflow 5: optional LoRA adapters

Optional LoRAs are examples and were not used in the paper. Use them only when the local model tree contains the matching safetensors files.

Realism:

```bash
python scripts/run_infinite_you_flux.py --enable-realism-lora ...
```

Anti-blur:

```bash
python scripts/run_infinite_you_flux.py --enable-anti-blur-lora ...
```

Try Realism alone first when the user asks for more naturalistic output. If LoRA paths are missing, use the demo/model setup sub-skill's model-layout checker before retrying.

## Workflow 6: prompt and seed iteration

- Use inclusive, respectful person descriptors.
- If generated gender or presentation differs from the user's intent, add explicit prompt words such as `a man`, `a woman`, or a more specific neutral description chosen by the user.
- Use a nonzero `--seed` when comparing model variants or guidance settings.
- Use `--seed 0` when the user wants a random seed.

## Workflow 7: explicitly authorized downloads

If the user has accepted model licenses and wants remote/fallback downloads, make that explicit:

```bash
python scripts/run_infinite_you_flux.py \
  --id-image path/to/id.jpg \
  --prompt "A person, portrait, cinematic" \
  --model-dir ByteDance/InfiniteYou \
  --base-model-path black-forest-labs/FLUX.1-dev \
  --allow-downloads \
  --cpu-offload --quantize-8bit
```

Do not add `--allow-downloads` unless the user has approved network/model-license consequences and credential handling.

## What not to do

- Do not run full generation as a quick installation check; use `--check-only` first.
- Do not require the original source checkout for normal generated-skill operation; use the bundled runtime entry point.
- Do not treat a CPU import or `--cpu-offload` as evidence that generation will work without CUDA.
- Do not download gated or non-commercial-use models without confirming the user's license/access constraints.
