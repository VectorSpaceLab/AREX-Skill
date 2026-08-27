# Repository Provenance Snapshot

This file records the checkout against which the `text-classification` repo skill was authored. It is a provenance aid, not a claim that the upstream repository, external datasets, or historical checkpoints are reproducible.

## Checkout identity

| Field | Captured value |
| --- | --- |
| Captured at (UTC) | `2026-08-15T06:24:49Z` |
| Upstream repository | `brightmart/text_classification` |
| Git remote `origin` | `https://github.com/brightmart/text_classification.git` |
| Commit | `091ff9910839ba5053302383af99762c0c91a992` |
| Branch | `master` |
| Skills-scoped dirty state | Dirty/untracked: `git status --short -- skills` returned `?? skills/` |

The commit and branch identify the source snapshot. The dirty-state result means the generated `skills/` tree was not tracked by that commit when this snapshot was taken; therefore, the skill files themselves must not be treated as upstream content. Re-running the same status command after import or commit may legitimately produce a different result.

## Source evidence used by this skill

### Repository-level claims

- `README.md` — stated goals, model inventory, historical performance table, train/predict conventions, legacy TensorFlow environment, cache guidance, raw `__label__` examples, and model descriptions.
- `.travis.yml` — historical continuous-integration/runtime evidence.
- `pre-processing.ipynb` — repository preprocessing workflow evidence.

### Data, caches, and labels

- `aa1_data_util/data_util_zhihu.py` — vocabulary/label construction, raw-data loading, padding-related helpers, adjacent n-grams, and seq2seq label tokens.
- `a00_Bert/utils.py` — HDF5 dataset names and vocabulary/label pickle tuple expectations.
- `data/sample_single_label.txt` and `data/sample_multiple_label.txt` — checked-in raw format examples.

### Classic classifiers

- `a01_FastText/p6_fastTextB_model_multilabel.py`
- `a02_TextCNN/p7_TextCNN_model.py`
- `a03_TextRNN/p8_TextRNN_model.py`
- `a04_TextRCNN/p71_TextRCNN_model.py`
- `a05_HierarchicalAttentionNetwork/p1_HierarchicalAttention_model.py`
- `a00_Bert/bert_modeling.py` and `a00_Bert/train_bert_multi-label.py`
- `aa2_ClassificationTflearn/p2_classification_tflearn.py` and `aa3_CNNSentenceClassificationTflearn/p4_conv_classification_tflearn.py`

### Sequence, memory, relation, and ensemble workflows

- `a06_Seq2seqWithAttention/a1_seq2seq_attention_model.py`
- `a07_Transformer/a2_transformer.py` and `a07_Transformer/a2_transformer_classification.py`
- `a08_EntityNetwork/a3_entity_network.py`
- `a09_DynamicMemoryNet/a8_dynamic_memory_network.py`
- `aa5_BiLstmTextRelation/p9_BiLstmTextRelation_model.py`
- `aa6_TwoCNNTextRelation/p9_twoCNNTextRelation_model.py`
- `aa4_TextCNN_with_RCNN/p72_TextCNN_with_RCNN_model.py`
- `a00_boosting/a08_boosting.py` and `a08_predict_ensemble.py`

## Refresh and staleness procedure

Before reusing this skill for another checkout:

1. Compare `git rev-parse HEAD`, `git branch --show-current`, and `git remote get-url origin` with the values above.
2. Inspect `git status --short -- skills` separately from source changes so generated assets are not mistaken for upstream modifications.
3. Diff the evidence paths above, especially source imports, placeholders, loss functions, cache keys, label tokens, and checkpoint/config flags.
4. Refresh the routing overview and troubleshooting guidance if families were added, removed, renamed, or migrated away from direct TensorFlow 1.x APIs.
5. Re-run the root environment smoke check only when validation is explicitly requested; the provenance snapshot itself does not assert that dependencies are installed.
