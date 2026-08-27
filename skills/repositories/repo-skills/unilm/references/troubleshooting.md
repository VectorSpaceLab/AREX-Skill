# Cross-Cutting Troubleshooting

Use this reference when a UniLM-family workflow fails before the problem clearly belongs to one sub-skill.

## Installation And Imports

- The monorepo is not one installable package. Identify the project directory first, then install only that project and its documented requirements.
- Legacy language workflows may require old PyTorch, Apex, `pyrouge`, NLTK data, or `scipy`; modern Python environments often fail on these stacks.
- Vision/document workflows may require Detectron2, MMCV, mmsegmentation, Deepspeed, fairseq, or specific Transformers versions.
- Audio/multimodal workflows often require checkpoint-specific libraries, fairseq user dirs, FlashAttention/xformers, image/audio libraries, and GPU memory.
- Retrieval workflows may run with modern Transformers but benchmark scripts often download datasets/model weights and can take hours.

## Data, Checkpoints, And Configs

- Validate file existence, format, and task-specific fields before launching native scripts.
- Distinguish model-family checkpoints from tokenizer/vocab/config files. A cased checkpoint with uncased tokenizer or missing UniLM S2S special tokens can silently degrade outputs.
- Many scripts write predictions, caches, or checkpoints near the model/output path; choose explicit output directories and confirm free disk space.
- Benchmark and training commands often assume preprocessed data rather than raw datasets.

## Hardware And Backends

- Confirm GPU count, CUDA visibility, memory, and backend package versions before using `torchrun`, `python -m torch.distributed.launch`, Deepspeed, fairseq, Detectron2, or custom kernels.
- Match `nproc_per_node`, batch size, gradient accumulation, world size, and visible GPUs.
- Treat FlashAttention, xformers, custom CUDA kernels, and old Apex builds as workflow-specific dependencies, not general prerequisites.

## Network, Credentials, And Services

- Model and dataset downloads require explicit network permission and cache planning.
- PFPO OpenAI/service callers require credentials or running services; use offline JSON/JSONL validation when credentials are absent.
- Hosted demos and notebooks are evidence only unless the user explicitly wants to use external services.

## Safety Defaults

- Start with bundled helper scripts and `--help`/dry-run style checks.
- Ask before executing long training, benchmark, generation, distributed, or credentialed workflows.
- Do not rely on the original source checkout from this generated skill; use it only when the user is explicitly working in a compatible checkout.
