# Examples and conversion troubleshooting

Use this matrix when an example-family plan fails or the user asks why a recipe is unsafe to run directly. Keep fixes non-mutating unless the user explicitly approves installs, downloads, training, conversion, service startup, or checkpoint writes.

## Quick route by symptom

| Symptom or request | Read first | Route if deeper |
|---|---|---|
| Ziya HF/Fengshen/tensor-parallel confusion | [ziya-llama.md](ziya-llama.md), [conversion-utilities.md](conversion-utilities.md) | `../model-zoo/SKILL.md` for LLaMA internals; `../data-training/SKILL.md` for distributed training details. |
| Taiyi CPU vs FP16 CUDA path | [taiyi-diffusion.md](taiyi-diffusion.md) | `../model-zoo/SKILL.md` for Taiyi CLIP/text encoder internals. |
| CLUE output format mismatch | [clue-and-task-recipes.md](clue-and-task-recipes.md) | `../pipelines-cli/SKILL.md` for UniMC/Ubert pipeline use. |
| Summary/QA/translation script fails | [nlg-nlt-recipes.md](nlg-nlt-recipes.md) | `../data-training/SKILL.md` for Trainer/data flags. |
| Any checkpoint conversion writes unexpected files | [conversion-utilities.md](conversion-utilities.md) | Stop and require backup/output plan. |

## Dependency failures

| Error/symptom | Likely missing or incompatible dependency | Why it happens | Safe next step |
|---|---|---|---|
| `ModuleNotFoundError: diffusers` | `diffusers` | Taiyi inference/fine-tuning and Diffusers conversion depend on it | Use `check_recipe_requirements.py --recipe taiyi-inference`; install only in an approved environment. |
| FP16/device-map warnings | `accelerate` or incompatible `torch`/CUDA stack | Diffusers and HF large-model loading often rely on accelerate integration | Verify CUDA and package versions; fall back to CPU/full precision planning if no CUDA. |
| `ModuleNotFoundError: bitsandbytes` | `bitsandbytes` | Ziya HF INT8/INT4 quantized inference uses bitsandbytes | Use FP16 or llama.cpp path if bitsandbytes/CUDA is unavailable. |
| `ModuleNotFoundError: llama_cpp` | `llama-cpp-python` | llama.cpp high-level Python inference wrapper missing | Treat llama.cpp path as unverified until toolchain or Python package is installed. |
| Deepspeed import/build failure | `deepspeed`, CUDA compiler/toolchain, compatible PyTorch | Ziya/Taiyi/NLG fine-tuning examples use Deepspeed strategies | Do not run training; prepare backend-specific env or choose static planning. |
| Tokenizer import failure | SentencePiece/protobuf/tokenizer package mismatch | LLaMA/T5/DeltaLM tokenizers can require optional tokenizer deps | Add tokenizer dependency to environment plan before loading models. |
| Lightning/torchmetrics API mismatch | Example stack is older than active environment | Source examples target older Lightning/Transformers/Torch combinations | Isolate a compatible env; do not patch training scripts blindly. |

## Mutation and output safety

| Risk | Examples affected | Required guardrail |
|---|---|---|
| Existing output directory removed/recreated | Delta application utility may recreate the target model directory | Require a fresh `target-model-path`; back up anything valuable. |
| Output path equals input path | All conversion utilities | Reject the plan; use separate input and output locations. |
| Checkpoint directory overwritten during training | Taiyi fine-tune, DreamBooth, Ziya fine-tune, NLG fine-tune | Require explicit `save_ckpt_path`, resume policy, storage estimate, and backup. |
| Temporary shards fill disk | Delta low-memory mode, tensor-parallel conversion, Diffusers conversion | Estimate disk as at least input + output + temporary overhead. |
| Submission/prediction files overwritten | CLUE post-processing, summary validation outputs | Use new output paths and keep original predictions immutable. |

## Resource failures

