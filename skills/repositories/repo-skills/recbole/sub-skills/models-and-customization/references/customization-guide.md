# Customization Guide

Use this guide to sketch or diagnose custom RecBole components at operating
level. Training execution, evaluation runs, HPO, checkpointing, and case-study
analysis belong to the sibling `training-evaluation-and-tuning` sub-skill.
Atomic schema and config validation belong to `configuration-and-data`.

## Custom Model Contract

All ordinary custom RecBole models should:

1. Subclass the base recommender that matches the task family.
2. Set `input_type` to `InputType.POINTWISE` or `InputType.PAIRWISE` unless the
   model has a deliberately different advanced contract.
3. Implement `__init__(self, config, dataset)` and call `super().__init__(config,
   dataset)`.
4. Read hyperparameters from `config`.
5. Implement `calculate_loss(self, interaction)` returning a scalar tensor.
6. Implement `predict(self, interaction)` returning one score per requested
   user-item (or equivalent) pair.
7. Optionally implement `full_sort_predict(self, interaction)` for efficient
   full-ranking evaluation.

Base recommender signatures and inherited fields:

| Base class | Use for | Constructor | Important inherited fields |
|---|---|---|---|
| `GeneralRecommender` | CF/top-N from interactions | `(config, dataset)` | `USER_ID`, `ITEM_ID`, `NEG_ITEM_ID`, `n_users`, `n_items`, `device` |
| `SequentialRecommender` | next-item/session history | `(config, dataset)` | `ITEM_SEQ`, `ITEM_SEQ_LEN`, `POS_ITEM_ID`, `NEG_ITEM_ID`, `max_seq_length`, `n_items`, `device`, `gather_indexes()` |
| `ContextRecommender` | CTR and side features | `(config, dataset)` | `LABEL`, feature field groups, `concat_embed_input_fields()`, `first_order_linear`, `device` |
| `KnowledgeRecommender` | KG-enhanced recommendation | `(config, dataset)` | user/item fields plus `ENTITY_ID`, `RELATION_ID`, head/tail entity fields, counts for users/items/entities/relations, `device` |

### Choosing `input_type`

- `InputType.POINTWISE`: the dataloader supplies item and label-style fields.
  Use for binary classification, CTR, rating/value losses, or CE-style
  objectives.
- `InputType.PAIRWISE`: the dataloader supplies positive and negative item
  fields, commonly `ITEM_ID` and `NEG_PREFIX + ITEM_ID`. Use `BPRLoss` or a
  task-appropriate pairwise ranking loss.

If `input_type` is absent, RecBole may infer input from `loss_type` for some
built-ins, but custom models should set it explicitly to avoid configuration
errors.

## Minimal Pairwise General Model Pattern

```python
import torch
import torch.nn as nn

from recbole.model.abstract_recommender import GeneralRecommender
from recbole.model.init import xavier_normal_initialization
from recbole.model.loss import BPRLoss
from recbole.utils import InputType


class NewGeneralMF(GeneralRecommender):
    input_type = InputType.PAIRWISE

    def __init__(self, config, dataset):
        super().__init__(config, dataset)
        self.embedding_size = config["embedding_size"]
        self.user_embedding = nn.Embedding(self.n_users, self.embedding_size)
        self.item_embedding = nn.Embedding(self.n_items, self.embedding_size)
        self.loss = BPRLoss()
        self.apply(xavier_normal_initialization)

    def forward(self, user, item):
        user_e = self.user_embedding(user)
        item_e = self.item_embedding(item)
        return torch.mul(user_e, item_e).sum(dim=1)

    def calculate_loss(self, interaction):
        user = interaction[self.USER_ID]
        pos_item = interaction[self.ITEM_ID]
        neg_item = interaction[self.NEG_ITEM_ID]
        pos_score = self.forward(user, pos_item)
        neg_score = self.forward(user, neg_item)
        return self.loss(pos_score, neg_score)

    def predict(self, interaction):
        return self.forward(interaction[self.USER_ID], interaction[self.ITEM_ID])

    def full_sort_predict(self, interaction):
        user = interaction[self.USER_ID]
        user_e = self.user_embedding(user)
        scores = torch.matmul(user_e, self.item_embedding.weight.transpose(0, 1))
        return scores.view(-1)
```

Use this pattern for BPR-like models. For pointwise models, replace the pairwise
negative-item branch with a label loss such as BCE/CE and read `interaction`'s
label field.

## Family-Specific Notes

### Sequential custom models

Subclass `SequentialRecommender`. Read `interaction[self.ITEM_SEQ]` and
`interaction[self.ITEM_SEQ_LEN]`, encode the sequence, and score the target item
or all items. Use `self.gather_indexes(sequence_output, item_seq_len - 1)` for
last-position pooling when appropriate. If `loss_type` is configurable, make the
negative-sampling contract match it: `CE` normally needs no train negative
sampling; `BPR` needs pairwise negatives.

