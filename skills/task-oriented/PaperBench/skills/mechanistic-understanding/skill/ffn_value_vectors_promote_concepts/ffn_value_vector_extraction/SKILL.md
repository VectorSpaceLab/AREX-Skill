---
name: ffn_value_vector_extraction
description: Extract and normalize feed-forward output value vectors from transformer-like model weights for concept-promotion analysis.
---

# FFN Value Vector Extraction

Use this skill when a recovery or interpretability task needs the value vectors of transformer feed-forward neurons. It is appropriate for state dictionaries, named matrices, or explicit FFN output projection tensors. Do not use it to read an original paper repository during recovery; provide current-attempt matrices or model weights from allowed sources.

## Inputs

- A JSON state dictionary mapping tensor names to 2D numeric arrays, or a direct 2D matrix.
- Optional orientation hint: `neurons_by_rows` or `neurons_by_columns`.
- Optional layer/name hints such as `mlp.c_proj.weight`, `fc2.weight`, `W_out`, or `down_proj.weight`.

## Outputs

A JSON object with `vectors`, each containing `layer`, `neuron`, `source_name`, and `vector`, plus `orientation` and validation metadata.

## Workflow

1. Identify likely FFN output projections by name.
2. Infer whether neurons are rows or columns. GPT-style `c_proj.weight` and `W_out` often need columns-as-neurons; generic `fc2.weight` commonly uses columns-as-neurons when shaped hidden by intermediate.
3. Split the matrix into one vector per neuron and preserve provenance.
4. Validate that vectors are numeric and have a consistent residual dimension.
5. Pass these vectors to the vocabulary projection skill.

## Validation

Run `python scripts/extract_value_vectors.py --fixture` or the tests in `tests/test_extract_value_vectors.py`. The fixture checks orientation and neuron identifiers on deterministic matrices.

## Limitations

The skill does not run a transformer model and does not infer semantic concepts. It only exports the value side of FFN neurons for downstream projection and grouping.
