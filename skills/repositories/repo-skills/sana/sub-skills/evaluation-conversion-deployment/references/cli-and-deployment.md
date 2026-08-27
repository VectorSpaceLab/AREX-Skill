# CLI and Deployment

This reference explains the public Sana utility commands and deployment routes
that future agents may plan.

## `sana-run`

`Sana-run` is the SLURM launcher used by the repository CI and by human users
who want retry-aware launches.

### Planning requirements
- `SANA_SLURM_ACCOUNT` must be set.
- `SANA_SLURM_PARTITION` must be set.
- `CONDA_ENV_NAME` controls which environment the launcher activates.
- `HF_TOKEN` is used only when a login step is needed; treat it as secret input.
- The planner should surface job name, node count, GPU count, wall time, retry budget, and pty mode.

### Common behavior
- Derives output directories from the job name when not specified.
- Wraps the command in `srun` and a timeout.
- Retries timed-out jobs according to the max-retry policy.
- Can disable GPU-per-node flags on environments that do not support them.
- If a token is present, the launcher may attempt Hugging Face auth before the user command.

### Safe checks
- `sana-run --help` is safe.
- A dry planning command should confirm env vars before trying to launch SLURM.
- Safe inspection:
  ```bash
  python scripts/inspect_sana_cli.py --command sana-run --show-version
  ```
- Example launcher shape:
  ```bash
  SANA_SLURM_ACCOUNT=<account> SANA_SLURM_PARTITION=<partition> \
  CONDA_ENV_NAME=<env-name> sana-run --pty -m ci -J test-inference bash tests/bash/inference/test_inference.sh
  ```

## `sana-upload`

`Sana-upload` uploads a local folder to Hugging Face.

### Planning requirements
- Treat the destination as private unless explicitly changed by the underlying tool.
- Confirm whether the target is a model repo or dataset repo.
- Confirm the repo org or explicit repo id.
- Verify whether the user wants custom exclude patterns.
- Treat the token as secret input and never echo it back in plaintext.

### Safety behavior
- The uploader skips files matching exclude patterns such as checkpoints, git metadata, and wandb logs by default.
- Individual files larger than the supported size limit are skipped.
- Commits are batched to respect file-count and total-size limits.
- If a file already exists remotely, the tool can compare hashes and skip identical content.

### Safe checks
- `sana-upload --help` is safe.
- Planner output should include the repo id, repo type, root directory, token source, and exclude patterns without exposing credentials.
- Safe inspection:
  ```bash
  python scripts/inspect_sana_cli.py --command sana-upload --show-version
  ```
- Example upload shape:
  ```bash
  sana-upload <local_folder> --repo-type model --repo-org <org> --model-name <name> \
    --exclude 'checkpoint-[0-9]*/.*' --exclude '.git/.*' --exclude 'wandb/.*'
  ```

## SGLang deployment

SGLang supports Sana as an inference backend for image generation.

### Route selection
- Use the CLI for a single render request.
- Use the Python SDK when embedding generation in a Python service.
- Use the server mode when an OpenAI-compatible HTTP endpoint is needed.

### Memory/offload options
- CPU offload options exist for the text encoder, VAE, and DiT.
- Choose offload options when GPU memory is limited, but document the speed trade-off.
- The planner should point out that the model path must already match the supported Sana diffusers family.
- Example CLI shape:
  ```bash
  sglang generate \
    --model-path Efficient-Large-Model/SANA1.5_1.6B_1024px_diffusers \
    --prompt 'a cyberpunk cat with a neon sign that says "Sana"' --save-output
  ```
- Example server shape:
  ```bash
  sglang serve --model-path Efficient-Large-Model/SANA1.5_1.6B_1024px_diffusers --host 0.0.0.0 --port 30000
  ```
- Limited-memory shape:
  ```bash
  sglang generate --model-path Efficient-Large-Model/SANA1.5_1.6B_1024px_diffusers \
    --text-encoder-cpu-offload --vae-cpu-offload --pin-cpu-memory \
    --prompt 'A beautiful landscape' --save-output
  ```

## ComfyUI deployment

- ComfyUI runs as a local interactive workflow UI.
- Sana support relies on the custom nodes and a sample workflow JSON.
- The planner should remind the user to use the workflow that matches the chosen image family and resolution.
- Do not assume a ComfyUI workflow can be used without the required checkpoint and custom node setup.
- Example setup shape:
  ```bash
  git clone https://github.com/comfyanonymous/ComfyUI.git
  cd ComfyUI
  git clone https://github.com/lawrence-cj/ComfyUI_ExtraModels.git custom_nodes/ComfyUI_ExtraModels
  python main.py
  ```
- Workflow families include Sana FlowEuler, Sana 2K/4K FlowEuler, Sana Sprint, and Sana+CogVideoX.

## Gradio deployment

- Gradio app launchers are convenience demos, not a benchmark or export route.
- They are best treated as interactive UI surfaces that may download weights and keep long-lived state.
- The planner should caution the user when a request would start a server or rely on model downloads.
- Example launch shapes:
  ```bash
  python app/app_sana.py
  python app/app_sana_4bit.py
  python app/app_sana_4bit_compare_bf16.py
  ```

## Provenance labels

- `sana/cli/run.py`
- `sana/cli/upload2hf.py`
- `docs/sglang.md`
- `docs/ComfyUI/comfyui.md`
- `docs/model_zoo.md`
- `docs/4bit_sana.md`
- `.github/workflows/ci.yaml`
