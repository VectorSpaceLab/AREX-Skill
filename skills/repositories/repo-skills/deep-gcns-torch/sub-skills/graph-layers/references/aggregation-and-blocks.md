# Aggregation, message normalization, and block choices

## GENConv message path

The inspected `GENConv` path is:

1. If edge encoding is enabled and `edge_attr` is present, encode it to the
   node feature width. With `bond_encoder=True`, categorical bond fields are
   embedded; otherwise `edge_feat_dim` is required for a learned linear
   encoder.
2. For each directed edge, form `x_j + edge_attr` when edge attributes are
   present, apply ReLU, and add `eps`.
3. Aggregate messages at target nodes.
4. If enabled, normalize the aggregate with `MsgNorm`, which L2-normalizes the
   message, rescales it by the norm of the target's input feature, and applies
   a scalar `msg_scale` (optionally learnable).
5. Add the message to the input and apply the configured MLP. The MLP has
   `mlp_layers` linear stages, expands intermediate widths to `2 * in_dim`,
   and ends at `emb_dim`.

For an edge-attribute tensor, verify both its row count (`E`) and its feature
width. A shape that happens to broadcast is not evidence that edge semantics
are correct.

## Aggregator selection

The accepted names in the implementation are:

- `add`, `mean`, `max`: delegated to PyG message passing.
- `softmax`: softmax weights use temperature `t`; `learn_t=True` makes `t`
  trainable.
- `softmax_sg`: softmax weights use `t` under `no_grad`, so the temperature
  path is stop-gradient even though the aggregation remains differentiable in
  messages.
- `softmax_sum`: softmax aggregation followed by degree scaling with
  `sigmoid(y)`; `y` can be learned.
- `power`: power-mean aggregation with `p`; messages and result are clamped to
  `[1e-7, 1e1]` by the inspected implementation.
- `power_sum`: power mean followed by degree scaling with `sigmoid(y)`.

The common task argument lists mention a subset (`mean`, `max`, `add`,
`softmax`, `softmax_sg`, `power`), while the layer implementation also
contains the `_sum` forms. Treat a task parser's allow-list as a separate
contract from the layer's accepted names. `p=0` is not a safe choice for the
power path because the inverse exponent is `1/p`.

Temperature, power, degree exponent, and message-scale learning are not
interchangeable stability controls. Start with fixed `t`, `p`, and `y`, then
turn on one learnable parameter at a time while checking finite gradients.
For very deep stacks, message normalization and a same-width residual block
should be tested together rather than inferred from a forward-only result.

## Edge encoding choices

- `encode_edge=False`: `edge_attr` is used directly in `x_j + edge_attr`; its
  width must match `in_dim`.
- `encode_edge=True, bond_encoder=False`: supply `edge_feat_dim` and continuous
  or already numeric edge features; a linear encoder maps them to `in_dim`.
- `encode_edge=True, bond_encoder=True`: supply the categorical fields expected
  by the atom/bond feature encoder. Do not pass arbitrary floating point edge
  vectors to this mode.

The `BondEncoder` itself is a sum of embeddings for each categorical edge
column. Dataset-specific feature construction belongs to `ogb-workflows`.

## Plain, residual, and dense composition

Choose a block based on the width and memory plan:

- **Plain** is the simplest diagnostic baseline. It does not require equal
  input/output widths except that the block constructor itself is same-width
  for sparse `PlainDynBlock` and dense `PlainDynBlock2d`.
- **Residual** preserves the input width and adds `res_scale * x`. Use it for
  stable deep stacks or when the next layer expects a fixed width. A non-unit
  `res_scale` changes the skip magnitude; document it in checkpoints/configs.
- **Dense** concatenates each new representation with the old channels. Track
  channel growth after every block and size the next layer accordingly.

Sparse dynamic blocks return `(features, batch)`, while sparse static blocks
return `(features, edge_index)`. Dense blocks return only features. A common
composition error is to feed the complete tuple into the next layer or to use
`batch` where an `edge_index` is required.

## Validation sequence

For a custom layer composition, use this order:

1. Build a tiny graph with at least `k*dilation` nodes per batch element and
   explicit edges.
2. Check output shape and `torch.isfinite(output).all()` for `add`, one
   softmax variant, and one power variant.
3. If training, run a scalar loss backward and check finite gradients for
   learnable `t`, `p`, `y`, or `msg_scale`.
4. Replace explicit edges with dynamic KNN only after the static case passes.
5. Add residual/dense composition and assert the expected channel width.
6. Only then hand off dataset/config/training questions to the relevant sibling
   skill.
