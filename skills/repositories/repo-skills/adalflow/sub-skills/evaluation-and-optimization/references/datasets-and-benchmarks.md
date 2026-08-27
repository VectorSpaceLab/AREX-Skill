# Datasets and benchmarks

AdalFlow includes convenience dataset classes for common optimization examples. They are useful for demos and benchmarking, but most loaders can download external data and require optional packages. For first-pass evaluation or training, prefer user-provided tiny data or loader `size` limits.

## Dataset loader summary

| Loader | Typical task | Constructor shape | Data item | Constraints |
|---|---|---|---|---|
| `GSM8K` | Grade-school math QA | `GSM8K(root=None, split="train", size=None)` | `GSM8KData(id, question, answer, gold_reasoning, reasoning)` | Uses Hugging Face `datasets`; downloads full source data if split cache is missing; official test is large enough to require sampling for quick runs. |
| `TrecDataset` | Question classification | `TrecDataset(root=None, split="train")` | `TrecData(id, question, class_name, class_index)` | Requires optional `torch` and `datasets`; prepares balanced train/val/test CSV splits. Good for exact-label evaluation. |
| `HotPotQA` | Multi-hop QA and retrieval evaluation | `HotPotQA(root=None, split="train", keep_details="dev_titles", size=None, only_hard_examples=True)` | `HotPotQAData(id, question, answer, gold_titles, context)` | Uses Hugging Face `datasets`; fullwiki data is large; keep `size` small for smoke runs. Retrieval gold can use `gold_titles`. |
| `BigBenchHard` | BBH object-counting and related tasks | `BigBenchHard(task_name="object_counting", root=None, split="train")` | `Example(id, question, answer)` | Downloads task JSON from the public BBH repository when missing; default split sizes are train 50, val 100, test 100. |

## Import patterns

```python
from adalflow.datasets import GSM8K, TrecDataset, HotPotQA, BigBenchHard

small_math = GSM8K(split="train", size=5)
example = small_math[0]
print(example.question, example.answer)

small_hotpot = HotPotQA(split="train", size=5, keep_details="dev_titles")
print(small_hotpot[0].gold_titles)

bbh_train = BigBenchHard(task_name="object_counting", split="train")
print(len(bbh_train))  # 50 for the default object-counting split
```

When optional packages or network access are unavailable, do not block skill use. Replace the loader with a tiny in-memory list of dataclass-like objects that expose the same fields (`id`, input, and output/label). `AdalComponent` and metrics only need the fields you read in `prepare_task`, `prepare_eval`, and `prepare_loss`.

## Field mapping by workflow

### Classification with TREC

- Input: `sample.question`.
- Ground truth: `sample.class_name` for exact label scoring, or `sample.class_index` if the task outputs numeric labels.
- Metric: `AnswerMatchAcc(type="exact_match").compute_single_item`.
- Optimization: mark task instructions as `ParameterType.PROMPT`; mark demos as `ParameterType.DEMOS` if using few-shot examples.

### QA with GSM8K or BBH

- Input: `sample.question`.
- Ground truth: `sample.answer`.
- Metric: exact/fuzzy/F1 answer match depending on output format.
- Prompt instruction should require a final answer format so `prepare_eval` can extract a stable answer string.
- For GSM8K, `gold_reasoning` is reference reasoning, not necessarily a required output unless the task is chain-of-thought recovery.

### HotPotQA retrieval and multi-hop QA

- Input: `sample.question`.
- Answer metric: `AnswerMatchAcc(type="fuzzy_match")` or a task-specific answer evaluator.
- Retrieval metric: `RetrieverEvaluator` over `gold_titles`, document IDs, or exact context snippets.
- RAG construction belongs to `retrieval-rag-and-data-pipelines`; this sub-skill covers only how to score and optimize the task once predictions/retrieved contexts exist.

## Download and cache safeguards

Before using bundled loaders, establish:

1. Is network access allowed?
2. Are optional packages installed (`datasets`, and for TREC also `torch`)?
3. Where should dataset cache files be written?
4. What is the maximum number of examples for the first run?
5. Does the user need reproducible shuffling/splitting?

Safe first-run pattern:

```python
# Pseudocode: use a user-approved writable cache root if needed.
train_data = GSM8K(split="train", size=8)
val_data = GSM8K(split="val", size=8)
```

For no-network environments, create synthetic examples:

```python
from dataclasses import dataclass

@dataclass
class TinyExample:
    id: str
    question: str
    answer: str

train_data = [
    TinyExample(id="ex-1", question="2+2?", answer="4"),
    TinyExample(id="ex-2", question="3+5?", answer="8"),
]
```

This is sufficient to validate `prepare_task`, `prepare_eval`, `prepare_loss`, and `Trainer.diagnose` plumbing without benchmark downloads.

## Benchmark constraints

Repository benchmark examples cover larger workflows such as HotPotQA multi-hop RAG optimization, TREC classification training, GSM8K/BBH QA, and `optimize_anything` experiments. Treat these as reference workflows, not default verification commands.

Do not start full benchmark runs unless the user explicitly provides:

- Dataset availability or permission to download.
- Provider/model-client configuration for any live LLM calls.
- Maximum examples, maximum optimizer steps, and worker count.
- Expected wall-clock and cost budget.
- Checkpoint destination and resume policy.

Reduced benchmark recipe:

1. Load or synthesize 2-8 examples.
2. Run a deterministic metric smoke.
3. Run `Trainer.diagnose` with `num_workers=1` if task inference is available.
4. If provider-backed optimization is approved, run `Trainer.fit` with `max_steps=1`, `train_batch_size=1`, tiny `train_dataset`, and tiny `val_dataset`.
5. Inspect score movement and failure logs before increasing scale.

## Dataset troubleshooting quick hits

- `ImportError` for `datasets`: install the optional dataset dependency or use synthetic examples.
- `ImportError` for `torch` while loading TREC: install the torch optional dependency or avoid TREC loader.
- Network timeout or HTTP failure: retry later, use an existing local cache, or switch to synthetic data.
- `ValueError` for split: valid splits are `train`, `val`, and `test`.
- Missing `id` field in custom data: add stable ids before using `Trainer.diagnose` or training callbacks.
- HotPotQA memory/time issue: set `size` small and prefer `keep_details="dev_titles"` unless full contexts are explicitly required.
