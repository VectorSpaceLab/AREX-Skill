# Workflows

## 1. Anonymize a single text

Use this when you already have `RecognizerResult` spans.

```python
engine = AnonymizerEngine()
result = engine.anonymize(
    text,
    analyzer_results,
    {
        "PERSON": OperatorConfig("redact"),
        "DEFAULT": OperatorConfig("replace", {"new_value": "<PII>"}),
    },
)
```

Inspect:

- `result.text` for the anonymized string
- `result.items` for output spans and operator names

## 2. Reversible encrypt/decrypt

Use this for round-tripping data that must be restored later.

```python
key = b"1234567890abcdef"
anon = AnonymizerEngine().anonymize(
    text,
    analyzer_results,
    {"PERSON": OperatorConfig("encrypt", {"key": key})},
)
restored = DeanonymizeEngine().deanonymize(
    anon.text,
    anon.items,
    {"PERSON": OperatorConfig("decrypt", {"key": key})},
)
```

Guidance:

- keep the `OperatorResult` list from the anonymizer output;
- use the same key for decrypt;
- expect the returned offsets to be normalized to the decrypted output.

## 3. Batch list workflow

Use `BatchAnonymizerEngine.anonymize_list()` when you have parallel lists of texts and spans.

```python
batch = BatchAnonymizerEngine()
texts_out = batch.anonymize_list(texts, recognizer_results_list, operators=operators)
```

- Items that are not string, bool, int, or float pass through unchanged.
- Missing recognizer lists are treated as empty lists.
- Extra kwargs are forwarded to the underlying anonymizer.

Use `BatchDeanonymizeEngine.deanonymize_list()` for the reverse direction.

## 4. Batch nested-dict workflow

Use the dict helpers when the analyzer produced a `DictRecognizerResult` tree.

- `BatchAnonymizerEngine.anonymize_dict()` recurses through nested dict/list values.
- `BatchDeanonymizeEngine.deanonymize_dict()` mirrors that structure for reversed flows.
- Scalars are preserved.

This is the right workflow when the content tree already exists and you do not need DataFrame-specific logic.

## 5. Custom operator workflow

Choose the smallest extension that fits the task:

- one-off behavior: use `OperatorConfig("custom", {"lambda": callable})`;
- reusable behavior: subclass `Operator` and register it with the engine.

Remember:

- the lambda must return `str`;
- validation checks callability, but the return type is enforced when the operator runs;
- `add_anonymizer()` and `add_deanonymizer()` are the registration points.

## 6. AHDS surrogate workflow

Use `surrogate_ahds` only when the optional AHDS surface is available.

```python
result = AnonymizerEngine().anonymize(
    text,
    analyzer_results,
    {
        "DEFAULT": OperatorConfig(
            "surrogate_ahds",
            {
                "entities": analyzer_results,
                "input_locale": "en-US",
                "surrogate_locale": "en-US",
            },
        )
    },
)
```

Keep this flow behind a feature flag or environment check because it depends on the external AHDS service and SDKs.

## 7. Overlap-aware workflow

When spans overlap, decide the conflict strategy before choosing the operator map.

- Use the default merge policy for same-entity fragments that should collapse together.
- Use `REMOVE_INTERSECTIONS` when you want non-overlapping spans after trimming.
- Set `merge_entities_with_spaces=False` if every space-separated span must remain independent.
