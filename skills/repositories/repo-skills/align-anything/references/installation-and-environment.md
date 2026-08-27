# Installation and environment guidance

Use this reference before executing Align-Anything package code in a new runtime. The skill is self-contained, but the package itself still needs a prepared Python environment, model/data assets, and appropriate accelerator hardware for real workloads.

## Minimum environment profile

A practical base environment for the selected skill scope needs:

- Python 3.10 or 3.11.
- CUDA-capable PyTorch when running training, model loading, or multimodal generation.
- Transformers, tokenizers, datasets, accelerate, DeepSpeed, Gradio, Pillow, NumPy, and standard scientific Python dependencies.
- Media dependencies for serving/data paths that handle audio or video, such as PyAV, moviepy, ffmpeg-capable system libraries, and any model-family-specific processor packages.
- Remote reward dependencies when using `remote-reward-models`: Flask, requests, python-Levenshtein, latex/math verification dependencies when using `math_verifier`.
- Optional packages only for selected workflows: vLLM for vLLM/evaluation/language-feedback paths, Janus-compatible packages for Janus workflows, Chameleon/InterMT/Eval-Anything runtimes for the satellite projects.

## Pre-flight checks

Run the bundled checker from the root of this skill tree or copy it into the active workspace:

```bash
python scripts/check_align_anything_environment.py --json
```

For specific workflows also use the sub-skill scripts:

```bash
# Training config/trainer import probe
python sub-skills/training-and-alignment/scripts/inspect_alignment_config.py --task text_to_text/sft --import-trainer

# Serving/model-loading probe without loading weights
python sub-skills/multimodal-serving/scripts/check_model_loading.py --model-name-or-path <model> --preset text --no-load

# Remote reward payload validation; requires a running server for the HTTP call
python sub-skills/remote-reward-models/scripts/probe_remote_rm_payload.py --endpoint http://127.0.0.1:6000/get_reward
```

## Backend interpretation

| Result | Meaning | Next step |
| --- | --- | --- |
| Package imports and CPU-only checks pass | The code is importable, but GPU execution is not proven. | Use for planning, config inspection, and static workflows only. |
| CUDA is available in PyTorch | Basic GPU runtime is available. | Still confirm model memory, CUDA toolkit, DeepSpeed custom ops, and vLLM/flash-attention extras as needed. |
| DeepSpeed warns about `CUDA_HOME` | Imports can still pass, but custom fused ops may not compile. | Install/configure a matching CUDA toolkit or avoid fused optimizers/custom op paths. |
| Janus import fails | Optional Janus runtime is missing. | Treat Janus as project guidance until its package/model environment is explicitly prepared. |
| vLLM/Eval-Anything imports fail | Separate heavy runtime is missing. | Do not claim Eval-Anything or vLLM execution readiness; use project docs as reference only. |

## Execution safety

- Long training and benchmark runs should have explicit model/data/output paths, GPU count, wall-time estimate, and checkpoint policy.
- Gradio CLIs in the package may request shareable links. Run only in trusted environments or adapt the launcher to local-only serving.
- `trust_remote_code` executes model repository code. Use only with trusted model sources.
- Never treat construction-time package versions or local paths as required runtime paths. Re-check versions in the user's active environment.
