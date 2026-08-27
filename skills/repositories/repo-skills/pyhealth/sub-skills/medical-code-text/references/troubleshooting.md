# Medical-code/text troubleshooting

- **Unknown vocabulary/code:** check exact source/target names and code-system
  version. Do not use a code from another ontology or silently drop unmapped
  values.
- **`InnerMap.load`/`CrossMap.load` cache failure:** inspect local assets and
  network/license access; `refresh_cache=True` is an explicit side effect, not a
  recovery to run automatically.
- **NLP import error:** install `[nlp]` and rerun the optional probe. A missing
  NLTK corpus is separate; provide an authorized preloaded resource or stop.
- **Tokenizer/model mismatch:** keep tokenizer revision and model revision
  aligned; inspect token IDs, padding, truncation, and vocabulary before loading
  weights.
- **Text processor shape error:** compare raw value type (string, sequence, or
  time-text tuple) with processor contract and inspect one output.
- **Multimodal dimension/time error:** print each modality's named schema,
  dtype, shape, timestamp units, and mask. Align before fusion; do not reshape
  blindly.
- **Model download/OOM:** test local architecture with no weights, then use a
  bounded cache/device decision. CUDA availability does not guarantee enough
  memory for a pretrained multimodal model.
- **PHI or credential exposure:** stop and remove sensitive values from fixtures,
  logs, and checkpoints; use de-identified local data.
