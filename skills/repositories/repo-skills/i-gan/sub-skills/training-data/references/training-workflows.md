# iGAN Training and Data Workflows

This reference turns the legacy iGAN training scripts into safe, explicit
operating recipes. The commands shown here are for a user-managed checkout and a
user-approved legacy runtime. The bundled helper scripts in this sub-skill are
planning tools only and do not perform network, HDF5-write, training, or GPU
work.

## 1. Public HDF5 Dataset Planning

Use the bundled URL planner before downloading large public archives:

```bash
python scripts/igan_dataset_urls.py --list
python scripts/igan_dataset_urls.py --dataset shoes_64 --output-dir datasets
python scripts/igan_dataset_urls.py --dataset outdoor_128 --json
```

The planner reports the archive URL, expected ZIP target, expected HDF5 target,
compressed size, domain, image resolution, channel count, and a conservative
peak-disk warning. It intentionally does not run `wget`, `unzip`, or `rm`.

If the user approves a real download, the legacy shell behavior is equivalent
to:

```bash
FILE=shoes_64
URL="http://efrosgans.eecs.berkeley.edu/iGAN/datasets/${FILE}.zip"
wget -N "$URL" -O "datasets/${FILE}.zip"
unzip "datasets/${FILE}.zip" -d datasets/
rm -f "datasets/${FILE}.zip"
```

Keep the ZIP until the HDF5 file is confirmed when debugging; deleting it is
only a cleanup step, not part of validation.

## 2. Custom Image Directory Preflight

Run the dry-run preflight before converting a custom image collection:

```bash
python scripts/inspect_dataset_plan.py \
  --mode dir \
  --dataset-dir ./images \
  --width 64 \
  --channel 3 \
  --hdf5-file datasets/custom_64.hdf5
```

Useful variants:

```bash
python scripts/inspect_dataset_plan.py --mode dir --dataset-dir ./edges --width 64 --channel 1 --model-name hed_shoes_64 --hdf5-file datasets/edges.hdf5
python scripts/inspect_dataset_plan.py --mode dir --dataset-dir ./images --recursive --json --hdf5-file datasets/images.hdf5
```

The helper reports the intended `imgs` shape, train/test split, ignored file
names, and compatibility warnings. It does not import OpenCV, h5py, Fuel, or
Theano and does not write the HDF5 file.

A real conversion in a compatible environment uses the legacy conversion script
pattern:

```bash
python create_hdf5.py \
  --dataset_dir ./images \
  --width 64 \
  --mode dir \
  --channel 3 \
  --hdf5_file datasets/custom_64.hdf5
```

For grayscale sketch or edge datasets, pass `--channel 1` explicitly. Do not
rely on defaults when reproducing older Python2 behavior.

## 3. HDF5 Readiness Gate

Before training, confirm:

- The file path passed with `--data_file` exists.
- Dataset `imgs` exists and has shape `(N, width, width, channel)`.
- `imgs` is `uint8` image data before the training transform.
- Dimension labels are `batch`, `height`, `width`, and `channel` if created by
  the legacy converter.
- File attributes include a Fuel-compatible `split` value with `train` and
  `test` sets.
- The training config selected by `--model_name` has matching `npx` and `nc`.

The loader opens `H5PYDataset(path, which_sets=('train',))` and
`H5PYDataset(path, which_sets=('test',))`, then builds shuffled or sequential
Fuel data streams. Missing split metadata is a data-format error even if the
raw `imgs` array exists.

## 4. DCGAN Training

Real DCGAN training is a legacy GPU workflow. Use a command pattern like:

```bash
THEANO_FLAGS='device=gpu0, floatX=float32, nvcc.fastmath=True' \
python train_dcgan.py \
  --model_name shoes_64 \
  --data_file datasets/shoes_64.hdf5 \
  --cache_dir train_cache/shoes_64 \
  --batch_size 128 \
  --update_k 2 \
  --save_freq 1 \
  --lr 0.0002 \
  --weight_decay 0.00001 \
  --b1 0.5
```

Default behavior if arguments are omitted:

- `--data_file` defaults to `../datasets/<model_name>.hdf5` relative to the
  training script directory.
- `--cache_dir` defaults to `./cache/<model_name><ext>/`.
- `--batch_size` defaults to `128`.
- `--update_k` defaults to two discriminator updates per generator update.
- The train loop runs `niter + niter_decay` epochs from the selected config.

Expected cache outputs:

- `samples/real_samples.png` after loading the test split.
- `samples/gen_*.png` generated at each epoch.
- `web_dcgan/` HTML pages showing generated samples.
- `models/disc_params` and `models/gen_params` latest checkpoints.
- Numbered checkpoints such as `disc_params_001` and `gen_params_001` when
  `--save_freq` divides the epoch count.
- `log/training_log.ndjson` with epoch, update count, examples, seconds,
  generator cost, and discriminator cost.

## 5. DCGAN Batchnorm Estimation

After `disc_params` and `gen_params` exist, estimate batchnorm statistics for
packed inference:

```bash
THEANO_FLAGS='device=gpu0, floatX=float32, nvcc.fastmath=True' \
python batchnorm_dcgan.py \
  --model_name shoes_64 \
  --cache_dir train_cache/shoes_64 \
  --batch_size 128 \
  --num_batches 1000
```

Outputs under `models/`:

- `gen_batchnorm`
- `disc_batchnorm`

This step samples latent vectors and runs Theano functions; it does not read the
HDF5 dataset, but it still needs the trained generator and discriminator
parameters plus the legacy GPU stack.

