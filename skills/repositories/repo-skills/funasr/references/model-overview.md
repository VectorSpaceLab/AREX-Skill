# FunASR model overview

Use this page when the user asks which checkpoint to start with. The detailed backend caveats live in the relevant sub-skill.

## Common model families

| Family | Common model id | Start here when... | Route |
|---|---|---|---|
| SenseVoiceSmall | `iic/SenseVoiceSmall` | You want a CPU-friendly general ASR path, often with punctuation, emotion tags, or speaker-aware meetings. | `python-asr-pipelines` |
| Paraformer | `paraformer-zh` | You want Mandarin ASR with hotwords, timestamps, or subtitle-friendly output. | `python-asr-pipelines` |
| Paraformer English | `paraformer-en` | You want a compact English-only route. | `python-asr-pipelines` |
| Fun-ASR-Nano | `FunAudioLLM/Fun-ASR-Nano-2512` | You want LLM-based ASR on a GPU or vLLM-capable environment. | `llm-asr-and-vllm` |
| Fun-ASR-MLT-Nano | `FunAudioLLM/Fun-ASR-MLT-Nano-2512` | You want the multilingual Nano checkpoint. | `llm-asr-and-vllm` |
| GLM-ASR-Nano | `zai-org/GLM-ASR-Nano-2512` or `ZhipuAI/GLM-ASR-Nano-2512` | You want an LLM-ASR checkpoint with its own vLLM caveats. | `llm-asr-and-vllm` |
| Qwen3-ASR | `Qwen/Qwen3-ASR-0.6B` or `Qwen/Qwen3-ASR-1.7B` | You want Qwen3-ASR itself. | `llm-asr-and-vllm` for dependency routing; use the external `qwen-asr` runtime when intentionally choosing that stack |
| `fsmn-vad` | `fsmn-vad` | You need segmentation for long audio. | `python-asr-pipelines` |
| `ct-punc` | `ct-punc` | You need punctuation-aware sentence segmentation. | `python-asr-pipelines` |
| `cam++` | `cam++` | You need speaker diarization. | `python-asr-pipelines` or `serving-and-runtime` |
| ERes2NetV2 speaker verification | `iic/speech_eres2netv2_sv_zh-cn_16k-common` | You need a standalone speaker-verification embedding or short-form speaker similarity check. | `python-asr-pipelines` |
| `emotion2vec_plus_large` | `emotion2vec_plus_large` | You need emotion labels after ASR or as a separate model. | `python-asr-pipelines` |

## Simple choice rules

- **CPU default:** start with `SenseVoiceSmall`.
- **Mandarin production:** start with `paraformer-zh`.
- **GPU / LLM-ASR / batch throughput:** route to `Fun-ASR-Nano` or `GLM-ASR-Nano` and read the vLLM sub-skill.
- **Service deployment:** choose the model in the serving sub-skill after deciding the runtime surface.
- **Training/export:** the model family still matters, but the workflow should move to the training/export sub-skill.

## When not to pick a model here

- If the user only wants to fix punctuation spacing or run ITN/TN, do not change the ASR model; route to `text-normalization`.
- If the user only wants to expose a speech API or realtime service, route to `serving-and-runtime` after the model choice is clear.
- If the user is asking about vLLM applicability, tensor parallelism, dtype, or NPU/Ascend caveats, route to `llm-asr-and-vllm`.

## Context clues that matter

- **Long audio**: prefer a model plus VAD rather than a single-pass transcript.
- **Speaker labels**: pair ASR with VAD and CAM++ or a compatible speaker model.
- **Subtitle generation**: prioritize timestamp-aware output and sentence segmentation.
- **Model hub choice**: `ms` and `hf` are both supported, but the best default depends on the checkpoint and region.
