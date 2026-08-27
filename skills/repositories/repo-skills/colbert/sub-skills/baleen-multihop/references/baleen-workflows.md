# Baleen Workflows

Baleen is an optional multi-hop retrieval extension layered on ColBERT. Handle it as an artifact-aware workflow: first verify import surfaces and local prerequisites, then plan retrieval only if the user already has compatible checkpoints, index data, and devices.

## Multi-hop flow

1. The user question enters `Baleen.search(query, num_hops, depth)`.
2. `HopSearcher.search(query, context, k=depth)` retrieves candidate passages; `context` is `None` on the first hop.
3. The Baleen engine filters out passages already represented by selected facts and keeps `k = depth // num_hops` new passage ids for condensation.
4. `Condenser._stage1()` uses the L1 Electra reader to select sentence facts from current passages plus previous facts.
5. `Condenser._stage2()` uses the L2 Electra reader to rerank condensed facts and keep a smaller fact set.
6. The engine builds next-hop context by joining selected `collectionX[(pid, sid)]` sentences with ` [SEP] `.
7. After all hops, the engine returns final fact ids, a bag of passage ids, and stage-one predictions.

## Required artifacts checklist

Confirm these before suggesting an end-to-end run:

- A ColBERT index and compatible retrieval checkpoint that can initialize `Searcher`/`HopSearcher`.
- A search collection aligned with the index.
- A Baleen `collectionX` JSONL file with sequential `pid` values, a `title`, and `text` as a list of sentences.
- L1 and L2 Baleen condenser checkpoints whose `arguments.model` is an Electra discriminator and whose `arguments.maxlen` values match.
- Torch and Transformers installed; Electra tokenizer/model assets available locally or through an allowed download path.
- Device availability matching `Condenser(..., deviceL1=..., deviceL2=...)`; defaults are `cuda`.
- A chosen `num_hops` and `depth` where `depth` is divisible by `num_hops`.

## Safe import/signature inspection

When the user only needs diagnostics, or lacks artifacts, run:

```bash
python scripts/inspect_baleen_imports.py --tiny-fixture
```

This checks:

- Import availability for Baleen engine, hop searcher, condenser, model, tokenizer, and loader symbols.
- Constructor/function signatures through `inspect.signature()` where import succeeds.
- Tiny temporary `collectionX` and context loader behavior.

It deliberately does not instantiate `HopSearcher` or `Condenser`, load checkpoints, create tokenizers, build indexes, run retrieval, download models, or write persistent files.

## Planning an adaptation

Use this sequence for a user who wants to adapt Baleen code:

1. Identify whether the task is concept explanation, static diagnostics, or a real run.
2. If it is a real run, inventory paths for index, retrieval checkpoint, collection, `collectionX`, `checkpointL1`, and `checkpointL2`.
3. Validate the `collectionX` shape with a tiny parser or the inspector's fixture pattern before loading large files.
4. Decide device settings explicitly; on CPU-only machines, set `deviceL1='cpu'` and `deviceL2='cpu'` only as a slow diagnostic fallback.
5. Keep `depth` modest during smoke tests and ensure `depth % num_hops == 0`.
6. Interpret returned facts as `(pid, sid)` identifiers into `collectionX`, not as natural-language answers.
7. If results are empty or duplicated, inspect collection alignment and searcher/index compatibility before changing condenser thresholds.

## `collectionX` format notes

Baleen collection loaders expect one JSON object per line:

```json
{"pid": 0, "title": "Solar System", "text": ["Earth orbits the Sun.", "The Moon orbits Earth."]}
{"pid": 1, "title": "Gravity", "text": ["Gravity keeps planets in orbit."]}
```

Important constraints:

- `pid` must match the zero-based line number.
- `text` must be a list of sentence strings, not one passage string.
- Loader output prefixes every sentence with `title | `.
- `Baleen.search()` later uses `(pid, sid)` facts to recover context sentences from the flat loader output.
- If the search collection and `collectionX` are derived from different passage ids or sentence splits, later hops can become empty, duplicated, or misleading.

## CPU-only handling

For CPU-only environments, be explicit:

- Import checks are safe and usually enough to answer availability questions.
- Constructing `Condenser` defaults to CUDA and must be overridden for CPU diagnostics.
- CPU inference over Electra readers can be slow and may still fail if checkpoints or tokenizer assets are absent.
- Full retrieval over large ColBERT indexes is not a good default CPU validation step.

## Difficult synthetic usability cases

Use these when planning verification for this sub-skill:

- CPU-only Baleen request: the user asks to run multi-hop retrieval, but `Condenser` defaults to CUDA and the environment has only CPU imports. A good agent runs import inspection, explains artifact/device gaps, and provides a CPU diagnostic plan without pretending to execute retrieval.
- Mismatched `collectionX`/query context: the user has an index and sentence JSONL produced from different passage ids, causing empty or duplicated hops. A good agent identifies alignment risk, checks `pid`/`sid` format, explains why facts are identifiers, and recommends small-depth diagnostics before full runs.

## What not to do

- Do not use Baleen for ordinary one-hop `Searcher.search()` questions.
- Do not instantiate `Condenser` just to see whether imports work.
- Do not assume model downloads are allowed in offline or production environments.
- Do not treat `stage2_L3x` output as final answers without mapping facts back to sentences and the user's answer extraction strategy.
