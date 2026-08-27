# Saving and Loading

## Purpose

Read this when the user wants to persist an explainer and load it again later.

## Public behavior

- `save_explainer(explainer, path)` writes the serialized explainer to a directory.
- `load_explainer(path, predictor)` loads it back and reattaches the predictor.
- The explainer itself is saved, but the model or predictor is not.
- A version mismatch warning is expected when the save-time and load-time Alibi versions differ.

## Practical implications

- Always keep the original predictor or a compatible replacement.
- Treat the saved directory as explainer state, not as a fully self-contained model bundle.
- Use a temporary directory for smoke tests and examples.

## Safe round-trip pattern

1. Fit a tiny explainer.
2. Save it to a fresh temporary directory.
3. Reload it with the original predictor.
4. Re-run the same tiny explanation to confirm the round-trip.

## Common mistakes

- Trying to load without a predictor.
- Assuming version drift is harmless.
- Saving the wrong object and then expecting the same metadata on reload.

## Read next

- `troubleshooting.md` for recovery steps.
- `scripts/smoke_confidence_prototypes.py` for a full small round-trip example.
