# Align-Anything Satellite Project Map

This reference distills the satellite workflow evidence from the Align-Anything project folders and related shell patterns. It is self-contained: use the source-relative path names only as locator labels when a checkout is available; do not rely on Markdown links back to the source tree.

## Decision States

| State | Meaning | Required action before execution |
| --- | --- | --- |
| Runnable | The project provides a script or package entrypoint that can be run after its documented runtime, model, data, and device assumptions are satisfied. | Verify optional packages, model/data paths, GPU/backend capacity, and output directory. Run only the selected entrypoint. |
| Extension pattern | The project is useful as evidence for adapting or extending Align-Anything trainers, tokenization, data formatting, or model initialization, but not necessarily as a turnkey command. | Extract the pattern, then route to the appropriate core training/model sub-skill for implementation details. |
| Reference-only | The material documents a dataset, benchmark, external package, or under-development workflow that should not be executed from the base repo skill. | Cite the distilled behavior and prerequisites; require a separate runtime or source package before treating it as runnable. |

## Top-Level Project Directory

`projects/README.md` identifies five satellite projects:

- `text_image_to_text_image`: Chameleon text-image interleaved alignment, with pre-tokenization scripts for SFT, DPO/RM, and PPO-style prompt-only data.
- `any_to_text`: multimodal LLM initialization scripts that combine a text LLM with vision and optionally audio encoders.
- `lang_feedback`: language-feedback data generation, explicitly described as under development and internal-use oriented.
- `janus`: Janus model SFT/DPO generation and understanding patterns, requiring an optional Janus-compatible package.
- `intermt`: InterMT dataset and InterMT-Bench documentation for multi-turn interleaved preference alignment.

## Project Routing Table

| Project | Primary files/signals | Default state | Main entrypoints | Runtime prerequisites | Output shape/use |
| --- | --- | --- | --- | --- | --- |
| Any-to-Text | `projects/any_to_text/README.md`; `build_llama_vision.py`; `build_llama_vision_audio.py` | Runnable for model initialization; extension pattern for training. | `python build_llama_vision.py`; `python build_llama_vision_audio.py` with explicit path flags. | Base Align-Anything install, `torch`, `transformers`, model access for the LLM and encoders. Vision-audio script imports `align_anything.models.llama_vision_audio_model`. | Saved Hugging Face-style model and processor directories for vision-text or vision-audio-text models. |
| Janus | `projects/janus/README.md`; `supervised_text_to_image.py`; `preference_text_to_image.py`; `scripts/janus/*.sh` | Optional runtime; extension pattern if Janus package/model is absent. | Tokenizers write `.pt` tokenized datasets; shell scripts call `align_anything.trainers.janus.*` via DeepSpeed. | Separate Janus-compatible package on `PYTHONPATH`, Janus model weights, CUDA-capable device plan, JSON data with expected image fields. | Tokenized `.pt` files consumed by Janus SFT/DPO generation or understanding trainers. |
| InterMT | `projects/intermt/README.md`; `projects/intermt/intermt_bench/README.md` | Reference-only by default. | No safe in-repo runnable entrypoint was evidenced in the inspected files. | Dataset/benchmark assets and external InterMT-Bench runtime must be prepared separately. | Dataset/benchmark context for multi-turn multimodal preference alignment. |
| Language Feedback | `projects/lang_feedback/README.md`; `base_gen.py`; `critique_gen.py`; `refine_gen.py` | Internal/development; runnable only after explicit vLLM runtime prep. | `python base_gen.py`, `python critique_gen.py`, `python refine_gen.py` with model, input, output flags. | vLLM, multimodal model supported by vLLM, GPUs matching tensor parallel size, image files accessible from JSON. | JSON augmented with a `generated` field for base, critique, or refined responses. |
| Text-Image-to-Text-Image | `projects/text_image_to_text_image/README.md`; pre-tokenization Python scripts | Optional Chameleon runtime; extension pattern for core trainers. | `python pre_tokenize_example.py`; `python pre_tokenize_parallel_example.py`; `python preference_tokenize_example.py`; `python prompt_only_tokenize_example.py`. | Chameleon-capable model and processor, Align-Anything Chameleon model wrapper, suitable Transformers fork/model, CUDA/GPU for practical processing. | Tokenized `.pt` datasets that feed SFT/DPO/RM/PPO trainers. |
| Eval-Anything | `projects/eval-anything/README.md`; package metadata; `eval_anything/cli.py`; `eval_anything/__main__.py`; configs and pipeline files | Reference-only unless a separate heavy runtime is prepared. | `eval-anything-cli eval <config>`; `python -m eval_anything --eval_info <config>` in an installed Eval-Anything environment. | Python 3.11-style environment, `vllm >= 0.6.2` or selected backend deps, model weights/API credentials, benchmark data, optional VLA extras for embodied benchmarks. | Benchmark result directories, JSONL details, optional cache and visualization artifacts. |

