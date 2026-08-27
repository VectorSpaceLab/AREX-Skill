# CLIP Troubleshooting

Use this reference for package-wide issues before routing into a focused sub-skill.

## Install and Import Failures

Symptoms:

- `ModuleNotFoundError: No module named 'clip'`.
- `ModuleNotFoundError` for `torch`, `torchvision`, `ftfy`, `regex`, `tqdm`, or `PIL`.
- Import succeeds in one shell but not another.

Fixes:

- Install PyTorch and torchvision for the user's CPU/CUDA platform before installing CLIP.
- Install the CLIP runtime dependencies: `ftfy`, `regex`, `tqdm`, `torch`, and `torchvision`.
- Run `python scripts/validate_clip_runtime.py --json` to confirm import, model names, and tokenization without checkpoint downloads.
- Check for local files or directories named `clip.py` or `clip/` that shadow the installed package.

## Torch and Torchvision Compatibility

Symptoms:

- Import crashes inside torchvision transforms.
- CUDA is visible but model/tensors are on mixed devices.
- A workflow works on CPU but fails after switching to CUDA.

Fixes:

- Install matching `torch` and `torchvision` builds from the same package channel or wheel family.
- Choose `device = "cuda" if torch.cuda.is_available() else "cpu"`, then move images and text tokens to the same device as the model.
- For CPU-only environments, use `device="cpu"`; CLIP's eager CPU path converts model weights to float32.
- Avoid assuming GPU availability just because the package imports successfully.

## Checkpoint Download and Cache Failures

Symptoms:

- `clip.load("ViT-B/32")` hangs or fails on network access.
- A cached file is re-downloaded because its SHA256 does not match.
- `RuntimeError: ... exists and is not a regular file`.
- Named models fail in an offline environment.

Fixes:

- Ask before triggering named-model downloads; named checkpoints are large external artifacts.
- Pass `download_root=` to a writable cache directory or a pre-populated cache.
- For strict offline operation, pass a local checkpoint path as the `name` argument to `clip.load`.
- If a cache file has a checksum mismatch, delete or replace only that corrupted checkpoint file and rerun with an approved network/cache policy.
- If the cache path exists as a directory where CLIP expects a file, choose a clean cache directory or remove the conflicting path.

## Tokenizer and Prompt Length Errors

Symptoms:

- `RuntimeError: Input ... is too long for context length 77`.
- User passes raw strings directly to `encode_text`.
- User tokenizes on CPU but sends the model to CUDA.

Fixes:

- Use `clip.tokenize([...], context_length=77, truncate=False)` to catch overlong prompts before model inference.
- Shorten class names/templates when exact wording matters; use `truncate=True` only when losing tail tokens is acceptable.
- Move token tensors to the same device as the model before calling `encode_text` or `model(image, text)`.
- Route prompt template design and ensembling to [prompt-engineering](../sub-skills/prompt-engineering/).

## Probability and Evaluation Misuse

Symptoms:

- User treats CLIP top-k probabilities as calibrated open-world confidence.
- Results change drastically when labels or prompts change.
- Linear-probe accuracy is used as the only model-quality signal.

Fixes:

- `softmax` probabilities are relative to the candidate labels supplied for that image, not calibrated absolute truth.
- Use fixed, non-overlapping class taxonomies and prompt templates; document every class/template decision.
- Normalize image and text features before similarity/search unless intentionally using `model(image, text)` logits.
- Route feature extraction, linear probes, and responsible evaluation caveats to [feature-evaluation](../sub-skills/feature-evaluation/).

## Safety and Out-of-Scope Use

Symptoms:

- Request involves surveillance, facial recognition, sensitive demographic classification, deployed decision-making, or non-English generalization claims.
- User wants to evaluate people-related labels without an audit plan.

Fixes:

- Treat CLIP as a research model unless the user supplies task-specific safety, fairness, and deployment validation requirements.
- Avoid surveillance/facial-recognition workflows and warn before sensitive demographic classification.
- State that CLIP was not purposefully trained or evaluated for languages other than English.
- Use [responsible-evaluation.md](../sub-skills/feature-evaluation/references/responsible-evaluation.md) before designing any evaluation involving people or deployment impact.
