# Model and dataset registry

`pipeline.benchmarks.evaluate` imports benchmark implementations dynamically from exact registry keys. A name mismatch fails before evaluation with an assertion such as `<name> is not an available model` or `<name> is not an available eval dataset`.

## Dataset registry

| `datasets[].name` | Class | Default data source | Useful config keys | Credential / output notes |
|---|---|---|---|---|
| `magnifierbench` | `MagnifierBenchDataset` | `Otter-AI/MagnifierBench` | `split`, `data_path`, `prompt`, `cache_dir`, `default_output_path`, `debug`, `api_key` | Computes option accuracy, then queries GPT for free-form scoring. Treat `api_key` as required for full scoring. Writes answer and score JSON under `default_output_path` (default `./logs/MagBench`). |
| `mmbench` | `MMBenchDataset` | `Otter-AI/MMBench` | `split` (`test` or `dev`), `version`, `sys_prompt`, `cache_dir`, `default_output_path`, `debug` | Writes an XLSX result file under `default_output_path` (default `./logs/MMBench`). |
| `mmvet` | `MMVetDataset` | `Otter-AI/MMVet` | `split`, `api_key`, `gpt_model`, `num_run`, `prompt`, `cache_dir`, `default_output_path`, `debug` | `api_key` is a keyword-only required constructor argument. GPT grading writes model result JSON plus grade/capability CSV files under `default_output_path` (default `./logs/MMVet`). |
| `mathvista` | `MathVistaDataset` | `Otter-AI/MathVista` | `split` (`test` or `dev`), `api_key`, `gpt_model`, `quick_extract`, `cache_dir`, `default_output_path`, `debug` | Uses GPT-assisted answer extraction when quick extraction is insufficient. Treat `api_key` and `gpt_model` as required for full benchmark scoring. Writes submit and score JSON under `default_output_path` (default `./logs/MathVista`). |
| `pope` | `PopeDataset` | `Otter-AI/POPE` | `split`, `cache_dir`, `default_output_path`, `batch_size` | Writes JSONL-style submit output under `default_output_path` (default `./logs/POPE`). |
| `mme` | `MMEDataset` | `Otter-AI/MME` | `split`, `cache_dir`, `default_output_path`, `debug` | Groups results by cognition/perception category and writes per-task JSON plus score summaries under a timestamped subdirectory. |
| `scienceqa` | `ScienceQADataset` | `Otter-AI/ScienceQA` | `split`, `cache_dir`, `default_output_path`, `batch`, `prompt`, `debug` | Writes prediction JSON and score JSON under `default_output_path` (default `./logs/ScienceQA`). |
| `seedbench` | `SEEDBenchDataset` | `Otter-AI/SEEDBench` | `split`, `cache_dir`, `default_output_path` | Writes submit JSON under `default_output_path` (default `./logs`). |

Dataset caveats:

- All listed datasets use the Hugging Face `datasets` loader by default, so first runs may download data and need a writable `cache_dir` or default HF cache.
- Config mode passes every dataset mapping directly into the dataset constructor after removing `name`; typoed keys fail at runtime unless caught by validation.
- `MagnifierBench`, `MM-VET`, and `MathVista` should be skipped when GPT credentials are unavailable or paid/API network calls are not allowed.
- Public documentation includes a spelling typo, `SicenceQA`; the actual registry key is `scienceqa`.

## Model registry

| `models[].name` | Class | Common config keys | Notes |
|---|---|---|---|
| `otter_image` | `OtterImage` | `model_path`, `load_bit` (`bf16`, `fp16`, or implementation-supported precision) | Default path points to an Otter image checkpoint. Loads with sequential device mapping. |
| `otter_video` | `OtterVideo` | `model_path`, `load_bit` | Video/image Otter wrapper with default Otter video checkpoint. Requires video/image dependencies such as OpenCV when used. |
| `otterhd` | `OtterHD` | `model_path`, `cuda_id`, `resolution`, `max_new_tokens` | Fuyu-style high-resolution wrapper; `resolution` controls short-edge resizing when not `-1`. |
| `fuyu` | `Fuyu` | `model_path`, `cuda_id`, `resolution`, `max_new_tokens` | Default model path is `adept/fuyu-8b`. Useful for MagnifierBench/OtterHD-style high-resolution tests. |
| `idefics` | `Idefics` | `model_path`, `batch` | Default model path is `HuggingFaceM4/idefics-9b-instruct`; can batch some eval-forward paths. |
| `instructblip` | `InstructBLIP` | `model_path`, `cuda_id`, `max_new_tokens` | Default model path is `Salesforce/instructblip-vicuna-7b`. |
| `qwen_vl` | `QwenVL` | `model_path`, optional `model_name` | Default model path is `Qwen/Qwen-VL-Chat`; uses `trust_remote_code=True`. |
| `llava_model` | `LLaVA_Model` | `model_path`, `model_base`, `model_name`, `conv_mode` | Requires LLaVA package/runtime to be importable. |
| `llama_adapter` | `LlamaAdapter` | `model_path` | Requires the LLaMA-Adapter repository/package layout to be importable. No default `model_path`; provide one. |
| `mplug_owl` | `mPlug_owl` | `model_path` | Requires mPLUG-Owl video dependencies. No default `model_path`; provide one. |
| `video_chat` | `VideoChat` | `model_path` | Requires Ask-Anything/VideoChat dependencies and video runtime packages. No default `model_path`; provide one. |
| `video_chatgpt` | `Video_ChatGPT` | `model_path` | Requires Video-ChatGPT dependencies and projection/model assets. No default `model_path`; provide one. |
| `gpt4v` | `OpenAIGPT4Vision` | `api_key`, `max_new_tokens` | Calls OpenAI-compatible vision API directly; skip when credentials/network are unavailable. |
| `frozen_bilm` | `FrozenBilm` registry entry | Not usable as-is | The registry names this key, but the representative source file is empty in the inspected checkout; treat it as blocked unless a local implementation is supplied. |

Model caveats:

- Each model entry is passed directly into the constructor after removing `name`.
- If `model_path` points to a remote Hugging Face id, the run may download weights. If it points to a local path, make sure the path exists in the runtime environment.
- Several wrappers depend on third-party repositories that are not installed by Otter itself. If an import fails for LLaVA, LLaMA-Adapter, mPLUG-Owl, VideoChat, or Video-ChatGPT, skip that model or prepare the dependency explicitly before running benchmarks.
- The registry contains `instructblip` once semantically even though the underlying mapping repeats the key in source; use the key `instructblip`.

## Choosing a launch set

Use this order when making benchmark plans:

1. Validate exact registry keys and constructor fields.
2. Decide whether GPT-judged datasets/models are permitted. If not, remove `magnifierbench`, `mmvet`, `mathvista`, and `gpt4v`.
3. Decide whether public HF dataset downloads are permitted. If not, use pre-cached datasets and set dataset-level `cache_dir`, or skip.
4. Decide whether model downloads are permitted. If not, use local `model_path` values and validate existence with the validator's `--check-paths` option.
5. Start with one model and one low-credential dataset before expanding to a full benchmark matrix.
