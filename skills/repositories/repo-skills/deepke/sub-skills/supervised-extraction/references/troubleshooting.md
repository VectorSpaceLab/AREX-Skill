# Supervised extraction troubleshooting

Start here when a DeepKE supervised NER/RE/AE/EE workflow fails. Prefer the smallest safe check first: imports, data layout, config values, checkpoint paths, then a tiny prediction or config-resolution run. Full training failures are often caused by the same small issues.

## Safe first checks

```bash
python scripts/check_supervised_env.py --task ner-standard
python scripts/check_supervised_env.py --task re-standard --data-dir data/origin --checkpoint checkpoints/model.pth
python scripts/check_supervised_env.py --task ee-standard --data-dir data/DuEE --require-cuda
```

The script does not train, download, or mutate configs. It checks installed imports, CUDA visibility, and optional data/checkpoint path expectations.

## Install and import failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'deepke'` | Package not installed in the active environment. | Install DeepKE in the environment that runs the command, preferably editable/source install when using a checkout. Then verify with `python -I -c "import deepke"`. |
| Package imports work in one shell but not another | Different Python/conda/venv is active. | Print `python -c "import sys; print(sys.executable)"` in the failing shell and reinstall/activate the intended environment. |
| `ModuleNotFoundError: No module named 'past'` | Missing `future` package. | Install `future` in the active environment. |
| `omegaconf` / Hydra config errors after installing latest packages | Scenario docs pin older Hydra for classic examples; EE may require a newer Hydra than older examples. | Use a fresh environment per workflow family when conflicts appear. For EE, check the EE-specific Hydra requirement before forcing the global classic pin. |
| `transformers` / `tokenizers` import or tokenizer errors | Version mismatch with DeepKE scenario. | Use a scenario-compatible Transformers/Tokenizers pair; classic configs often expect `transformers` around 4.26 for current imports, while some older docs mention 3.x. |
| `pip install deepke` fails with newer pip | DeepKE docs warn that direct PyPI install may be sensitive to pip version. | Prefer source/editable install for workflow work; if using PyPI, keep pip at a compatible version and verify imports. |
| Changes to DeepKE source do not affect runtime | Installed wheel shadows edited source. | Use source/editable install in the same environment that runs the command. |
| Windows path behavior is odd | Native docs recommend Windows users handle backslashes carefully. | Prefer Linux for training; on Windows, escape paths or use raw strings/forward-compatible path handling in config. |

## Model and checkpoint failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Prediction config still has `fp: xxx/checkpoints/...` or `load_path: load path` | Placeholder checkpoint path was never replaced. | Set `predict.fp` or `load_path` to an existing trained checkpoint/model path. Run the diagnostic script with `--checkpoint`. |
| Standard RE/AE prediction cannot load checkpoint | Wrong model family selected or checkpoint path points to another architecture. | Ensure `model` in the config matches the trained checkpoint family (`cnn`, `rnn`, `capsule`, `gcn`, `transformer`, or `lm`). |
| NER BiLSTM-CRF prediction fails after training | Vocabulary pickle from training is missing or mismatched. | Reuse the exact vocabulary generated from the training data and configured by the BiLSTM-CRF model YAML. |
| BERT/BART/T5/CLIP model download hangs or fails | Remote model hosting unavailable, proxy blocked, or no network approval. | Download/copy the model to local storage using an approved method and point `bert_name`, `bart_name`, `model_name_or_path`, `lm_file`, or `vit_name` to that local path. |
| Multimodal CLIP model fails to load with old Transformers | CLIP requires a compatible Transformers version and tokenizer/model files. | Use a Transformers version that supports `openai/clip-vit-base-patch32` or provide a complete local CLIP model directory. |
| cnSchema NER model directory loads partially | Missing tokenizer/config/model files. | Confirm the directory contains complete transformer assets such as config, vocabulary/tokenizer files, and model weights for the selected NER family. |
| cnSchema RE predicts wrong/unknown labels | Relation class count or label inventory mismatched. | Use the cnSchema relation inventory count expected by the config (`num_relations: 51` in the documented setup) and the matching checkpoint. |
| EE role prediction fails with missing trigger file | Trigger stage output JSON was not produced or path is wrong. | Run/repair the trigger stage first; then set `dev_trigger_pred_file` and `test_trigger_pred_file` to the actual JSON files. |

