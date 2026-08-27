# Baichuan-7B API and Script Surface Reference

Read this when a task needs source-derived class names, signatures, dependency surfaces, or script responsibilities before choosing a deeper sub-skill. Detailed workflows live in the three sub-skills.

## Repository surfaces

| Surface | Public role | Owning sub-skill |
|---|---|---|
| `BaiChuanConfig` | Hugging Face `PretrainedConfig` subclass for Baichuan dimensions, token IDs, and cache defaults. | [architecture-and-loading](../sub-skills/architecture-and-loading/SKILL.md) |
| `BaiChuanForCausalLM` | Decoder model plus LM head, causal-LM loss, generation input preparation, and beam-cache reorder. | [architecture-and-loading](../sub-skills/architecture-and-loading/SKILL.md) |
| C-Eval evaluation behavior | Loads `ceval/ceval-exam`, builds Chinese few-shot multiple-choice prompts, scores A/B/C/D logits, writes task JSON and `acc.json`. | [evaluation-workflows](../sub-skills/evaluation-workflows/SKILL.md) |
| MMLU evaluation behavior | Expects Hendrycks/test CSV layout and `categories.py`, builds English few-shot prompts, scores A/B/C/D logits, writes per-subject CSVs. | [evaluation-workflows](../sub-skills/evaluation-workflows/SKILL.md) |
| DeepSpeed pretraining demo | Reads UTF-8 corpus shards, loads SentencePiece tokenizer, creates a Baichuan model under DeepSpeed ZeRO, trains indefinitely by epochs, and saves checkpoints. | [pretraining-and-deepspeed](../sub-skills/pretraining-and-deepspeed/SKILL.md) |

## Configuration defaults

`BaiChuanConfig` defaults from the source model code:

| Field | Default | Notes |
|---|---:|---|
| `model_type` | `"baichuan"` | Transformers config identity. |
| `vocab_size` | `64000` | Embedding and LM-head size. |
| `hidden_size` | `4096` | Must be divisible by `num_attention_heads`. |
| `intermediate_size` | `11008` | SwiGLU feed-forward width. |
| `num_hidden_layers` | `32` | Decoder layer count. |
| `num_attention_heads` | `32` | Attention head count. |
| `hidden_act` | `"silu"` | Activation used in the MLP gate. |
| `max_position_embeddings` | `4096` | Rotary cache length; README notes long-context extrapolation tests. |
| `initializer_range` | `0.02` | Linear/embedding init std. |
| `rms_norm_eps` | `1e-6` | RMSNorm epsilon. |
| `use_cache` | `true` | Default generation/cache behavior. |
| `pad_token_id`, `bos_token_id`, `eos_token_id` | `0`, `1`, `2` | Token IDs used by tokenizer/model workflows. |
| `tie_word_embeddings` | `false` | Input/output embeddings are not tied by default. |

## Important signatures

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

## Architecture notes

- The model stack is decoder-only: token embeddings, repeated `DecoderLayer`, final RMSNorm, and an untied linear `lm_head`.
- `Attention` packs Q/K/V in one `W_pack` projection, applies rotary embeddings, and uses two execution paths:
  - training mode: xFormers memory-efficient attention with a lower-triangular mask;
  - eval mode: explicit matmul/softmax attention with cache concatenation.
- `Model.forward` rejects passing both `input_ids` and `inputs_embeds`; pass exactly one.
- Attention masks should normally be 2D tokenizer masks passed into the model, not hand-built 4D low-level masks.
- `prepare_inputs_for_generation` slices `input_ids` and `position_ids` to the last token when `past_key_values` is present.
- Gradient checkpointing and `use_cache=True` conflict; training mode disables cache with a warning when checkpointing is active.

## Dependency surfaces

| Dependency | Required for | Notes |
|---|---|---|
| `torch` | all model workflows | README pins `torch==2.0.0`; CUDA support is required for full generation/evaluation/training. |
| `transformers` | model loading and custom config/model integration | README pins `transformers==4.29.1`; newer versions may have custom-model generation warnings. |
| `xformers` | importing local model code and training attention path | `modeling_baichuan.py` imports xFormers at module import time. |
| `sentencepiece` | tokenizer model loading for pretraining and official tokenizer assets | Training expects a `tokenizer.model` file. |
| `deepspeed` | pretraining launch | Demo training imports and initializes DeepSpeed at process startup. |
| `datasets` | C-Eval script | Not listed in `requirements.txt`; needed for `ceval/ceval-exam`. |
| `pandas` | MMLU script | Not listed in `requirements.txt`; needed for CSV benchmark rows. |

## Safe checks

- Architecture smoke: `sub-skills/architecture-and-loading/scripts/local_model_smoke.py`.
- Evaluation preflight: `sub-skills/evaluation-workflows/scripts/check_evaluation_inputs.py`.
- Training input validation: `sub-skills/pretraining-and-deepspeed/scripts/validate_training_inputs.py`.
- Training command rendering: `sub-skills/pretraining-and-deepspeed/scripts/render_deepspeed_command.py`.

These helpers are bundled with the skill and are safe by default. They do not fetch model weights, download datasets, or run training unless a future user separately performs those actions outside the helper default path.
