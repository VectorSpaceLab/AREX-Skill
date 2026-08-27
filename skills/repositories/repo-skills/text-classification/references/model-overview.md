# Model Family Routing Overview

This repository is a collection of legacy TensorFlow 1.x scripts, not an installable Python package. Use this page to choose the narrowest operating sub-skill before inspecting or adapting code. The model inventory and the historical comparison table come from the repository `README`; architecture details below are cross-checked against the named source files rather than inferred from current TensorFlow APIs.

## Route first

| Task or model family | Route | Repository evidence |
| --- | --- | --- |
| Raw `__label__` text, vocabulary/label dictionaries, HDF5 or pickle caches, adjacent n-grams, prediction TSVs | [data-preparation](../sub-skills/data-preparation/SKILL.md) | `aa1_data_util/data_util_zhihu.py`, `a00_Bert/utils.py`, `pre-processing.ipynb` |
| fastTextB, TextCNN, TextRNN, TextRCNN, Hierarchical Attention Network, BERT, or TFLearn demonstrations | [classification-models](../sub-skills/classification-models/SKILL.md) | `a01_FastText/p6_fastTextB_model_multilabel.py`, `a02_TextCNN/p7_TextCNN_model.py`, `a03_TextRNN/p8_TextRNN_model.py`, `a04_TextRCNN/p71_TextRCNN_model.py`, `a05_HierarchicalAttentionNetwork/p1_HierarchicalAttention_model.py`, `a00_Bert/bert_modeling.py` |
| Seq2seq label generation, Transformer encoder-decoder/classifier, EntityNetwork, Dynamic Memory Network | [sequence-and-memory-models](../sub-skills/sequence-and-memory-models/SKILL.md) | `a06_Seq2seqWithAttention/a1_seq2seq_attention_model.py`, `a07_Transformer/a2_transformer.py`, `a07_Transformer/a2_transformer_classification.py`, `a08_EntityNetwork/a3_entity_network.py`, `a09_DynamicMemoryNet/a8_dynamic_memory_network.py` |
| Paired-text relation models, CNN+RCNN hybrids, per-label boosting, exported-logit fusion and top-k decoding | [relation-and-ensemble-workflows](../sub-skills/relation-and-ensemble-workflows/SKILL.md) | `aa5_BiLstmTextRelation/p9_BiLstmTextRelation_model.py`, `aa6_TwoCNNTextRelation/p9_twoCNNTextRelation_model.py`, `aa4_TextCNN_with_RCNN/p72_TextCNN_with_RCNN_model.py`, `a00_boosting/a08_boosting.py`, `a08_predict_ensemble.py` |

## Family selection

| Family | Data and output contract | Choose it when | Key constraint |
| --- | --- | --- | --- |
| fastTextB | Padded token/ngram ids to dense multi-label logits | You need the smallest order-insensitive baseline and can encode local order as n-grams. | The active multi-label graph uses dense multi-hot labels and sigmoid loss; comments about sampled/NCE paths do not describe that active path. |
| TextCNN | Fixed-length token ids to multi-label logits through parallel convolution and max-pooling | Local phrase features are a strong baseline and documents fit a fixed padded length. | Filter sizes, embedding width, label count, and batch-normalization behavior must agree with the checkpoint. |
| TextRNN / TextRCNN | Ordered token ids to recurrent or recurrent-context representations | Token order or left/right context matters more than a bag-of-ngrams baseline. | Common TextRNN code is single-label; some RCNN tensors bake in `batch_size`, and some model files run tests at import time. |
| Hierarchical Attention Network | A flattened document split into sentence segments, then word- and sentence-level attention | Long input has a meaningful section/sentence hierarchy. | Total sequence length must match the configured sentence split; multiple HAN variants have different heads. |
| BERT | `input_ids`, `input_mask`, and `segment_ids` to a pooled classification head | A compatible TF1 BERT vocabulary/config/checkpoint exists and contextual encoding is required. | The bundled code uses TF1 and `tf.contrib`; the multi-label head uses sigmoid, while the online pair example is a different softmax contract. |
| Seq2seq with attention | Input token sequence to an ordered, fixed-length label-token sequence | Multi-label prediction is deliberately framed as label generation. | `_GO`, `_END`, and `_PAD` placement and shifted decoder targets are part of the model contract. |
| Transformer | Either encoder-decoder generation or a separate encoder-only classifier | Attention-only sequence modeling is the explicit target. | Do not confuse the two source variants; their inputs, losses, and decoding workflows differ. |
| EntityNetwork / Dynamic Memory Network | Story/query-style tensors to memory-conditioned answers or labels | Context tracking, question answering, or explicit memory updates are required. | Input ranks, fixed batch assumptions, hops/episodes, and answer mappings must match the selected source and checkpoint. |
| Relation models / CNN+RCNN hybrid | Two texts, either concatenated with an `EOS` token or supplied as separate tensors, to relation logits | The label depends on a sentence pair or two compatible feature branches. | Establish the pair encoding and branch/logit shapes before adapting training code. |
| Boosting / ensemble | Existing validation or prediction logits to label weights or fused top-k results | Models have already produced aligned logits and only post-processing remains. | Every model must use the same example order, class count, and label-index mapping. This route does not require model import or checkpoint restoration. |
| TFLearn examples | Toy vectors/images/IMDB ids to categorical outputs | You need syntax evidence for the repository's TFLearn-era demonstrations. | Some examples download or expect toy data; they are not a safe smoke test for the main models. |

## Shared operating assumptions

- The `README environment section` names Python 2.7+ and TensorFlow 1.8, with historical claims for TensorFlow 1.1–1.13; the generated skill standardizes safe tooling on Python 3.7-era syntax. Treat those versions as legacy evidence, not a modern compatibility guarantee.
- Direct uses of `tf.Session`, `tf.placeholder`, `tf.app.flags`, and `tf.contrib` occur throughout the source. TensorFlow 2.x plus `tf.compat.v1` does not restore `tf.contrib` and is not a drop-in runtime.
- Full runs depend on external HDF5 caches, vocabulary/label pickles, pretrained embeddings, and checkpoints. Confirm those artifacts and their schemas before building a graph.
- README scores and training times are historical context only. Hardware, data snapshots, preprocessing, dependency versions, and checkpoints are not pinned sufficiently for a reproduction claim.
- Prefer static source inspection, the root [environment smoke check](../scripts/check_legacy_text_classification_env.py), and the narrow sub-skill helper scripts. Do not import every model module: several files contain import-time tests, flag registration, session creation, or other side effects.
