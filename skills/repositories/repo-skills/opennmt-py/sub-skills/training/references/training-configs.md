# OpenNMT-py training configs

This reference condenses the training behavior exposed by `onmt_train`: option parsing, data/vocab validation, model construction, optimizer setup, checkpoint loading, distributed launch, and advanced fine-tuning options.

## Training lifecycle

`onmt_train -config train.yaml` performs these high-level steps:

1. Parse YAML and command-line options.
2. Validate training options, then normalize model options.
3. Validate data, transform, vocabulary, feature, language-model, and model compatibility options.
4. Prepare transforms and vocabularies, including optional pretrained embedding conversion.
5. If `train_from` is set, load the checkpoint, checkpoint options, vocabulary, model weights, and optimizer metadata according to `reset_optim`.
6. Build the model, optimizer, saver, trainer, training iterator, and validation iterator.
7. Train until `train_steps`, or indefinitely when `single_pass` overrides steps to one corpus pass.

The parser has defaults for many options, but production configs should still set the keys below explicitly so future agents can reason about them.

## Required training shape

A minimal seq2seq training YAML should contain:

```yaml
data:
  train:
    path_src: data/src-train.txt
    path_tgt: data/tgt-train.txt
    transforms: []
    weight: 1
  valid:
    path_src: data/src-val.txt
    path_tgt: data/tgt-val.txt
    transforms: []

src_vocab: run/example.vocab.src
tgt_vocab: run/example.vocab.tgt
save_model: run/model
train_steps: 1000
valid_steps: 500
world_size: 1
gpu_ranks: [0]
```

Key rules:

- `data` should normally be a mapping of corpus names to corpus records. Each corpus needs `path_src` or `path_txt`. Seq2seq corpora also need `path_tgt`; if a corpus lacks `path_tgt`, OpenNMT-py treats that corpus as language-model style input.
- Include a `valid` corpus whenever `valid_steps` is set and you expect periodic validation.
- `src_vocab` is required. `tgt_vocab` is required unless `share_vocab: true` is used.
- For `model_task: lm`, use `share_vocab: true`; language-model configs commonly omit `tgt_vocab` and rely on source/shared vocab.
- `save_model` is the prefix used to write checkpoints such as `prefix_step_N.pt`.
- `train_steps` and `valid_steps` should be positive integers unless `single_pass: true` is intentionally used.

## Model patterns

### Default RNN / small seq2seq

If no model type is specified, OpenNMT-py constructs an RNN-style encoder/decoder with two layers and 500-dimensional hidden states. This is suitable for quick smoke tests and toy data, not for modern Transformer baselines.

Useful explicit settings:

```yaml
encoder_type: rnn
decoder_type: rnn
word_vec_size: 500
hidden_size: 500
layers: 2
optim: sgd
learning_rate: 1.0
batch_size: 64
```

### Copy-attention summarization

A summarization-style RNN config commonly combines a bidirectional encoder, copy attention, MLP global attention, reuse of copy attention, and Adagrad:

```yaml
encoder_type: brnn
word_vec_size: 128
hidden_size: 512
layers: 1
copy_attn: true
global_attention: mlp
reuse_copy_attn: true
copy_loss_by_seqlength: true
bridge: true
optim: adagrad
learning_rate: 0.15
adagrad_accumulator_init: 0.1
max_grad_norm: 2
batch_size: 16
```

Copy-attention changes the generator and the data iterator. Route corpus/vocab problems back to `../data-preparation/` because copy attention also depends on source/target alignment in the example stream.

### Transformer baseline

A Transformer baseline should set model, initialization, batching, and schedule together:

```yaml
encoder_type: transformer
decoder_type: transformer
word_vec_size: 512
hidden_size: 512
layers: 6
transformer_ff: 2048
heads: 8
param_init: 0.0
param_init_glorot: true
position_encoding: true
optim: adam
adam_beta1: 0.9
adam_beta2: 0.998
decay_method: noam
warmup_steps: 8000
learning_rate: 2.0
batch_type: tokens
normalization: tokens
batch_size: 4096
accum_count: [4]
accum_steps: [0]
dropout: [0.1]
attention_dropout: [0.1]
dropout_steps: [0]
label_smoothing: 0.1
max_grad_norm: 0.0
```

