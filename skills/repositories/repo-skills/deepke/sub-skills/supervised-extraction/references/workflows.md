# Supervised extraction workflows

This reference turns the DeepKE supervised examples and docs into task-selection and end-to-end operating recipes. It is intentionally self-contained: use it to decide what to run and what to validate without opening upstream README files.

## First decision: task and scenario

| User intent | Choose | Why |
| --- | --- | --- |
| Extract entity spans/types from short text with a normal train/dev/test set | NER standard | Fully supervised BIO tagging; BERT/BiLSTM-CRF/W2NER choices. |
| Train NER with very few labeled examples | NER few-shot | LightNER-style prompt tuning around BART; expects k-shot files or domain datasets. |
| Transfer NER across domains with prefix tuning | NER cross-domain | CP-NER-style T5 prefix workflows; requires per-domain JSON and schema files. |
| Use images or detected visual objects with entity extraction | NER multimodal | IFAformer-style text + visual object features; requires image/object folders and CLIP/BERT assets. |
| Classify relation between one entity pair in a sentence | RE standard | Fully supervised sentence-level RE; CNN/RNN/Capsule/GCN/Transformer/LM options. |
| Relation extraction with few labeled samples | RE few-shot | KnowPrompt-style prompt tuning; expects SEMEVAL/Wiki-style k-shot text and relation label JSON. |
| Extract relations among entities in a whole document | RE document | DocuNet-style document-level RE for DocRED-like JSON. |
| Relation extraction from text plus images | RE multimodal | IFAformer-style multimodal RE over MNRE-style text/image/object data. |
| Extract attributes of an entity, such as birthplace/time/value | AE standard | Same supervised classification family as standard RE, but label file is `attribute.csv`. |
| Extract event triggers and arguments | EE standard | Two-stage BERT-CRF pipeline: train/predict trigger, then train/predict roles. |
| Use Chinese cnSchema NER/RE without training | cnSchema quick-load | Requires downloaded off-the-shelf NER and/or RE checkpoints and cnSchema labels. |

## Before any long run

1. **Clarify the runtime goal**: training, prediction, config inspection, or result interpretation.
2. **Check data readiness**: use `references/data-and-config.md` for the expected split files, columns, labels, and offsets.
3. **Check the environment**: run `python scripts/check_supervised_env.py --task <scenario>` from this sub-skill tree. Add `--data-dir`, `--checkpoint`, or `--pretrained-model` if the user has provided those paths.
4. **Check compute and downloads**: BERT/BART/T5/CLIP checkpoints may download unless model paths are local. Multimodal, cross-domain, document-level, and EE training are not tiny smoke tests.
5. **Keep config edits explicit**: DeepKE examples use Hydra YAMLs. Record which YAML field you changed and why before rerunning.

## Reference-only native entrypoints

This sub-skill does **not** bundle replacements for DeepKE's native training and prediction scripts. They are reference-only operations because they depend on the user's installed DeepKE code, mutable Hydra config directories, datasets, checkpoints, GPU availability, and long-running training. Use the bundled diagnostic script for safe checks; use the native entrypoints only in the user's own DeepKE runtime when they have approved the data/model/resource requirements.

Common native entrypoint names you may see in a DeepKE installation:

| Scenario | Training entrypoint pattern | Prediction entrypoint pattern | Why not bundled here |
| --- | --- | --- | --- |
| NER standard | `run_bert.py`, `run_lstmcrf.py`, or W2NER `run.py` | `predict.py` | Training requires task config, labels, data splits, and optional GPU/checkpoints. |
| NER few-shot/cross/multimodal | `run.py` with Hydra overrides | `predict.py` where provided | Requires large PLMs, scenario data, and model paths. |
| RE/AE standard | `run.py` | `predict.py` | Requires generated vocab/embedding state and a trained `.pth` checkpoint for prediction. |
| RE few-shot/document/multimodal | `run.py` | `predict.py` where provided | Requires prompt/document/multimodal dependencies and trained `.pt`/checkpoint paths. |
| EE standard/DEGREE | `run.py` after selecting trigger/role/DEGREE settings | `predict.py` | Two-stage pipeline and dataset-specific preprocessing are required. |

## NER standard recipe

Use for BIO-tagged sequence labeling with Chinese or English text.

1. **Choose model family**:
   - `bert`: best first choice when a BERT-like local or remote model is available.
   - `lstmcrf`: lighter baseline; requires a dataset-derived vocabulary pickle for later prediction.
   - `w2ner`: specialized unified NER path for flat, nested, and discontinuous entities; has its own subdirectory/config.
