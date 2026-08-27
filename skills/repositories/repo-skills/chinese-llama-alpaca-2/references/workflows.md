# Workflow map

This repository is a compact workflow bundle around the Chinese-LLaMA-2 and Chinese-Alpaca-2 model family. Use the sub-skill that matches the user-facing surface, and read the cross-cutting references only when a task spans multiple surfaces.

## Quick routing

| User intent | Read first | Primary runtime files |
| --- | --- | --- |
| Build or preprocess instruction data, train pretraining or SFT runs, or merge LoRA weights | `sub-skills/train-and-merge/SKILL.md` | `sub-skills/train-and-merge/scripts/training/` |
| Run local HF generation, chat interactively, or use speculative sampling | `sub-skills/hf-inference/SKILL.md` | `sub-skills/hf-inference/scripts/inference/` |
| Expose the model behind an OpenAI-style HTTP service | `sub-skills/api-serving/SKILL.md` | `sub-skills/api-serving/scripts/openai_server_demo/` |
| Run C-Eval, CMMLU, or LongBench | `sub-skills/evaluation/SKILL.md` | `sub-skills/evaluation/scripts/` |
| Use llama.cpp launch wrappers or review the external RAG integration notes | `sub-skills/local-integrations/SKILL.md` | `sub-skills/local-integrations/scripts/llama-cpp/` |

## Shared assets

- `assets/prompts/alpaca-2.txt` is the default minimal Alpaca-2 system prompt.
- `assets/prompts/alpaca-2-long.txt` extends the response style for longer answers.
- `assets/tokenizer/` contains the bundled Chinese tokenizer files used by the repo examples and scripts.

## Common workflow patterns

### Training and merge
1. Validate the instruction JSON schema or training data directory.
2. Run the pretraining or SFT CLI from `sub-skills/train-and-merge/scripts/training/`.
3. Save the PEFT adapter output and merge it with the base model when needed.
4. Read the training troubleshooting notes before touching DeepSpeed, bitsandbytes, or the vendored `peft/` package.

### HF inference and chat
1. Choose base model, tokenizer path, and optional LoRA path.
2. Decide whether the run should be CPU-only, quantized, flash-attention accelerated, or speculative-sampling accelerated.
3. Use `inference_hf.py` for one-off generation or `gradio_demo.py` for chat.
4. Keep `assets/prompts/` handy for prompt-template decisions and `assets/tokenizer/` handy when you need a local tokenizer copy.

### OpenAI-style serving
1. Pick the non-vLLM or optional vLLM branch.
2. Confirm the model name, tokenizer path, and whether LoRA/quantization is allowed.
3. Start the server, then validate the completion/chat request schema.
4. Use the troubleshooting notes when the server complains about GPU capability, model mismatch, or missing optional dependencies.

### Evaluation
1. Point the benchmark script at the expected input directories or remote dataset source.
2. Choose few-shot, CoT, prompt wrapping, and constrained decoding only when the benchmark script supports them.
3. Save the per-task outputs and summary JSON/CSV artifacts under a run-specific directory.
4. Use the benchmark-specific references before changing subject mappings, prompt formats, or long-context settings.

### Local integrations
1. Use the llama.cpp wrappers only when an external `main` binary and model files are already available.
2. Treat the LangChain/privateGPT notes as integration guidance rather than bundled runtime code.
3. Read the integration troubleshooting notes before assuming a missing file or package is a repo bug.

## Cross-cutting dependencies

- `torch`, `transformers`, `peft`, `datasets`, `sentencepiece`, `gradio`, `fastapi`, `uvicorn`, `shortuuid`, `pandas`, `scikit-learn`, `jieba`, `rouge`, `fuzzywuzzy`, and `accelerate` form the minimum inspection baseline.
- `bitsandbytes`, `flash-attn`, `xformers`, and `vllm` are optional acceleration or serving dependencies that are not part of the minimum inspection environment.
- The repo's bundled `peft/` directory under `sub-skills/train-and-merge/scripts/training/` is part of the runtime skill and should stay adjacent to the training CLIs.
