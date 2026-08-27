# Operators and conflicts

## Operator map rules

- The anonymizer first looks for an entity-specific operator such as `{"PERSON": OperatorConfig(...)}`.
- If no entity-specific entry exists, it falls back to `DEFAULT`.
- If the operator map is empty or missing `DEFAULT`, Presidio inserts `DEFAULT = replace` automatically.
- `replace` with an empty or missing `new_value` emits `<ENTITY_TYPE>`.

## Built-in operators

| Operator | Direction | Parameters | Notes |
| --- | --- | --- | --- |
| `replace` | anonymize | `new_value` | Replaces the entity text. Empty or missing `new_value` falls back to `<ENTITY_TYPE>`. |
| `redact` | anonymize | none | Removes the entity text. |
| `hash` | anonymize | `hash_type`, `salt` | `hash_type` is `sha256` or `sha512`. Omit `salt` for a random per-entity salt. If supplied, salt must be at least 16 bytes after encoding. |
| `mask` | anonymize | `masking_char`, `chars_to_mask`, `from_end` | `masking_char` must be a single character. |
| `encrypt` | anonymize | `key` | AES-CBC encryption. Key must be 128, 192, or 256 bits after UTF-8 encoding. |
| `custom` | anonymize | `lambda` | Callable must return a string. Validation checks callability; return type is enforced at runtime. |
| `keep` | anonymize | none | Leaves the entity text unchanged. |
| `surrogate_ahds` | anonymize | `endpoint`, `entities`, `input_locale`, `surrogate_locale` | Optional AHDS surface. Requires the AHDS extra and Azure SDKs. Endpoint can come from `AHDS_ENDPOINT`. |
| `decrypt` | deanonymize | `key` | Reverses `encrypt` with the same AES key. |
| `deanonymize_keep` | deanonymize | none | Leaves the text unchanged during deanonymization. |

## Custom operator extension points

To add a reusable operator class:

1. Subclass `Operator`.
2. Implement `operate`, `validate`, `operator_name`, and `operator_type`.
3. Register it with `AnonymizerEngine.add_anonymizer()` or `DeanonymizeEngine.add_deanonymizer()`.

The `custom` built-in operator is usually the fastest one-off path. Use a callable that returns `str`.

## Conflict handling

### Default strategy

`AnonymizerEngine.anonymize()` defaults to `ConflictResolutionStrategy.MERGE_SIMILAR_OR_CONTAINED`.

This means:

- same-span results keep the higher score;
- contained entities prefer the larger span;
- same-type spans separated only by spaces can be merged before replacement;
- partial intersections may be emitted as concatenated output pieces.

### `REMOVE_INTERSECTIONS`

Use `ConflictResolutionStrategy.REMOVE_INTERSECTIONS` when you need the engine to trim overlaps into non-overlapping spans instead of relying on the default merge behavior.

This is useful when:

- you want to preserve both entities but not their overlap;
- you need output spans to remain non-overlapping for downstream processing;
- the default merge policy would collapse adjacent spans too aggressively.

### `merge_entities_with_spaces`

`merge_entities_with_spaces=True` by default.

- Same-entity spans separated only by spaces are merged.
- Tabs and newlines are not merged.
- Set it to `False` when every space-separated token must remain a separate output item.

## AHDS boundary

`surrogate_ahds` is optional. If the operator is missing, the AHDS extra or Azure SDKs are not installed in the runtime.

Treat AHDS as an external service path:

- verify the extra is installed;
- provide `endpoint` or `AHDS_ENDPOINT`;
- supply the detected `entities` list;
- keep locale values explicit when you need reproducible output.
