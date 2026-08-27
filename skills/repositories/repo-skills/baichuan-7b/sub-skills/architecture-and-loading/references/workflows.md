# Architecture and Loading Workflows

This reference distills the Baichuan-7B README inference snippets, `models/configuration_baichuan.py`, `models/modeling_baichuan.py`, and verified installed-package smoke facts. It is self-contained for future operation; use source-file names only as provenance labels, not as required runtime reads.

## Evidence-backed identity

- Public model: `baichuan-inc/Baichuan-7B`, an open-source 7B causal language model for Chinese and English.
- Architecture family: decoder-only Transformer with LLaMA-like design choices.
- README inference path: Hugging Face `AutoTokenizer` and `AutoModelForCausalLM` with `trust_remote_code=True`; examples move tokenized inputs to CUDA and call `model.generate`.
- Local source path: `models/configuration_baichuan.py` defines `BaiChuanConfig`; `models/modeling_baichuan.py` defines the model stack and causal-LM wrapper.
- Skill validation facts: local source imports succeeded with a tiny config; eval forward produced logits shape `(1, 4, 32)` and finite loss; `prepare_inputs_for_generation` returned the expected keys; a compatible Transformers runtime exposed `generate()` while also warning that custom-model generation inheritance is version-sensitive.

## Configuration defaults

`BaiChuanConfig` extends Hugging Face `PretrainedConfig`.

| Field | Default | Operational meaning |
| --- | ---: | --- |
| `model_type` | `"baichuan"` | Remote-code/config identity used by Transformers. |
| `vocab_size` | `64000` | Token vocabulary size used by embeddings and `lm_head`. |
| `hidden_size` | `4096` | Decoder hidden width. Must be divisible by `num_attention_heads`. |
| `intermediate_size` | `11008` | SwiGLU feed-forward width. |
| `num_hidden_layers` | `32` | Decoder layer count. |
| `num_attention_heads` | `32` | Attention heads; `head_dim = hidden_size // num_attention_heads`. |
| `hidden_act` | `"silu"` | Activation used in the gated MLP. |
| `max_position_embeddings` | `4096` | Initial rotary-cache length; README notes extrapolation beyond training length may work for inference. |
| `initializer_range` | `0.02` | Weight initialization std. |
| `rms_norm_eps` | `1e-6` | RMSNorm epsilon. |
| `use_cache` | `true` | Default causal generation cache behavior. |
| `pad_token_id`, `bos_token_id`, `eos_token_id` | `0`, `1`, `2` | Special-token IDs inherited by Transformers generation/config logic. |
| `tie_word_embeddings` | `false` | Input embeddings and output head are not tied by default. |
| `keys_to_ignore_at_inference` | `["past_key_values"]` | Avoids treating cache tensors as inference outputs of interest. |

Tiny synthetic configs may reduce these values, for example `vocab_size=32`, `hidden_size=32`, `intermediate_size=64`, `num_hidden_layers=1`, `num_attention_heads=4`, `max_position_embeddings=16`.

## Class roles and signatures

### Main classes

- `BaiChuanConfig`: stores model dimensions, token IDs, cache defaults, and Transformers config metadata.
- `RMSNorm`: T5-style root-mean-square normalization with learned scale.
- `RotaryEmbedding`: builds and extends cosine/sine caches for rotary position embeddings.
- `MLP`: gated feed-forward block: `down_proj(silu(gate_proj(x)) * up_proj(x))`.
- `Attention`: packs Q/K/V in one `W_pack` projection, applies rotary embeddings, supports cache concatenation in eval, and uses xFormers memory-efficient attention in training mode.
- `DecoderLayer`: pre-norm attention plus MLP residual block.
- `Model`: decoder stack with embeddings, causal/padding attention-mask preparation, optional gradient checkpointing, hidden states, attentions, and cache output.
- `BaiChuanForCausalLM`: wraps `Model` with `lm_head`, causal-LM loss, generation input preparation, and beam cache reorder.

### Important signatures

```python
BaiChuanConfig(
    vocab_size=64000,
    hidden_size=4096,
    intermediate_size=11008,
    num_hidden_layers=32,
    num_attention_heads=32,
    hidden_act="silu",
    max_position_embeddings=4096,
    initializer_range=0.02,
    rms_norm_eps=1e-6,
    use_cache=True,
    pad_token_id=0,
    bos_token_id=1,
    eos_token_id=2,
    tie_word_embeddings=False,
    **kwargs,
)
```

```python
BaiChuanForCausalLM.forward(
    input_ids=None,
    attention_mask=None,
    position_ids=None,
    past_key_values=None,
    inputs_embeds=None,
    labels=None,
    use_cache=None,
    output_attentions=None,
    output_hidden_states=None,
    return_dict=None,
)
```

```python
BaiChuanForCausalLM.prepare_inputs_for_generation(
    input_ids,
    past_key_values=None,
    attention_mask=None,
    inputs_embeds=None,
    **kwargs,
)
```

## Local source smoke workflow

Use the bundled helper when a user wants to prove that a checkout's local source can be imported and that the architecture still behaves as expected without downloading the official model weights.

```bash
python sub-skills/architecture-and-loading/scripts/local_model_smoke.py --repo-root /path/to/Baichuan-7B
```

What it checks:

