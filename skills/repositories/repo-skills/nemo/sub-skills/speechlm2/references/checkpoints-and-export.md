# SpeechLM2 Checkpoints and Export

Use this reference when loading, saving, resuming, converting, exporting, or serving SpeechLM2 checkpoints.

## Formats

SpeechLM2 checkpoint behavior differs from classic NeMo ASR/TTS:

- SpeechLM2 model checkpoints are HuggingFace-style directories with `config.json` and `model.safetensors`.
- `.safetensors` is the primary safe tensor format for SpeechLM2 `save_pretrained` / `from_pretrained` workflows.
- Distributed checkpoints are directories with PyTorch distributed checkpoint metadata and rank shard files, usually produced under FSDP2/TP/Automodel strategies.
- Single-file `.ckpt` and `.pt` checkpoints are PyTorch Lightning/training checkpoints.
- `.nemo` archives are not the primary SpeechLM2 output checkpoint format; SpeechLM2 uses `.nemo` mainly to load pretrained ASR/perception/audio components.

## Loading with `from_pretrained`

For non-distributed loading:

```python
from nemo.collections.speechlm2 import SALM, SALMAutomodel, NemotronVoiceChat

salm = SALM.from_pretrained("HF_DIR_OR_REPO_ID").eval()
automodel = SALMAutomodel.from_pretrained("HF_DIR_OR_REPO_ID").eval()
voicechat = NemotronVoiceChat.from_pretrained("VOICECHAT_HF_DIR").eval()
```

For distributed SALMAutomodel loading:

```python
from nemo.collections.speechlm2 import SALMAutomodel
from nemo.collections.speechlm2.parts.parallel import setup_distributed

strategy = setup_distributed(tp_size=2, ep_size=1, pp_size=1, cp_size=1)
model = SALMAutomodel.from_pretrained(
    "HF_DIR_OR_REPO_ID",
    device_mesh=strategy.device_mesh,
    distributed_config=strategy.distributed_config,
    moe_config=strategy.moe_config,
    moe_mesh=strategy.moe_mesh,
    torch_dtype="bfloat16",
).eval()
```

The `HFHubMixin` loader reads `config.json`, injects local cached artifact paths for bundled files, sets `pretrained_weights` false so original child modules are not reloaded over final trained weights, and loads `model.safetensors`. With a device mesh, it builds the parallelized model first and loads safetensors shards through distributed checkpoint utilities.

## Resume vs Fine-Tune Initialization

Use the right field:

- `exp_manager.resume_from_checkpoint`: resume the same run with optimizer state, scheduler state, and training step.
- `model.init_from_checkpoint`: initialize model weights only, discard optimizer/scheduler/step, and fine-tune with a fresh training state.

`model.init_from_checkpoint` supports:

- Distributed checkpoint directories with `.metadata` and shard files.
- HuggingFace directories containing `model.safetensors`.
- Single-file `.ckpt` or `.pt` checkpoints with a `state_dict`.

Do not try to initialize a classic `SALM` model from a `SALMAutomodel` checkpoint or vice versa unless the state dict was explicitly adapted; embedding/module structures differ and key mismatches are expected.

## Export SALM/SALMAutomodel to HuggingFace Format

The source `to_hf.py` behavior is distilled here as a reference-only workflow. It loads a training checkpoint plus the resolved experiment config, instantiates the model class, consolidates DTensor/distributed state if needed, writes `model.safetensors`, writes `config.json`, saves the LLM backbone config under `llm_backbone/`, and optionally patches the export for vLLM.

Inputs:

- `class_path`: e.g. `nemo.collections.speechlm2.models.SALM` or `nemo.collections.speechlm2.models.SALMAutomodel`.
- `ckpt_path`: single checkpoint file or distributed checkpoint directory.
- `ckpt_config`: experiment config used to instantiate the model architecture.
- `output_dir`: destination HF directory.
- `dtype`: export dtype such as `float32`, `float16`, `bfloat16`, or `bf16`.

Command shape for a user-owned conversion script based on the distilled behavior:

```bash
python user_to_hf.py \
  class_path=nemo.collections.speechlm2.models.SALMAutomodel \
  ckpt_path=CHECKPOINT_OR_DCP_DIR \
  ckpt_config=EXP_CONFIG.yaml \
  output_dir=HF_EXPORT_DIR \
  dtype=bfloat16
```

For distributed checkpoint directories trained with `AutomodelParallelStrategy`, launch with the same number of processes needed to reconstitute the checkpoint mesh:

```bash
torchrun --nproc-per-node=8 user_to_hf.py \
  class_path=nemo.collections.speechlm2.models.SALMAutomodel \
  ckpt_path=DISTRIBUTED_CKPT_DIR \
  ckpt_config=EXP_CONFIG.yaml \
  output_dir=HF_EXPORT_DIR \
  dtype=bfloat16
```

Important behavior:

- For distributed exports, the converter reads `trainer.strategy` from `ckpt_config`, creates the Automodel device mesh, builds the model with `init_configure_model: false`, loads checkpoint shards, consolidates DTensors to full tensors on rank 0, and saves HF files.
- For non-distributed exports, the converter initializes the model, loads the checkpoint on CPU, casts to target dtype, and calls `save_pretrained`.
- `pretrained_weights` should be set false after loading the final checkpoint to prevent reloading initial pretrained child weights.

## Make SALM Exports vLLM-Ready

The vLLM prep step expects:

