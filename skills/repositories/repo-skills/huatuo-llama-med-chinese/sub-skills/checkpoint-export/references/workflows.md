# Checkpoint export workflows

This reference covers LoRA adapter merge/export behavior for Huatuo-Llama-Med-Chinese-style checkpoints. It distills the repository export scripts and LoRA weight documentation into self-contained operating guidance.

## Inputs and assumptions

Required inputs:

- `BASE_MODEL`: a Hugging Face model id or local model directory for the base model. The export logic reads this through the `BASE_MODEL` environment variable and fails immediately when it is unset.
- Adapter weights: a PEFT LoRA adapter path or Hugging Face adapter id. Downloaded adapter directories are expected to contain:
  - `adapter_config.json`
  - `adapter_model.bin`
- Output root: a writable directory where the export subdirectory will be created.

Important source assumption: the original export scripts hard-code the adapter id `tloen/alpaca-lora-7b`. For Huatuo-Llama-Med-Chinese exports, replace that default with the actual downloaded Huatuo adapter directory or a compatible Hugging Face adapter id. The bundled command builder exposes this as `--adapter-weights` and defaults to the legacy value only to make the inherited assumption visible.

Dependency expectations from the repository requirements:

- `transformers==4.30.1`
- `peft==0.3.0`
- `accelerate==0.20.1`
- `sentencepiece==0.1.97`
- `bitsandbytes==0.37.2` for related LoRA workflows, although the export scripts load on CPU with `load_in_8bit=False`
- A compatible `torch` install is still required even though it is not pinned in the requirements file.

## Mode 1: Hugging Face checkpoint export

Choose Hugging Face export when the downstream consumer can load a standard `save_pretrained` checkpoint.

High-level flow:

1. Read `BASE_MODEL` from the environment and load `LlamaTokenizer` plus `LlamaForCausalLM` from that base model.
2. Load the base model in half precision with CPU device placement.
3. Load the LoRA adapter with `PeftModel.from_pretrained(base_model, adapter_weights, ...)`.
4. Merge LoRA weights into the base model. The source logic toggles merge behavior for attention `q_proj` and `v_proj` layers and switches the LoRA model to evaluation mode; newer PEFT versions may use `merge_and_unload()` instead.
5. Save the merged model as Hugging Face shards.

Expected output layout under the chosen output root:

```text
hf_ckpt/
  config.json
  generation_config.json            # if produced by the installed Transformers version
  pytorch_model-00001-of-*.bin       # one or more weight shards, commonly capped near 400 MB
  pytorch_model.bin.index.json       # when sharded
  tokenizer files                    # save or copy these if downstream loading needs them
```

The source script names `./hf_ckpt` as the output directory and uses a `max_shard_size` of `400MB`. Treat missing tokenizer files as a downstream packaging issue: the source loads a tokenizer but does not rely on tokenizer save behavior for the weight merge itself.

Build a dry-run command template:

```bash
python scripts/build_export_command.py \
  --mode hf \
  --base-model BASE_MODEL_OR_LOCAL_PATH \
  --adapter-weights ADAPTER_DIR_OR_HF_ID \
  --output-dir EXPORT_ROOT
```

Review the printed command and warnings before running it in a prepared ML environment.

## Mode 2: original LLaMA state-dict checkpoint export

Choose state-dict export only when the target runtime expects original LLaMA checkpoint files rather than Hugging Face `save_pretrained` files.

Expected output layout under the chosen output root:

```text
ckpt/
  consolidated.00.pth
  params.json
```

The bundled guidance reflects a single-shard LLaMA-7B layout with these fixed parameters:

```json
{
  "dim": 4096,
  "multiple_of": 256,
  "n_heads": 32,
  "n_layers": 32,
  "norm_eps": 1e-06,
  "vocab_size": -1
}
```

State-dict key translation:

- `model.embed_tokens.weight` -> `tok_embeddings.weight`
- `model.norm.weight` -> `norm.weight`
- `lm_head.weight` -> `output.weight`
- LLaMA layer attention projections -> `layers.<n>.attention.wq/wk/wv/wo.weight`
- LLaMA MLP projections -> `layers.<n>.feed_forward.w1/w2/w3.weight`
- LLaMA layer norms -> `layers.<n>.attention_norm.weight` and `layers.<n>.ffn_norm.weight`
- LoRA-only tensors and rotary embedding inverse-frequency buffers are excluded.

For `wq` and `wk`, the source applies an `unpermute` transform. At a high level, this reverses the query/key tensor head packing used by Hugging Face LLaMA weights so that the saved tensor matches the original LLaMA checkpoint layout. It reshapes by `(n_heads, 2, dim_per_head/2, dim)`, swaps the paired dimensions, then reshapes back to `(dim, dim)`.

Build a dry-run command template:

```bash
python scripts/build_export_command.py \
  --mode state-dict \
  --base-model BASE_MODEL_OR_LOCAL_PATH \
  --adapter-weights ADAPTER_DIR_OR_HF_ID \
  --output-dir EXPORT_ROOT
```

State-dict mode is not a general checkpoint converter. Do not use it for Bloom, Huozi, ChatGLM, non-LLaMA adapters, non-7B LLaMA variants, or checkpoints with incompatible key names unless you first redesign and validate the parameter table and key translation.

## Practical preflight

Before running an export command:

1. Confirm the base model and adapter are legally available and accessible from the execution environment.
2. Confirm the adapter was trained for the same base architecture and hidden size as `BASE_MODEL`.
3. Confirm the adapter directory contains `adapter_config.json` and `adapter_model.bin`, or that the Hugging Face adapter id exposes equivalent PEFT files.
4. Confirm enough CPU RAM and disk are available for a 7B half-precision model merge plus output shards.
5. Prefer an isolated environment with compatible `transformers`, `peft`, and `torch` versions.
