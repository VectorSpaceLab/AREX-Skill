# iGAN Training Configuration Reference

## Model Configuration Table

The training configuration functions return:

```text
npx, n_layers, n_f, nc, nz, niter, niter_decay
```

| Model name | npx | n_layers | n_f | nc | nz | niter | niter_decay |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `shoes_64` | 64 | 3 | 128 | 3 | 100 | 25 | 25 |
| `outdoor_64` | 64 | 3 | 128 | 3 | 100 | 15 | 15 |
| `church_64` | 64 | 3 | 128 | 3 | 100 | 25 | 25 |
| `handbag_64` | 64 | 3 | 128 | 3 | 100 | 25 | 25 |
| `hed_shoes_64` | 64 | 3 | 128 | 1 | 100 | 25 | 25 |
| `sketch_shoes_64` | 64 | 3 | 128 | 1 | 100 | 25 | 25 |
| `shoes_128` | 128 | 4 | 64 | 3 | 100 | 25 | 25 |

The dataset preflight helper can compare a planned dataset against these known
values:

```bash
python scripts/inspect_dataset_plan.py --mode dir --dataset-dir ./images --width 64 --channel 3 --model-name shoes_64 --hdf5-file datasets/shoes_64.hdf5
```

## `train_dcgan.py` CLI

Purpose: train generator and discriminator from an HDF5 dataset.

Important arguments:

| Argument | Default | Meaning |
| --- | --- | --- |
| `--model_name` | `shoes_64` | Selects the configuration function and default dataset name. |
| `--ext` | empty | Appended to `model_name` for experiment/cache naming. |
| `--data_file` | `../datasets/<model_name>.hdf5` | HDF5 file with Fuel split metadata. |
| `--cache_dir` | `./cache/<model_name><ext>/` | Stores samples, logs, checkpoints, and web pages. |
| `--batch_size` | `128` | Examples per batch. |
| `--update_k` | `2` | Discriminator updates per generator update schedule. |
| `--save_freq` | `1` | Epoch frequency for numbered checkpoints. |
| `--lr` | `0.0002` | Initial Adam learning rate. |
| `--weight_decay` | `1e-5` | L2 regularization. |
| `--b1` | `0.5` | Adam momentum term. |

The learning rate is linearly decayed after `niter` epochs for `niter_decay`
additional epochs.

## `batchnorm_dcgan.py` CLI

Purpose: estimate generator and discriminator batchnorm statistics after DCGAN
training.

| Argument | Default | Meaning |
| --- | --- | --- |
| `--model_name` | `shoes_64` | Selects architecture dimensions. |
| `--ext` | empty | Appended to cache experiment name. |
| `--batch_size` | `128` | Latent samples per batch. |
| `--num_batches` | `1000` | Number of latent batches for statistics. |
| `--cache_dir` | `./cache/<model_name><ext>/` | Must contain `models/disc_params` and `models/gen_params`. |

Outputs: `models/gen_batchnorm` and `models/disc_batchnorm`.

## `train_predict_z.py` CLI

Purpose: train image-to-latent predictor for projection workflows.

| Argument | Default | Meaning |
| --- | --- | --- |
| `--model_name` | `shoes_64` | Selects architecture dimensions. |
| `--ext` | empty | Appended to cache experiment name. |
| `--data_file` | `../datasets/<model_name>.hdf5` | HDF5 file for image batches. |
| `--cache_dir` | `./cache/<model_name><ext>/` | Must contain generator params and batchnorm. |
| `--batch_size` | `128` | Examples per batch. |
| `--save_freq` | `1` | Epoch frequency for numbered predictor checkpoints. |
| `--lr` | `0.0002` | Adam learning rate. |
| `--weight_decay` | `1e-5` | L2 regularization. |
| `--b1` | `0.5` | Adam momentum term. |
| `--layer` | `conv4` | AlexNet layer used for feature loss. |
| `--alpha` | `0.002` | Feature loss weight in `pixel_loss + alpha * feature_loss`. |

Outputs: `models/predict_params`, reconstruction samples, web pages, and
`log/training_predict_log.ndjson`.

## `batchnorm_predict_z.py` CLI

Purpose: estimate predictor batchnorm statistics after predictor training.

| Argument | Default | Meaning |
| --- | --- | --- |
| `--model_name` | `shoes_64` | Selects architecture dimensions. |
| `--ext` | empty | Appended to cache experiment name. |
| `--data_file` | `../datasets/<model_name>.hdf5` | HDF5 file for image batches. |
| `--batch_size` | `128` | Examples per batch. |
| `--num_batches` | `1000` | Maximum number of batches to read. |
| `--cache_dir` | `./cache/<model_name><ext>/` | Must contain `models/predict_params`. |

Output: `models/predict_batchnorm`.

## `pack_model.py` CLI

Purpose: collect cache model files into one compact model pickle.

| Argument | Default | Meaning |
| --- | --- | --- |
| `--model_name` | `shoes_64` | Used for default cache/model naming. |
| `--cache_dir` | `./cache/<model_name><ext>/` | Contains `models/` files to pack. |
| `--output_model` | `<cache_dir>/<model_name><ext>.dcgan_theano` | Destination packed model. |
| `--ext` | empty | Appended to experiment name. |

Missing files are reported and omitted. Inspect packed keys before relying on
projection or predictor behavior.

## `upgrade_model.py` CLI

Purpose: remap older packed model keys into the newer key layout.

| Argument | Default | Meaning |
| --- | --- | --- |
| `--old_model` | `../models/shoes_64.dcgan_theano` | Legacy packed model path. |
| `--new_model` | `<old_model>_new.dcgan_theano` | Output model path if omitted. |

The old model must contain `postlearn_params` for discriminator/generator
batchnorm and `postlearn_predict_params` for predictor batchnorm.

## Runtime Flags

Most native training commands require Theano flags similar to:

```bash
THEANO_FLAGS='device=gpu0, floatX=float32, nvcc.fastmath=True'
```

Adjust `device=gpu0` only when the legacy environment actually exposes a
compatible GPU device. Do not treat `device=cpu` as equivalent for full training
or interactive performance.
