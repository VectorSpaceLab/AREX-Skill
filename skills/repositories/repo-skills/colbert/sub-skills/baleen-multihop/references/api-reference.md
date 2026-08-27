# Baleen API Reference

This reference summarizes Baleen surfaces that matter when helping users adapt the optional multi-hop retrieval extension. Treat these as repository-bundled research APIs: verify the user's installed environment before writing code that depends on them.

## Verified package facts

- Distribution package: `colbert-ai` version `0.2.22`.
- Import package: `colbert`.
- Verified imports include `colbert`, `colbert.infra`, `colbert.data`, `colbert.modeling.checkpoint`, `utility`, and `baleen`.
- CPU import inspection is safe; practical ColBERT indexing/training and many Baleen runs usually require CUDA/GPU plus local artifacts.
- Core public signatures relevant to composition include `Searcher(index, checkpoint=None, collection=None, config=None, index_root=None, verbose=3)` and `Collection(path=None, data=None)`.

## Module map

| Module | Surface | Role |
| --- | --- | --- |
| `baleen.engine` | `Baleen` | Coordinates iterative multi-hop retrieval and fact condensation. |
| `baleen.hop_searcher` | `HopSearcher`, `TextQueries` | Extends ColBERT `Searcher` with context-aware query encoding. |
| `baleen.condenser.condense` | `Condenser` | Loads L1/L2 Electra reader checkpoints and selects sentence facts. |
| `baleen.condenser.model` | `ElectraReader` | Scores `[MASK]` sentence candidates from Electra encodings. |
| `baleen.condenser.tokenization` | `AnswerAwareTokenizer` | Builds question/passage encodings and candidate spans for condenser inference. |
| `baleen.utils.loaders` | `load_collectionX`, `load_contexts` | Loads sentence-expanded collections and prior-hop contexts. |

## `baleen.engine.Baleen`

Constructor:

```python
Baleen(collectionX_path: str, searcher, condenser: Condenser)
```

Behavior:

- Loads `collectionX_path` through `load_collectionX()` into a flat mapping keyed by `(pid, sid)`.
- Stores a searcher expected to behave like `HopSearcher` and a `Condenser` instance.
- `search(query, num_hops, depth=100, verbose=False)` asserts `depth % num_hops == 0` and sets per-hop `k = depth // num_hops`.
- At each hop, calls `searcher.search(query, context=context, k=depth)`, filters out passages already used by selected facts, calls `condenser.condense(query, backs=facts, ranking=ranking_)`, and updates context by joining selected fact sentences with ` [SEP] `.
- Returns `(stage2_L3x, pids_bag, stage1_preds)` after asserting the unique passage bag reaches `depth`.

Caveats:

- The `depth` divisibility assertion is user-visible and should be checked before a run.
- Empty, duplicated, or insufficient search results can violate the final `len(pids_bag) == depth` assertion.
- `stage2_L3x` contains `(pid, sid)` fact identifiers, not answer strings.

## `baleen.hop_searcher.HopSearcher`

Definition:

```python
class HopSearcher(Searcher):
    def __init__(self, *args, config=None, interaction='flipr', **kw_args)
    def encode(self, text, context)
    def search(self, text: str, context: str, k=10)
    def search_all(self, queries, context, k=10)
```

Behavior:

- Builds a default `ColBERTConfig(query_maxlen=64, interaction=interaction)` and merges it with any user config.
- Inherits normal ColBERT `Searcher` initialization, so it still needs an index, checkpoint/collection configuration, and compatible ColBERT runtime setup.
- `encode()` normalizes single text/context values to lists, sets `checkpoint.query_tokenizer.query_maxlen`, and calls `checkpoint.queryFromText(..., context=context, bsize=bsize, to_cpu=True)`.
- `search()` runs dense search over the encoded query/context pair.
- `search_all()` casts query and context inputs with `Queries.cast()` and searches a batch.

Boundary note: use `HopSearcher` only when the user explicitly needs context-conditioned retrieval. For ordinary one-hop search, use the core `Searcher` workflow.

## `baleen.condenser.condense.Condenser`

Constructor:

```python
Condenser(collectionX_path, checkpointL1, checkpointL2, deviceL1='cuda', deviceL2='cuda')
```

Behavior:

- Loads two checkpoints with `torch.load(..., map_location='cpu')` and ColBERT's `load_checkpoint()`.
- Requires checkpoint arguments to identify `google/electra-base-discriminator` or `google/electra-large-discriminator`.
- Moves L1 and L2 `ElectraReader` models to `deviceL1` and `deviceL2`; defaults are CUDA devices.
- Asserts both checkpoints use the same `maxlen`.
- Creates `MixedPrecisionManager(activated=True)` and `AnswerAwareTokenizer(total_maxlen=maxlen)`.
- Loads `collectionX` into passage-level `CollectionX` and sentence-level `CollectionY` mappings.
- `condense(query, backs, ranking)` returns `(stage1_preds, stage2_preds, stage2_preds_L3x)`.

Stage behavior:

- `_stage1()` prepends previous facts (`backs`) to the query using ` # `, builds passages by joining title/sentences with ` [MASK] `, scores sentence positions, and keeps up to nine unique `(pid, sid)` facts.
- `_stage2()` scores condensed facts together, keeps positive facts plus at least two L3x facts, limits L3x to at most four unique passages, and asserts at least two facts remain.

Caveats:

- Constructing `Condenser` loads neural checkpoints and can fail before any retrieval starts.
- CPU fallback may be possible with `deviceL1='cpu', deviceL2='cpu'`, but it is slow and still requires compatible Torch, Transformers, checkpoint files, and tokenizer/model availability.
- `AnswerAwareTokenizer` may call Hugging Face tokenizer loading for Electra; offline environments need cached assets or local-compatible checkpoints.

## `baleen.utils.loaders`

`load_collectionX(collection_path, dict_in_dict=False)` expects JSONL rows like:

```json
{"pid": 0, "title": "Passage title", "text": ["Sentence one.", "Sentence two."]}
```

Rules:

- `text` must be a list.
- `pid` must equal the zero-based line number.
- Flat mode returns `{(pid, sid): "title | sentence"}`.
- Nested mode returns `{pid: {sid: "title | sentence"}}`.
- Sentence id `sid` starts at `0` for the first sentence in `text`; title is prefixed to each sentence in loader output.

`load_contexts(first_hop_topk_path)` expects JSONL records shaped like `[qid, facts]`, converts list facts to tuples, and returns `qid -> facts`.

## Composition pattern

A full Baleen setup usually looks like this conceptually:

```python
from baleen.engine import Baleen
from baleen.hop_searcher import HopSearcher
from baleen.condenser.condense import Condenser

searcher = HopSearcher(index="...", checkpoint="...", collection="...")
condenser = Condenser("collectionX.jsonl", "checkpointL1.pt", "checkpointL2.pt")
baleen = Baleen("collectionX.jsonl", searcher, condenser)
facts, passage_ids, stage1 = baleen.search("question", num_hops=2, depth=100)
```

Use this pattern as an adaptation outline only. Before running it, confirm all paths, devices, index roots, collection alignment, and checkpoint compatibility.