## Any-to-Text Details

### Vision-text builder

`build_llama_vision.py` statically constructs a Llava-style model by loading:

- `--language_model_path` (default: `meta-llama/Meta-Llama-3.1-8B-Instruct`)
- `--vision_tower_path` (default: `openai/clip-vit-large-patch14-336`)
- `--save_path` (default: `Any2Text/llama_vision`)

It adds `<image>`, `<unk>`, and `<pad>` as tokenizer special tokens, builds a `LlavaConfig`, sets `image_token_index`, installs the loaded language model and vision tower into `LlavaForConditionalGeneration`, resizes token embeddings, makes parameters contiguous, then saves the model and processor.

Treat it as runnable when the model identifiers are valid and large downloads/checkpoint writes are acceptable. Treat it as extension evidence when the task is about how to initialize another vision-language model.

### Vision-audio-text builder

`build_llama_vision_audio.py` loads:

- `--language_model_path` (default: `meta-llama/Meta-Llama-3.1-8B-Instruct`)
- `--vision_tower_path` (default: `openai/clip-vit-large-patch14-336`)
- `--audio_tower_path` (script default: `laion/clap-htsat-fused`)
- `--save_path` (default: `Any2Text/llama_vision_audio`)

It adds `<image>` and `<audio>` special tokens and creates `LlamaVisionAudioConfig`, `LlamaVisionAudioForConditionalGeneration`, and `LlamaVisionAudioProcessor` from the Align-Anything model wrapper. It uses `device_map='auto'` for the vision and language model loads. Verify the CLAP model identifier before running because the README and script differ slightly in the final spelling of the CLAP checkpoint name.

### Training-pattern evidence

The Any-to-Text README recommends two training stages for the resulting multimodal model:

1. Train only the projector between encoder and LLM, using `align_anything.trainers.text_image_to_text.sft` with the vision tower frozen, mm projector trainable, and language model frozen.
2. Jointly train the projector and language model, keeping the vision tower frozen while unfreezing the language model.

For multi-dataset training, the README pattern supplies comma-separated `--train_datasets`, `--train_template`, and `--train_split`. In DeepSpeed ZeRO-3 image-audio-text training, it notes that `prefetch_bucket_size` should be set to `0` in the configuration.

## Janus Details

The Janus README says the workflow depends on a forked/stable Janus package installed separately. Therefore, a missing `janus` import is an optional-runtime gap, not evidence that Align-Anything itself is broken.

### Tokenization scripts

- `supervised_text_to_image.py` expects JSON records with `prompt` and `image`; it encodes the output image into Janus vision token IDs and returns `input_ids`, `labels`, and `task: generation`.
- `preference_text_to_image.py` expects `prompt`, `better_image`, and `worse_image`; it encodes both images, pads token sequences to the same length, and returns `better_input_ids`, `worse_input_ids`, and `task: generation`.

Both scripts expose `--input_path`, `--output_path`, `--model_path`, `--cache_dir`, `--num_processes`, and `--num_gpus`. They spawn one process per configured process and map process ids cyclically to GPUs.

### Shell trainer patterns

The `scripts/janus` shell patterns map to these trainer modules:

| Shell pattern | Trainer module | Dataset flavor | Notes |
| --- | --- | --- | --- |
| `janus_sft_gen.sh` | `align_anything.trainers.janus.sft_gen` | supervised text-to-image tokenized `.pt` | Uses `--train_data_files train_tokenized.pt`. |
| `janus_dpo_gen.sh` | `align_anything.trainers.janus.dpo_gen` | preference text-to-image tokenized `.pt` | Uses `--train_data_files train_tokenized.pt`. |
| `janus_sft_und.sh` | `align_anything.trainers.janus.sft_und` | supervised text-image-to-text | Uses `--train_template Janus_TI2T`. |
| `janus_dpo_und.sh` | `align_anything.trainers.janus.dpo_und` | preference text-image-to-text | Uses `--train_template Janus_TI2T`. |

These shell scripts set a `JANUS_REPO_PATH` placeholder, extend `PYTHONPATH`, source the repository setup script, and invoke DeepSpeed. Do not run them without replacing the placeholder and confirming the trainer/data pair.

