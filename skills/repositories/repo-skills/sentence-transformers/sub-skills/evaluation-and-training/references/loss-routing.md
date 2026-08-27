# Loss Routing

Choose the loss from the model type and row shape. When row shape and target model disagree, reshape the dataset or mine hard negatives before training.

## Dense `SentenceTransformer` losses

Import dense losses from `sentence_transformers.sentence_transformer.losses`.

| Data shape | Labels | Recommended route |
| --- | --- | --- |
| Single text | class label | Batch triplet family: `BatchAllTripletLoss`, `BatchHardTripletLoss`, `BatchSemiHardTripletLoss`; use `BatchSamplers.GROUP_BY_LABEL` |
| Single text | none | `ContrastiveTensionLoss` or `DenoisingAutoEncoderLoss` for specialized unsupervised setups |
| `(anchor, positive)` | none | `MultipleNegativesRankingLoss` or `CachedMultipleNegativesRankingLoss`; use `BatchSamplers.NO_DUPLICATES` |
| `(anchor, positive, negative)` | none | `MultipleNegativesRankingLoss`, cached MNRL, `TripletLoss`, or GIST variants |
| `(anchor, positive, negative_1, ...)` | none | `MultipleNegativesRankingLoss`, cached MNRL, or GIST variants |
| `(input_a, input_b)` | class label | `SoftmaxLoss` |
| `(input_a, input_b)` | binary label | `ContrastiveLoss` or `OnlineContrastiveLoss` |
| `(input_a, input_b)` | float similarity | `CoSENTLoss`, `AnglELoss`, or `CosineSimilarityLoss` |
| teacher embeddings | embedding vector labels | `MSELoss` or `EmbedDistillLoss` |
| teacher score margins | margin labels | `MarginMSELoss` |
| logits / teacher distributions | score-list labels | `DistillKLDivLoss` or `MarginMSELoss` |

Common defaults:

- Retrieval with positive pairs: `MultipleNegativesRankingLoss` plus `BatchSamplers.NO_DUPLICATES`.
- Need larger effective batch without more memory: `CachedMultipleNegativesRankingLoss`; do not combine cached losses with `gradient_checkpointing=True`.
- STS-style scores: prefer `CoSENTLoss` or `AnglELoss`; normalize scores to `[0, 1]` only when the selected loss requires that scale, such as `CosineSimilarityLoss`.
- Matryoshka embeddings: wrap the base loss in `MatryoshkaLoss`, `Matryoshka2dLoss`, or `AdaptiveLayerLoss` only after the base data/loss route is correct.

## `CrossEncoder` losses

Import cross-encoder losses from `sentence_transformers.cross_encoder.losses`.

| Data shape | Labels | `num_labels` | Recommended route |
| --- | --- | --- | --- |
| `(input_a, input_b)` | class label | number of classes | `CrossEntropyLoss` |
| `(anchor, positive)` | none | `1` | `MultipleNegativesRankingLoss` or cached variant |
| `(anchor, positive/negative)` | `1` for positive, `0` for negative | `1` | `BinaryCrossEntropyLoss` |
| `(input_a, input_b)` | float similarity in `[0, 1]` | `1` | `BinaryCrossEntropyLoss` |
| `(anchor, positive, negative)` | none | `1` | `MultipleNegativesRankingLoss` or cached variant |
| `(anchor, positive, negative_1, ...)` | none | `1` | `MultipleNegativesRankingLoss` or cached variant |
| `(query, [doc1, doc2, ...])` | `[score1, score2, ...]` | `1` | `LambdaLoss`, `PListMLELoss`, `ListNetLoss`, `RankNetLoss`, `ListMLELoss`, or `ADRMSELoss` |
| pair or list data | teacher scores/margins | `1` | `MSELoss` or `MarginMSELoss` |

Pair dataset for reranker decision:

- If rows are positive/negative pairs with binary labels, choose `BinaryCrossEntropyLoss`, `CrossEncoder(num_labels=1)`, and evaluate with `CrossEncoderClassificationEvaluator` or reranking evaluator if candidates are available.
- If rows are only `(query, positive)` pairs, mine hard negatives. Use `output_format="labeled-pair"` for BCE or `output_format="labeled-list"` for listwise ranking.
- If rows contain candidate lists per query with graded labels, use a listwise loss such as `LambdaLoss`; evaluate with `CrossEncoderRerankingEvaluator` or `CrossEncoderNanoBEIREvaluator`.
- For distillation/listwise/pairwise losses that operate on raw ranking scores, construct the model with an identity activation. Keep the default sigmoid-style behavior only for BCE-style training.

