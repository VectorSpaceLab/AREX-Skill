# pix2code Package Overview

## Purpose

Read this for shared facts about the pix2code repository layout, source modules, dependency constraints, and research-code assumptions. Use the sub-skills for workflow-specific steps.

## Repository purpose

pix2code demonstrates a 2017 end-to-end neural system that maps one GUI screenshot to a simple intermediate DSL and then compiles that DSL into platform scaffold code. The README and paper frame the project as educational research, not a production UI generator.

## Source layout

| Area | Role |
| --- | --- |
| `model/` | Legacy model workflows: dataset split, image-to-array conversion, Keras/TensorFlow model definition, training, single-image sampling, and batch generation. |
| `model/classes/` | Runtime classes for `Vocabulary`, image utilities, `Sampler`, beam search, `Dataset`, generator batches, and model configuration constants. |
| `compiler/` | DSL parser/compiler workflows for web, Android, and iOS output. |
| `compiler/assets/` | Token-to-template mappings for the three target platforms. |
| `datasets/` | Multi-part zip archives for the official datasets. Do not unpack these unless the user explicitly needs the data and accepts storage/time cost. |

## Important verified constants and APIs

- `model/classes/model/Config.py` sets `CONTEXT_LENGTH = 48`, `IMAGE_SIZE = 256`, `BATCH_SIZE = 64`, `EPOCHS = 10`, and `STEPS_PER_EPOCH = 72000`.
- `compiler/classes/Compiler.Compiler.compile(input_file_path, output_file_path, rendering_function=None)` parses a `.gui` file and writes rendered platform code.
- `model/classes/Vocabulary.py` defines `START_TOKEN = "<START>"`, `END_TOKEN = "<END>"`, `PLACEHOLDER = " "`, and `SEPARATOR = "->"`.
- `model/classes/dataset/Dataset.Dataset.load(path, generate_binary_sequences=False)` discovers paired `.gui` plus `.png` or `.npz` files in one directory and expands each token into context/next-word training examples.

## Dependency constraints

The original requirements target a legacy stack: Keras 2.1.2, TensorFlow 1.4.0, NumPy 1.13.3, h5py 2.7.1, and OpenCV 3.3.0.10. Modern Python versions usually cannot run this exact stack. Use a legacy Python environment and expect the exact OpenCV pin to require a nearby compatible old wheel if the original wheel is unavailable.

Do not infer paper-quality results from import success. Full model training originally took hours per dataset on a GPU, and trained model artifacts are not part of this checkout.

## Runtime data contracts

A pix2code sample is identified by a shared basename:

```text
sample_id.gui
sample_id.png
```

The `.gui` file is tokenized line-by-line. Commas and newlines are turned into explicit tokens during dataset loading. For array-preprocessed datasets, the image becomes:

```text
sample_id.npz   # contains key: features
sample_id.gui
```

A trained artifact directory must contain:

```text
pix2code.json        # Keras architecture
pix2code.h5          # weights
meta_dataset.npy     # array containing input shape, output size, dataset size
words.vocab          # serialized vocabulary rows using token->one-hot-vector
```

## Skill-owned helpers

- [../scripts/check_pix2code_environment.py](../scripts/check_pix2code_environment.py) checks optional imports and warns about legacy-stack issues.
- [../sub-skills/data-and-training/scripts/prepare_pix2code_dataset.py](../sub-skills/data-and-training/scripts/prepare_pix2code_dataset.py) validates, splits, and optionally converts pix2code datasets.
- [../sub-skills/sampling-and-generation/scripts/check_pix2code_artifacts.py](../sub-skills/sampling-and-generation/scripts/check_pix2code_artifacts.py) validates trained model artifact directories.
- [../sub-skills/dsl-compilation/scripts/compile_gui.py](../sub-skills/dsl-compilation/scripts/compile_gui.py) compiles `.gui` files without depending on the original checkout.