| Symptom | Likely cause | Safe response |
|---|---|---|
| CUDA OOM in Taiyi inference | Full precision, large resolution, insufficient VRAM | Use FP16 CUDA if supported, reduce resolution/steps, or switch to CPU planning. |
| CUDA OOM in Taiyi fine-tune/DreamBooth | Batch/resolution too high or training too many components | Reduce batch/resolution, freeze components, use FP16/BF16, or prepare Deepspeed offload. |
| CUDA OOM in Ziya fine-tune | 13B full-parameter fine-tune too large for available GPUs | Use tensor parallel, ZeRO/offload, shorter sequence/batch, or switch to quantized inference. |
| CPU RAM exhaustion during conversion | Large checkpoint loaded or split/merge process duplicates tensors | Use low-memory mode where available, larger RAM host, or staged conversion. |
| Training appears stuck compiling | Deepspeed/fused extensions building | Check toolchain and cache path; do not keep retrying without logs and resource plan. |

## Hard-coded path and scheduler failures

Many example shell scripts were authored for a specific cluster or workspace. Do not preserve their paths or scheduler directives in runtime instructions.

| Pattern | Why unsafe | Replacement |
|---|---|---|
| Absolute data/model/checkpoint paths | Not portable and may reveal private infrastructure | Use `<data_dir>`, `<model_dir>`, `<output_dir>` placeholders supplied by the user. |
| Slurm-only `srun` wrappers | Not valid on non-Slurm hosts | Express the Python command separately; add scheduler wrapper only after user confirms cluster type. |
| Hard-coded `CUDA_VISIBLE_DEVICES`, `MASTER_PORT`, extension cache | Host-specific and can collide | Let the user or launcher set device/port/cache, or generate unique safe values. |
| Embedded logging/API keys | Secret risk | Require environment variables or a secret manager; never hard-code keys. |

## Network/download failures

| Trigger | Why it occurs | Safe response |
|---|---|---|
| `from_pretrained("IDEA-CCNL/...")` hangs or fails | Model ID requires network or cache miss | Ask for network permission or a local cached model path. |
| Dataset download unavailable | CLUE, AFQMC, Ziya sample data, image datasets are external | Require user-supplied datasets; do not download in verification. |
| Submodule fetch via SSH fails | Dataset submodule may use SSH remotes | Do not depend on submodule contents for this sub-skill; if user needs it, switch remote to an approved accessible protocol outside runtime docs. |
| API/demo calls unreachable | Demo code may expect a backend model service | Treat demos as UI patterns only; require user-provided backend endpoint and auth. |

## Checkpoint shard mismatches

| Mismatch | Typical message | Fix |
|---|---|---|
| Missing shard from HF checkpoint | Weight map references absent `pytorch_model-*.bin` | Verify all shards and weight map before conversion. |
| Wrong Fengshen TP size | Missing `part_<rank>` or shape mismatch | Use the same `model_parallel_size` for conversion, training, and loading. |
| LLaMA config not divisible by TP size | Assertion on attention heads/hidden dims | Choose a TP size that divides config dimensions. |
| Tokenizer from different model | Bad tokens, unexpected BOS/EOS, generation quality collapse | Use tokenizer saved with the converted checkpoint or a known compatible tokenizer. |
| Diffusers component missing | Converter cannot find UNet/VAE/text encoder weights | Use a complete local Diffusers pipeline directory. |

## FastDemo and API caveats

The demo/API examples are useful as patterns but unsafe as verification targets.

- Streamlit demo pattern: sidebar parameters, text input, cached model or service call, result rendering. Do not reuse placeholder backend URLs or assume the demo host has GPUs.
- API pattern: FastAPI service loads a pipeline from JSON configuration, currently centered on POST requests and pipeline module imports. Do not start Uvicorn in verification.
- Before building a real demo, ask for model source, device, request/response schema, authentication, service port, CORS policy, logging path, and whether model loading should happen in-process or via a separate backend service.

## Safe response templates

### When the user asks to run a heavy example directly

> This example is not safe to run as-is because it can download large models, assumes CUDA/Deepspeed resources, and writes checkpoints. I can first produce a dry-run plan with dependencies, data shape, device/VRAM requirements, output paths, and side effects. Please confirm model path/cache, data path, device, and whether checkpoint writes are allowed.

### When a conversion path is ambiguous

> I need the source format (`delta`, full HF, Fengshen single-shard, Fengshen TP shards, Diffusers directory, or TF checkpoint), target format, new output path, storage budget, and overwrite permission. Until then I will only run the dry-run planner.

### When a model ID would download

> The model ID may trigger a network download. Provide a local cache path or explicitly allow downloads before execution.
