# Cross-cutting troubleshooting

## Backend and environment issues

- **CUDA is missing**: the selected training, sampling, compression, composition, and evaluation workflows require a CUDA-capable runtime. Use the delta extraction route only if you are intentionally staying on the CPU-safe path.
- **Torch or torchvision import fails**: reinstall a matching CUDA-enabled PyTorch stack before debugging the repo scripts further.
- **Optional packages are absent**: `xformers`, `bitsandbytes`, `deepspeed`, and `modelcards` are optional. Only install them when the route you picked explicitly needs them.

## Data and layout issues

- **Concept JSON is malformed**: validate the manifest with `scripts/validate_concepts.py` before starting training.
- **Regularization files do not line up**: use `sub-skills/data-preparation/scripts/validate_regularization_layout.py` to check image lists, caption files, and expected counts.
- **Benchmark inputs do not line up**: use `sub-skills/benchmarking/scripts/validate_benchmark_layout.py` before calling the evaluator.

## Workflow-specific issues

- **Modifier token count mismatch**: the training routes split `--modifier_token` and `--initializer_token` on `+`; make sure the initializer list is at least as long as the modifier list.
- **Duplicate modifier token**: the tokenizer already contains the token you tried to add. Pick a different token string.
- **Initializer token is multi-token**: the initializer must encode to a single token in the target tokenizer.
- **Wrong freeze mode**: `crossattn_kv` is the default; `crossattn` updates all cross-attention weights.
- **Compressed delta sampled without the compression flag**: inspect the file with `sub-skills/checkpoint-tools/scripts/check_delta_layout.py` and pass the matching sampler flag or regenerate the delta.
- **Sample filenames collide**: the sampler truncates long prompts when naming montages, so shorten or normalize the prompt text if files overwrite each other.
- **Benchmark prompt stems are missing**: ensure every PNG stem has a matching entry in `prompts.json`.

## Network and credentials

- **Real-prior retrieval is blocked**: the LAION KNN helper is network-sensitive. Switch to a local bundle or retry only when network access is allowed.
- **Model downloads are unavailable**: the training and sampling routes can require Hugging Face model downloads. Cache the needed base model before running the expensive route.
- **Hub push fails**: provide a valid Hugging Face token and repository id before enabling `--push_to_hub`.

## Legacy-path boundary

- Legacy Stable Diffusion checkout flows and their direct dependencies are treated as reference-only or excluded. Route users to the diffusers-side path instead.
