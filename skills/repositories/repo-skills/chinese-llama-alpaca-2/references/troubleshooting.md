# Cross-cutting troubleshooting

## Environment and package issues

- If `torch` fails to import with an MKL or `iJIT_NotifyEvent` symbol error, the private inspection env likely has an incompatible Intel MKL/OpenMP combination. Recreate or repair the env before proceeding.
- If `bitsandbytes`, `flash-attn`, `xformers`, or `vllm` are missing, first check whether the task truly needs those optional accelerators. The minimum skill environment does not require them.
- If the repo's training scripts import the wrong `peft` implementation, run them from inside `sub-skills/train-and-merge/scripts/training/` so the bundled vendored `peft/` package stays on the import path.

## Model and tokenizer issues

- Tokenizer vocabulary mismatches are expected when a model checkpoint and tokenizer come from different model families. Most load paths resize embeddings to compensate, but a bad tokenizer choice still causes poor outputs.
- If generation looks truncated or oddly short, check whether the task is using the minimal system prompt instead of the long-form prompt asset.
- Do not mix first-generation Chinese-LLaMA/Alpaca tokenizers with the second-generation repo assets.

## Training issues

- DeepSpeed configs are part of the training workflow, not the inference workflow.
- The training scripts expect dataset fields such as `instruction`, `input`, and `output` for supervised instruction tuning.
- LoRA merge commands need a compatible base model and LoRA adapter pair; a missing adapter path or incompatible model family is the most common failure.

## Inference and serving issues

- Quantized loading is not available on CPU in the bundled scripts.
- The optional vLLM branch is GPU-only and does not support the same LoRA, 4-bit/8-bit, CFG, or speculative-sampling combinations as the non-vLLM branch.
- Flash-attention and xformers are acceleration helpers, not hard requirements for the core inference path.
- If `--use_ntk` is set, make sure the selected checkpoint actually supports the intended long-context setting.

## Evaluation issues

- CEval and CMMLU expect the benchmark directory layout and subject metadata files that the scripts already know how to read.
- LongBench prediction uses dataset/config files from the bundled `scripts/longbench/config/` directory; missing config files usually mean the generated skill tree is incomplete.
- Benchmark outputs should go to a fresh run directory; do not overwrite a previous result tree unless you intend to compare only the latest run.

## Local integration issues

- The llama.cpp shell wrappers assume an external `main` binary and a compatible GGUF model are already available.
- The LangChain/privateGPT snippets are integration notes, not a bundled self-sufficient stack. They rely on external project scaffolding and upstream package APIs that may differ from the exact code in this repo snapshot.
