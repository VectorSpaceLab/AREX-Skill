# Training Workflows

These workflows focus on preparing training inputs and planning safe invocation. They assume BEIR-format data is already loaded into `corpus`, `queries`, and `qrels`. For file schemas and loaders, route to `../data-loading/SKILL.md`.

## 1. No-Download Training Data Smoke Test

Run the bundled helper before adapting a user dataset or debugging a training script:

```bash
python scripts/training_data_smoke.py
python scripts/training_data_smoke.py --exercise-max-corpus-error
```

The helper verifies that BEIR can create pair `InputExample` objects, exposes missing-corpus-id preflight errors, validates triplet tuple shape, constructs a tiny IR evaluator, checks the empty-dev-set error, and optionally exercises the `max_corpus_size` guard. It does not instantiate a transformer model, download weights, or call `fit()`.

## 2. Pair Training from BEIR Qrels

Use when the dataset has relevant query-document pairs and no mined negatives.

```python
from sentence_transformers import SentenceTransformer, losses
from beir.retrieval.train import TrainRetriever

model = SentenceTransformer("sentence-transformers/msmarco-distilbert-base-v3")
retriever = TrainRetriever(model=model, batch_size=16)

train_samples = retriever.load_train(corpus, queries, qrels)
train_dataloader = retriever.prepare_train(train_samples, shuffle=True)
train_loss = losses.MultipleNegativesRankingLoss(model=retriever.model)
```

Preflight checklist:

- Every `qrels` query id exists in `queries`.
- Every positive `qrels` doc id exists in `corpus`.
- Relevant scores are numeric and positives are `>= 1`; score `0` entries are ignored.
- The resulting sample count is nonzero.
- The batch size is large enough for useful in-batch negatives but small enough for available memory.

Example warmup calculation from the BEIR examples:

```python
num_epochs = 1
warmup_steps = int(len(train_samples) * num_epochs / retriever.batch_size * 0.1)
```

## 3. Triplets and Hard Negatives

Use triplets when the user has explicit `(query, positive, negative)` text tuples or can mine hard negatives safely.

```python
triplets = [(query_text, positive_text, negative_text)]
train_samples = retriever.load_train_triplets(triplets)
train_dataloader = retriever.prepare_train_triplets(train_samples)
```

Triplet validation rules:

- Each item must have exactly three strings: query, positive passage, negative passage.
- Do not pass ids to `load_train_triplets`; resolve ids to text first.
- Avoid duplicates inside the same batch when using `NoDuplicatesDataLoader` and multiple-negatives losses.
- Keep source metadata externally if the user needs auditability; BEIR `InputExample` texts do not preserve ids.

Hard-negative sources seen in BEIR examples:

- BM25/Elasticsearch mining over positives, then exclude known positive ids from negatives.
- MS MARCO hard-negative JSONL files with dense, cross-encoder, and lexical systems.
- Cross-encoder score margin filtering where a negative is kept only if it is sufficiently below the positive score.

Route BM25 backend setup and lexical retrieval mechanics to retrieval/evaluation guidance; this sub-skill only owns converting mined negatives into training examples.

## 4. Margin-MSE Distillation Triplets

Use when each triplet has teacher scores for positive and negative passages.

```python
from sentence_transformers import InputExample
from beir.losses import MarginMSELoss

example = InputExample(
    texts=[query_text, positive_text, negative_text],
    label=float(positive_teacher_score) - float(negative_teacher_score),
)
train_loss = MarginMSELoss(model=retriever.model)
```

Validation rules:

- Label is the teacher margin, not a binary relevance label.
- Positive and negative texts must correspond to the scores used in the label.
- The loss implementation computes student dot-product margin; confirm the model and downstream retrieval plan are dot-product-compatible.

## 5. Binary Passage Retriever Training

Use `BPRLoss` only when the user intentionally wants binary-code retriever training.

```python
from beir.losses import BPRLoss
train_loss = BPRLoss(model=retriever.model)
```

Planning notes:

- The BEIR BPR example uses triplets and a pooling setup with CLS pooling.
- `BPRLoss` maintains `global_step` and applies a tanh approximation for binary representations.
- It is a specialized training objective, not the default for ordinary dense retrieval fine-tuning.
- Full BPR training can be long and GPU-sensitive; require a resource plan before starting.

## 6. Dev Evaluator Construction

Use a real dev evaluator when the user has a dev split or held-out validation set:

```python
ir_evaluator = retriever.load_ir_evaluator(dev_corpus, dev_queries, dev_qrels, name="dev")
```

Preflight checklist:

- `dev_queries` is nonempty.
- `dev_qrels` query ids are present in `dev_queries`.
- Positive `dev_qrels` doc ids are present in `dev_corpus`.
- `max_corpus_size`, if set, is at least the number of unique positive dev doc ids.
- The evaluator corpus is small enough for periodic evaluation at the chosen `evaluation_steps` interval.

Use dummy evaluator only when there is no dev split and checkpoint selection by retrieval metric is not required:

```python
ir_evaluator = retriever.load_dummy_evaluator()
```

Record clearly that dummy evaluator scores are not retrieval quality.

## 7. Safe Training Invocation Plan

Before calling `retriever.fit()`, write down the training budget and exit criteria.

Minimum plan fields:

- Dataset name/split and counts: train queries, train positives, triplets, dev queries, dev relevant docs.
- Model source and whether it triggers downloads or credentials.
- Loss, score function, batch size, max sequence length, epochs, warmup steps, and evaluation steps.
- Device expectation: CPU/GPU, mixed precision, and memory estimate.
- Checkpoint directory chosen by the user.
- Resume/overwrite policy for existing output paths.
- Validation command that runs before full training, such as the bundled smoke helper plus a small sample dry run.

Safe invocation shape:

```python
retriever.fit(
    train_objectives=[(train_dataloader, train_loss)],
    evaluator=ir_evaluator,
    epochs=num_epochs,
    output_path=model_save_path,
    warmup_steps=warmup_steps,
    evaluation_steps=evaluation_steps,
    use_amp=use_amp,
)
```

Avoid implying this is quick or offline. BEIR examples download datasets, model weights, and MS MARCO hard-negative files, and they can run for many epochs.

## 8. Post-Training Routing

After a checkpoint exists:

- Route first-stage retrieval and metric evaluation to `../retrieval-evaluation/SKILL.md`.
- Route cross-encoder or second-stage scoring to `../reranking/SKILL.md`.
- Route generated-query training inputs back to `../generation/SKILL.md` for generation provenance and layout checks.
- Keep training checkpoints and experiment logs in user-selected output directories, not inside the generated skill directory.
