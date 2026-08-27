# Backend Matrix

## Required for this sub-skill's safe guidance

- Python supported by LazyLLM (`>=3.10,<3.14`).
- Base `lazyllm` import.
- No model/provider/GPU backend is required for planning, signature inspection, model type mapping, or online chat message utility checks.

## Optional backend classes

| Backend class | Signals | Install/runtime requirements | Verification posture |
| --- | --- | --- | --- |
| Online LLM/VLM provider | `OnlineModule`, `OnlineChatModule`, `source`, `api_key`, provider model names, timeout/auth errors | Provider SDK or HTTP endpoint, credentials, quota/budget, network | Optional unless user requests real provider call. Use message/model-type tests first. |
| Local model serving | `TrainableModule`, `ServerModule`, `lazyllm deploy`, vLLM/LMDeploy/LightLLM | backend extra, model weights/cache, GPU/CPU memory, port/security plan | Optional; classify GPU/backend and ask before execution. |
| Fine-tuning/distillation | finetune examples, LLaMA-Factory, Alpaca-LoRA, Collie, dataset path | training framework extra, GPU, dataset, output path, budget | Optional and expensive; never infer success from CPU import. |
| Multimodal generation/audio/OCR | painting, TTS, STT, OCR, multimodal examples | provider or local multimodal extra, file codecs, model/backend, credentials | Optional; run only tiny local format checks without approval. |
| Launcher/cluster deployment | k8s/slurm/SCO, replicas, service URLs | cluster access, launcher config, ports, credentials | External/optional. Keep as planning unless environment is explicitly provided. |

## Extra selection hints

- `vllm`, `lmdeploy`, `lightllm`, `deploy-all`: local inference/serving.
- `llama-factory`, `finetune-all`, framework-specific extras: training/fine-tuning.
- `multimodal`, `online-advanced`: multimodal/provider features.
- `standard`/`full`: broad installations; can be heavy and should be justified.

## CPU substitution

If the task is documentation, code generation, or triage rather than model execution, use CPU-safe substitutions:

- inspect signatures with root `scripts/inspect_lazyllm_surface.py`,
- run `scripts/model_surface_smoke.py`,
- validate provider model categories with `get_model_type`,
- test stream/message utilities with synthetic payloads,
- design `ServerModule`/flow wiring around a deterministic Python callable before replacing it with a real model.

## Stop conditions

Stop and ask for missing information when a real execution would require:

- an API key or provider account,
- model weights or download approval,
- a GPU or accelerator not already verified,
- a port/service that could conflict with user systems,
- a cluster/launcher credential,
- fine-tuning dataset and time/budget.
