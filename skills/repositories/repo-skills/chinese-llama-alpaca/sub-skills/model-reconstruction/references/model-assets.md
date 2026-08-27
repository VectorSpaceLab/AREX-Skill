# Model Assets and Compatibility

Read this before choosing reconstruction commands. Chinese-LLaMA-Alpaca assets are patch-style LoRA releases that must be combined with legally obtained original LLaMA-compatible base weights.

## Asset Types

| Asset | Required for | Notes |
| --- | --- | --- |
| Original LLaMA base model | Any full reconstructed model | The original LLaMA weights are not distributed by this project. Users must provide their own licensed copy or compatible HF-format conversion. |
| Chinese LLaMA LoRA | Base/continuation model reconstruction | Use for Chinese LLaMA workflows. Not an instruction-following/chat adapter by itself. |
| Chinese Alpaca LoRA | Instruction/chat model reconstruction | Use for instruction-following and dialogue. Requires Alpaca-compatible tokenizer assets. |
| Chinese LLaMA Plus LoRA | Higher-data base model variant | Alpaca-Plus reconstruction may require merging base Plus and Alpaca Plus adapters in the documented order. |
| Chinese Alpaca Plus/Pro LoRA | Improved instruction model variants | Pro is recommended in repo docs when Plus responses are too short. |
| Tokenizer files | Every merge and inference path | LLaMA and Alpaca tokenizers differ. Do not mix LLaMA tokenizer with Alpaca LoRA or Alpaca tokenizer with LLaMA LoRA. |

## Model-Family Decision Rules

- **Text continuation / base model use:** choose Chinese LLaMA. Do not expect chat instruction following without prompting/training changes.
- **Instruction following, QA, writing, advice, or chat:** choose Chinese Alpaca. In HF inference, add the Alpaca prompt wrapper with `--with_prompt` for instruction-style inputs.
- **Short-response problem in Alpaca Plus:** prefer Alpaca Pro variants when available.
- **Bigger model is not always practical:** 7B is easiest to test; 13B/33B require much more RAM/disk; 65B-style scripts exist but are out of ordinary laptop scope.

## Vocabulary Sizes and Tokenizers

The source scripts infer and validate vocabulary compatibility:

- Original LLaMA tokenizer size is commonly `32000`.
- Chinese LLaMA expanded tokenizer size is `49953`.
- Chinese Alpaca tokenizer size is `49954` because it adds a pad token.
- The SFT training script expects Chinese Alpaca tokenizer length `49954`.
- Merge scripts resize model embeddings when the tokenizer is larger than the base model embedding table.

If an error mentions `[49953, 4096]`, wrong tokenizer size, or a tokenizer smaller than model vocab, re-check whether the LoRA and tokenizer both belong to LLaMA or both belong to Alpaca.

## Multi-LoRA Ordering

The merge scripts accept comma-separated LoRA paths in `--lora_model`. Order matters because each adapter is merged into the current base before the next is applied. For Alpaca-Plus-style workflows, the usual order is base Chinese LLaMA/Plus adapter first, then Alpaca/Plus instruction adapter. Confirm the exact model-family relation before merging multiple LoRAs.

## Output Formats

| Output type | Use when | Main outputs |
| --- | --- | --- |
| `pth` | llama.cpp/manual PTH-style conversion workflows | `consolidated.00.pth` ... shards plus `params.json` and tokenizer files. |
| `huggingface` | Transformers inference, Gradio, API server, LangChain, C-Eval script | HF model directory with config/model/tokenizer files. |

Use Hugging Face output for most bundled inference and evaluation scripts. Use PTH output only when the downstream tool specifically expects original LLaMA-style shards.

## Resource Planning

Approximate minimum disk/RAM needs are model-size dependent. The README reports original FP16 sizes around 13 GB (7B), 24 GB (13B), 60 GB (33B), and 120 GB (65B), with quantized outputs smaller. Reconstruction can require additional temporary disk and RAM. The low-memory merge script reduces peak RAM at the cost of speed and intermediate shard management.
