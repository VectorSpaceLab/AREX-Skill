# SpeechLM2 Workflows

This reference gives checkout-independent workflows for SpeechLM2 tasks. It distills evidence from the SpeechLM2 docs, examples, source, and tests named in `../SKILL.md`; do not require the original checkout at runtime.

## Import Surface

Use the package import surface first:

```python
import nemo.collections.speechlm2 as slm

# Public classes exposed by the collection:
# slm.SALM, slm.SALMAutomodel, slm.SALMWithAsrDecoder
# slm.DuplexS2SModel, slm.DuplexS2SSpeechDecoderModel, slm.DuplexSTTModel
# slm.DuplexEARTTS, slm.NemotronVoiceChat
# slm.SALMDataset, slm.DuplexS2SDataset, slm.DuplexSTTDataset, slm.DuplexEARTTSDataset, slm.DataModule
```

SpeechLM2 has no package console entry points in the verified package metadata. Prefer API snippets or user-owned scripts. If a task started from a NeMo source example, treat the example as evidence for structure, not as a runtime dependency.

## SALM Generation

Use `SALM` for a HuggingFace-Transformers LLM backbone on one device. Use `SALMAutomodel` for distributed inference or an Automodel-trained checkpoint.

```python
import torch
import soundfile as sf
from transformers import GenerationConfig
from nemo.collections.audio.parts.utils.transforms import resample
from nemo.collections.speechlm2 import SALM

model = SALM.from_pretrained("CHECKPOINT_OR_HF_DIR").eval().to("cuda")
audio, sample_rate = sf.read("AUDIO.wav")
audio = torch.as_tensor(audio, dtype=torch.float32).unsqueeze(0)
if sample_rate != 16000:
    audio = resample(audio, sample_rate, 16000)
audio = audio.to(model.device)
audio_lens = torch.tensor([audio.shape[-1]], device=model.device)

prompt = [[{"role": "user", "content": f"Transcribe this: {model.audio_locator_tag}"}]]
answer_ids = model.generate(
    prompts=prompt,
    audios=audio,
    audio_lens=audio_lens,
    generation_config=GenerationConfig(max_new_tokens=128, bos_token_id=model.text_bos_id, eos_token_id=model.text_eos_id, pad_token_id=model.text_pad_id),
)
print(model.tokenizer.ids_to_text(answer_ids[0]))
```

Key constraints:

- The number of audio placeholders in `prompts` must match the number of provided audio segments.
- `prompts` may be a list of chat turns or already-tokenized tensors; if tensors are passed, they must already include the correct chat template and audio placeholder token id.
- If audio paths are embedded inside prompt dictionaries, do not also pass `audios`/`audio_lens`; the model asserts that the two mechanisms are mutually exclusive.
- Use `enable_thinking` only with prompt formats that support a thinking/reasoning flag.

## SALMAutomodel Distributed Generation

Distributed inference must use `SALMAutomodel`. Evidence from the generation/evaluation scripts shows the distributed branch rejects plain `SALM` because it needs Automodel device meshes.

```python
import torch
from nemo.collections.speechlm2 import SALMAutomodel
from nemo.collections.speechlm2.parts.parallel import setup_distributed

strategy = setup_distributed(tp_size=1, ep_size=2, pp_size=1, cp_size=1)
model = SALMAutomodel.from_pretrained(
    "CHECKPOINT_OR_HF_DIR",
    device_mesh=strategy.device_mesh,
    distributed_config=strategy.distributed_config,
    moe_config=strategy.moe_config,
    moe_mesh=strategy.moe_mesh,
    torch_dtype="bfloat16",
).eval()

with torch.inference_mode():
    answer_ids = model.generate(prompts=prompt, audios=audio, audio_lens=audio_lens, max_new_tokens=128)
```

Launch distributed Python with the user's normal PyTorch launcher, for example `torchrun --nproc_per_node=N user_salm_infer.py`. Do not set `tp_size`, `ep_size`, `pp_size`, or `cp_size` greater than the actual world size product. If `use_nemo_automodel` is false or absent in a checkpoint config and the user requests distributed inference, convert/retrain/export from a SALMAutomodel-compatible checkpoint first or keep inference non-distributed.

Difficult case: if the user asks for distributed SALM inference while `use_nemo_automodel: false`, explain that distributed SpeechLM2 inference is an Automodel path. Changing only the CLI flags is not enough; the checkpoint/config must load via `SALMAutomodel`.

## SALM Training Pattern