2. **Prepare data**: `train.txt`, `valid.txt`, and `test.txt` with one token/character and one BIO tag per line; blank lines separate sentences.
3. **Edit config**:
   - Set the model selector (`hydra/model`) to `bert` or `lstmcrf` for the standard path.
   - Update `labels` in the training YAML to match every entity type, excluding the `B-`/`I-` prefix.
   - Set `lan` to `zh` or `en`; English prediction also needs NLTK tokenization resources.
   - For BERT, set the model path/name in the model YAML and tune `learning_rate`/`num_train_epochs` for dataset size.
4. **Train**: launch the model-specific training entrypoint. For BERT, the documented recipe recommends a lower learning rate around `2e-5` and about 10 epochs on the default dataset.
5. **Predict**: set the input text in prediction YAML, ensure the correct model checkpoint/vocab is discoverable, and run the prediction entrypoint.
6. **Validate**: confirm BIO tags only use configured labels, sentences preserve token order, and the output spans reconstruct valid substrings.

## NER few-shot recipe

Use when labels are scarce and the workflow should adapt a prompt-based model.

1. **Data**: CoNLL-2003 style split files (`train.txt`, `valid.txt`, `test.txt`, `indomain-train.txt`) or MIT/ATIS k-shot files such as `10-shot-train.txt`, `20-shot-train.txt`, etc.
2. **Config**:
   - `bart_name`: BART checkpoint or local path; use a Chinese BART path for Chinese few-shot.
   - `dataset_name`: one of the prepared dataset names.
   - `device`: usually `cuda`; CPU is for config/import checks only.
   - `save_path`/`load_path`: explicit output/input checkpoint locations.
   - Prompt controls: `use_prompt`, `prompt_len`, `prompt_dim`, `freeze_plm`, and `learn_weights`.
3. **Train**:
   - Baseline CoNLL path runs with the default train config.
   - Few-shot path uses a train override such as `+train=few_shot`.
   - Chinese few-shot uses the Chinese train override and requires local Chinese BART assets.
4. **Predict**: add the prediction config route, set non-empty `load_path`, and set `write_path` for predicted tags.
5. **Validate**: compare entity labels in predictions with the k-shot label inventory; ensure the output file is written and not empty.

## NER cross-domain recipe

Use for CP-NER-style cross-domain prefix transfer.

1. **Data per domain**: `train.json`, `val.json`, `test.json`, and schema files such as `record.schema`, plus optional entity/event/relation schemas.
2. **Warm up domain prefix**: train on one domain with `model_name_or_path`, `train_file`, `validation_file`, `test_file`, `record_schema`, `output_dir`, and `logging_dir` set.
3. **Single-source transfer**: set `source_prefix_path` to the source domain prefix/model and `target_prefix_path`/`model_name_or_path` to the target domain path.
4. **Multi-source transfer**: first save each source prefix/label-word bundle, then set `multi_source_path` as a comma-separated list of source paths.
5. **Validate**: check that each path in the prefix list exists, each target domain uses its own schema, and generated outputs use the `spotasoc` decoding format expected by the config.

## NER multimodal recipe

Use when each text sample has associated image/object features.

1. **Data**: CoNLL-like text split files plus image directories and detected visual object/visual grounding folders.
2. **Model assets**: BERT text model and CLIP/Vision Transformer model. If remote model download is unreliable, set `bert_name` and `vit_name` to local cache paths.
3. **Config**: set `dataset_name`, `max_seq`, `aux_size`, `rcnn_size`, `save_path`, and `load_path` for resume/prediction.
4. **Train/predict**: run only after images/object features are present. Prediction requires a non-empty `load_path`.
5. **Validate**: verify every text sample's image id resolves to the expected image/object files and token length does not exceed `max_seq` unexpectedly.

## RE standard recipe

Use for sentence-level relation classification between a head and tail entity.

1. **Data**: `train.csv`, `valid.csv`, `test.csv`, and `relation.csv`, usually under an origin data folder. Main columns are `sentence`, `relation`, `head`, `head_offset`, `tail`, and `tail_offset`.
2. **Choose model**: `cnn`, `rnn`, `capsule`, `gcn`, `transformer`, or `lm`.
3. **Config**:
   - Select `model` in the defaults.
   - For LM, set `lm_file` to a local or resolvable pretrained model.
   - Set `embedding.num_relations` to the number of relation labels, including any no-relation/other class.
   - Configure `use_gpu`, `gpu_id`, `use_multi_gpu`, and `gpu_ids` deliberately.
4. **Train**: run the standard RE training entrypoint; logs go to the configured log path and checkpoints to the checkpoint path.
5. **Predict**: set `predict.fp` to the trained checkpoint. The native docs often expect a fully resolved path; avoid ambiguous working-directory assumptions.
6. **Validate**: offsets should point at the first character/token of `head` and `tail`; every relation in data should appear in `relation.csv`.

