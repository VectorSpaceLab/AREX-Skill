# Link Prediction and KG Troubleshooting

## Edge split leakage

**Symptoms**

- Evaluation looks unrealistically good.
- Train graph still contains held-out positive edges.

**Recovery**

- Create test split first, then train split from the remaining graph.
- Use the original graph as `g_master` only when the splitter needs to avoid
  sampling false negatives from known positives.
- Preserve `edge_ids_*` and `edge_labels_*` together; do not reshuffle one
  without the other.

## `EdgeSplitter` cannot keep graph connected

**Symptoms**

- Split fails when `keep_connected=True`.

**Recovery**

- Lower `p` so fewer edges are removed.
- Use `keep_connected=False` only when the downstream model does not require the
  remaining train graph to stay connected, and document that decision.

## Invalid link IDs or endpoint types

**Symptoms**

- Link generator reports missing nodes.
- HinSAGE link generator cannot infer head node types.

**Recovery**

- Check every pair endpoint exists in the graph.
- For heterogeneous links, pass `head_node_types` explicitly when source and
  target types are ambiguous.
- Keep source/target order consistent for directed and typed relationships.

## Link head output and target mismatch

**Symptoms**

- Keras loss rank/dimension errors.
- Regression outputs are clipped unexpectedly.

**Recovery**

- Use `link_classification(output_dim=1, output_act="sigmoid")` for binary
  labels and binary cross-entropy.
- Use `output_dim=num_classes`, `output_act="softmax"` for multiclass labels.
- Use `link_regression(..., clip_limits=(low, high))` only when the target range
  is known, such as ratings.

## Knowledge graph negative sampling failures

**Symptoms**

- KG training has no negatives.
- Ranking includes known true triples as negatives.

**Recovery**

- Set `negative_samples` in `KGTripleGenerator.flow` for training.
- Maintain train/validation/test known-edge graphs for filtered ranking.
- Use relation-aware triples with clean edge types rather than ordinary edge
  pairs.

## Temporal link workflow confusion

**Symptoms**

- Static random walks ignore timestamps.
- CTDNE-style examples fail to find time-respecting walks.

**Recovery**

- Use `TemporalRandomWalk` and verify edge time attributes before embedding
  training.
- Reduce walk length or context size for sparse temporal graphs.

## Tiny diagnostic

Run:

```bash
python sub-skills/link-prediction-kg/scripts/link_prediction_smoke.py
```

If this passes, basic full-batch link generator and Keras link-head wiring work;
compare real edge split IDs, targets, and generator choice to the smoke.