A SALM training script follows this skeleton. The user's config controls model, trainer, data, and experiment manager.

```python
import torch
from lightning.pytorch import Trainer, seed_everything
from omegaconf import OmegaConf
from nemo.collections.speechlm2 import DataModule, SALM, SALMAutomodel, SALMDataset
from nemo.utils.exp_manager import exp_manager
from nemo.utils.trainer_utils import resolve_trainer_cfg

cfg = OmegaConf.load("speechlm2_salm.yaml")
OmegaConf.resolve(cfg)
if torch.cuda.is_available() and cfg.trainer.devices != 1:
    torch.distributed.init_process_group(backend="nccl")
seed_everything(cfg.data.train_ds.seed)
trainer = Trainer(**resolve_trainer_cfg(cfg.trainer))
log_dir = exp_manager(trainer, cfg.get("exp_manager", None))
OmegaConf.save(cfg, log_dir / "exp_config.yaml")
model_cls = SALMAutomodel if cfg.model.get("use_nemo_automodel", False) else SALM
with trainer.init_module():
    model = model_cls(OmegaConf.to_container(cfg.model, resolve=True))
dataset = SALMDataset(tokenizer=model.tokenizer, multispeaker_cfg=cfg.data.get("multispeaker_cfg", None))
datamodule = DataModule(cfg.data, tokenizer=model.tokenizer, dataset=dataset)
trainer.fit(model, datamodule)
```

Use `SALMAutomodel` when training with MoE backbones, Automodel-native LoRA, FSDP2, TP, PP, CP, EP, HSDP, grouped GEMM, DeepEP, or large distributed Nemotron backbones. Use `SALM` when a simpler HuggingFace backend is sufficient.

## Duplex STT and S2S

Duplex models use conversation-style Lhotse cuts where input roles are user-side speech/text and output roles are agent/assistant responses.

- `DuplexSTTModel`: predicts agent text in duplex conversations.
- `DuplexS2SModel`: predicts text and discrete audio codes for speech-to-speech.
- `DuplexS2SSpeechDecoderModel`: uses a specialized speech decoder for generated speech.
- `DuplexEARTTS`: streaming/duplex text-to-speech component; supports interruption-aware generation and audio prompt speaker conditioning.

Minimal validation/inference structure for `DuplexSTTModel`:

```python
from lightning.pytorch import Trainer
from omegaconf import OmegaConf
from nemo.collections.speechlm2 import DataModule, DuplexSTTDataset, DuplexSTTModel
from nemo.utils.exp_manager import exp_manager
from nemo.utils.trainer_utils import resolve_trainer_cfg

cfg = OmegaConf.load("duplex_stt.yaml")
trainer = Trainer(**resolve_trainer_cfg(cfg.trainer))
log_dir = exp_manager(trainer, cfg.get("exp_manager", None))
with trainer.init_module():
    model = DuplexSTTModel(OmegaConf.to_container(cfg.model, resolve=True))
dataset = DuplexSTTDataset(
    tokenizer=model.tokenizer,
    frame_length=cfg.data.frame_length,
    source_sample_rate=cfg.data.source_sample_rate,
    input_roles=cfg.data.input_roles,
    output_roles=cfg.data.output_roles,
    cfg=OmegaConf.to_container(cfg.data, resolve=True),
)
datamodule = DataModule(cfg.data, tokenizer=model.tokenizer, dataset=dataset)
trainer.validate(model, datamodule)
```

For direct offline inference, construct tensors at the model source sample rate and call `offline_inference(input_signal=..., input_signal_lens=...)`. Speech-generating models return text plus audio/audio length outputs; STT returns text-oriented outputs.

## Duplex EAR-TTS

`DuplexEARTTS` is the SpeechLM2 duplex TTS component, not the classic TTS collection. It relies on precise token padding and EOS placement for interruption-aware generation. Use it when a SpeechLM2/Nemotron VoiceChat pipeline needs streamable agent speech, not for ordinary TTS-only tasks.

Expected inference/eval record shape for EAR-TTS-style JSONL:

```json
{"text": "Short response text.", "context_audio_filepath": "speaker_reference.wav", "audio_filepath": "output.wav"}
{"text": ["Yes.", "Sure.", "I understand."], "context_audio_filepath": "speaker_reference.wav", "audio_filepath": "multi_turn_output.wav"}
```

Important parameters:

