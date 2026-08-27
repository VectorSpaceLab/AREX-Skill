# MOSS model architecture and runtime API

## Purpose

Read this reference when you need source-backed MOSS runtime facts before writing
code that imports, loads, or validates MOSS model components. It is intentionally
safe: it explains APIs and checks that do not require downloading checkpoints.

## Runtime shape

MOSS is a source-checkout and Hugging Face `trust_remote_code` style model
release rather than a normal Python package with distribution metadata. Local
work usually needs the MOSS source root on `PYTHONPATH`, while Hugging Face
checkpoint loading can fetch the model's custom `configuration_moss.py`,
`modeling_moss.py`, and `tokenization_moss.py` through `trust_remote_code=True`.

Primary PyTorch classes:

| Object | Role | Important facts |
| --- | --- | --- |
| `MossConfig` | `PretrainedConfig` subclass | `model_type="moss"`; maps `hidden_size`, `num_attention_heads`, and `num_hidden_layers` to MOSS fields. |
| `MossTokenizer` | byte-level BPE tokenizer | Uses `vocab.json` and `merges.txt`; `model_input_names=["input_ids", "attention_mask"]`; default EOS token is `<eom>`. |
| `MossModel` | base transformer | Embedding + repeated `MossBlock` stack + final layer norm; supports cache and gradient checkpointing. |
| `MossForCausalLM` | causal LM head | Wraps `MossModel`, exposes `prepare_inputs_for_generation`, supports loss with shifted labels, and can quantize linear layers when `wbits` is 4 or 8. |

## Verified configuration defaults

The inspection environment instantiated `MossConfig()` and a tiny
`MossForCausalLM` with reduced dimensions. The public defaults are:

| Field | Default | Meaning |
| --- | ---: | --- |
| `vocab_size` | 107008 | Token vocabulary size. |
| `n_positions` / `n_ctx` | 2048 | Maximum context length used by demos and training loader. |
| `n_embd` | 4096 | Hidden size. |
| `n_layer` | 28 | Transformer block count. |
| `n_head` | 16 | Attention heads. |
| `rotary_dim` | 64 | Rotary embedding dimension. |
| `activation_function` | `gelu_new` | MLP activation name. |
| `bos_token_id` | 106028 | Base beginning/end-of-text id. |
| `eos_token_id` | 106068 | MOSS `<eom>` id used for generation termination. |
| `wbits` | 32 | Non-quantized by default; 4 and 8 trigger GPTQ quantized linear layers. |
| `groupsize` | 128 | GPTQ grouping used by quantized layers. |

## Model families and memory planning

The public checkpoint families include:

- `OpenMOSS-Team/moss-moon-003-base` — base pretrained model.
- `OpenMOSS-Team/moss-moon-003-sft` — supervised fine-tuned chat model.
- `OpenMOSS-Team/moss-moon-003-sft-plugin` — plugin-augmented SFT model.
- `OpenMOSS-Team/moss-moon-003-sft-int4` and `*-int8` — quantized chat models.
- `OpenMOSS-Team/moss-moon-003-sft-plugin-int4` and `*-int8` — quantized plugin
  variants documented in the model catalog.

The MOSS documentation estimates batch-size-1 GPU memory as:

| Precision | Load model | One-turn dialogue | Max 2048 context |
| --- | ---: | ---: | ---: |
| FP16 | 31 GB | 42 GB | 81 GB |
| INT8 | 16 GB | 24 GB | 46 GB |
| INT4 | 7.8 GB | 12 GB | 26 GB |

Quantized checkpoints are documented as single-GPU only. Use the FP16 SFT model
when the task requires Accelerate model parallelism across multiple GPUs.

## Quantization behavior

When `config.wbits` is 4 or 8, `MossForCausalLM.__init__` disables ordinary
initialization, creates the transformer and LM head, then calls `quantize()`,
which delegates to GPTQ/Triton quantized linear support. That path requires a
compatible PyTorch/CUDA/Triton setup. A successful class import does not prove
that Triton kernels can execute for the selected GPU; run a task-specific smoke
check if quantized generation is the goal.

## Safe import and tiny model check

Use the bundled script from this sub-skill when you need runtime evidence:

```bash
python sub-skills/model-runtime/scripts/check_model_runtime.py --repo-root /path/to/MOSS --json
python sub-skills/model-runtime/scripts/check_model_runtime.py --repo-root /path/to/MOSS --cuda --json
```

Expected safe checks:

- imports `MossConfig`, `MossForCausalLM`, and `MossTokenizer`;
- reports configuration defaults;
- instantiates a tiny model from a small config;
- optionally allocates a tiny CUDA tensor.

The script does not call `from_pretrained`, does not download files, and does
not validate full checkpoint generation.

## Common object-use notes

- `MossForCausalLM.prepare_inputs_for_generation` slices to the last token when
  `past_key_values` exist and constructs `position_ids` from `attention_mask`.
- `MossForCausalLM.forward` returns `CausalLMOutputWithPast` by default and
  computes shifted language-model loss when `labels` are supplied.
- `MossModel.forward` rejects simultaneous `input_ids` and `inputs_embeds` and
  raises if neither is supplied.
- `MossTokenizer.decode(..., truncate_before_pattern=...)` can truncate decoded
  completions before regular-expression patterns, in addition to ordinary
  special-token skipping.
