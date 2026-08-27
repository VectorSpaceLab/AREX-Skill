---
name: training-data
description: "Plan and operate iGAN dataset preparation, HDF5 schema checks,
  DCGAN training, batchnorm, predictor, packing, and training configuration
  workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# iGAN Training Data Router

Use this sub-skill when the task is about building or auditing the data and
training side of iGAN rather than loading a finished model for inference.
It is intentionally safe to load in a modern environment: the bundled scripts
only plan, inspect, and print commands; they never download datasets, write
HDF5 files, start Theano, train networks, or touch a GPU.

## Route Here

- Plan which public HDF5 dataset archive is needed and how much disk/network
  budget it implies.
- Preflight a custom image directory before converting it to iGAN's HDF5 layout.
- Explain the `imgs` dataset shape, channel convention, Fuel split metadata,
  and train/test slicing expected by the legacy loaders.
- Build a DCGAN training command sequence from an existing HDF5 file.
- Estimate the required post-training batchnorm steps for the generator,
  discriminator, and optional predictor.
- Plan predictor training for image-to-latent `x -> z` support.
- Pack trained cache files into a compact `.dcgan_theano` model.
- Upgrade an older packed model layout to the newer key layout.
- Add or compare entries in the training configuration table.
- Explain cache directories, sample grids, logs, model checkpoints, and web
  pages emitted during training.
- Advise how to extend iGAN with a custom Theano generative model class after
  training data and model packing are understood.

## Route Elsewhere

- For loading a pre-trained `.dcgan_theano` model, sampling images, or model
  download planning, use [model-inference](../model-inference/SKILL.md).
- For interactive drawing UI behavior, PyQt4 windows, brush tools, and display
  issues, use [interactive-ui](../interactive-ui/SKILL.md).
- For non-UI constrained generation from color, mask, and edge inputs, use
  [constraint-generation](../constraint-generation/SKILL.md).
- For running image projection or reconstruction at inference time, use
  [image-projection](../image-projection/SKILL.md); keep predictor training
  and predictor batchnorm planning here.
- For general installation/import failures not tied to training scripts, check
  the root troubleshooting reference if one is available, then return here for
  training-specific symptoms.

## First Checks

1. Identify the intended model name, image size, and channel count.
2. Decide whether the user already has an HDF5 dataset or only an image folder.
3. Confirm whether the work is planning-only or a real legacy training run.
4. For any real training run, require an explicit legacy Python/Theano/CUDA plan;
   modern CPU-only Python environments are enough for this sub-skill's helpers
   but not for native DCGAN training.
5. Check disk budget before suggesting a public HDF5 archive; several archives
   are multi-gigabyte compressed files.
6. Check cache and output paths before packing; packing only includes model
   files that already exist.

## Safe Bundled Helpers

- Use `scripts/igan_dataset_urls.py --list` to list known public HDF5 archives,
  compressed sizes, and URL/target path plans without network access.
- Use `scripts/igan_dataset_urls.py --dataset shoes_64 --output-dir datasets`
  to reproduce the download target naming convention in dry-run form.
- Use `scripts/inspect_dataset_plan.py --mode dir --dataset-dir images --width 64 --channel 3 --hdf5-file datasets/custom.hdf5`
  to preflight a custom image directory and report the intended `imgs` shape
  and train/test split without writing HDF5.
- Add `--model-name hed_shoes_64` or another known config to the preflight script
  when you want width/channel mismatch warnings.
- Add `--json` to either helper when another tool needs deterministic structured
  output.

## Main References

- [training-workflows.md](references/training-workflows.md) gives runnable
  command templates for dataset acquisition planning, HDF5 conversion, DCGAN
  training, batchnorm estimation, predictor training, packing, upgrading, and
  custom model extension.
- [data-formats.md](references/data-formats.md) explains public dataset names,
  HDF5 schema, image preprocessing, Fuel split metadata, cache outputs, and
  packed model keys.
- [configuration.md](references/configuration.md) summarizes model configuration
  functions, default hyperparameters, CLI options, and path conventions.
- [troubleshooting.md](references/troubleshooting.md) maps concrete symptoms to
  likely causes and recovery steps for legacy Theano/CUDA, Fuel/HDF5, OpenCV,
  predictor, packing, and script-typo failures.

## Dataset Decision Pattern

1. If the user wants one of the public domains, run the URL planner first.
2. If network or disk budget is not approved, stop at a plan and mark the native
   dataset download case as skipped.
3. If the user has local images, run the dataset preflight helper before any
   conversion command.
4. Keep the conversion output name explicit; the training scripts otherwise
   assume `datasets/<model_name>.hdf5`.
5. Make the model configuration match the dataset width and channel count.

## Training Decision Pattern

1. Start from an HDF5 file with an `imgs` dataset and `train`/`test` Fuel split.
2. Run DCGAN training only in a compatible legacy GPU environment.
3. Estimate DCGAN batchnorm after generator/discriminator checkpoints exist.
4. Train the optional predictor only when image projection through `cnn` or
   `cnn_opt` needs a learned `x -> z` network.
5. Estimate predictor batchnorm after predictor parameters exist.
6. Pack all available model and batchnorm artifacts into one `.dcgan_theano`
   file for downstream inference and UI workflows.

## Corrected End-to-End Sequence

Use this corrected order when reconstructing the legacy shell recipe:

1. `train_dcgan.py`
2. `batchnorm_dcgan.py`
3. `train_predict_z.py` when predictor support is wanted
4. `batchnorm_predict_z.py` when predictor support is wanted
5. `pack_model.py`

The historical shell recipe misspelled the fourth command as
`batchnorm_precit_z.py`; that file is not part of the workflow. Always use the
correct `batchnorm_predict_z.py` command shown in the reference.

## Verification Expectations

- The bundled helpers should run with `python <script> --help` on any modern
  Python 3 environment.
- The URL helper can be checked without network by comparing names, URLs, sizes,
  and target paths.
- The dataset preflight helper can be checked with a tiny directory of fake or
  real image-named files because it only inspects names and plans shapes.
- Native HDF5 creation is optional CPU verification if OpenCV, h5py, and Fuel
  are installed.
- Native DCGAN training, DCGAN batchnorm, predictor training, predictor
  batchnorm, and real projection-dependent checks are optional expensive CUDA
  cases unless a compatible legacy stack and artifacts are provided.

## Operating Reminders

- Do not present planning helper output as proof that a model was trained.
- Do not hide legacy constraints: the original code targets Python2-era Theano,
  CUDA, cuDNN, Fuel, Lasagne, and OpenCV APIs.
- Do not download public archives or delete ZIP files from inside this skill;
  only show a plan and ask for explicit execution outside the helper if needed.
- Do not point users back to source checkout files for routine workflows; this
  sub-skill and its references contain the needed commands and contracts.
- Keep inference-only questions out of this sub-skill even when they mention a
  trained model file; route them to model inference unless the question is about
  creating, packing, or upgrading that file.
