# Installation and Runtime Matrix

## When to read

Read this before creating an environment for any InternLM-XComposer workflow. The repository has several dependency profiles; do not install every optional stack unless the user selected the corresponding workflow.

## General prerequisites

- Python: repository docs state Python 3.8+; the examples commonly use Python 3.9 or 3.10.
- PyTorch: docs state PyTorch 1.12+ with PyTorch 2.0+ recommended; reproducibility examples use PyTorch 2.0.1 / CUDA 11.7.
- CUDA: docs recommend CUDA 11.4+ for GPU users. Most model execution paths call `.cuda()` directly and have no full CPU substitute.
- Trust boundary: model APIs are usually loaded through `transformers` with `trust_remote_code=True`; only do this for trusted model IDs or local checkpoints.

## Workflow dependency profiles

| Workflow | Core packages | Optional/extra packages | Notes |
| --- | --- | --- | --- |
| XComposer 2.5 Transformers inference | `torch`, `torchvision`, `torchaudio`, `transformers==4.33.2`, `timm==0.4.12`, `sentencepiece==0.1.99`, `markdown2==2.4.10`, `xlsxwriter==3.1.2`, `einops` | `accelerate` for multi-GPU dispatch; `flash-attn` for high-resolution memory efficiency | Use `model-inference`; model IDs are fetched from HF/ModelScope or local cache. |
| XComposer 2.5 Gradio demos | base inference profile + `gradio==4.13.0` | browser/network ports | Do not launch until model path and port policy are explicit. |
| LMDeploy / 4-bit AWQ | `lmdeploy` | CUDA-compatible LMDeploy wheel, AWQ model ID | LMDeploy docs default to CUDA 12.x; choose wheel for CUDA 11.x when needed. |
| XComposer 2.5 SFT/LoRA | base inference profile + `deepspeed==0.12.3`, `peft==0.8.2` | `flash-attn`, multi-GPU/Slurm tools | Use `finetuning`; validate JSON/data.txt before `torchrun`. |
| XComposer 2.0 / 1.0 legacy | older docs pin `transformers==4.33.2` for 2.0 and `transformers==4.33.1` for 1.0; both use `timm==0.4.12`, `sentencepiece==0.1.99`, `markdown2`, `xlsxwriter`, `einops` | `auto_gptq` for legacy 4-bit; `deepspeed`, `peft`, `flash-attn`, rotary op for legacy training | Keep legacy envs separate if dependency pins conflict with 2.5. |
| XComposer 2.5 Reward | base inference profile + reward checkpoint | `pandas`, `pyarrow`, `tqdm` for reward benchmarks; `deepspeed`, `peft` for training | Use `reward-model`; README API uses `AutoModel`/`AutoModelForCausalLM` with `trust_remote_code=True`. |
| OmniLive audio/base/memory | `torch`, `transformers`, `swift` for audio, `decord` for video, `Pillow`, `torchvision` | `fastapi`, `uvicorn`, `gradio==5.8.0`, Node/npm, SRS Docker image, `peft` for merge | Use `omnilive`; validate component directories before commands. |
| ShareGPT4V project | install from `projects/ShareGPT4V` with `pip install -e .`; project deps include torch 2.0.1, transformers 4.31.0, tokenizers, peft, bitsandbytes, xformers, gradio, FastAPI stack | `pip install -e ".[train]"`, `flash-attn --no-build-isolation` | Use a separate environment; dataset/model license is research-oriented. |
| DualFocus project | install from `projects/DualFocus` with `pip install -e .`; deps mirror ShareGPT4V | `[train]`, `flash-attn` | Training is not released; evaluation scripts are first-class. |

## Bundled execution bundles

When the user approves actual execution, the repaired skill includes self-contained source-derived bundles so future agents do not reopen the original checkout:

| Bundle | Owns | Main dependencies |
| --- | --- | --- |
| `sub-skills/model-inference/entrypoints/gradio/` | XComposer2.5 Gradio chat/composition demos | base inference profile + Gradio + CUDA/model cache |
| `sub-skills/finetuning/entrypoints/xcomposer25/` | SFT `finetune.py`, DeepSpeed config, full/LoRA launchers, PEFT merge | training profile + model/data/GPU budget |
| `sub-skills/reward-model/entrypoints/ixc25-reward-training/` | Reward `finetune.py`, custom `RewardTrainer`, DeepSpeed config, full/LoRA launchers | reward training profile + preference data |
| `sub-skills/omnilive/entrypoints/omnilive-examples/` | OmniLive audio/base/memory examples and LoRA merge | Swift/Transformers/Decord/PEFT + model components |
| `sub-skills/omnilive/entrypoints/omnilive-gradio/` | OmniLive Gradio frontend and FastAPI backend trio | FastAPI/Gradio/Swift/LMDeploy/FunASR/TTS stack + ports |
| `sub-skills/omnilive/entrypoints/omnilive-srs/` | OmniLive SRS Docker launcher, FastAPI backend package, and JavaScript frontend | Docker/SRS, Node/npm, FastAPI, Swift/LMDeploy/FunASR/TTS stack + LAN ports |

Run each bundle from its own directory or use its wrapper scripts; they resolve their bundled support files/configs locally.

## Safe environment checks

The root helper does not import heavy modules unless you request it; it checks module availability and host CUDA visibility:

```bash
python scripts/check_environment.py --modules torch,transformers,accelerate
python scripts/check_environment.py --modules lmdeploy --check-cuda-host
python scripts/check_environment.py --modules swift,decord,fastapi,gradio --check-cuda-host
```

For actual model execution, also run a tiny torch CUDA allocation in the target environment before loading a 7B checkpoint.

## Environment isolation guidance

- Do not mutate a shared/base environment to reconcile conflicting legacy pins.
- Use separate environments for root XComposer 2.5, ShareGPT4V, DualFocus, and old 1.0/2.0 workflows when their torch/transformers/xformers/flash-attn pins conflict.
- Install `flash-attn` only after torch is installed and ABI-compatible; source builds need `nvcc` and enough RAM.
- If the task only needs data validation or command planning, run the bundled stdlib helpers instead of installing the full model stack.
