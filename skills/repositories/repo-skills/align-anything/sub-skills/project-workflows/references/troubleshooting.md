# Project Workflow Troubleshooting

Use this reference when an Align-Anything satellite project looks runnable but fails during setup, entrypoint discovery, tokenization, or evaluation planning. Many project workflows require optional forks, heavy model downloads, GPU plans, or data schemas that are not part of the base package install.

## General Triage

1. Confirm the selected project decision state: runnable, extension pattern, or reference-only.
2. Run the bundled static discovery script before running project code if the user asks what entrypoints exist.
3. Verify optional runtime deltas: forked package, model weights, GPU count, backend, API credentials, dataset path, and output/cache directory.
4. Replace placeholder path tokens and local model ids in example configs/scripts. Never run commands that still contain unfilled placeholders, empty model variables, or private/local placeholders.
5. For DeepSpeed shell patterns, confirm the script is run from a directory where its relative `source` command resolves correctly and that `OUTPUT_DIR` is safe to create.

## Entrypoint Discovery Issues

| Symptom | Likely cause | Resolution |
| --- | --- | --- |
| Discovery script reports missing files | The checkout is incomplete, a different branch is used, or the script root argument points at the wrong directory. | Re-run with `--root <repository-root>` and inspect the reported project directories. Missing optional projects should be reported as gaps, not silently invented. |
| Discovery output lists a Python file but no argparse flags | The file may be a package module or script without `argparse`. | Inspect functions/classes; do not assume it is directly runnable. |
| User asks to run all project scripts | Project scripts can download models, allocate GPUs, call APIs, or write large outputs. | Select one workflow and verify prerequisites first. Do not execute bulk discovery by running scripts. |

## Any-to-Text

| Symptom | Likely cause | Resolution |
| --- | --- | --- |
| Model download/authentication failure | Default Llama, CLIP, or CLAP identifiers require network access, cache access, or license approval. | Ask for accessible local model paths or confirm the user has authenticated model access. |
| `LlamaVisionAudio...` import failure | Base Align-Anything import is unavailable or installed version lacks the vision-audio model wrapper. | Verify Align-Anything installation and route to model/package setup before treating the script as runnable. |
| CLAP identifier not found | README and script spell the default CLAP checkpoint slightly differently. | Validate the actual audio tower id with the user or use a known local CLAP model path. |
| OOM during builder load | The builder loads large language and encoder models; the audio script uses `device_map='auto'` for language/vision loads. | Use smaller checkpoints, adequate GPU/CPU memory, or a staged/offline initialization plan. |
| Saved model cannot consume images/audio | Special tokens or processor artifacts may not match downstream trainer assumptions. | Confirm `<image>`/`<audio>` token ids, processor class, and trainer template before training. |

## Janus

| Symptom | Likely cause | Resolution |
| --- | --- | --- |
| `ModuleNotFoundError: janus` | Janus is an optional separate package/fork, not part of base Align-Anything. | Install/prepare the Janus-compatible runtime only if the user selected Janus workflows; otherwise mark as optional. |
| Shell scripts contain an unfilled `JANUS_REPO_PATH` placeholder | Example placeholder not replaced. | Stop and ask for the actual Janus package path or use an installed package approach; do not run with the placeholder. |
| Tokenizer script fails on missing JSON keys | `supervised_text_to_image.py` expects `prompt` and `image`; `preference_text_to_image.py` expects `prompt`, `better_image`, and `worse_image`. | Validate or transform the dataset schema before tokenization. |
| Worker cache path does not follow `--cache_dir` | The inspected multiprocessing spawn pattern passes the literal `.cache` to workers. | Confirm where cache files are written; if necessary, patch a copy or run from a scratch directory where `.cache` is acceptable. |
| CUDA-only failure in preference tokenizer | One script constructs `device = f'cuda:{gpu}'` directly. | Do not claim CPU fallback. Prepare CUDA or adapt the script intentionally. |
| Trainer script starts but data shape mismatches | SFT/DPO generation scripts expect tokenized `.pt` files from the Janus tokenizers; understanding scripts use text-image-to-text data and `Janus_TI2T` template. | Match tokenizer output to the selected `align_anything.trainers.janus.*` module. |

## InterMT

| Symptom | Likely cause | Resolution |
| --- | --- | --- |
| User asks to run InterMT-Bench from this repo | The inspected project material is documentation/dataset description, not a complete local runner. | Treat as reference-only unless a separate InterMT-Bench runtime and data assets are prepared. |
| Missing benchmark images | InterMT-Bench images are described as a dataset asset. | Ask for the prepared image/data location or mark the benchmark blocked. |
| Confusion between InterMT and Eval-Anything | Both are evaluation-related but different surfaces. | Use InterMT for multi-turn multimodal preference benchmark context; use Eval-Anything notes for the separate safety evaluation package. |

