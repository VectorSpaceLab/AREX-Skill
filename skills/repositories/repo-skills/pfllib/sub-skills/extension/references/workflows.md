# Extension Workflows

## 1. Add a new algorithm

1. Start from the nearest existing `Server` and `Client` subclasses.
2. Implement the new client behavior in a new `clientNAME.py` module.
3. Implement the scheduling and aggregation logic in a new `serverNAME.py`
   module.
4. Add the new imports and algorithm branch in `system/main.py`.
5. Check whether the algorithm needs a backbone/head split or a plain model.
6. Run `scripts/scan_registry.py` to confirm the algorithm appears in the
   registry snapshot.
7. Run a tiny experiment smoke path from the `experiments` route.

## 2. Add a new dataset

1. Create a `generate_DATA.py` script under `dataset/`.
2. Use the shared split helpers from `dataset/utils/`.
3. Download or stage the raw data in the dataset-specific `rawdata/` area.
4. Convert the raw content into arrays or token sequences.
5. Write `config.json`, `train/`, and `test/` files through `save_file()`.
6. Validate the output tree with the data-preparation route.
7. If the new dataset uses a new modality, update the data loader path in
   `system/utils/data_utils.py`.

## 3. Add a new model

1. Implement the module in `system/flcore/trainmodel/`.
2. Make sure the output shape and classifier head match the dataset family.
3. Register the model in the `main.py` model-selection block.
4. Re-check the model family notes in `sub-skills/experiments/references/model-overview.md`.
5. Run a tiny experiment smoke path to confirm the new model is selectable.

## 4. Add a new optimizer

1. Extend the optimizer helper in `system/flcore/optimizers/fedoptimizer.py`.
2. Route the new optimizer from the training code that needs it.
3. Confirm the optimizer does not break existing algorithms that do not use it.

## 5. Keep the registry in sync

After any extension, run the registry scanner and the install checker again so
future agents can see the updated supported surface and dependency requirements.
