# Model overview

DeepKE's classic supervised stack is organized by task first, then by scenario. Each scenario combines data tooling, a model family, and training/prediction runtime code. Use this overview to choose the smallest adequate model family before editing configs or running entrypoints.

## Package/import layout

The import roots verified for the supervised scope are:

| Import root | Owns |
| --- | --- |
| `deepke.name_entity_re.standard` | Standard NER, including BERT and BiLSTM-CRF support. |
| `deepke.name_entity_re.few_shot` | LightNER-style few-shot NER. |
| `deepke.name_entity_re.multimodal` | IFAformer-style multimodal NER. |
| `deepke.name_entity_re.cross` | CP-NER-style cross-domain NER. |
| `deepke.relation_extraction.standard` | Standard sentence-level RE. |
| `deepke.relation_extraction.few_shot` | KnowPrompt-style few-shot RE. |
| `deepke.relation_extraction.document` | DocuNet-style document-level RE. |
| `deepke.relation_extraction.multimodal` | IFAformer-style multimodal RE. |
| `deepke.attribution_extraction.standard` | Standard AE. |
| `deepke.event_extraction.standard` | Standard EE trigger/role extraction. |
| `deepke.transform_data` | Shared data conversion helpers used before supervised training; route operational conversion tasks to the sibling data-preparation skill. |

## Scenario table

| Task | Scenario | Core model families | Typical data | Main config selectors | Best for | Main limitation |
| --- | --- | --- | --- | --- | --- | --- |
| NER | Standard | BERT, BiLSTM-CRF, W2NER | BIO `txt`; prepared `json`/`docx` converted to BIO | `hydra/model`, `labels`, `lan`, BERT/BiLSTM model YAML | General entity extraction with normal labels | Needs quality BIO labels; BERT/W2NER need compatible model/checkpoint assets. |
| NER | Few-shot | LightNER / BART prompt tuning | CoNLL/MIT/ATIS k-shot text splits | `+train=few_shot`, `bart_name`, `dataset_name`, `load_path` | Low-resource entity extraction | Large PLM dependency; prediction requires trained/tuned path. |
| NER | Cross-domain | CP-NER / T5 prefix tuning | Per-domain JSON plus schema files | `hydra/run=*`, `source_prefix_path`, `target_prefix_path`, `multi_source_path` | Transfer from source domains to target domains | Complex multi-stage prefix management; usually not a quick CPU workflow. |
| NER | Multimodal | IFAformer, BERT text encoder, CLIP/Vision Transformer | CoNLL text plus images, RCNN objects, visual grounding | `bert_name`, `vit_name`, `dataset_name`, `max_seq`, `aux_size`, `rcnn_size` | Entity extraction where image context helps | Requires aligned visual assets and CLIP-compatible dependencies. |
| RE | Standard | CNN, RNN, Capsule, GCN, Transformer, LM/BERT | CSV/JSON/XLSX converted to split CSV plus `relation.csv` | `model`, `lm_file`, `num_relations`, `predict.fp` | Sentence-level relation classification between known entity pair | Head/tail offsets and relation inventory must be consistent. |
| RE | Few-shot | KnowPrompt / BERT masked LM prompt tuning | SEMEVAL/Wiki-style text plus `rel2id.json` | `data_dir`, `model_name_or_path`, `model_class`, `litmodel_class`, `train_from_saved_model` | Low-resource relation extraction | Sensitive to PyTorch Lightning and prompt-label setup. |
| RE | Document | DocuNet / RoBERTa-style encoder + U-Net blocks | DocRED-style JSON and relation metadata | `dataset`, `num_class`, `max_seq_length`, `train_file`, `load_path` | Relations requiring document context | Memory-heavy; long documents may truncate. |
| RE | Multimodal | IFAformer, BERT, CLIP/Vision Transformer | MNRE-style text/image/object folders | `bert_name`, `vit_name`, `max_seq`, `aux_size`, `rcnn_size`, `load_path` | Visual-enhanced relation extraction | Requires image/object alignment and GPU-preferred runtime. |
| AE | Standard | CNN, RNN, Capsule, GCN, Transformer, LM/BERT | CSV/JSON/XLSX converted to split CSV plus `attribute.csv` | `model`, `lm_file`, `num_attributes`, `predict.fp` | Attribute/value extraction for entities | Same offset/label pitfalls as RE, with attribute inventory. |
| EE | Standard | BERT-CRF trigger and role extraction | ACE/DuEE trigger, role, and schema folders | `data_name`, `task_name`, `model_name_or_path`, trigger prediction files | Event detection and argument extraction | Two-stage pipeline; role prediction depends on trigger outputs. |
| EE | DEGREE variant | DEGREE-style generative/event extraction workflow | ACE-derived processed data | DEGREE-specific config and `e2e_model` | Research-oriented event extraction variant | Treat as dependency- and data-prep-sensitive, not a first smoke path. |
| NER/RE | cnSchema quick-load | Off-the-shelf Chinese NER and RE checkpoints | cnSchema-compatible text and checkpoints | NER model selector, RE `predict.fp`, `num_relations: 51` | Chinese NER/RE without training | Only covers the released cnSchema inventory. |

