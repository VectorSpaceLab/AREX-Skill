# Baleen Troubleshooting

Use this guide to keep Baleen support scoped and safe. Most failures come from missing optional dependencies, missing artifacts, CUDA assumptions, collection mismatch, or treating Baleen as a stable one-command workflow.

## Install and import failures

Symptoms:

- `ModuleNotFoundError` for `colbert`, `baleen`, `torch`, `transformers`, or `ujson`.
- Import-time errors from ColBERT utilities while importing Baleen modules.
- `baleen` imports but concrete modules such as `baleen.engine` or `baleen.condenser.condense` fail.

Actions:

- Run `python scripts/inspect_baleen_imports.py --json` to identify the first failing module/symbol.
- Explain that Baleen inherits core ColBERT dependencies; do not patch around missing ColBERT installation inside Baleen code.
- If only `Condenser`-related imports fail, check `torch` and `transformers` before debugging search/index artifacts.
- Avoid using `import baleen` alone as proof; concrete module imports are more informative.

## Optional dependency and tokenizer failures

Symptoms:

- Errors loading `ElectraTokenizerFast` or Electra model classes.
- Network or cache failures from Hugging Face tokenizer/model loading.
- Version mismatch errors from Transformers or Torch.

Actions:

- State that `AnswerAwareTokenizer` uses an Electra tokenizer and may need cached or downloadable model assets.
- Keep import inspection separate from condenser construction; the safe script avoids creating tokenizers.
- In offline environments, ask the user to provide or pre-cache compatible Electra assets rather than allowing accidental downloads.

## CUDA and backend failures

Symptoms:

- `Torch not compiled with CUDA enabled`.
- `CUDA error`, `invalid device ordinal`, or device placement errors during `Condenser(...)`.
- Slow or stalled inference after switching to CPU.

Actions:

- Point out that `Condenser(collectionX_path, checkpointL1, checkpointL2)` defaults to `deviceL1='cuda'` and `deviceL2='cuda'`.
- For CPU-only diagnostics, use `deviceL1='cpu', deviceL2='cpu'` only after confirming checkpoint and tokenizer availability.
- Do not recommend full-scale Baleen runs on CPU as a routine validation path.
- Separate CUDA issues from ordinary ColBERT searcher/index issues: `HopSearcher` and `Condenser` have different artifact and device requirements.

## Checkpoint failures

Symptoms:

- `torch.load()` fails for `checkpointL1` or `checkpointL2`.
- Assertion failure because checkpoint `arguments.model` is not `google/electra-base-discriminator` or `google/electra-large-discriminator`.
- Assertion failure because L1 and L2 checkpoint `maxlen` values differ.
- User passes a ColBERT retriever checkpoint as a condenser checkpoint.

Actions:

- Confirm that `checkpointL1` and `checkpointL2` are Baleen Electra reader checkpoints, not ColBERT retrieval checkpoints.
- Check that both checkpoints expose compatible `arguments` fields and matching `maxlen`.
- Preserve the distinction between the ColBERT retrieval checkpoint used by `HopSearcher` and the L1/L2 condenser checkpoints used by `Condenser`.

## `collectionX` and data failures

Symptoms:

- Assertion failure that `text` is not a list.
- Assertion failure that `pid` does not equal the JSONL line number.
- Empty contexts, duplicated hops, or facts that do not map to expected sentences.
- Key errors for `(pid, sid)` in condenser stages.

Actions:

- Validate that `collectionX` is JSONL with sequential `pid`, `title`, and sentence-list `text` fields.
- Confirm the search index collection and Baleen `collectionX` were derived from the same passage ids and sentence segmentation.
- Explain that Baleen facts are `(pid, sid)` identifiers; the engine maps them through `collectionX` to build later-hop context.
- For mismatched data, repair alignment before changing depth, hop count, or condenser thresholds.

## API misuse

Symptoms:

- Calling normal `Searcher` methods while expecting context-aware hops.
- Passing `context` to APIs that are not `HopSearcher.search()`/`encode()`.
- Treating `Baleen.search()` output as answer text.
- Batch contexts do not line up with batch queries in `search_all()`.

Actions:

- Use `HopSearcher` when context-conditioned query encoding is required; use core `Searcher` for one-hop retrieval.
- Ensure query and context batches have compatible shapes when using `search_all()`.
- Map returned `(pid, sid)` facts back to `collectionX` and decide separately how the user wants answers extracted or displayed.

## Depth, hops, and explosion failures

Symptoms:

- `depth=... must be divisible by num_hops=...` assertion.
- Final assertion that the unique passage bag length equals `depth` fails.
- Multi-hop runs become expensive or produce many duplicates.
- `_stage2()` assertion fails because fewer than two L3x facts remain.

Actions:

- Require `depth % num_hops == 0`; start with small `depth` during diagnostics.
- Explain that each hop searches `k=depth` but only keeps `depth // num_hops` new passages for condensation.
- Investigate duplicate/insufficient search results, bad collection alignment, or weak condenser outputs before increasing depth.
- Avoid deep multi-hop settings until a one- or two-hop smoke test returns stable fact identifiers.

## Workflow-specific guidance

When the user asks for a full Baleen run but lacks artifacts, provide a staged response:

1. Run or suggest safe import inspection.
2. Inventory missing index, retrieval checkpoint, L1/L2 condenser checkpoints, and `collectionX` path.
3. Explain device constraints and whether CPU fallback is reasonable.
4. Provide an adaptation skeleton only after the artifact list is complete.
5. Route normal indexing/search or training questions to the appropriate ColBERT sub-skill instead of expanding Baleen scope.
