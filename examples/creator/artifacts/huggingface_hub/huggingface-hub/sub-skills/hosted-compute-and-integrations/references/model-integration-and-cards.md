# Model integration and repository cards

Read this reference when a framework model needs Hub save/load behavior or when
creating a Model, Dataset, or Space README card. Keep local generation and
parsing separate from Hub publishing: local card/model serialization is safe,
while `push_to_hub`, `RepoCard.push_to_hub`, remote `ModelCard.load`, and any
upload are credentialed network side effects.

## ModelHubMixin contract

`ModelHubMixin` is the framework-neutral integration. A subclass must implement:

```python
from pathlib import Path
from huggingface_hub import ModelHubMixin

class MyModel(ModelHubMixin):
    def _save_pretrained(self, save_directory: Path) -> None:
        ...  # write framework weights and any required files

    @classmethod
    def _from_pretrained(
        cls, *, model_id, revision, cache_dir, force_download,
        local_files_only, token, **model_kwargs
    ):
        ...  # construct and load the framework model
```

The private methods are implementation hooks; users call the public
`save_pretrained`, `from_pretrained`, and `push_to_hub` methods. The installed
class inspects the subclass `__init__` signature and records JSON-serializable
constructor/default arguments in `_hub_mixin_config`. On save it:

1. creates the target directory and removes a stale `config.json`;
2. calls `_save_pretrained`;
3. writes `config.json` from the inferred or explicit `config` unless the hook
   already wrote it;
4. writes `README.md` from `generate_model_card` unless the hook already wrote
   it; and
5. optionally calls `push_to_hub`.

A dataclass config is converted to a dictionary. Non-JSONable constructor values
are omitted unless a custom `coders={Type: (encoder, decoder)}` pair is defined.
When loading a local directory, `from_pretrained` reads local `config.json`
without network and passes matching values into `__init__` and the loading hook.
When loading a Hub id, it downloads config/weights unless
`local_files_only=True`; `revision`, `cache_dir`, `force_download`, `token`, and
model kwargs control that operation. Explicit model kwargs take precedence over
values from config. Validate that the restored constructor configuration matches
the checkpoint before using it.

Useful public signatures are:

```python
model.save_pretrained(
    save_directory, *, config=None, repo_id=None, push_to_hub=False,
    model_card_kwargs=None, **push_to_hub_kwargs
) -> str | None
model.from_pretrained(
    pretrained_model_name_or_path, *, force_download=False, token=None,
    cache_dir=None, local_files_only=False, revision=None, **model_kwargs
)
model.push_to_hub(
    repo_id, *, config=None, commit_message="Push model using huggingface_hub.",
    private=None, token=None, branch=None, create_pr=None,
    allow_patterns=None, ignore_patterns=None, delete_patterns=None,
    model_card_kwargs=None
) -> str
```

`push_to_hub` creates the model repository with `exist_ok=True`, saves into a
temporary directory, and uploads a commit. It can filter files with allow,
ignore, and delete patterns or create a PR. Never call it in a local smoke test;
mock `HfApi.create_repo` and `upload_folder` if checking the forwarding contract.

## PyTorchModelHubMixin

For a PyTorch `nn.Module`, use multiple inheritance with
`PyTorchModelHubMixin`:

```python
import torch.nn as nn
from huggingface_hub import PyTorchModelHubMixin

class Tiny(nn.Module, PyTorchModelHubMixin, library_name="tiny-lib", tags=["demo"]):
    def __init__(self, width: int = 4):
        super().__init__()
        self.linear = nn.Linear(width, width)
```

The mixin saves `model.safetensors` using safetensors and loads that file first;
when absent, it falls back to `pytorch_model.bin`. Loading uses `map_location`
(default `"cpu"`) and `strict` (default `False`), then calls `eval()`. For
training after loading, call `model.train()` explicitly. A missing or
incompatible torch/safetensors install is an environment problem, not a model
config fix.

The class declaration can provide `library_name`, `license`, `language`,
`pipeline_tag`, `tags`, `repo_url`, `paper_url`, `docs_url`, a custom
`model_card_template`, and custom coders. The mixin adds
`model_hub_mixin`/`pytorch_model_hub_mixin` tags and the generated card inherits
these metadata values. Avoid putting secrets, machine paths, or transient
runtime state into constructor arguments because they may enter `config.json`
or the generated README.

A local round trip should be the first test:

```python
model = Tiny(width=4)
model.save_pretrained("./tmp-tiny")
restored = Tiny.from_pretrained("./tmp-tiny")
assert restored.linear.weight.shape == model.linear.weight.shape
```

Use a temporary directory in real checks and compare tensor values, config
values, card metadata, and training/eval mode. This test does not validate Hub
permissions, remote revisions, or server-side card validation.

## Cards and metadata

Cards are Markdown files with an optional YAML frontmatter block followed by a
Markdown body. `RepoCard(content, ignore_metadata_errors=False)` parses the
block and exposes `data`, `text` (body only), and `content` (round-trippable
frontmatter plus body). `RepoCard.load(path)` is local when `path` is a file;
loading an id downloads `README.md` and therefore requires network/auth for
private repos. `card.save(path)` is local and creates parent directories.

The typed card classes are:

