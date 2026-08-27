# DeepKE triple-extraction workflows

This reference distills DeepKE's PRGC, PURE, ASP, MT5, and cnSchema triple-extraction examples into operating recipes. Use it to choose a workflow and to decide which native operation is safe to run in the user's environment.

## Scenario decision table

| User intent or data shape | Choose | Runtime expectation | Why |
| --- | --- | --- | --- |
| Jointly extract `(head, relation, tail)` triples from sentences with classic supervised datasets such as CMeIE, NYT, or WebNLG | PRGC | Python 3.8-era PyTorch/Transformers, BERT/RoBERTa assets, normal GPU recommended | PRGC is DeepKE's most direct classic joint triple-extraction path with `rel2id.json` and `*_triples.json` splits. |
| Build a staged entity extractor and relation classifier, or debug entity/relation errors separately | PURE | Older AllenNLP/Transformers/PyTorch compatibility; GPU recommended | PURE separates entity and relation components, which helps diagnose whether entity spans or relation classification is the bottleneck. |
| Use autoregressive structured prediction over entity-relation structures | ASP | CUDA, compatible PyTorch, `apex`/mixed precision expectations, nontrivial setup | ASP is powerful but the most environment-sensitive DeepKE triple example. Treat as GPU/reference-only unless the user has prepared the exact stack. |
| Fine-tune or post-process a generative MT5/DeepSpeed model for CCKS-style triple extraction | MT5 | Python 3.9-era Transformers/DeepSpeed, multiple GPUs recommended for training | MT5 uses generated `output` strings and a converter to produce `kg` triples for submission/evaluation. |
| Chinese schema-oriented extraction over a fixed schema/inventory, often cnSchema | cnSchema | Chinese PLM/checkpoint assets and schema label files | Use when the relation/entity inventory is the main constraint and the user already accepts cnSchema-style labels. |

## Common preflight checklist

Before any native run:

1. Confirm whether the user wants **training**, **prediction**, **conversion**, or **config diagnosis**.
2. Run `python scripts/check_triple_env.py --task <scenario>` to inspect local imports and CUDA visibility without downloads or training.
3. Check data layout and required filenames in [data-and-config.md](data-and-config.md).
4. Prefer local pretrained model/checkpoint paths. Remote model ids can trigger downloads in native DeepKE scripts.
5. Record Hydra/DeepSpeed/config changes explicitly: dataset path, relation labels, model name, output directory, checkpoint path, GPU selection, and seed.
6. Keep output directories unique between runs. The MT5 docs explicitly warn that reusing `output_dir`/`logging_dir` can overwrite earlier results.

## PRGC recipe

Use PRGC when the user has sentence-level triples and wants a classic joint extractor.

1. **Data**: expected files are commonly `rel2id.json`, `train_triples.json`, `val_triples.json`, and `test_triples.json` under the task data directory. Datasets named in the source workflow include CMeIE, NYT, NYT*, WebNLG, and WebNLG*.
2. **Pretrained encoder**: use a local BERT/RoBERTa-style directory with tokenizer vocab and config. Source docs note that some BERT configs are renamed to `bert_config.json` and folder names may avoid hyphens.
3. **Config**: check the `conf` settings for data directory, relation labels, pretrained model path, output model directory, logging directory, batch sizes, learning rate, and sequence length.
4. **Train**: the native entrypoint is a `run.py`-style PRGC training script. Treat it as a long GPU/PLM run unless the user explicitly requests and the environment is ready.
5. **Predict**: prediction reads a trained model under the configured model directory. Verify the checkpoint exists before running.
6. **Validate**: compare predicted relation strings against `rel2id.json`; inspect whether symmetric or overlapping triples are represented as expected.

## PURE recipe

Use PURE when staged diagnosis matters or when the data is already in PURE's JSON format.

1. **Data**: the CMeIE-style source path uses JSON splits such as `train.json`, `dev.json`, and `test.json`. Relation type constants may live in model code/config rather than a loose CSV.
2. **Compatibility**: PURE is sensitive to AllenNLP, Transformers, PyTorch, and Hugging Face Hub versions. The source README documents separate stacks for older Transformers and for a 4.26-era adaptation.
3. **Entity stage**: inspect fields such as entity train/eval flags, BERT model path, output directory, context window, train batch size, and learning rates.
4. **Relation stage**: inspect relation train/eval files, max sequence length, output directory, prediction filename, `no_cuda`, and model path consistency with the entity model.
5. **Train/predict**: run the native script only after dependency compatibility is proven. Prediction output usually lands under the relation output directory.
6. **Validate**: if relations look poor, first decide whether entity span predictions were wrong or relation classification failed on correct spans.

## ASP recipe

Use ASP only when the user needs autoregressive structured prediction and has a compatible GPU stack.

1. **Data**: expected CMeIE-style JSON splits are `train.json`, `dev.json`, and `test.json` under a dataset-specific data directory.
2. **Environment**: source docs pin Python 3.8.16, CUDA-enabled PyTorch, Transformers, sentencepiece, pyhocon, truecase, and an Apex build. CPU-only diagnostics do not verify ASP runtime readiness.
3. **Config**: the native command accepts a dataset/config name and GPU id. The environment variable used by the source workflow points the code at the ASP working directory.
4. **Train**: native training uses a `run_ere.py <config_name> <gpu_id>` pattern and writes logs/checkpoints under the dataset output folder.
5. **Evaluate**: native evaluation uses `evaluate_ere.py <config_name> <saved_suffix> <gpu_id>` and requires a real saved suffix from training.
6. **Validate**: confirm the saved suffix exists, CUDA is visible, Apex import/build is compatible, and decoding produces parseable entity-relation structures.

## MT5/CCKS recipe

Use MT5 for generative CCKS-style triple extraction and conversion.

1. **Data**: training usually reads `train.json`; the file named `valid.json` in the source docs is the competition test file, not necessarily a validation set. If no validation file is supplied, native training may split part of train data internally.
2. **Training**: source commands use DeepSpeed, `google/mt5-base`, generation flags, bf16, gradient checkpointing, and a DeepSpeed config. This is a large-model GPU workflow, not a tiny smoke test.
3. **Prediction**: a trained model path is passed as `model_name_or_path`; output goes to a separate `output_dir` containing `test_preds.json`.
4. **Conversion**: convert model `output` strings into `kg` triples with:

   ```bash
   python scripts/convert_mt5_predictions.py \
     --src-path data/valid.json \
     --pred-path output/test_preds.json \
     --tgt-path output/valid_result.jsonl
   ```

5. **Validate**: inspect a few records where `kg` is empty. Empty triples may mean the generated text omitted parentheses, used a different delimiter, or included an unsupported schema.

## cnSchema triple-oriented recipe

Use cnSchema when the user needs Chinese schema-constrained extraction and accepts a fixed inventory.

1. Confirm the target entity/relation inventory before running; cnSchema is not a universal open-schema extractor.
2. Prefer local Chinese PLM/checkpoint paths, because native scripts may otherwise download models.
3. If the workflow chains NER then RE into triples, validate entity spans and candidate-pair generation before blaming relation classification.
4. For custom schema relations, retrain or adapt labels instead of forcing out-of-schema facts into cnSchema labels.

## What a safe generated-skill run can prove

The bundled diagnostics and converter can prove that Python imports, CUDA visibility, file paths, JSONL parsing, and post-processing syntax are correct. They do **not** prove PRGC/PURE/ASP/MT5 model quality, full GPU compatibility, checkpoint availability, or training reproducibility. Preserve those as explicit runtime requirements when reporting readiness.
