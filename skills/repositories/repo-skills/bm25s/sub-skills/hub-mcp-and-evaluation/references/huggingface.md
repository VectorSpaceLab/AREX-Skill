# Hugging Face Hub integration

`bm25s.hf` is an optional integration around `huggingface_hub.HfApi`. Import it
only when Hub support is actually needed:

```python
from bm25s.hf import BM25HF, TokenizerHF
```

The package extra is `hf`; installing `huggingface_hub` separately is also
supported. The Hub is a remote service, so a successful Python import proves
only that the adapter is available—not that a repository is reachable or that
the caller is authorized.

## Authorization and mutation policy

- Require an explicit user decision before calling either `save_to_hub` or a
  tokenizer `save_*_to_hub` method. These methods call `create_repo(...,
  exist_ok=True)` and then `upload_folder`; they can create or update a remote
  model repository.
- Never manufacture, print, commit, or persist a token. Pass a user-provided
  `token` value or rely on an already configured Hugging Face client only after
  the user has authorized the operation. A token in an environment variable is
  not, by itself, upload authorization.
- `private=True` is the implementation default for writes. Use `private=False`
  only when the user explicitly requests a public repository and understands
  that the corpus and index may become public.
- Remote overwrite is not controlled by `overwrite_local`; the adapter uses
  `exist_ok=True` and uploads a commit to the named repository. Confirm the
  repository and commit intent separately.
- Prefer `allow_pickle=False`. Setting it to `True` changes the NumPy loading
  trust boundary and should require an explicit reason and trusted artifacts.

## `BM25HF` save/load contract

`BM25HF` is a `BM25` subclass. Build and index it with the normal local API,
then save a local staging copy or upload it:

```python
import bm25s
from bm25s.hf import BM25HF

corpus = [
    "a cat likes to purr",
    "a dog likes to play",
    "a fish swims in water",
]
retriever = BM25HF()
retriever.index(bm25s.tokenize(corpus))

# Only after explicit authorization and a valid token:
# retriever.save_to_hub(
#     "user/retriever-name", token=token, corpus=corpus,
#     private=True, include_readme=True,
# )
```

The important arguments are:

| Argument | Meaning and boundary |
| --- | --- |
| `repo_id` | Hub model repository identifier, normally `user/name`. |
| `token` | Token forwarded to `HfApi`; `None` may use client authentication or fail. Never guess it. |
| `local_dir` | Optional local staging directory for writes, or download destination for reads. |
| `corpus` | Optional iterable saved as JSONL with the index; include it when later retrieval must return documents or MCP must load a corpus. |
| `private` | Remote repository visibility on save; defaults to `True`. |
| `commit_message` | Commit message for `upload_folder`. |
| `overwrite_local` | Allows use of a non-empty local staging directory. It does not authorize remote overwrite. |
| `include_readme` | Adds the generated index README; defaults to `True`. |
| `allow_pickle` | Passed to local index save/load. Keep `False` unless trusted legacy data requires it. |
| `show_progress`, `leave_progress` | Progress display for local save/load; they do not make network operations bounded. |
| `**kwargs` | Forwarded to `HfApi.upload_folder` on save; review every extra before use. |

When `local_dir` is `None`, or is non-empty with `overwrite_local=False`, the
implementation stages files in a temporary directory and removes that staging
directory after upload. When `local_dir` is absent/non-existent or empty, it
is used directly. A non-empty staging directory is not cleared automatically;
`overwrite_local=True` allows the save to write there, so inspect it first.

The model save includes the normal BM25 arrays, vocabulary, parameters, and an
optional `corpus.jsonl`. `include_readme` describes the saved model and records
parameters, but it is documentation rather than a manifest validator.

Load is a remote read followed by the ordinary local loader:

```python
# Network/credential operation; use only with explicit intent.
retriever = BM25HF.load_from_hub(
    "user/retriever-name",
    revision="main",       # branch/tag/commit when reproducibility matters
    token=token,
    local_dir="./hub-cache",
    load_corpus=True,
    mmap=True,
    allow_pickle=False,
)
```

`load_from_hub` first asks the Hub for repository information and then calls
`snapshot_download`. `revision` is optional but should be pinned for a
reproducible recovery. `local_dir` is a download/cache destination; it is not a
way to load an arbitrary local directory without contacting the Hub. For a
purely local saved index use `BM25.load(...)` in the persistence route.
`load_corpus=True` requires the repository snapshot to contain the expected
corpus file. `mmap=True` maps the NumPy score arrays after download and is a
memory choice, not a network optimization.

## `TokenizerHF`

`TokenizerHF` inherits the normal tokenizer and exposes four instance methods:

- `save_vocab_to_hub(repo_id, token=None, local_dir=None, commit_message=..., overwrite_local=False, private=True, **kwargs)`
- `load_vocab_from_hub(repo_id, revision=None, token=None, local_dir=None)`
- `save_stopwords_to_hub(repo_id, token=None, local_dir=None, commit_message=..., overwrite_local=False, private=True, **kwargs)`
- `load_stopwords_from_hub(repo_id, revision=None, token=None, local_dir=None)`

The load methods mutate an existing tokenizer instance; do not call them as
class methods. Create the tokenizer with the same lower/splitter/stemmer
configuration used for the index, then load the vocabulary and, if relevant,
the stopwords. The vocabulary file is JSON named
`vocab.tokenizer.json`; stopwords use `stopwords.tokenizer.json`. These names
are separate from the BM25 index's `vocab.index.json`.

A tokenizer Hub write follows the same create/upload/temporary-staging path as
`BM25HF`. Saving vocabulary and stopwords separately can produce multiple
commits; authorize and record each intended mutation. A tokenizer snapshot does
not automatically prove that its settings match an independently saved BM25
index.

## Safe preflight

Before any remote call, run a local equivalent:

1. Construct a three-document `BM25HF` index and save it with `BM25.save` to a
   fresh temporary directory, including the corpus.
2. Load it with `BM25.load(..., load_corpus=True, mmap=True)` and query with the
   same tokenizer.
3. For a tokenizer, call `save_vocab`/`load_vocab` and
   `save_stopwords`/`load_stopwords` locally and compare the resulting state.
4. Only after those checks pass and the user approves the exact `repo_id`,
   visibility, revision/commit policy, token handling, and destination should
   the Hub adapter be called.

No bundled check uploads or downloads. For failures and refusal wording, see
[troubleshooting.md](troubleshooting.md).
