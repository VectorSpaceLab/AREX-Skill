# Application Overview

| User goal | Application | Package name | Main prerequisites | Route next |
| --- | --- | --- | --- | --- |
| RLHF, SFT, DPO, PPO, GRPO, reward models | ColossalChat / Coati | `coati` | PyTorch/ColossalAI, Transformers, datasets, flash-attn for some paths, model/data assets | `colossalchat.md` and `../booster-training/SKILL.md` |
| Continual pretraining or SFT of LLaMA models | Colossal-LLaMA | `colossal_llama` | LLaMA-compatible model/tokenizer, datasets, CUDA GPUs, Apex/flash-attn for some configurations | `llama-eval-qa-moe.md` and Booster/parallelism routes |
| LLM benchmark/evaluation pipeline | ColossalEval | `colossal_eval` | datasets, model backend, evaluation configs, optional vLLM/OpenAI | `llama-eval-qa-moe.md` |
| Retrieval conversation / document QA | ColossalQA | `colossalqa` | separate older torch/langchain stack, vector store, local/API LLM, document data | `llama-eval-qa-moe.md` |
| MoE training/inference | ColossalMoE | `colossal_moe` | CUDA GPUs, Transformers, datasets/model assets | `llama-eval-qa-moe.md` and parallelism routes |

## Environment isolation

Create a new app-specific environment when the app pins a different PyTorch version from the core package, requires `flash-attn`, Apex, vLLM, LangChain, Chroma, or OpenAI clients, installs editable packages from nested application directories, or needs large models, datasets, or services.
