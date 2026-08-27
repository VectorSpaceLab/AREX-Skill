# Model and runtime overview

DeepKE's classic extraction examples and DeepKE-LLM examples should normally be treated as separate runtime families. Do not merge their dependencies into one environment unless a project has already proven compatibility.

## Runtime families

| Family | Examples | Typical dependency shape | Runtime risk |
| --- | --- | --- | --- |
| Classic DeepKE | Standard NER/RE/AE/EE, PRGC, PURE, ASP | Older PyTorch/Transformers/Hydra stacks, sometimes AllenNLP or Apex | Version conflicts across examples; GPU/Apex requirements for some paths. |
| DeepKE-LLM local fine-tuning | InstructKGC LoRA/P-tuning/OpenDelta, CPM-Bee | Python 3.9-era LLM stack, PEFT/OpenDelta, Accelerate/DeepSpeed, model-specific packages | Large GPU memory, model checkpoint downloads, mixed precision/config complexity. |
| DeepKE-LLM local inference | OneKE and local instruction models | Transformers/tokenizer stack plus local checkpoint/cache | Model may not fit memory; output schema may drift. |
| API/ICL | LLMICL, UnleashLLMRE, CodeKGC with OpenAI-compatible engines | `openai`/HTTP clients, prompt templates, API credentials | Cost, latency, network, tool-call or response-format incompatibility. |

## Models and methods named by DeepKE-LLM docs

- **OneKE**: bilingual schema-based information extraction model family.
- **KnowLM/ZhiXi and LLaMA-series**: instruction KGC fine-tuning and inference family.
- **ChatGLM**: LoRA and P-tuning instruction KGC paths.
- **MOSS, Baichuan, Qwen**: OpenDelta/adapter-style fine-tuning paths in the source docs.
- **CPM-Bee**: separate OpenDelta-style workflow with its own model assumptions.
- **GPT-series / OpenAI-compatible models**: ICL, data augmentation, CCKS KGC, UnleashLLMRE, and CodeKGC API workflows.

## Method selection

| Method | Use when | Avoid when |
| --- | --- | --- |
| In-context prompting | You have few examples, an API/local chat model, and need quick extraction or augmentation | Labels require high recall/precision guarantees without human review. |
| LoRA fine-tuning | You have enough instruction data, local model weights, and GPU resources | The user only needs one-off extraction or cannot provide checkpoints. |
| P-tuning | The selected model family explicitly supports it and prompt-tuning is desired | The base model path or tuning code is unverified. |
| OpenDelta/adapters | The workflow is written for OpenDelta and the model family is supported | Dependencies conflict with the active DeepKE classic environment. |
| Code-style prompting | Relation triples are naturally represented as schema classes and examples | The output would need to be executed or labels are not valid code identifiers. |

## Environment isolation guidance

- Use a separate environment for DeepKE-LLM from classic DeepKE unless the user already validated a shared stack.
- Use another separate environment for fragile workflows such as ASP/Apex or PURE/AllenNLP if they conflict with LLM packages.
- Keep model caches and output directories explicit.
- For API workflows, keep credentials only in local environment variables or secret managers.
- For GPU workflows, log GPU count, visible device ids, precision mode, maximum sequence/generation length, batch size, gradient accumulation, and adapter checkpoint path.

## What not to infer from a passing import check

A successful `import torch` and `import transformers` means only that packages import. It does not prove that:

- a 7B/13B model fits on the visible device;
- tokenizers or model weights are already cached;
- DeepSpeed can initialize with the selected config;
- an OpenAI-compatible endpoint accepts the configured model;
- OneKE output follows the desired schema;
- generated synthetic labels are good enough for training.

Treat those as separate runtime or quality checks.
