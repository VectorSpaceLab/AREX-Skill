# Model packaging and checkpoint compatibility

Use this reference before changing MOSS-TTS model directories, fusing codec weights, moving remote-code snapshots, or debugging import/model-load behavior.

## Installation profiles relevant to this sub-skill

| Profile | Command shape | Use | Caveats |
|---|---|---|---|
| Runtime HF generation | `python -m pip install --extra-index-url https://download.pytorch.org/whl/cu128 -e ".[torch-runtime]"` | AutoModel/AutoProcessor generation, Gradio-style demos | Requires torch, torchaudio, torchcodec, transformers, accelerate, and FFmpeg. Match CUDA/CPU wheel index to the host. |
| Runtime + FlashAttention | `python -m pip install --extra-index-url https://download.pytorch.org/whl/cu128 -e ".[torch-runtime,flash-attn]"` | Faster/lower-memory CUDA generation | Only useful on supported NVIDIA GPUs and fp16/bf16 dtype; fallback to SDPA/eager if install/build fails. |
| Lightweight source inspection | `python -m pip install -e .` or package metadata only | Metadata and non-torch helper checks | Current packaging may not expose source packages after editable install; see package exposure caveat below. |
| llama.cpp / torch-free | route to `../llama-cpp-backend/SKILL.md` | GGUF/ONNX/TRT inference | Do not solve here. |
| SoundEffect v2 | route to `../soundeffect-v2/SKILL.md` | Separate DiT pipeline | Separate environment and dependency set. |

## Package exposure caveat

The current project metadata declares `name = "moss-tts"`, version `0.1.0`, and has `[tool.setuptools] py-modules = []`. In some editable installs, this produces distribution metadata but does **not** expose importable source packages such as `moss_tts_delay` from arbitrary working directories.

Symptoms:

- `pip show moss-tts` or `importlib.metadata.version("moss-tts")` succeeds.
- `import moss_tts_delay` or a console/script that imports package modules fails with `ModuleNotFoundError`.

Safe fixes until packaging metadata is corrected:

1. Run from a source checkout directory that puts the source packages on `sys.path`.
2. Set `PYTHONPATH` to the checkout root for the process that needs local package imports.
3. Build/install a wheel or editable layout that explicitly includes the package directories.
4. For Hugging Face remote-code generation, prefer `AutoProcessor.from_pretrained(..., trust_remote_code=True)` and `AutoModel.from_pretrained(..., trust_remote_code=True)`, which load model code from the model snapshot rather than from the local package import path.

Do not hide this caveat when diagnosing import failures; successful package metadata is not proof that source modules are importable.

## Remote-code model directory checklist

A MOSS-TTS Hugging Face snapshot or local model directory must keep its model code, config, tokenizer, and weights mutually compatible.

Minimum high-level contents for a remote-code-capable directory:

- `config.json` with the correct `model_type`, `architectures`, audio token IDs, `n_vq`, sampling rate, language/backbone config, and any codec config when fused.
- Tokenizer assets: `tokenizer.json`, `tokenizer_config.json`, `special_tokens_map.json`, `chat_template.jinja`, plus optional added vocab/merge files as applicable.
- Processor config with the intended processor class and `auto_map` for `AutoProcessor` when not relying on repository code installed elsewhere.
- Modeling/configuration/processing Python files referenced by the `auto_map` or packaged in the model snapshot.
- `model.safetensors` or `model.safetensors.index.json` with all referenced shard files.
- Matching audio codec path or embedded/fused codec weights.

Do not manually combine files from different model families unless you also update config fields and verify tensor names/shapes.

## Compatibility matrix

| Model family | Architecture/code family | Typical `n_vq` | Codec/audio assumptions | Common incompatibility |
|---|---|---:|---|---|
| MOSS-TTS-v1.5 / MOSS-TTS 1.0 | `MossTTSDelay` | 32 | standard MOSS audio tokenizer, 24 kHz-style Delay workflow | Using Local code or TTSD 16-codebook audio codes. |
| MOSS-TTS-Local-Transformer 1.0 | `MossTTSLocal` | 32 | local-transformer 24 kHz mono workflow | Using Delay delay-pattern placeholder/code handling. |
| MOSS-TTS-Local-Transformer-v1.5 | `MossTTSLocal` v1.5 | 12 | MOSS-Audio-Tokenizer-v2, 48 kHz stereo | Flattening stereo output or passing 32-codebook codes. |
| MOSS-TTSD-v1.0 | `MossTTSDelay` TTSD checkpoint | 16 | per-speaker references and concatenated prompt audio | Reusing TTS 32-codebook processor config or fine-tune code. |
| MOSS-VoiceGenerator | `MossTTSDelay` 1.7B voice-design checkpoint | model-specific | instruction + text, no reference audio | Supplying reference audio instead of required `instruction`. |
| MOSS-SoundEffect v1 | `MossTTSDelay` | model-specific | `ambient_sound` prompt field | Confusing with SoundEffect v2 DiT pipeline. |

