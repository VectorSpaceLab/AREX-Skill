# Document and Data Troubleshooting

- Invalid JSON: confirm the saved value is an object, not a string containing an object.
- Wrong nesting: multi-sentence output is nested by sentence; tokenized input must be `list[list[str]]`.
- Prefix ambiguity: use exact keys when both `ner/msra` and `ner/ontonotes` or similar keys exist.
- CoNLL conversion issues: token field must exist, dependency fields must align with tokens, and root head is `0`.
- Pretty print issues: terminal font/width affects alignment; do not parse pretty text as data.
- AMR conversion can require optional AMR dependencies.