## RE few-shot recipe

Use for KnowPrompt-style few-shot relation extraction.

1. **Data**: relation label file such as `rel2id.json` plus `train.txt`, `val.txt`, and `test.txt`; k-shot data may live in a `data/k-shot/<setting>` layout.
2. **Config**:
   - `data_dir` selects the k-shot split.
   - `model_name_or_path` selects the PLM.
   - `model_class`/`litmodel_class` define the masked-LM and Lightning wrapper.
   - `train_from_saved_model`, `load_checkpoint`, `save_path`, and `load_path` control resume/prediction.
3. **Train/predict**: run the few-shot entrypoints after confirming PyTorch Lightning compatibility with the installed versions.
4. **Validate**: label words in `rel2id.json` must match the model prompt setup; empty or unseen relation labels usually indicate a split/config mismatch.

## RE document recipe

Use for DocRED-like document-level relation extraction.

1. **Data**: `train_annotated.json` or `train_distant.json`, `dev.json`, `test.json`, `rel2id.json`, and `rel_info.json`.
2. **Config**: check `dataset`, `data_dir`, `train_file`, `dev_file`, `test_file`, `num_class`, `max_seq_length`, `model_name_or_path`, `transformer_type`, `train_from_saved_model`, and `load_path`.
3. **Train**: choose manual or distant training file intentionally; document-level batches are memory heavy.
4. **Predict**: output is a JSON result file in the active workflow directory.
5. **Validate**: relation id count should match `num_class`; long documents may truncate at `max_seq_length` if not planned.

## RE multimodal recipe

Use for MNRE-style relation extraction with text and images.

1. **Data**: text split folder, relation id JSON, original image folder, detected object folder, visual grounding folder, and bounding/visual-grounding metadata.
2. **Model assets**: BERT plus CLIP/Vision Transformer. Set `vit_name` to a local model path when offline.
3. **Config**: `max_seq`, `aux_size`, `rcnn_size`, `save_path`, and `load_path` are the usual first checks.
4. **Validate**: each relation instance must align text ids with available image/object files; prediction without `load_path` cannot work.

## AE standard recipe

Use when the relation-like label is an attribute between an entity and a value.

1. **Data**: `train.csv`, `valid.csv`, `test.csv`, and `attribute.csv`. Core columns are `sentence`, `attribute`/`att`, entity text and offset, value text and offset.
2. **Model/config**: same model selector family as standard RE. Set `embedding.num_attributes` to the number of attribute labels.
3. **Train/predict**: train with the standard AE entrypoint; prediction needs the checkpoint path in `predict.fp`.
4. **Validate**: entity/value offsets must match substrings; attribute names in data must exist in `attribute.csv`.

## EE standard recipe

Use for event trigger detection/classification and event argument extraction.

1. **Data**: choose `ACE` or `DuEE`. ACE requires preprocessing into trigger, role, schema, and optional DEGREE folders. DuEE uses the provided extracted dataset layout.
2. **Trigger stage**:
   - Set `data_name` and `model_name_or_path`.
   - Set `task_name: trigger`.
   - Train and let evaluation/prediction produce trigger prediction JSON where configured.
3. **Role stage**:
   - Set `task_name: role`.
   - Train with gold trigger data when training role extraction.
4. **Pipeline prediction**:
   - Set `do_pipeline_predict: True`.
   - Set role `model_name_or_path` to the trained role model path.
   - Set `dev_trigger_pred_file` and `test_trigger_pred_file` to the trigger-stage prediction JSON files.
5. **Validate**: trigger labels and role labels must come from the selected dataset schema; role prediction cannot proceed if trigger prediction files are missing.

## cnSchema quick-load recipe

Use for Chinese off-the-shelf NER/RE when the user wants extraction without training.

1. **Download/provide checkpoints**:
   - NER checkpoint is usually a directory of transformer/tokenizer files or a supported NER model directory.
   - RE checkpoint is usually a `.pth` model file for the LM relation extractor.
2. **NER quick-load**:
   - Put the model where the active NER config points.
   - Set the NER model selector to match the downloaded model family (`bert` or `lstmcrf`).
   - Set prediction text in the prediction YAML and run prediction.
3. **RE quick-load**:
   - Set `predict.fp` to the RE checkpoint.
   - Set relation count to 51 when using the cnSchema relation inventory.
   - Set LM model path/name to a local Chinese BERT/RoBERTa asset if remote download is blocked.
4. **Joint use**: first run NER, convert recognized entities into candidate pairs, then run RE over candidate pairs. More than two entities in a sentence can create spurious pairs; report confidence and validate manually.
5. **Validate**: cnSchema covers a finite inventory of entity and relation types; out-of-schema facts need custom training rather than quick-load.