## `SparseEncoder` losses

Import sparse losses from `sentence_transformers.sparse_encoder.losses`.

Sparse retrieval has two decisions: the inner task loss and the sparsity wrapper.

| Data shape | Labels | Inner loss | Wrapper / route |
| --- | --- | --- | --- |
| `(anchor, positive)` | none | `SparseMultipleNegativesRankingLoss` | `SpladeLoss` for SPLADE, `CachedSpladeLoss` for GradCache, or `CSRLoss` for sparse autoencoders |
| `(anchor, positive, negative)` | none | `SparseMultipleNegativesRankingLoss` or `SparseTripletLoss` | Usually `SpladeLoss` |
| `(anchor, positive, negative_1, ...)` | none | `SparseMultipleNegativesRankingLoss` | Usually `SpladeLoss` |
| `(input_a, input_b)` | float similarity | `SparseCoSENTLoss`, `SparseAnglELoss`, or `SparseCosineSimilarityLoss` | Use with sparse model; add SPLADE regularization when appropriate |
| text inputs | sparse teacher embeddings | `SparseMSELoss` | Can be used independently for embedding-level distillation |
| query-positive-negative | teacher score margins | `SparseMarginMSELoss` | Wrap in `SpladeLoss` for SPLADE |
| query-positive-negatives | teacher distributions | `SparseDistillKLDivLoss` or `SparseMarginMSELoss` | Wrap in `SpladeLoss` for SPLADE |

For SPLADE-style models, do not train with only `SparseMultipleNegativesRankingLoss` unless you intentionally want no FLOPS regularization. Use:

```python
inner = SparseMultipleNegativesRankingLoss(model)
loss = SpladeLoss(
    model=model,
    loss=inner,
    query_regularizer_weight=5e-5,
    document_regularizer_weight=3e-5,
)
```

`SpladeLoss` uses FLOPS-style regularization to keep sparse vectors sparse. `FlopsLoss` is the regularizer concept; most training workflows access it through `SpladeLoss` rather than as a standalone main loss. Track active dimensions in the sparse evaluator and tune regularizer weights if query/document vectors become too dense.

## Hard-negative routing

Use `sentence_transformers.util.mine_hard_negatives` when positive pairs need negatives or ranked lists:

| Desired training shape | `output_format` |
| --- | --- |
| `(anchor, positive, negative)` | `triplet` |
| `(anchor, positive, negative_1, ...)` | `n-tuple` |
| `(anchor, document, label)` | `labeled-pair` |
| `(anchor, [doc1, ...], [label1, ...])` | `labeled-list` |

Filtering false negatives is often more important than adding many negatives. Use a cross-encoder filter, `max_score`, `relative_margin`, or `absolute_margin` when candidate negatives may actually be relevant.

## Sampler requirements

- MNRL, sparse MNRL, cached MNRL, and GIST-style losses: `BatchSamplers.NO_DUPLICATES`.
- Batch triplet losses: `BatchSamplers.GROUP_BY_LABEL`.
- Very large duplicate-checking workloads: consider `BatchSamplers.NO_DUPLICATES_HASHED`.
- Multi-dataset training: choose `MultiDatasetBatchSamplers.PROPORTIONAL` or `ROUND_ROBIN` based on desired dataset contribution.

## Routing examples

### Reranker pair dataset

User gives `(query, passage, label)` with `label` 0/1 for a reranker.

- Model: `CrossEncoder(..., num_labels=1)`.
- Loss: `BinaryCrossEntropyLoss`.
- Evaluator: `CrossEncoderClassificationEvaluator` for pair AP/F1, or `CrossEncoderRerankingEvaluator` if candidate lists/qrels are available.
- Add early stopping and compare against baseline evaluator score.

If the same user instead gives query plus candidate lists and graded labels, route to a listwise loss such as `LambdaLoss` and a reranking evaluator.

### Sparse SPLADE training plan

User gives `(query, positive)` pairs for learned sparse retrieval.

- Model: `SparseEncoder` initialized from a fill-mask/SPLADE-compatible checkpoint.
- Inner loss: `SparseMultipleNegativesRankingLoss`.
- Wrapper: `SpladeLoss` with query/document regularizer weights.
- Sampler: `BatchSamplers.NO_DUPLICATES`.
- Evaluator: `SparseNanoBEIREvaluator` or `SparseInformationRetrievalEvaluator`.
- Monitoring: nDCG/MRR plus `query_active_dims` and `document_active_dims`.

If active dimensions climb into the thousands, increase FLOPS regularization or review whether `SpladeLoss` is actually wrapping the inner loss.