### Context-aware / CTR custom models

Subclass `ContextRecommender`. Use `self.concat_embed_input_fields(interaction)`
for dense+sparse feature embeddings and `self.first_order_linear(interaction)`
for first-order terms. The label is `interaction[self.LABEL]`. CTR losses are
usually pointwise, and `predict()` commonly applies a sigmoid to logits.

A CTR request with side features should load those features through `.inter`,
`.user`, and/or `.item` config. If the custom model cannot see a feature, check
`load_col`, feature type declarations, and dataset files via
`configuration-and-data` before changing model code.

### Knowledge-aware custom models

Subclass `KnowledgeRecommender` when the model uses `.kg` and `.link`. Use the
inherited entity and relation field names instead of hard-coded column names.
Many KG models need both recommendation loss and KG-specific loss. If the model
uses graph libraries or sparse operations, declare optional dependency and GPU
memory assumptions in the run plan.

## Registering Or Running A Custom Model

For a project-local model, the most robust path is to import the class and pass
it directly to RecBole config or construction code, for example
`Config(model=NewGeneralMF, dataset=...)`. Do not expect
`get_model('NewGeneralMF')` to find an arbitrary local file.

Use string resolution only when the model is installed where RecBole searches,
with a lower-case module filename and an exact class name. If the model needs
new default hyperparameters, provide them through config or a package-visible
model-property YAML. Missing YAML defaults are a common cause of constructor
`KeyError`.

## Trainer Extension

Use a custom trainer when the model's optimization or evaluation loop differs
from the default, for example:

- alternating multiple losses by epoch or batch;
- special pretraining/finetuning stages;
- custom optimizer parameter groups or layer-specific learning rates;
- mixed precision or gradient-scaling policy;
- model-specific evaluation, checkpoint, or early-stopping behavior.

Typical extension points are `fit`, `evaluate`, `_train_epoch`, `_valid_epoch`,
and `_build_optimizer` on `Trainer`. If using automatic trainer resolution, name
the class `<ModelName>Trainer`; otherwise instantiate the trainer explicitly.
After the design is clear, route actual fitting and evaluation to
`training-evaluation-and-tuning`.

## Dataloader Extension

Customize a dataloader only when the model needs a different batch structure
than RecBole's standard train/eval loaders. Useful cases include user-only
batches, extra aligned tensors, pair construction that standard negative
sampling cannot express, or a model-specific pretraining batch.

Operating contract:

- inherit `AbstractDataLoader` or `NegSampleDataLoader`, or extend an existing
  concrete dataloader;
- implement batch-size/step initialization, end pointer, shuffle behavior, and
  next-batch/collate behavior as required by the chosen base;
- return `Interaction` objects with the exact fields the model's
  `calculate_loss` and `predict` methods read;
- for negative sampling, keep the `InputType` contract aligned with the model.

Test strategy: instantiate config+dataset, create one loader, pull one batch,
and assert that required keys, shapes, dtypes, and device moves are valid before
running training.

## Sampler Extension

Customize a sampler when the default uniform or popularity-biased negative
sampling cannot express the negative policy. Inherit `AbstractSampler` or a
nearby concrete sampler and define:

- `_uni_sampling(sample_num)` for uniform candidate draws;
- `_get_candidates_list()` for popularity-biased candidate counts;
- `get_used_ids()` so known positives are never sampled as negatives;
- a public sampling method such as `sample_by_user_ids` or
  `sample_by_entity_ids` that calls `sample_by_key_ids`.

Test strategy: use a tiny synthetic interaction/KG set, sample repeatedly, and
assert that positives and padding ids are excluded for each key.

## Metric Extension

Use a custom metric when the evaluator must report a new ranking or value
measure. A metric class should inherit `AbstractMetric` or a suitable base and
set:

- `metric_need`: required collector inputs such as `rec.items`, `rec.topk`,
  `rec.meanrank`, `rec.score`, `data.num_items`, `data.num_users`,
  `data.count_items`, `data.count_users`, or `data.label`;
- `metric_type`: `EvaluatorType.RANKING` or `EvaluatorType.VALUE`;
- `smaller`: `True` only when lower is better;
- `calculate_metric(self, dataobject)`: returns a dictionary whose keys are
  lower-case metric names, optionally with `@k` suffixes.

Because RecBole collects metric classes from its metric module at import time,
custom metric registration must be planned with the run entry point. If a metric
name is not found, diagnose registration/import first, then route any execution
check to `training-evaluation-and-tuning`.