- `datasets_json_path`: JSONL file of requested utterances and optional speaker references.
- `checkpoint_path`: EAR-TTS checkpoint directory/file.
- `out_dir`: generated waveform output directory.
- `user_custom_speaker_reference`: optional override speaker reference.
- `inference_guidance_scale`, `inference_noise_scale`, `inference_top_p_or_k`, `inference_guidance_enabled`, and `inference_force_speech_silence_on_eos`: generation behavior knobs used in Nemotron VoiceChat configs.

## Nemotron VoiceChat

`NemotronVoiceChat` chains a `DuplexSTTModel` with `DuplexEARTTS`. It is inference-only; `training_step` is intentionally not implemented. To improve capabilities, train the STT and EAR-TTS components independently, then export a joint checkpoint.

```python
import torch
import soundfile as sf
from nemo.collections.audio.parts.utils.transforms import resample
from nemo.collections.speechlm2 import NemotronVoiceChat

model = NemotronVoiceChat.from_pretrained("VOICECHAT_HF_DIR").eval().to("cuda")
user_audio, sample_rate = sf.read("user_prompt.wav")
user_audio = torch.as_tensor(user_audio, dtype=torch.float32).unsqueeze(0)
if sample_rate != model.full_cfg.data.source_sample_rate:
    user_audio = resample(user_audio, sample_rate, model.full_cfg.data.source_sample_rate)
user_audio = user_audio.to(model.device)
user_lens = torch.tensor([user_audio.shape[-1]], device=model.device)

# Optional explicit speaker reference; otherwise config-level speaker name/reference is used.
result = model.offline_inference(input_signal=user_audio, input_signal_lens=user_lens)
print(result["text"][0])
agent_waveform = result["audio"][0]
```

Speaker-conditioning precedence:

1. Explicit `speaker_audio` and `speaker_audio_lens` passed to `offline_inference`.
2. Config `model.inference_speaker_name`, such as a registered speaker name.
3. Config `model.inference_speaker_reference`, a reference waveform path.

Evaluation config usually includes a scoring ASR model, a Lhotse validation dataset, `data.source_sample_rate` for user input, `data.target_sample_rate` for generated speech, and `input_roles`/`output_roles`.

## vLLM Serving for SALM

The SpeechLM2 vLLM plugin registers:

- Config type: `nemo_speechlm`.
- Model architecture: `NeMoSpeechLMForConditionalGeneration`.
- Placeholder token: exactly `<|audio|>`.

Before vLLM serving, export/patch the checkpoint so `config.json` contains `model_type: "nemo_speechlm"`, `architectures: ["NeMoSpeechLMForConditionalGeneration"]`, and `audio_locator_tag: "<|audio|>"`; tokenizer files must include the audio token and a normalized `tokenizer_config.json`.

Serving shape:

```bash
vllm serve HF_EXPORT_DIR --trust-remote-code --max-num-seqs 1 --gpu-memory-utilization 0.8
```

Use the user's vLLM parameters for tensor parallelism, model length, tool calling, or reasoning parsers. For SpeechLM2 checkpoints with any audio token other than `<|audio|>`, vLLM loading fails by design; export with `<|audio|>` or update both plugin placeholder constants and model class behavior together.

## Voice Agent

The NeMo voice-agent code composes local ASR, optional diarization, an LLM backend, TTS, turn-taking, WebSocket transport, browser client, and optional tool calling. Use it when the task is a local conversational voice-agent service rather than a single SpeechLM2 model.

Config surfaces:

- `llm.type`: `auto`, `hf`, or `vllm`; `auto` tries vLLM then HuggingFace.
- `llm.model`, `llm.system_prompt`, `llm.generation_kwargs`, `llm.apply_chat_template_kwargs`, `llm.vllm_server_params`, and `llm.vllm_generation_params`.
- `asr.model`, diarization enable/model knobs, TTS model/config, VAD/turn-taking `stop_secs`, backchannel phrases, and component GPU assignment.
- Tool calling is supported through vLLM for selected LLMs; direct tools and component behavior tools are registered into the LLM service.

Deployment prerequisites are larger than library inference: GPU, microphone/speaker, Python environment with voice-agent dependencies, Node/npm for the browser client, WebSocket reachable host/port, and browser microphone permissions.

## Reference-Only Source Scripts

The original `examples/speechlm2/*.py` and `examples/voice_agent/**` scripts are reference-only for this generated skill. Reasons: they are long-running, training/evaluation/GPU-heavy, often network/checkpoint-bound, may mutate checkpoint/output directories, and some depend on source checkout-relative Hydra config paths or browser/server files. This sub-skill distills their behavior into API snippets and bundled references instead of copying them verbatim.
