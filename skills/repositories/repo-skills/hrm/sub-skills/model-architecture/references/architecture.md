# HRM ACT v1 Architecture

## Object graph

`HierarchicalReasoningModel_ACTV1` is a thin ACT wrapper around
`HierarchicalReasoningModel_ACTV1_Inner`. The inner model owns:

- Token embeddings and LM output head.
- Optional sparse puzzle embeddings when `puzzle_emb_ndim > 0`.
- RoPE or learned positional encodings.
- High-level (`H_level`) and low-level (`L_level`) recurrent reasoning modules.
- Learned persistent initial states `H_init` and `L_init`.
- Q head with two logits: halt and continue.

The configured loss wrapper is `ACTLossHead`, which receives the model outputs,
computes LM and halting losses, and returns `(new_carry, loss, metrics, outputs,
all_finish)`.

## Carry objects

The model uses dataclass carries rather than a simple tensor hidden state:

- `HierarchicalReasoningModel_ACTV1InnerCarry`: `z_H`, `z_L` tensors.
- `HierarchicalReasoningModel_ACTV1Carry`: `inner_carry`, `steps`, `halted`, and
  `current_data`.

`initial_carry(batch)` creates empty H/L tensors, marks all samples as halted,
and stores empty tensors matching the batch. The first forward pass resets
halted samples to `H_init`/`L_init` and injects the current batch data.

## Forward sequence

For each call:

1. Reset H/L states for halted sequences.
2. Replace `current_data` entries for halted samples with the new batch.
3. Build input embeddings from token ids plus optional puzzle embeddings and
   positional encodings.
4. Run nested H/L recurrence. Most recurrence happens under `torch.no_grad()`;
   the final L and H updates are differentiable.
5. Produce token logits for the puzzle sequence and Q halt/continue logits.
6. Increment step counts and decide whether each sample halted. During
   evaluation, samples run to `halt_max_steps`; during training, Q logits and
   exploration can halt earlier.
7. When training with `halt_max_steps > 1`, compute `target_q_continue` by one
   extra inner forward for bootstrapping.

## Configuration implications

- `hidden_size` must be divisible by `num_heads` because attention head dim is
  `hidden_size // num_heads`.
- `pos_encodings` is either `rope` or `learned`; any other value raises
  `NotImplementedError`.
- `puzzle_emb_ndim = hidden_size` in the default config adds one puzzle-token
  slot because the code rounds embedding length up to a multiple of hidden
  size.
- `global_batch_size` in training must be divisible by `world_size`; the local
  model config uses `global_batch_size // world_size`.
- The model code uses CUDA-oriented context managers in `pretrain.create_model`;
  CPU-only operation is not a faithful substitute for train/eval.

## Known runtime compatibility note

A bounded inspection with a current CUDA/FlashAttention environment verified
CUDA, FlashAttention, and model class import. A tiny forward pass using the
repository code can fail at `models/layers.py` because `Attention.forward` calls
`.view(...)` on a FlashAttention output that may be non-contiguous:

```text
RuntimeError: view size is not compatible with input tensor's size and stride ... Use .reshape(...) instead.
```

For a downstream debugging task, this points to the attention output reshape in
`models/layers.py`. For the generated skill, record it as an environment/API
compatibility risk rather than claiming full forward training was verified.
