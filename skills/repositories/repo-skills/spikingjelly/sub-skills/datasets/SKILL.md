---
name: datasets
description: "Load, preprocess, integrate, transform, and debug SpikingJelly
  neuromorphic datasets and data utilities."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# datasets

Use this sub-skill when the task is about SpikingJelly data: loading a built-in neuromorphic dataset, preparing manual download files, choosing `event` versus `frame` samples, integrating events to frames, applying dataset transforms, or using data utility helpers.

## Route here for

- Built-in `spikingjelly.datasets` dataset wrappers such as `DVS128Gesture`, `CIFAR10DVS`, `CIFAR10DVSTEBNSplit`, `NMNIST`, `NCaltech101`, `ASLDVS`, `DVSLip`, `ESImageNet`, `HARDVS`, `NAVGestureSit`, `NAVGestureWalk`, `Bullying10kClassification`, `SpikingHeidelbergDigits`, and `SpikingSpeechCommands`.
- Dataset-base and builder questions around `NeuromorphicDatasetFolder`, `NeuromorphicDatasetConfig`, `EventBuilder`, `FrameFixedNumberBuilder`, `FrameFixedDurationBuilder`, and `FrameCustomIntegrateBuilder`.
- Download/manual-data boundaries: `downloadable()`, `resource_url_md5()`, expected `root/download` contents, archive extraction, raw `events_np` / `events_h5` creation, and processed frame directories.
- Event/frame layout: event dictionaries with `t`, `x`, `y`, `p`; frame archives containing `frames`; fixed-number, fixed-duration, and custom integration workflows.
- Dataset utilities: `load_aedat_v3`, `load_ATIS_bin`, `load_npz_frames`, `integrate_events_*`, `pad_sequence_collate`, `padded_sequence_mask`, `split_to_train_test_set`, `create_sub_dataset`, `save_as_pic`, and `play_frame`.
- Dataset transforms, especially `random_temporal_delete` and `RandomTemporalDelete`, including their `batch_first` time-axis convention.

## Do not handle here

- Model construction, training loops, optimizers, distributed launch, epoch scheduling, or data-loader-to-training recipes. Use `../training-and-scaleout/`.
- SNN state reset, `step_mode`, recurrent state, surrogate gradients, encoders, monitors, or layer semantics. Use `../core-snn/`.
- ANN-to-SNN conversion, calibration data selection for conversion, or converted-model timestep behavior. Use `../ann2snn/`.
- CUDA/CuPy/Triton backend performance, precision, memory optimization, profiling, or deployment speed. Use `../performance-and-analysis/`.
- Exchange/deployment formats or hardware runtime export. Use `../deployment-exchange/`.

## Read first

- [`references/data-workflows.md`](references/data-workflows.md) for dataset-class coverage, root layouts, builder selection, event/frame integration contracts, transforms, utilities, and the verified `DVS128Gesture` signature.
- [`references/troubleshooting.md`](references/troubleshooting.md) for manual-download failures, corrupted/existing extracted dirs, split/layout mistakes, frame-shape mismatches, fixed-duration collation, and preprocessing configuration.

## Skill-owned script

- [`scripts/dataset_tiny_fixture_smoke.py`](scripts/dataset_tiny_fixture_smoke.py) creates temporary event fixtures, runs the fixed-number and custom frame builders, and checks variable-length padding plus temporal-delete transform behavior. It performs no downloads and does not require a real dataset.

## Operating workflow

1. Identify the dataset class and whether its constructor uses `train`, `split`, `train_test_val`, or no split argument.
2. Check `downloadable()` before assuming a dataset can be fetched automatically. For manual datasets, place every `resource_url_md5()` file under `root/download` before instantiating the dataset.
3. Choose `data_type='event'` for raw event dictionaries, or `data_type='frame'` with exactly one frame strategy: `frames_number` plus `split_by`, `duration`, or `custom_integrate_function`.
4. Verify the expected layout: `root/download`, `root/extract`, default raw `root/events_np` or dataset-specific `root/events_h5`, then the processed root selected by the builder.
5. For fixed-duration frame data, plan for variable `T`; use `pad_sequence_collate` and `padded_sequence_mask` before handing batches to training code.
6. Run the no-download smoke script when you need a quick sanity check of builder contracts before debugging a real dataset tree.

## Cross-links

- If the data are loaded and the question becomes “how do I train or scale this?”, switch to `../training-and-scaleout/`.
- If the question is about temporal state, `step_mode`, `reset_net`, or sequence tensor semantics after loading data, switch to `../core-snn/`.
- If the data are being used only for ANN2SNN calibration or conversion validation, switch to `../ann2snn/` after the dataset contract is clear.
