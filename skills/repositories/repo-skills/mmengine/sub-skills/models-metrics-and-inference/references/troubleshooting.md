# Troubleshooting Models, Metrics, and Inference

Use this symptom map before changing Runner, dataset, registry, or visualization code. Start with tiny CPU batches and the bundled scripts, then scale to project code.

## BaseModel and Step Contracts

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Training fails with `TypeError` from `parse_losses`. | `forward(..., mode='loss')` returned a non-tensor value in the loss dict. | Return tensors or lists of tensors only; convert Python numbers to tensors on the same device. |
| Backward fails or total loss is zero/missing. | The loss dict has no key containing `loss`. | Name backward-contributing keys like `loss_cls` or `loss_total`; keep metric-only tensors under names without `loss`. |
| Validation metric receives raw logits instead of samples. | `mode='predict'` returns the same tensor as `mode='tensor'`. | Return a sequence of prediction dicts or task data elements from `mode='predict'`; reserve raw tensors for `mode='tensor'`. |
| `val_step` or `test_step` raises unexpected keyword errors. | Data preprocessor returns a dict whose keys do not match `forward` parameters. | Align batch keys with `forward(inputs, data_samples=None, mode=...)`, or override `_run_forward` behavior through step methods only when necessary. |
| Custom `train_step` logs nothing or optimizer does not update. | The override bypasses `OptimWrapper.update_params()` or returns an incompatible value. | Use `with optim_wrapper.optim_context(self)`, parse or compute a scalar loss, call `update_params(loss)`, and return a log dict. |
| Data is on CPU while model is on GPU, or the inverse. | The custom preprocessor did not use `BaseDataPreprocessor.cast_data()`, or the model/device move happened before attaching the preprocessor. | Subclass `BaseDataPreprocessor`, call `cast_data`, and attach it through `BaseModel.__init__`; move the final model after construction. |

## Data Preprocessor and Image Batches

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `data_preprocessor should be a dict or nn.Module` | A list, callable class, or already-built non-module object was passed. | Pass `dict(type='...')` registered in `MODELS` or an `nn.Module` preprocessor instance. |
| `ImgDataPreprocessor` rejects `mean` or `std`. | Only one of them is set, or one has length other than 1 or 3. | Set both to `None`, both length 1, or both length 3. |
| Channel conversion assertion fires. | Both `bgr_to_rgb` and `rgb_to_bgr` are true. | Choose exactly one direction, or leave both false. |
| Image normalization assertion mentions expected `(3, H, W)`. | Three-channel mean/std were used with a gray image, missing channel dimension, or wrong channel order. | Make single images `(3, H, W)` or batched inputs `(N, 3, H, W)`, or use length-1 mean/std for gray images. |
| Model receives a list when it expected a stacked tensor. | `pseudo_collate` preserved per-sample tensors and no image preprocessor stacked them. | Use `ImgDataPreprocessor` or switch fixed-shape dataloaders to `default_collate` when appropriate. |

## Metrics and Evaluators

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Metric warns that `self.results` is empty. | `process()` did not append to `self.results`, or `evaluate()` was called before any process calls. | Append compact per-sample results in `process()` and call `evaluate(size)` after all batches. |
| Metrics disappear on second evaluation. | `BaseMetric.evaluate()` clears `self.results` after computing. | Re-run `process()` for every evaluation pass or use separate metric instances. |
| `Evaluator.evaluate()` raises duplicate metric name error. | Two metrics return the same final key after prefixing. | Set distinct `prefix` values or `default_prefix` values, and match `save_best` to the final prefixed key. |
| Offline evaluation length assertion fails. | `data_samples` and `data` lengths differ. | Pass matching lists or omit `data` when metric `process()` does not need batch data. |
| Distributed metric collection hangs or fails. | `collect_device`, `collect_dir`, or picklability is wrong. | Use CPU collection first; ensure processed results are picklable; set `collect_dir` only with `collect_device='cpu'`. |
| GPU tensors leak into metric computation or dumps. | Metric stores raw predictions without CPU conversion, or custom dump code bypasses `DumpResults`. | Let `BaseMetric.evaluate()` CPU-convert before `compute_metrics`; use `DumpResults` for prediction pickles. |
| `DumpResults` rejects the output file. | Path does not end in `.pkl` or `.pickle`. | Use a pickle suffix and a caller-owned output path. |

