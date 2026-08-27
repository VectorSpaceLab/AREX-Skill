# IXC-2.5-Reward API Reference

This reference distills the IXC-2.5-Reward quickstart and reward benchmark scripts into a self-contained operating contract. It describes call shapes only; this sub-skill does not load the 7B model or run CUDA inference.

## Model loading pattern

The reward model is loaded through Hugging Face Transformers with repository-provided remote code:

```python
import torch
from transformers import AutoModel, AutoTokenizer

model_id = "internlm/internlm-xcomposer2d5-7b-reward"
model = AutoModel.from_pretrained(
    model_id,
    device_map="cuda",
    torch_dtype=torch.float16,
    trust_remote_code=True,
)
tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
model.tokenizer = tokenizer
```

Operational prerequisites:

- Python 3.8+, PyTorch 1.12+ with CUDA 11.4+ recommended; PyTorch 2.x is preferred by the training docs.
- `trust_remote_code=True` is required because scoring methods are provided by the model code, not by a standard Transformers class.
- Use `torch.autocast(device_type="cuda", dtype=torch.float16)` around scoring calls on CUDA hosts.
- The source quickstart uses `hd_num=9` for image reward scoring. Higher `hd_num` increases high-resolution image tiling and VRAM use.

## Chat and image inputs

IXC-2.5-Reward inference uses a chat schema different from the training-data schema:

| Context | Message keys | Example role values | Notes |
| --- | --- | --- | --- |
| API scoring/evaluation | `role`, `content` | `user`, `assistant` | Used by `get_score`, `get_scores`, `compare`, and `rank`. |
| Preference training data | `from`, `value` | `human`, `user`, `bot`, `assistant`, `system` | See `data-formats.md`; do not pass this schema directly to inference methods. |

A single chat is a list of messages, normally a user prompt followed by one assistant response:

```python
chat = [
    {"role": "user", "content": "Describe the receipt in JSON."},
    {"role": "assistant", "content": "{...}"},
]
```

Images are passed as a list of path strings for one chat. For text-only calls, the benchmark scripts pass an empty list for each sample.

```python
single_image = ["/data/receipt.jpg"]
text_only = []
batch_images = [single_image, single_image]  # aligned with a two-chat batch
text_batch_images = [[]] * 2
```

For multi-image tasks, keep the API image argument as one nested list per candidate chat, for example `[["a.jpg", "b.jpg"], ["a.jpg", "b.jpg"]]`. Preserve the same image-list nesting across all responses that answer the same prompt.

## Scoring methods

### `get_score(chat, image, ..., hd_num=9)`

Scores one chat/image pair and returns a numeric reward. Higher is better.

```python
with torch.autocast(device_type="cuda", dtype=torch.float16):
    score = model.get_score(chat, ["/data/image.jpg"], hd_num=9)
```

Use this for one-off absolute scoring. If comparing candidates, prefer `get_scores`, `compare`, or `rank` so the batch shape and ordering are explicit.

### `get_scores(chats, images, max_length=..., hd_num=...)`

Scores a batch of chats and returns a list of floats aligned with input order.

```python
with torch.autocast(device_type="cuda", dtype=torch.float16):
    scores = model.get_scores([chat_a, chat_b], [["/data/image.jpg"], ["/data/image.jpg"]], hd_num=9)
```

Text-only RewardBench/RM-Bench evaluation uses empty image lists:

```python
scores = model.get_scores([chat_chosen, chat_rejected], [[]] * 2)
```

RM-Bench source code passes `max_length=16384` and `hd_num=9` positionally when scoring six text-only candidates. If you render your own code, prefer keywords when the remote model version supports them to avoid positional ambiguity.

### `compare(chat_a, image_a, chat_b, image_b, ..., hd_num=9)`

Compares two candidate chats and returns `True` when the first chat scores higher than the second.

```python
with torch.autocast(device_type="cuda", dtype=torch.float16):
    is_a_better = model.compare(chat_a, image, chat_b, image, hd_num=9)
```

Use this for pairwise decisions when only the boolean ordering matters. If you also need margins or audit logs, call `get_scores` and record both score values.

### `rank(chats, images, max_length=..., hd_num=...)`

Ranks multiple candidate chats. The model returns one rank label per input chat; lower rank index means a better response, and the highest-scoring chat receives rank `0`.

```python
with torch.autocast(device_type="cuda", dtype=torch.float16):
    ranks = model.rank([chat_a, chat_b], [image, image], hd_num=9)
# Example from source README: [0, 1] means chat_a outranks chat_b.
```

VL-RewardBench uses `rank` with two responses and image lists, then compares the returned rank labels to the benchmark `human_ranking` field. Do not treat the return value as a sorted list of candidate ids unless you have verified that behavior for the exact remote-code revision.

## Recommended planning patterns

### Pairwise visual answer preference

1. Build two chats with identical user prompt and different assistant responses.
2. Use the same image list for both candidates.
3. Score via `get_scores` or `compare`.
4. Interpret higher score, `compare=True`, or lower rank index as better.

### Multi-candidate ranking with one image

```python
chats = [chat_0, chat_1, chat_2]
images = [["/data/query.jpg"] for _ in chats]
ranks = model.rank(chats, images, hd_num=9)
```

Check that `len(chats) == len(images)` and that every nested image list preserves the same order. This avoids the common mistake of passing one flat image list for a whole candidate batch.

### Text-only benchmark scoring

```python
chats = [chosen_chat, rejected_chat]
images = [[] for _ in chats]
scores = model.get_scores(chats, images)
correct = scores[0] > scores[1]
```

Use this shape for RewardBench-style prompt/chosen/rejected rows. Passing `None` or omitting the image argument is not what the source evaluation scripts demonstrate.

## Result interpretation

- Reward scores are relative model outputs; the source examples show positive and negative values. Do not compare raw scores across unrelated tasks as calibrated probabilities.
- Pairwise benchmark correctness is normally `score_chosen > score_rejected`.
- For ranking outputs, lower index means better; `0` is best.
- Record model id/path, `hd_num`, `max_length`, dtype, and image preprocessing assumptions with every reported score.