When `processor(..., n_vq=<value>)` is used, it checks provided audio-code tensors against the expected codebook count. A mismatch is a real compatibility error, not a warning to ignore.

## Model/code replacement rules

Use these rules when a user has a fine-tuned checkpoint, copied model directory, or custom cached snapshot:

1. Identify the base architecture first: Delay, Local 1.0, Local v1.5, TTSD, VoiceGenerator, or SoundEffect v1.
2. Keep the model's original remote-code files unless the fine-tune instructions explicitly require replacing them.
3. If replacing code, replace the whole compatible set: configuration, modeling, processing, processor config, tokenizer config class references, and any special token IDs.
4. Confirm `n_vq`, audio start/end/slot token IDs, `audio_pad_code`, sampling rate, and tokenizer added-token contents are consistent.
5. Confirm the audio codec expected by the processor: explicit `codec_path`, processor config path, or fused codec.
6. Run a tiny load/shape smoke before any long generation:

```python
processor = AutoProcessor.from_pretrained(model_dir, trust_remote_code=True)
model = AutoModel.from_pretrained(model_dir, trust_remote_code=True, torch_dtype=dtype)
print(processor.model_config.n_vq, processor.model_config.sampling_rate)
```

If generated audio is gibberish after a code/checkpoint change, revert to a known-matched snapshot and reapply changes one category at a time.

## Fused Delay model + codec packaging

The repository includes a maintenance workflow for producing a single local directory that embeds a Delay model and an audio codec. Treat this as a multi-GB checkpoint mutation, not a lightweight runtime step.

A correct fusion utility must perform these operations:

1. Validate both input directories are model directories with `config.json` and safetensors (`model.safetensors` or `model.safetensors.index.json`).
2. Copy tokenizer assets from the main model directory.
3. Copy or generate the fused processor source and write `processor_config.json` with an `AutoProcessor` mapping to the fused processor class.
4. Patch `tokenizer_config.json` so `processor_class` names the fused processor class.
5. Build a merged config:
   - remove top-level `auto_map` from the main config;
   - set `architectures` to the fused Delay-with-codec architecture;
   - set `model_type` to the fused Delay-with-codec type;
   - copy codec config under `codec_config` after removing codec `auto_map`;
   - propagate `audio_end_token_id` to `language_config.eos_token_id`;
   - propagate dtype into `language_config.dtype`.
6. Remap main model tensors from `language_model.*` to `model.*` when required by the fused architecture.
7. Prefix codec tensors with `codec_model.` and fail on any name collision.
8. Write output safetensors shards and a sorted `model.safetensors.index.json` with relative shard names only.
9. Verify the output index has exactly the expected main + codec tensor keys and that all tensors can be read from the written shards.

Command shape for a fusion tool with those semantics:

```bash
python <moss-tts-delay-codec-fusion-tool> \
  --model-path ./models/main-delay-model \
  --codec-model-path ./models/audio-codec-model \
  --save-path ./models/fused-output \
  --overwrite
```

Before running such a command, ensure there is enough disk space for rewritten safetensors and that the output path is disposable or backed up.

## Model download and cache controls

For production or offline runs:

```python
processor = AutoProcessor.from_pretrained(model_id_or_dir, trust_remote_code=True, revision="main")
model = AutoModel.from_pretrained(model_id_or_dir, trust_remote_code=True, local_files_only=True)
```

Use `local_files_only=True` only after the model and codec snapshots are already cached or present locally. If using a custom cache, set the standard Hugging Face cache environment variables before process start. Keep main model and codec revisions pinned together when reproducibility matters.

## Acceptance checks after packaging changes

Run these lightweight checks before expensive generation:

```python
from transformers import AutoConfig, AutoProcessor, AutoModel

cfg = AutoConfig.from_pretrained(model_dir, trust_remote_code=True)
processor = AutoProcessor.from_pretrained(model_dir, trust_remote_code=True)
print(type(cfg).__name__, type(processor).__name__)
print("n_vq=", getattr(processor.model_config, "n_vq", None))
print("sampling_rate=", getattr(processor.model_config, "sampling_rate", None))
```

Then run a one-sentence generation with `max_new_tokens` capped low only after runtime dependencies, device memory, model downloads, and codec loading are known to work.
