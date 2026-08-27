# OA JSONL data formats and safe utilities

Open-Assistant data exports use UTF-8 JSON Lines: one JSON object per line, with file names typically ending in `.jsonl` or `.jsonl.gz`. Objects may be individual messages, linear conversation threads, or full branching message trees.

Use the bundled [`../scripts/oasst_jsonl_tool.py`](../scripts/oasst_jsonl_tool.py) for safe inspection, flattening, filtering, and deterministic splitting. It works with only the Python standard library for basic operations and validates with `oasst_data` when that package is importable.

## Object types

### Individual message object

Identified by a top-level `message_id` field.

Minimal required fields in installed schema checks are `message_id`, `text`, and `role`; practical OA exports usually also include `lang`.

```json
{
  "message_id": "13714ad5-3161-4ead-9593-7248b0a3f218",
  "text": "List the pieces of a reinforcement learning system.",
  "role": "prompter",
  "lang": "en"
}
```

Common optional fields:

| Field | Meaning |
| --- | --- |
| `parent_id` | Parent message id; absent/null for root prompts. |
| `user_id` | Anonymized or backend UUID user id. |
| `created_date` | ISO timestamp. |
| `review_count`, `review_result` | Review status; `review_result: false` is treated as spam/failed review by helper filters. |
| `deleted` | Deleted flag. |
| `rank` | Ranking position. |
| `synthetic` | Whether generated/synthetic content is present. |
| `model_name` | Model name for synthetic/model messages. |
| `emojis` | Aggregate emoji counts. |
| `labels` | Average label values by label name. |
| `events` | Detailed rating/ranking/emoji/report/score events when exported. |
| `message_tree_id`, `tree_state` | Present on flattened tree outputs or message-list exports that preserve tree context. |

### Conversation thread object

Identified by top-level `thread_id` and a `thread` list. `thread_id` is the id of the last message in the linear path. Threads are less central to backend export/import than full trees and flat message lists.

```json
{
  "thread_id": "534c7711-afb5-4410-9006-489dc885280e",
  "thread": [
    {"message_id": "root", "text": "Prompt", "role": "prompter", "lang": "en"},
    {"message_id": "reply", "text": "Answer", "role": "assistant", "lang": "en"}
  ]
}
```

### Message tree object

Identified by top-level `message_tree_id`. In full tree exports, `message_tree_id` matches the root prompt's `message_id`.

```json
{
  "message_tree_id": "14fbb664-a620-45ce-bee4-7c519b16a793",
  "tree_state": "ready_for_export",
  "origin": "optional-origin",
  "prompt": {
    "message_id": "14fbb664-a620-45ce-bee4-7c519b16a793",
    "text": "Why can't we divide by zero?",
    "role": "prompter",
    "lang": "en",
    "replies": [
      {
        "message_id": "894d30b6-56b4-4605-a504-89dd15d4d1c8",
        "text": "Because division asks for a multiplicative inverse.",
        "role": "assistant",
        "lang": "en",
        "replies": []
      }
    ]
  }
}
```

Tree states seen by backend data tooling include:

```text
prompt_lottery_waiting, growing, ready_for_export, aborted_low_grade,
halted_by_moderator, backlog_ranking, ranking
```

## `oasst_data` helper API

When available, `oasst_data` exposes these useful helpers:

| Helper | Behavior |
| --- | --- |
| `read_message_trees(input_file_path)` | Iterate `ExportMessageTree` objects from `.jsonl` or `.jsonl.gz`; asserts every line is a tree. |
| `read_message_tree_list(input_file_path, filter=None)` | Materialize filtered tree list. |
| `read_messages(input_file_path)` | Iterate `ExportMessageNode` objects from a flat message file; asserts every line is a message. |
| `read_message_list(input_file_path, filter=None)` | Materialize filtered message list. |
| `visit_messages_depth_first(node, visitor, predicate=None)` | Visit every node in a tree/subtree depth-first. |
| `visit_threads_depth_first(node, visitor, predicate=None)` | Visit every root-to-node thread depth-first. |
| `write_message_trees(output_file_name, trees, exclude_none)` | Write tree JSONL or JSONL.GZ. |
| `write_messages(output_file_name, messages, exclude_none)` | Write flat messages without nested `replies`. |

Data classes:

- `ExportMessageNode`: message node. Required installed fields: `message_id`, `text`, `role`. Includes optional `parent_id`, `lang`, `review_result`, `deleted`, `rank`, `synthetic`, `model_name`, `emojis`, `replies`, `labels`, `events`, `detoxify`, `message_tree_id`, `tree_state`.
- `ExportMessageTree`: tree wrapper. Required installed field: `message_tree_id`; practical full-tree operations also require a non-null `prompt` node.
- Event models include emoji, rating, ranking, report, and score events.
- `LabelAvgValue(value, count)` represents averaged labels in exports.

## Safe bundled tool recipes

The bundled tool refuses to overwrite output files unless `--overwrite` is supplied.

### Inspect a file

```bash
python scripts/oasst_jsonl_tool.py inspect input.jsonl.gz
python scripts/oasst_jsonl_tool.py inspect input.jsonl --sample 3
```