Parser constraints to remember:

- `dropout`, `attention_dropout`, and `dropout_steps` lists must have the same length.
- `accum_count` and `accum_steps` lists must have the same length.
- `position_encoding: true` cannot be combined with nonzero `max_relative_positions`; use one positional strategy.

### Language-model / LLM fine-tuning

LLM fine-tuning usually starts from a converted OpenNMT-py checkpoint and overrides model options deliberately:

```yaml
model_task: lm
encoder_type: transformer_lm
decoder_type: transformer_lm
train_from: base-model.pt
save_model: run/finetuned
share_vocab: true
src_vocab: vocab.txt
override_opts: true
model_dtype: fp16
optim: fusedadam
learning_rate: 0.0001
batch_type: tokens
batch_size: 1024
accum_count: [32]
accum_steps: [0]
normalization: tokens
param_init: 0
param_init_glorot: true
position_encoding: false
max_relative_positions: -1
layer_norm: rms
pos_ffn_activation_fn: silu
```

When `train_from` is set and `override_opts` is false, training reuses most model options from the checkpoint. Use `override_opts: true` only when you can restate the full architecture and you intentionally need to change options such as LoRA, quantization, layer norm, positional encoding, hidden sizes, or layer counts.

## Optimization and checkpoint continuation

`train_from` loads a previous checkpoint. `reset_optim` determines how optimizer options and optimizer state are reused:

| `reset_optim` | Effect | Typical use |
|---|---|---|
| `none` | Load checkpoint optimizer options and optimizer state. | Exact resume after interruption. |
| `states` | Keep checkpoint optimizer options and training counters, but drop optimizer tensor state. | Vocabulary update or state reset while preserving schedule metadata. |
| `all` | Build optimizer from current options and no checkpoint optimizer state. | New fine-tune schedule from an existing model. |
| `keep_states` | Use current optimizer options but load checkpoint optimizer state. | Advanced experiments; validate carefully. |

For vocabulary update:

```yaml
train_from: old-model_step_N.pt
update_vocab: true
reset_optim: states
src_vocab: new.vocab.src
tgt_vocab: new.vocab.tgt
```

OpenNMT-py requires `update_vocab` to have `train_from` and `reset_optim` set to `states` or `all`. `states` is the safer default because old embeddings are mapped into the new vocabulary while optimizer tensor states are dropped.

## Multi-GPU layout

Training uses `world_size` as the total number of distributed processes and `gpu_ranks` as the ranks local to the current process invocation.

Common single-node layouts:

```yaml
# CPU-only smoke or config debugging
world_size: 1
gpu_ranks: []

# One visible GPU
world_size: 1
gpu_ranks: [0]

# Four visible GPUs on one node
world_size: 4
gpu_ranks: [0, 1, 2, 3]
```

Rules enforced by the parser:

- `len(gpu_ranks)` must be less than or equal to `world_size`.
- If `len(gpu_ranks) == world_size`, rank `0` must be present.
- When CUDA is available and `gpu_ranks` is empty, OpenNMT-py warns that you probably intended GPU training.

Operational guidance:

- Set `CUDA_VISIBLE_DEVICES` before launching if you want ranks to map onto a subset of physical devices.
- Single-node training should normally use `world_size == len(gpu_ranks)`.
- Multi-node rank slicing uses `world_size` greater than the local `gpu_ranks` length plus consistent `master_ip` and `master_port`; treat this as advanced because it is not the recommended path for current OpenNMT-py workflows.
- `parallel_mode` defaults to `data_parallel`; `tensor_parallel` changes model loading offsets and should be kept for model-parallel experiments that have been separately validated.

## Pretrained embeddings

There are two embedding surfaces:

1. Raw pretrained embeddings supplied through `both_embeddings`, `src_embeddings`, or `tgt_embeddings`.
2. Torch-serialized pretrained vectors supplied through `pre_word_vecs_enc` and/or `pre_word_vecs_dec`.

For raw embeddings:

```yaml
both_embeddings: embeddings/glove.txt
embeddings_type: GloVe
save_data: run/example
word_vec_size: 100
```