- `ModelCard` with `ModelCardData` for model metadata;
- `DatasetCard` with `DatasetCardData` for dataset metadata; and
- `SpaceCard` with `SpaceCardData` for Space title, SDK, app file/port, related
  models/datasets, license, duplication, and tags.

Build typed metadata and a card locally:

```python
from huggingface_hub import ModelCard, ModelCardData

data = ModelCardData(
    language="en", license="apache-2.0", library_name="tiny-lib",
    pipeline_tag="text-classification", tags=["local-check"],
)
card = ModelCard.from_template(
    data, model_id="tiny-local", model_description="A local fixture"
)
card.save("./tmp-tiny/README.md")
```

`from_template` uses Jinja2; install the package providing Jinja2 if it is
missing. `RepoCard.from_template` accepts `card_data`, `template_path` or
`template_str`, plus template variables. For a minimal card, construct a
frontmatter string directly and pass it to `ModelCard` without Jinja.

Card data acts like a small mapping (`get`, `pop`, item access/assignment,
`to_dict`, `to_yaml`). Unknown metadata is retained by `CardData`. `ModelCardData`
normalizes tags and supports base model, datasets, language, license, library,
metrics, pipeline tag, and `eval_results`. `DatasetCardData` serializes its
Python `train_eval_index` attribute as YAML `train-eval-index`. `SpaceCardData`
keeps Space-specific metadata. Do not assume every field is accepted by the Hub
card validator merely because YAML can parse it.

## Evaluation metadata and validation

An `EvalResult` requires `task_type`, `dataset_type`, `dataset_name`,
`metric_type`, and `metric_value`. `model_name` is required when passing
`eval_results` to `ModelCardData`; the data class converts those results to the
Hub `model-index` shape. Use:

```python
from huggingface_hub import EvalResult, ModelCardData

result = EvalResult(
    task_type="text-classification", dataset_type="local-fixture",
    dataset_name="Local fixture", metric_type="accuracy", metric_value=1.0,
)
data = ModelCardData(model_name="tiny-local", eval_results=[result])
assert data.to_dict()["model-index"][0]["results"][0]["metrics"][0]["value"] == 1.0
```

`model_index_to_eval_results` parses a list of model-index entries back into a
model name and `EvalResult` objects. `eval_results_to_model_index` groups
results by task/dataset identity. A `source_name` without `source_url` is
invalid. Malformed model-index metadata raises `ValueError` by default;
`ignore_metadata_errors=True` keeps the card usable but drops invalid
 evaluation data and warns, so record that loss.

`card.validate()` calls the remote Hub YAML validator and therefore is not a
local-only check. Use parsing, `to_dict`, required-field assertions, and a mock
HTTP response for safe verification. `card.push_to_hub(...)` validates then
uploads `README.md`; it supports repo type, revision, PR, parent commit, and
commit message/description options, all of which are remote operations.

## TensorBoard logging

`HFSummaryWriter(repo_id, *, logdir=None, commit_every=5,
squash_history=False, repo_type=None, repo_revision=None, repo_private=None,
path_in_repo="tensorboard", repo_allow_patterns="*.tfevents.*",
repo_ignore_patterns=None, token=None, **kwargs)` is an experimental drop-in
wrapper around a TensorBoard `SummaryWriter`. It writes event files locally,
then asynchronously schedules uploads to the Hub. Construction may create or
read a repo/card, and context exit triggers an upload, so it is not a harmless
local logger. A TensorBoard writer dependency (`tensorboardX` or the
TensorBoard dependency used by `torch.utils.tensorboard`) is required; this
package version has no dedicated TensorBoard extra.

For a practical local check, use the underlying writer without a Hub id:

```python
from pathlib import Path
from tempfile import TemporaryDirectory
from torch.utils.tensorboard import SummaryWriter

with TemporaryDirectory() as tmp:
    writer = SummaryWriter(log_dir=Path(tmp) / "events")
    writer.add_scalar("loss/train", 0.25, 1)
    writer.flush()
    writer.close()
```

`HFSummaryWriter` is different from that local writer. It creates a local event
file, constructs a `CommitScheduler` for `repo_id`, appends the local log
directory name below `path_in_repo` (or uses that name when the path is empty),
and adds an `hf-summary-writer` card tag. The scheduler can upload
asynchronously every `commit_every` minutes; leaving its context calls the
underlying writer exit and waits for a final trigger. Thus construction and
context exit can create/read a repo, push a card, and upload event files. Choose
`repo_type`, `repo_revision`, privacy, allow/ignore patterns, and a finite commit
interval deliberately; use a narrow log directory and never log tokens or
private request data. For a safe integration test, patch `CommitScheduler`,
`ModelCard.load`/`push_to_hub`, and upload calls, or use the plain local
`SummaryWriter`; do not create `HFSummaryWriter` with a real repo merely to
check logging.

The package first tries `tensorboardX.SummaryWriter` and otherwise tries
`torch.utils.tensorboard.SummaryWriter`. Install either `tensorboardX` or the
TensorBoard dependency expected by the installed PyTorch build in the same
environment; this package version has no dedicated `huggingface_hub`
TensorBoard extra. If neither import is available, constructing
`HFSummaryWriter` raises an actionable `ImportError` before the remote
scheduler should be used.
