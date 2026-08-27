# Weight loading and model compatibility

## Safetensors scan

The loader scans every `*.safetensors` file in the model directory. For each
key, it either applies a packed-module mapping or looks up a parameter with the
same name. The default loader copies tensor data directly into the parameter;
sharded parameters attach custom `weight_loader` methods.

There is no lazy remote download path in the engine. The model directory must
already contain the weights and config/tokenizer files.

## Packed-module mapping

`Qwen3ForCausalLM` packs these Hugging Face-style source names:

| Source key fragment | Internal parameter fragment | Shard id |
| --- | --- | --- |
| `q_proj` | `qkv_proj` | `q` |
| `k_proj` | `qkv_proj` | `k` |
| `v_proj` | `qkv_proj` | `v` |
| `gate_proj` | `gate_up_proj` | `0` |
| `up_proj` | `gate_up_proj` | `1` |

A key containing one of the source fragments is renamed by replacement, then
loaded into the corresponding slice of the packed parameter. All other keys
must match a model parameter directly, or `get_parameter` will fail.

## Tensor-parallel loading implications

- Column-parallel parameters copy only the rank's output slice.
- QKV parameters split each source projection by rank and place it into the
  correct packed section.
- Row-parallel parameters copy an input-feature slice and all-reduce at runtime.
- Vocabulary embeddings and the LM head shard rows by rank. If embeddings are
  tied, the LM head shares the embedding weight data.

A new model family must provide compatible sharding logic for its attention,
MLP, embeddings, and head. Do not assume the Qwen3 mapping works for Llama,
Mistral, or non-causal architectures.

## Compatibility checklist for new weights

1. Load the config with Transformers and confirm the model type is Qwen3-like.
2. Verify `num_attention_heads`, `num_key_value_heads`, `vocab_size`,
   `hidden_size`, and `intermediate_size` divide by the intended TP size where
   sharded layers require it.
3. Check whether `head_dim` is explicit; otherwise it is derived from
   `hidden_size // num_attention_heads`.
4. Verify the activation is `silu`; the implementation asserts that value.
5. Inspect `attention_bias` and tied embeddings because they change Q/K norms
   and head weight sharing.
6. Confirm all safetensors keys either match parameters or are covered by the
   packed mapping above.
7. Run a tiny eager-mode generation before graph-mode or benchmark runs.

## Common loading failures

- A renamed projection key causes `get_parameter` to fail after replacement.
- A non-Qwen3 config lacks attributes the model constructor reads.
- TP size does not divide heads, KV heads, vocabulary, or MLP dimensions.
- A checkpoint stores weights in a format other than safetensors.
- The config dtype creates unsupported kernel/dtype combinations for the
  installed FlashAttention/Triton stack.