## Inference

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Custom inferencer class raises an assertion at import. | A kwarg name appears in more than one `preprocess_kwargs`, `forward_kwargs`, `visualize_kwargs`, or `postprocess_kwargs` set. | Keep those sets disjoint; route each call kwarg to exactly one phase. |
| Inferencer call raises `unknown` kwarg error. | The kwarg was not listed in any `*_kwargs` set. | Add it to the phase that consumes it or remove it from the call. |
| `BaseInferencer` cannot initialize from model name. | Downstream package metafile support is not installed or registered. | Use a local config/dict and explicit weights, or install/register the downstream package with user approval. |
| Inference returns data elements when JSON is expected. | `postprocess()` ignores `return_datasamples=False`. | Convert predictions to dict/list/scalar structures in `postprocess()` unless `return_datasamples=True`. |
| A directory input yields no files or unexpected paths. | Backend does not support `isdir`, or path listing is backend-specific. | Convert inputs to an explicit list in caller code or use a backend that supports directory listing. |

## TTA

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `BaseTTAModel.forward` raises `NotImplementedError`. | TTA wrappers are meant to run through `test_step()`, not `forward()`. | Call `tta_model.test_step(data)` or run through Runner testing. |
| TTA model initialization asserts missing `test_step`. | Wrapped module is a plain module without MMEngine test-step contract. | Wrap a `BaseModel`-compatible module or implement `test_step()` on the model. |
| `merge_preds()` receives tuples in an unexpected order. | `BaseTTAModel.test_step()` zips predictions by original sample after running each augmentation batch. | Treat each item passed to `merge_preds()` as all augmentations for one original sample. |
| Merged predictions have wrong batch length. | `merge_preds()` returns one result per augmentation instead of one result per sample. | Return a list with length equal to the original batch size. |
| TTA runner config has no effect. | `tta_pipeline` was not placed on the test dataset, or `PrepareTTAHook` was not registered. | Use `build_runner_with_tta(cfg)` or explicitly replace the test pipeline and register `PrepareTTAHook(tta_cfg=...)`. |
| Downstream TTA example tries to download weights. | Source examples may include remote checkpoints or task packages. | Replace with local weights/configs, or use a tiny contract smoke test when only MMEngine behavior is being checked. |

## Complexity Analysis

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `get_model_complexity_info` raises that inputs should be set. | Neither `input_shape` nor `inputs` was provided. | Provide exactly one of them. |
| It raises that `inputs` and `input_shape` cannot both be set. | Both arguments were passed. | Prefer `inputs` for non-trivial forward signatures; otherwise use `input_shape`. |
| FLOPs look too low or warnings mention unsupported ops. | JIT analyzer has no handle for one or more operators. | Inspect `FlopAnalyzer.unsupported_ops()` and add justified op handles or report the undercount limitation. |
| Some submodules show `N/A` or are uncalled. | The sample input did not execute those modules or code called methods outside module `__call__`. | Use representative inputs and call the model normally; document intentionally unused branches. |
| Analysis fails on dynamic control flow or non-tensor values. | Tracing-style analysis cannot follow the model's runtime behavior. | Pass concrete `inputs`, simplify the analysis wrapper, or report params-only results when FLOPs are not reliable. |
| Optional import errors appear around analysis or downstream models. | Task model dependencies are missing, not MMEngine core. | Install only the required optional package with approval, or analyze a smaller dependency-free module. |

## Triage Order

1. Run `python scripts/model_metric_smoke.py --help` and `python scripts/tta_smoke.py --help` from this sub-skill directory to confirm the local MMEngine/PyTorch surface imports.
2. Reproduce the project failure with one tiny CPU batch and direct calls to `data_preprocessor`, `forward`, `val_step`, and `Evaluator.process()`.
3. Confirm metric final keys before configuring checkpoint `save_best` or comparing validation results.
4. For inference, test the subclass phase methods individually before calling the full inferencer.
5. For TTA, inspect the enhanced batch shape and the values received by `merge_preds()`.
6. For complexity reports, include unsupported-op or uncalled-module caveats with the reported numbers.

Route full Runner loop placement to `../runner-and-training/SKILL.md`, sample container internals to `../data-structures-and-io/SKILL.md`, config/registry import issues to `../configuration-and-registry/SKILL.md`, and visualizer/logging backend problems to `../runtime-utilities-and-visualization/SKILL.md`.