## InterMT Details

InterMT is presented as a dataset and benchmark package for multi-turn interleaved preference alignment with human feedback. The README describes:

- 15.6k prompts, 52.6k multi-turn dialogue instances, and 32.4k preference pairs.
- Human preferences at local turn and global conversation levels across nine dimensions.
- InterMT-Bench tasks: scoring evaluation, pair comparison, and crucial step recognition.
- Interleaved text and image histories, with benchmark images hosted as a dataset asset.

No safe Align-Anything-local runnable entrypoint was evidenced in the inspected project files. Use this material as reference evidence unless the user intentionally prepares the benchmark package/data and asks to work with that runtime.

## Language Feedback Details

The README states this folder is under development and internal-use oriented. The three scripts implement a pipeline pattern:

1. `base_gen.py`: creates base model outputs from input JSON records containing image paths and prompts.
2. `critique_gen.py`: uses prompt, image, and an existing response field to generate critique/refinement text.
3. `refine_gen.py`: uses prompt, image, response, and critique fields to generate refined output.

All three use vLLM with a multimodal prompt object containing `multi_modal_data: {'image': Image.open(image_file)}` and set `tensor_parallel_size=8`, `gpu_memory_utilization=0.95`, `swap_space=32`, `temperature=1.0`, `repetition_penalty=1.1`, and `max_tokens=2048` in the inspected pattern. Treat those as heavy defaults to be reduced or confirmed before any run.

## Text-Image-to-Text-Image Details

The README explains that this workflow relies on Chameleon image-output support that is not available in ordinary upstream Transformers at the time described by the project. It points to a forked Transformers runtime and Chameleon models `PKU-Alignment/AA-chameleon-7b-base` and `PKU-Alignment/AA-chameleon-7b-plus`.

### Pre-tokenization entrypoints

| Script | Data flavor | Expected records | Output |
| --- | --- | --- | --- |
| `pre_tokenize_example.py` | single-process SFT-style examples | `input_text`, `input_image`, and `output_text` in the generic formatter pattern | A `.pt` list of tokenized samples. |
| `pre_tokenize_parallel_example.py` | multi-process SFT-style examples | same generic Chameleon formatter pattern | Per-sample cache files gathered into one `.pt` file. |
| `preference_tokenize_example.py` | DPO/RM preference examples | generic `input_text`, input/better/worse image/text fields, with helper formatters for Pick-a-Pic and SPAVL-like data | A `.pt` list containing better/worse token ids. |
| `prompt_only_tokenize_example.py` | PPO prompt-only examples | generic prompt/image fields, with helper formatters for prompt-only internal data | A `.pt` list of prompt token ids. |

These scripts use `AccustomedChameleonModel.pre_tokenization(...)`, `ChameleonProcessor`, `AutoTokenizer`, and bfloat16 tensors. Several scripts drop samples longer than 4096 token ids. The parallel scripts expose `--cache_dir` but the worker-spawn pattern in the inspected code passes the literal `.cache` to child workers; verify the actual cache location before running.

### Training-pattern evidence

The README gives DeepSpeed command patterns for:

- `align_anything.trainers.text_image_to_text_image.sft` with template `ANYTHING_TI2TI`.
- `align_anything.trainers.text_image_to_text_image.dpo` with preference data files.
- `align_anything.trainers.text_image_to_text_image.rm` with train/eval data files and templates.
- `align_anything.trainers.text_image_to_text_image.ppo` with actor, critic, reward, PTX data, and template choices.

It also notes that PPO support is constrained by a Transformers-related issue and only supports batch size 1 in the described workflow. Batch inference and GPT-based evaluation are described as external-repository workflows, not integrated Align-Anything commands.

## Eval-Anything Overview

Eval-Anything is a separate package under the projects tree. Its high-level surface is summarized in `references/eval-anything-notes.md`. The most important routing point is that it should not be treated as a lightweight auxiliary script: its package metadata requires a broad evaluation stack, including vLLM, multimodal/audio/video/image packages, and optional VLA extras.

## Safe Entrypoint Discovery

Use the bundled `scripts/list_project_entrypoints.py` to produce a static inventory. The script:

- Reports project README presence and main headings.
- Parses Python files with `ast` to list imports, classes, functions, argparse flags, and `__main__` guards.
- Reads shell scripts as text and reports command-line patterns without executing them.
- Reports known state and prerequisite notes for each project.

The script intentionally does not import Align-Anything, Janus, Transformers, vLLM, Eval-Anything, or any project-local module.