1. Resolves `--repo-root` or auto-discovers a checkout containing `models/configuration_baichuan.py` and `models/modeling_baichuan.py`.
2. Prepends that root to `sys.path` and imports `models.configuration_baichuan.BaiChuanConfig` plus `models.modeling_baichuan.BaiChuanForCausalLM`.
3. Constructs a tiny one-layer config with compatible head divisibility.
4. Sets `model.eval()` so the inference attention path is tested and xFormers kernels are not invoked for training attention.
5. Runs a no-grad forward with toy `input_ids`, `attention_mask`, labels, and `use_cache=True`.
6. Asserts logits shape `(1, 4, 32)`, finite loss, and nonempty `past_key_values`.
7. Calls `prepare_inputs_for_generation` both before and after cache creation; the cache path must slice `input_ids` to the last token and produce last-token `position_ids`.
8. Builds an invalid config to confirm the expected `hidden_size must be divisible by num_heads` error.
9. Reports whether the current Transformers model object exposes `generate`.

Add a CUDA probe only when requested:

```bash
python sub-skills/architecture-and-loading/scripts/local_model_smoke.py --repo-root /path/to/Baichuan-7B --cuda
```

The CUDA probe only checks `torch.cuda.is_available()` and a tiny allocation. It is not a full 7B generation test.

## Hugging Face loading and inference-style usage

Use this for real Baichuan-7B weights or a local directory containing compatible weights, config, tokenizer files, and remote-code model files.

```python
from transformers import AutoModelForCausalLM, AutoTokenizer

model_id_or_path = "baichuan-inc/Baichuan-7B"  # or a local compatible weights directory

tokenizer = AutoTokenizer.from_pretrained(
    model_id_or_path,
    trust_remote_code=True,
)
model = AutoModelForCausalLM.from_pretrained(
    model_id_or_path,
    device_map="auto",
    trust_remote_code=True,
)

inputs = tokenizer("Hamlet->Shakespeare\nOne Hundred Years of Solitude->", return_tensors="pt")
# README examples use inputs.to("cuda:0"). For device_map="auto", place inputs on the first
# execution device used by the model when needed; for a single-GPU model, cuda:0 is typical.
if hasattr(model, "device"):
    inputs = inputs.to(model.device)
else:
    inputs = inputs.to("cuda:0")

pred = model.generate(**inputs, max_new_tokens=64)
print(tokenizer.decode(pred.cpu()[0], skip_special_tokens=True))
```

Operational notes:

- `trust_remote_code=True` is required for the official custom Baichuan model/tokenizer code path.
- Real 7B loading requires official weights/tokenizer access from Hugging Face/ModelScope cache or a local mirror; the tiny smoke does not validate those assets.
- README snippets assume CUDA. CPU is acceptable for config-only and tiny smoke checks, but full generation on 7B weights is slow and memory-heavy.
- The repository `requirements.txt` pins `torch==2.0.0`, `transformers==4.29.1`, `xformers==0.0.20`, and `sentencepiece==0.1.97`; newer environments can import the local code but may emit generation compatibility warnings.

## Generation and cache behavior

`BaiChuanForCausalLM.prepare_inputs_for_generation` implements the key cache contract used by `generate()`:

- If `past_key_values` is present, `input_ids` is sliced to `input_ids[:, -1:]` so only the next token is processed.
- If `attention_mask` is present and no explicit `position_ids` is passed, `position_ids = attention_mask.long().cumsum(-1) - 1`.
- Positions where `attention_mask == 0` are set to `1`.
- If `past_key_values` is present, `position_ids` is also sliced to the last position.
- If `inputs_embeds` is passed, it is used only on the first generation step; later cached steps use `input_ids`.
- Returned keys are `input_ids` or `inputs_embeds`, `position_ids`, `past_key_values`, `use_cache`, and `attention_mask`.

`Model.forward` uses `config.use_cache` unless an explicit `use_cache` is passed. During training with gradient checkpointing enabled, it warns and forces `use_cache=False` because checkpointing and cache reuse are incompatible.

## Attention and shape constraints

- `hidden_size` must be divisible by `num_attention_heads`; otherwise `Attention.__init__` raises `ValueError` before any forward pass.
- `head_dim = hidden_size // num_attention_heads`; Q/K/V are produced by `W_pack` and reshaped to `(batch, heads, seq, head_dim)`.
- In eval/inference mode, attention weights must have shape `(batch, num_heads, q_len, kv_seq_len)`.
- Directly supplied 4D attention masks must have shape `(batch, 1, q_len, kv_seq_len)`. Most users should pass a normal 2D tokenizer `attention_mask` into `Model`/`BaiChuanForCausalLM` and let `_prepare_decoder_attention_mask` expand it.
- `Model.forward` rejects passing both `input_ids` and `inputs_embeds`; exactly one is required.
- Training mode enters the xFormers memory-efficient attention path; eval mode uses the explicit matmul/softmax path and is safer for CPU/tiny checks.

## Cross-links

- Parent skill: [Baichuan-7B root](../../../SKILL.md)
- Shared API reference: [root API reference](../../../references/api-reference.md)
- Local troubleshooting: [troubleshooting](troubleshooting.md)
- Local helper: [local_model_smoke.py](../scripts/local_model_smoke.py)