- `model_cfg.pretrained_llm` is present and can load a HF config/tokenizer.
- `model_cfg.audio_locator_tag` is present.
- Exported `config.json` exists in `output_dir`.

It patches:

- `config.json` with `model_type: "nemo_speechlm"`, `architectures: ["NeMoSpeechLMForConditionalGeneration"]`, and `audio_locator_tag`.
- tokenizer files, adding the audio token if missing.
- `tokenizer_config.json`, coercing `extra_special_tokens` to `{"audio_token": AUDIO_TOKEN}` and `tokenizer_class` to `PreTrainedTokenizerFast` for broad HF/vLLM compatibility.
- `generation_config.json` with EOS token id.

The current vLLM plugin accepts only `audio_locator_tag: "<|audio|>"`. If an exported checkpoint uses `<|audioplaceholder|>` or another token, `NeMoSpeechLMConfig` rejects it at load time. Fix by training/exporting with `<|audio|>` for vLLM or making a deliberate plugin change that updates both config validation and model placeholder behavior.

## vLLM Plugin Details

The plugin registers itself through `nemo.collections.speechlm2.vllm.salm.register()` and declares:

```text
model_type: nemo_speechlm
architecture: NeMoSpeechLMForConditionalGeneration
audio placeholder: <|audio|>
```

It wraps the LLM backbone config and auto-detects hybrid backends:

- Hybrid backbones include `NemotronHForCausalLM` and `NemotronHybridForCausalLM`; they route to the hybrid/Mamba-aware backend.
- Standard transformer backbones such as Qwen/Llama route to the transformer backend and get `layer_types: ["attention", ...]` so vLLM treats them as attention-only at runtime.
- The plugin adds extra embedding rows for the SpeechLM audio token and alignment headroom.

Serving command shape:

```bash
vllm serve HF_EXPORT_DIR --trust-remote-code --max-num-seqs 1 --gpu-memory-utilization 0.8
```

Add user-specific flags for tensor parallelism, model length, prefix caching, tool calling, reasoning parsers, and Mamba cache dtype only when the selected LLM/backend requires them.

## Export Nemotron VoiceChat

Nemotron VoiceChat export constructs a joint model from separate Duplex STT and Duplex EAR-TTS checkpoints/configs and saves a HF-compatible directory loadable by `NemotronVoiceChat.from_pretrained(output_dir)`.

Inputs:

- `stt_ckpt_path`: STT checkpoint file, safetensors file, or distributed checkpoint directory.
- `stt_ckpt_config`: STT experiment config.
- `tts_ckpt_path`: EAR-TTS checkpoint file, safetensors file, or distributed checkpoint directory.
- `tts_ckpt_config`: EAR-TTS experiment config.
- `output_dir`: destination VoiceChat HF directory.
- `dtype`: target save dtype, often `float32`, `float16`, or `bfloat16`.
- `register_speaker_dict`: optional mapping from speaker names to reference audio files.
- `reinit_audio_prompt_frozen_projection`: optional flag to disable voice cloning effects by reinitializing the audio prompt projection.

Command shape:

```bash
python user_nemotron_voicechat_to_hf.py \
  stt_ckpt_path=STT_CKPT_OR_DIR \
  stt_ckpt_config=STT_EXP_CONFIG.yaml \
  tts_ckpt_path=TTS_CKPT_OR_DIR \
  tts_ckpt_config=TTS_EXP_CONFIG.yaml \
  output_dir=VOICECHAT_HF_DIR \
  dtype=float32
```

Exporter behavior to preserve in user-owned adaptations:

- Load STT and TTS configs with OmegaConf.
- Set STT preload fields such as `pretrained_perception_from_s2s` and `pretrained_s2s_model` to null when present so export uses checkpoint weights instead of reinitializing from external models.
- Set TTS `pretrained_codec_model` to null when present so export uses checkpoint weights.
- Construct a joint config with `model.scoring_asr`, `model.stt`, `model.speech_generation`, `data.frame_length`, `data.source_sample_rate`, and `data.target_sample_rate`.
- Load each checkpoint into the correct submodule (`stt_model`, `tts_model`) with support for DCP directories, safetensors, or PyTorch state dicts.
- Optionally register speaker reference audio at the TTS target sample rate before saving.

Difficult case: converting distributed STT/TTS checkpoint pieces to HF-compatible Nemotron VoiceChat requires restoring each component into the joint model under the correct submodule prefixes, not concatenating raw shard files or copying configs alone.

## `save_pretrained` Expectations

SpeechLM2 `HFHubMixin.save_pretrained` ensures HF-compatible fields in config dictionaries:

```json
{
  "model_type": "nemo_speechlm",
  "architectures": ["NeMoSpeechLMForConditionalGeneration"]
}
```

For non-SALM classes such as `NemotronVoiceChat`, preserve the config structure expected by `from_pretrained`; do not manually flatten nested STT/TTS configs unless the model's loader expects it.

## Safety Notes

- Export and conversion can create or overwrite large checkpoint directories. Confirm destination paths with the user if there is any ambiguity.
- Export may require network access to load tokenizer/backbone configs from HuggingFace unless all artifacts are local and cached.
- Distributed exports must run with CUDA/NCCL and a process count compatible with the saved checkpoint mesh.
- vLLM serving is optional and dependency-heavy; failure to prepare vLLM should leave a NeMo/HF-loadable checkpoint intact when possible.
- Do not promise `.nemo` packaging for SpeechLM2 final checkpoints; use HF/safetensors unless the task specifically concerns ASR/TTS component inputs.