Rules:

- Use either `both_embeddings` or side-specific `src_embeddings`/`tgt_embeddings`, not both.
- `embeddings_type` must be set to `GloVe` or `word2vec`.
- `save_data` is required because OpenNMT-py writes derived `.enc_embeddings.pt` and `.dec_embeddings.pt` files.
- Match `word_vec_size`, or side-specific word-vector sizes, to the embedding dimension unless truncation/padding is intentional.
- `freeze_word_vecs_enc` and `freeze_word_vecs_dec` freeze loaded word vectors.

## Alignment training

Supervised alignment training is enabled with `lambda_align > 0.0`:

```yaml
lambda_align: 0.05
alignment_layer: -3
alignment_heads: 1
full_context_alignment: true
data:
  train:
    path_src: data/src-train.txt
    path_tgt: data/tgt-train.txt
    path_align: data/src-tgt.align
    transforms: []
    weight: 1
  valid:
    path_src: data/src-val.txt
    path_tgt: data/tgt-val.txt
    path_align: data/src-tgt-val.align
    transforms: []
```

Constraints:

- The decoder must be `transformer`.
- `alignment_layer` must address an existing decoder layer: `-dec_layers <= alignment_layer < dec_layers`.
- Every corpus, including validation, needs `path_align` when `lambda_align > 0.0`.
- On-the-fly tokenization and token-add/delete transforms invalidate alignment indices. Avoid `sentencepiece`, `bpe`, `onmt_tokenize`, `tokendrop`, `prefix`, and `bart` in alignment-training corpora.
- `full_context_alignment` can improve alignment supervision but slows training.

## Gradient checkpointing

Use gradient checkpointing to reduce memory at the cost of extra compute:

```yaml
use_ckpting: [ffn, lora]
```

Allowed modules are `ffn`, `mha`, and `lora`. The checkpointed module must have gradients. For example, `lora` checkpointing only makes sense when `lora_layers` or `lora_embedding` creates trainable LoRA parameters.

## LoRA and quantized fine-tuning

LoRA options:

```yaml
lora_layers: [linear_values, linear_query, linear_keys, final_linear]
lora_rank: 8
lora_alpha: 16
lora_dropout: 0.05
lora_embedding: false
```

LoRA rules:

- LoRA replaces matching linear layers and marks only LoRA parameters and related LoRA biases trainable.
- Do not combine LoRA with `freeze_encoder` or `freeze_decoder`; model construction rejects that combination.
- When applying LoRA to a checkpoint, use `train_from` and usually `override_opts: true`; otherwise checkpoint model options can hide the new LoRA settings.
- Use `lora_embedding: true` when embeddings must remain trainable, especially for some vocabulary-update or adapter-tuning workflows.

Quantization options:

```yaml
quant_layers: [w_1, w_2, w_3, linear_values, linear_query, linear_keys, final_linear]
quant_type: bnb_NF4
```

Supported `quant_type` values are `bnb_8bit`, `bnb_FP4`, `bnb_NF4`, `awq_gemm`, and `awq_gemv`.

Quantization rules:

- `bnb_*` quantization and `adamw8bit`/`pagedadam*` optimizers require bitsandbytes.
- `awq_*` quantization requires AutoAWQ and uses `w_bit` and `group_size` constraints.
- Layers listed in both `lora_layers` and `quant_layers` are replaced as quantized LoRA linear layers; other `quant_layers` are quantized without LoRA.
- If `quant_layers` is non-empty but `quant_type` is empty, no useful quantized fine-tuning setup has been specified.
- CPU config checks cannot prove quantized GPU training viability.

## Pre-launch checklist

Before a long run:

1. Run `scripts/inspect_train_config.py` on the YAML.
2. Confirm data/vocab files are generated and aligned with the model task.
3. Confirm GPU visibility and rank layout.
4. For `train_from`, confirm the desired `reset_optim` behavior.
5. For `override_opts: true`, confirm all architecture options are restated.
6. For LoRA/quantized runs, confirm optional packages and GPU memory headroom.
7. For alignment runs, confirm alignment files have no blank lines and match post-transform tokens.