Expected output is JSON containing object counts, languages, roles, tree states, deleted/spam/synthetic counters, validation status, missing-field counts, and optional sample ids.

### Flatten trees to flat messages

```bash
python scripts/oasst_jsonl_tool.py tree-to-messages trees.jsonl.gz messages.jsonl.gz --exclude-nulls
```

Behavior:

- Reads only tree objects.
- Traverses each `prompt` depth-first.
- Emits one flat message per node.
- Adds/preserves `message_tree_id` and `tree_state` on each output message.
- Removes nested `replies` from flat message output.

### Filter flat messages

```bash
python scripts/oasst_jsonl_tool.py filter-messages messages.jsonl.gz en_ready_messages.jsonl.gz \
  --lang en --state ready_for_export --include-spam --include-synthetic --exclude-nulls
```

Useful filters:

| Filter | Effect |
| --- | --- |
| `--lang en,es` | Keep messages whose `lang` is one of the comma-separated tags. |
| `--state ready_for_export,ranking` | Keep messages with matching `tree_state`. |
| `--role prompter|assistant` | Keep one role. |
| `--prompts-only` | Keep only root messages where `parent_id` is null/missing. |
| `--include-deleted` / `--deleted-only` | Default excludes deleted messages; these widen or narrow deletion behavior. |
| `--include-spam` / `--spam-only` | Default excludes `review_result: false`; `--spam-only` keeps only failed-review messages. |
| `--include-synthetic` / `--synthetic-only` | Default excludes `synthetic: true`; these widen or narrow synthetic behavior. |
| `--text-contains STR` | Case-insensitive substring filter over message text. |
| `--flatten-trees` | If the input contains tree objects, flatten them before filtering. |

### Filter full trees

```bash
python scripts/oasst_jsonl_tool.py filter-trees trees.jsonl.gz ready_en_trees.jsonl.gz \
  --states ready_for_export --lang en --exclude-nulls
```

Behavior:

- Default `--states ready_for_export` matches the backend's common export target.
- `--states all` disables tree-state filtering.
- By default, trees containing any `synthetic: true` message are excluded; pass `--allow-synthetic` to keep them.
- `--min-messages` and `--max-messages` filter by depth-first message count.

### Deterministically split a flat message dataset

```bash
python scripts/oasst_jsonl_tool.py split-messages messages.jsonl.gz \
  --train-output train.jsonl.gz --val-output val.jsonl.gz --val-percent 5 --seed 13
```

Behavior:

- Groups by `message_tree_id` so messages from the same tree stay in the same split.
- Uses a deterministic PRNG seed.
- Fails if any message lacks `message_tree_id` unless `--fallback-id` is passed.

## Equivalent Python snippets

### Read and traverse full trees

```python
from oasst_data import read_message_trees, visit_messages_depth_first

for tree in read_message_trees("trees.jsonl.gz"):
    messages = []
    visit_messages_depth_first(tree.prompt, messages.append)
    print(tree.message_tree_id, tree.tree_state, len(messages))
```

### Flatten one tree to messages

```python
from oasst_data import read_message_trees, visit_messages_depth_first, write_messages

messages = []
for tree in read_message_trees("trees.jsonl.gz"):
    def add_context(msg):
        msg.message_tree_id = tree.message_tree_id
        msg.tree_state = tree.tree_state
        messages.append(msg)
    visit_messages_depth_first(tree.prompt, add_context)

write_messages("messages.jsonl.gz", messages, exclude_none=True)
```

### Filter messages with a predicate

```python
from oasst_data import read_message_list, write_messages

def keep(msg):
    return (
        msg.lang == "en"
        and msg.tree_state == "ready_for_export"
        and not msg.deleted
        and msg.review_result is not False
        and not msg.synthetic
    )

messages = read_message_list("messages.jsonl.gz", keep)
write_messages("filtered.jsonl.gz", messages, exclude_none=True)
```

### Depth-first threads ending in assistant replies

```python
from oasst_data import read_message_trees, visit_threads_depth_first

threads = []
for tree in read_message_trees("trees.jsonl.gz"):
    visit_threads_depth_first(
        tree.prompt,
        threads.append,
        predicate=lambda thread: thread[-1].role == "assistant",
    )
```

## Export/import relationship to backend DB

- Backend export can write either full tree objects or flat message objects depending on filters.
- Exports filtered by user, deleted, spam, synthetic, or review result may not contain complete trees; treat them as flat message files.
- Full tree imports expect tree objects whose prompt id matches `message_tree_id` and creates backend message/tree rows under an import API client and system import user.
- DB import is mutating unless dry-run rollback is explicitly enabled; keep that operation in backend workflow planning, not in the safe JSONL helper.

## Validation and common schema pitfalls

- Unknown JSONL line: no `message_id`, `message_tree_id`, or `thread_id`.
- Tree line has `message_tree_id` but missing/null `prompt`, so it cannot be flattened.
- Flat message lacks `message_id`; every safe operation treats this as invalid.
- Split by tree fails when flat messages lack `message_tree_id`; first flatten full trees or pass `--fallback-id` only when per-message split is acceptable.
- `review_result: false` is failed review/spam for filter semantics; missing/null review result is not considered spam by the bundled tool.
- `deleted` and `synthetic` default to false when missing for filtering purposes.