## Choosing standard versus variants

### Choose standard when

- You have enough labeled data for train/dev/test.
- The task is sentence- or sequence-level and does not require image or document context.
- You want the simplest debug surface and the broadest model-family choices.
- You need cnSchema quick-load for Chinese NER/RE and have downloaded the matching checkpoints.

### Choose few-shot when

- Labels are scarce and the user expects prompt-based adaptation.
- A BART/BERT-style PLM is available locally or remote downloads are approved.
- The acceptance target is a small-label experiment rather than a production baseline.

### Choose multimodal when

- The text alone is ambiguous and each instance has a stable image id.
- RCNN-detected objects and visual-grounding objects are already prepared.
- CLIP/Vision Transformer assets are local or download permission exists.

### Choose document-level RE when

- Relation evidence spans multiple sentences or entity mentions.
- Data is DocRED-like with entity mentions, relation metadata, and document tokens.
- GPU/memory budget can handle long sequences.

### Choose cross-domain NER when

- There are source and target domains with separate schema files.
- The goal is domain transfer through prefix tuning rather than ordinary fine-tuning.
- The user can manage source/target prefix artifacts explicitly.

## Model-family notes

### NER standard

- **BERT**: strongest default for standard NER when pretrained model access is available. Uses transformer tokenization and `labels` from training config.
- **BiLSTM-CRF**: lighter baseline; prediction depends on the vocabulary built during training.
- **W2NER**: handles flat, nested, and discontinuous NER by modeling word-word relations. It has a separate standard-subfamily workflow and dependency set.

### NER few-shot and cross-domain

- **LightNER**: prompt-based low-resource NER around BART; important knobs are prompt length/dimension, PLM freezing, and k-shot data selection.
- **CP-NER**: cross-domain prefix tuning with T5-style generative extraction; important knobs are source/target prefix paths and schema files.

### RE/AE standard

- **CNN / RNN / Capsule / GCN / Transformer**: conventional neural classifiers using word and position embeddings.
- **LM/BERT**: pretrained language model front-end, followed by recurrent/classification layers. Set `lm_file` to a resolvable local path or model name.
- For RE, `num_relations` must equal the relation inventory size.
- For AE, `num_attributes` must equal the attribute inventory size.

### RE few-shot

- **KnowPrompt**: knowledge-aware prompt tuning built on masked language modeling. It needs a relation label/answer-word mapping and compatible Lightning/runtime versions.

### RE document

- **DocuNet**: document-level relation extraction with transformer encoders and document-context modeling. It relies on DocRED-like JSON and relation metadata.

### Multimodal NER/RE

- **IFAformer**: combines text encoder outputs with CLIP/Vision Transformer features, RCNN object detections, and visual grounding objects.
- The visual directories are first-class data, not optional decorations. If they are missing or misaligned, route back to data validation before training.

### EE standard

- **BERT-CRF trigger/role pipeline**: first train or infer trigger labels, then train or infer role/argument labels. Pipeline prediction uses trigger prediction JSON as input to the role model.
- **DEGREE**: separate event extraction variant; use only when the user specifically asks for it and the required preprocessed data/dependencies are available.

## cnSchema inventory summary

DeepKE-cnSchema is an off-the-shelf Chinese NER/RE setup:

- NER supports a released inventory of 28 entity types, including common classes such as person, location, organization, work/product, date/number, website, city, school, company, language, and related cnSchema classes.
- RE supports 50 named cnSchema relation types plus an other/no-relation class in the documented relation-count setting.
- The quick-load path is for predefined cnSchema extraction. For a new ontology, train standard NER/RE with custom labels and relation mappings instead.

## Environment expectations

The supervised package imports were verified in a CPU inspection environment, including `deepke`, NER, RE, AE, EE, triple package roots, and `deepke.transform_data`. That verification proves importability and small helper safety, not full training success. Full training remains dataset-, checkpoint-, dependency-version-, and hardware-dependent.

For full classic supervised training, prefer a Python/PyTorch/Transformers/Hydra combination compatible with the scenario docs. For a first inspection pass, use the bundled diagnostic script to discover installed versions and missing optional modules before attempting a long run.