## Language Feedback

| Symptom | Likely cause | Resolution |
| --- | --- | --- |
| vLLM import/runtime failure | The folder is under-development and expects a heavy vLLM runtime. | Prepare vLLM/GPU dependencies or keep the workflow as a reference pattern. |
| OOM at startup | The scripts set `tensor_parallel_size=8`, `gpu_memory_utilization=0.95`, and `swap_space=32`. | Confirm actual GPU count and reduce/adapt parameters in a copy if the task permits. |
| JSON field errors in `base_gen.py` | Base generation expects records with `image` and `prompt`. | Validate the dataset and image file paths before running. |
| JSON field errors in `critique_gen.py` | Critique generation expects `image`, `prompt`, and `output_text`. | Generate or map base responses into `output_text` before critique generation. |
| JSON field errors in `refine_gen.py` | Refinement expects `image`, `prompt`, `output_text`, and `critique`. | Carry critique outputs into the expected field name before refining. |
| Image loading failure | Scripts pass `Image.open(image_file)` directly. | Ensure image paths are local and readable; the inspected language-feedback scripts do not implement HTTP image fetching. |

## Text-Image-to-Text-Image / Chameleon

| Symptom | Likely cause | Resolution |
| --- | --- | --- |
| `ChameleonProcessor` or image-output behavior missing | Ordinary Transformers may not support the required Chameleon image-output path. | Prepare the forked/compatible Transformers runtime described by the project before marking runnable. |
| `AccustomedChameleonModel` import failure | Base Align-Anything package is not installed or model wrapper is unavailable. | Fix the Align-Anything runtime or route to model setup. |
| Dataset schema mismatch | Generic scripts expect fields such as `input_text`, `input_image`, `output_text`, and preference-specific better/worse fields; helper formatters target selected datasets. | Choose or write the correct formatter before tokenization. |
| Samples silently missing from output | Several tokenization scripts keep only samples with token length at or below 4096. | Report the effective length and decide whether to change length limits or filter upstream. |
| Parallel tokenizer ignores requested cache dir | Several inspected multiprocessing calls pass `.cache` to child workers instead of the parsed `cache_dir`. | Run from a scratch directory or adapt the script copy to pass the chosen cache path. |
| PPO training cannot use large batch size | Project README notes a Transformers-related constraint with batch size 1 for PPO. | Do not promise scalable PPO without verifying a newer runtime. |
| Batch inference/evaluation command absent | README says batch inference and GPT-based evaluation rely on other repositories, not integrated commands. | Treat those as external workflows requiring separate setup. |

## Eval-Anything

| Symptom | Likely cause | Resolution |
| --- | --- | --- |
| Base Align-Anything environment cannot import `eval_anything` | Eval-Anything has its own package metadata under the projects tree. | Install/prepare Eval-Anything separately before execution; otherwise use as reference-only. |
| CLI `clean` command does not work | The usage table mentions `clean`, but the inspected dispatcher lacks a `clean` branch. | Clean cache directories manually after confirming paths, or patch Eval-Anything intentionally. |
| CLI `--gpu` has no effect | The inspected CLI parses `--gpu` but does not forward it into `run_eval()`. | Set GPU ids in YAML `infer_cfgs` or use main-module override keys. |
| Config points to a local model path | Example/default configs can contain machine-specific model paths. | Replace with a user-provided model id/path; do not preserve private placeholders in generated commands. |
| `KeyError` or import error for backend | `BaseTask` maps `{infer_backend}_{model_type}` to known model modules/classes. | Use one of the supported backend keys or add a proper model implementation in a separate development task. |
| vLLM OOM or GPU mismatch | Config `num_gpu`, `gpu_ids`, and utilization may exceed available devices. | Reduce GPU count/model size, switch backend, or prepare matching hardware. |
| Benchmark config not found | Benchmark names map to package benchmark folders and modality mappings. | Verify benchmark spelling/case and the packaged benchmark configs. |
| VLA setup fails | VLA requires Objaverse assets, house assets, datasets, optional extras, AI2-THOR, and AllenAct packages. | Treat VLA as blocked until all assets and extras are deliberately prepared. |
| API benchmark calls are costly or repeated | Eval tools include cached API requests but require stable cache dirs and API env vars. | Set `API_KEY`, `API_BASE`, output/cache dirs, and concurrency intentionally; avoid concurrent writes to the same cache if unsupported. |

## Unsupported or Optional Notes

- Project folders are not a promise that every script works in a base CPU environment.
- Janus, Chameleon, vLLM, Eval-Anything VLA, external batch inference, and external GPT-based evaluation are optional/heavy surfaces.
- InterMT project material should remain reference-only unless the benchmark/data runtime is separately acquired and verified.
- Do not use successful static discovery as proof of runtime readiness; it only proves that files and command patterns are present.
