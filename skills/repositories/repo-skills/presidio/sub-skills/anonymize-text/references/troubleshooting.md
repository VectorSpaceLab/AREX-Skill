# Troubleshooting

## Common failures and fixes

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `Invalid analyzer result, start: ... end: ... while text length is only ...` | Span is outside the current text, negative, or `start > end`. | Recompute offsets for the exact text being anonymized. Sort spans and validate them before calling the engine. |
| `Invalid operator class '...'` | Typo in the operator name or the class is not registered on the engine. | Use `get_anonymizers()` / `get_deanonymizers()` to confirm the available names, or register the custom class before use. |
| `Expected parameter ...` or `Invalid parameter value for ...` | Missing or wrong-typed operator params. | Check the operator table. `mask`, `hash`, `encrypt`, `decrypt`, and `custom` all validate their inputs. |
| `Invalid input, key must be of length 128, 192 or 256 bits` | Encrypt/decrypt key length is wrong after encoding. | Use a 16-, 24-, or 32-byte AES key. Prefer a bytes literal when you want byte-accurate length control. |
| Hash output changes every run | No explicit hash salt was provided. | Supply a stable salt of at least 16 bytes if you need repeatable hashes. Otherwise the random salt is expected. |
| Custom lambda works in one place but fails later | The callable does not return `str`, or it is not callable at all. | Ensure the lambda returns a string. Validation checks callability only; return-type failures surface when the operator runs. |
| Unexpected `<ENTITY_TYPE>` replacement | `replace` fell back to the default behavior. | Remember that missing or empty `new_value` becomes `<ENTITY_TYPE>`, and entity-specific operators override `DEFAULT`. |
| Overlaps produce merged or concatenated output | Default conflict handling is merging or trimming spans, not blind replacement. | Choose `ConflictResolutionStrategy.REMOVE_INTERSECTIONS` when you need trimmed non-overlapping spans, or disable `merge_entities_with_spaces` if space-separated fragments must stay separate. |
| Decrypt output offsets look wrong | The deanonymizer expects output spans from the anonymizer result, not the original analyzer spans. | Pass the returned `EngineResult.items` from the encrypting anonymizer into `DeanonymizeEngine.deanonymize()`. |
| `surrogate_ahds` is missing or raises import/endpoint errors | The optional AHDS extra or Azure SDKs are absent, or the endpoint is not configured. | Install the AHDS extra, set `endpoint` or `AHDS_ENDPOINT`, and keep the AHDS path behind an environment check. |

## Operator-specific notes

- `replace`: missing `new_value` is not an error; it becomes `<ENTITY_TYPE>`.
- `mask`: `masking_char` must be one character, `chars_to_mask` must be an integer, and `from_end` must be boolean.
- `hash`: `hash_type` must be `sha256` or `sha512`; a provided salt must be at least 16 bytes.
- `encrypt` / `decrypt`: use the same key on both sides.
- `custom`: the callable should be pure and deterministic when you want repeatable smoke tests.

## When in doubt

- If the problem is span detection, route it to `analyze-text`.
- If the problem is DataFrame or nested JSON orchestration, route it to `structured-data`.
- If the problem is CLI parsing or file scanning, route it to `cli-scans`.