## 6. Optional Predictor Training

Train the predictor only if downstream image projection should use the learned
`cnn` or `cnn_opt` solver path. The predictor maps images to latent vectors and
uses the trained generator plus AlexNet feature loss.

```bash
THEANO_FLAGS='device=gpu0, floatX=float32, nvcc.fastmath=True' \
python train_predict_z.py \
  --model_name shoes_64 \
  --data_file datasets/shoes_64.hdf5 \
  --cache_dir train_cache/shoes_64 \
  --batch_size 128 \
  --save_freq 1 \
  --lr 0.0002 \
  --weight_decay 0.00001 \
  --b1 0.5 \
  --layer conv4 \
  --alpha 0.002
```

Prerequisites:

- `models/gen_params` from DCGAN training.
- `models/gen_batchnorm` from DCGAN batchnorm estimation.
- A compatible AlexNet model for the selected feature layer.
- Lasagne, OpenCV, Theano, and the legacy CUDA/cuDNN stack.

Expected outputs:

- `models/predict_params` latest predictor checkpoint.
- Numbered predictor checkpoints.
- `rec/rec_epoch_*.png` reconstructions.
- `web_rec/` reconstruction pages.
- `log/training_predict_log.ndjson`.

## 7. Optional Predictor Batchnorm Estimation

After `predict_params` exists, estimate predictor batchnorm:

```bash
THEANO_FLAGS='device=gpu0, floatX=float32, nvcc.fastmath=True' \
python batchnorm_predict_z.py \
  --model_name shoes_64 \
  --data_file datasets/shoes_64.hdf5 \
  --cache_dir train_cache/shoes_64 \
  --batch_size 128 \
  --num_batches 1000
```

Output:

- `models/predict_batchnorm`

This step reads the HDF5 training stream and stops after `batch_size *
num_batches` examples or the available training split, whichever is smaller.

## 8. Corrected End-to-End Sequence

The corrected order is:

```bash
MODEL_NAME=shoes_64
CACHE_DIR=train_cache/${MODEL_NAME}
DATA_FILE=datasets/${MODEL_NAME}.hdf5

THEANO_FLAGS='device=gpu0, floatX=float32, nvcc.fastmath=True' \
python train_dcgan.py --model_name "$MODEL_NAME" --data_file "$DATA_FILE" --cache_dir "$CACHE_DIR"

THEANO_FLAGS='device=gpu0, floatX=float32, nvcc.fastmath=True' \
python batchnorm_dcgan.py --model_name "$MODEL_NAME" --cache_dir "$CACHE_DIR"

THEANO_FLAGS='device=gpu0, floatX=float32, nvcc.fastmath=True' \
python train_predict_z.py --model_name "$MODEL_NAME" --data_file "$DATA_FILE" --cache_dir "$CACHE_DIR"

THEANO_FLAGS='device=gpu0, floatX=float32, nvcc.fastmath=True' \
python batchnorm_predict_z.py --model_name "$MODEL_NAME" --data_file "$DATA_FILE" --cache_dir "$CACHE_DIR"

python pack_model.py --model_name "$MODEL_NAME" --cache_dir "$CACHE_DIR" --output_model "models/${MODEL_NAME}.dcgan_theano"
```

The historical shell recipe contains the typo `batchnorm_precit_z.py`. Replace
it with `batchnorm_predict_z.py`; otherwise the sequence fails with a missing
file before predictor batchnorm can be saved.

## 9. Model Packing

Packing is CPU-side pickle work once cache artifacts exist:

```bash
python pack_model.py \
  --model_name shoes_64 \
  --cache_dir train_cache/shoes_64 \
  --output_model models/shoes_64.dcgan_theano
```

The packer checks for these keys under `<cache_dir>/models/` and includes only
files that exist:

- `disc_params`
- `gen_params`
- `disc_batchnorm`
- `gen_batchnorm`
- `predict_params`
- `predict_batchnorm`

A packed file without predictor keys can still support ordinary generation and
UI use, but projection modes that rely on predictor inference will be limited.

## 10. Upgrading Older Packed Models

Older packed models may store batchnorm and predictor keys under legacy names.
Upgrade with:

```bash
python upgrade_model.py \
  --old_model models/old_shoes_64.dcgan_theano \
  --new_model models/shoes_64.dcgan_theano
```

Expected legacy input keys:

- `disc_params`
- `gen_params`
- `predict_params`
- `postlearn_predict_params`
- `postlearn_params` containing discriminator and generator batchnorm values

Expected new output keys:

- `disc_params`
- `gen_params`
- `predict_params`
- `predict_batchnorm`
- `gen_batchnorm`
- `disc_batchnorm`

## 11. Custom Generative Model Extension

The legacy architecture routes UI code to a Python optimization wrapper, then to
a Theano constrained optimizer, and finally to a model implementation class.
For a custom Theano generative model:

1. Train or otherwise provide a model class with the same interface as the
   DCGAN Theano model class used by iGAN.
2. Place the class in the model-definition layer used by your checkout.
3. Ensure the class exposes compatible generation, transform, inverse transform,
   and optional predictor/batchnorm behavior.
4. Pack any required parameters into a single model file or adjust the model
   loader consistently.
5. Launch downstream inference with `--model_type <your_model_type>` only after
   the loading and generation smoke path works.

TensorFlow support was described as planned rather than implemented in the
legacy training notes. Treat TensorFlow backend replacement as a new extension
project, not a drop-in training flag.