## Dataset and label failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| NER training reports unknown labels or bad BIO tags | `labels` config does not match `B-`/`I-` types in data. | List all entity types in `labels` without BIO prefix and remove stray tag variants. |
| NER sentence is unexpectedly huge | Missing blank lines between sentences. | Insert blank lines between BIO-tagged sentences. |
| English NER prediction fails around tokenization | `lan` not set to `en` or NLTK tokenizer resources missing. | Set `lan: en`; install NLTK and download/cache the required tokenizer resource. |
| RE/AE offsets produce wrong entities | Offsets are stale after editing text or count bytes instead of characters. | Recompute offsets so `sentence[offset:offset+len(entity)]` matches the entity/value string under the same encoding assumptions. |
| Relation/attribute id error | `relation.csv`/`attribute.csv` does not contain every label or count config is wrong. | Update the inventory file and `num_relations`/`num_attributes` together. |
| RE rows have multiple possible entity type pairs per relation | Label schema is ambiguous. | Include entity types in the input relation encoding consistently or split labels by type as planned. |
| Few-shot RE label words do not map to relations | `rel2id.json` and prompt setup are inconsistent. | Regenerate/check `rel2id.json`, label words, and data split relation names. |
| Document RE class-count assertion or shape mismatch | `num_class` differs from `rel2id.json`/`rel_info.json`. | Count the relation ids and update `num_class`; ensure metadata files come from the same dataset version. |
| Multimodal sample not found | Text image id does not match image/object filenames. | Validate image-id alignment across text splits, original images, detected objects, and visual grounding metadata. |
| Chinese customized data raises encoding/embedding errors | Invisible special characters or unsupported encoding in text. | Normalize and clean Chinese text, remove invisible characters, and rerun a tiny data check. |
| EE labels not found | `data_name`, `task_name`, schema folder, or tag path does not match data. | Verify `ACE`/`DuEE` selection, trigger/role stage, and generated schema/tag files before training. |

## Hydra and workflow errors

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `MissingMandatoryValue: cwd` when inspecting config directly | `cwd: ???` is filled by runtime code/Hydra, not static YAML. | Do not read unresolved Hydra config as a final config; run through the native entrypoint or supply/resolve required fields. |
| Config override is ignored | Override attached to wrong command or wrong working directory. | Run from the scenario directory and include the exact override, such as `+train=few_shot` or `hydra/run=single_transfer.yaml`. |
| Prediction reads old config values | Hydra output dir or defaults changed but prediction YAML still points to old path. | Inspect the composed config and update both model selector and predict/checkpoint fields. |
| W&B prompts block automation | `use_wandb` or `wandb` enabled without credentials/TTY. | Disable W&B for unattended runs unless the user explicitly wants online logging. |
| Training starts but writes outputs to surprising directory | Hydra output config changes working directory or output directory. | Check `hydra/output` and save/log fields. Record the generated checkpoint directory immediately after training. |
| Multi-GPU flag causes device error | GPU ids are unavailable or flag format differs by scenario. | Use `scripts/check_supervised_env.py --require-cuda` first; then set the scenario-specific GPU field correctly. |

## GPU and optional dependency issues

| Workflow | Optional dependency / hardware | Troubleshooting note |
| --- | --- | --- |
| Standard NER/RE/AE | CUDA optional but recommended for training. | CPU can verify imports/configs and tiny data checks; full training may be slow. |
| Few-shot NER/RE | GPU strongly preferred; PLM checkpoints required. | CPU is usually only for import/config validation. |
| Multimodal NER/RE | GPU recommended; CLIP/Vision Transformer, image/object files required. | Missing visual assets are data errors, not optional dependency warnings. |
| Cross-domain NER | GPU recommended; T5/generative PLM assets required. | Prefix paths and schema files are as important as the PLM. |
| Document RE | GPU/memory recommended; long sequence length. | Reduce batch size or gradient accumulation settings only after confirming data/class counts. |
| EE / DEGREE | Dataset-specific preprocessing and dependency versions. | Use isolated env if Hydra/Transformers/Torch constraints conflict with other DeepKE examples. |

## Recovery order for failed runs

1. Capture the exact command, active environment, and composed config values that affect data/model paths.
2. Run the diagnostic script with the target task and every provided path.
3. Validate data files and label inventories using `references/data-and-config.md`.
4. Replace placeholder model/checkpoint paths with known existing paths.
5. For training failures, try a tiny subset or short epoch only after imports, config, and data validation pass.
6. For resource-bound workflows, ask whether GPU/model downloads/long training are allowed before retrying.

## When to route elsewhere

- If the issue is converting doccano JSON, DOCX, XLSX, weak NER labels, or distant RE labels into DeepKE files, route to `data-preparation`.
- If the issue is PRGC/PURE/ASP/MT5 triple extraction, route to `triple-extraction`.
- If the issue is instruction KGC, OneKE, LLM prompts, or API-based extraction, route to `llm-workflows`.
- If the issue is local MCP service deployment or tool-calling wrappers, route to `mcp-tools`.
