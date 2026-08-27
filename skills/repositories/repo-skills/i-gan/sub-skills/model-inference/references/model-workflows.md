# iGAN model inference workflows

This reference is the self-contained replacement for reopening the repository's
model-zoo notes or sample-generation script. It covers pretrained model
selection, artifact planning, and safe command construction for random sample
generation.

## Scope and safety

The workflows here are split into safe planning and optional legacy execution.
The bundled helpers perform only planning and local file checks. They do not
open sockets, invoke `wget`, import Theano, compile CUDA kernels, import OpenCV,
train models, or write sample images.

Actual sample generation is optional and requires a compatible legacy runtime:
Python2-era Theano, CUDA/cuDNN support as documented by the original project,
OpenCV, local `model_def` and `lib` modules, and a downloaded model artifact.

## Model zoo

| Model | Target file | Public artifact URL | Preview evidence |
| --- | --- | --- | --- |
| `outdoor_64` | `models/outdoor_64.dcgan_theano` | `http://efrosgans.eecs.berkeley.edu/iGAN/models/theano_dcgan/outdoor_64.dcgan_theano` | real and generated sample PNGs are available under `/iGAN/samples/` using the same name prefix. |
| `church_64` | `models/church_64.dcgan_theano` | `http://efrosgans.eecs.berkeley.edu/iGAN/models/theano_dcgan/church_64.dcgan_theano` | LSUN church model previews use `church_64_real.png` and `church_64_dcgan.png`. |
| `handbag_64` | `models/handbag_64.dcgan_theano` | `http://efrosgans.eecs.berkeley.edu/iGAN/models/theano_dcgan/handbag_64.dcgan_theano` | handbag previews use `handbag_64_real.png` and `handbag_64_dcgan.png`. |
| `shoes_64` | `models/shoes_64.dcgan_theano` | `http://efrosgans.eecs.berkeley.edu/iGAN/models/theano_dcgan/shoes_64.dcgan_theano` | shoe previews use `shoes_64_real.png` and `shoes_64_dcgan.png`. |
| `hed_shoes_64` | `models/hed_shoes_64.dcgan_theano` | `http://efrosgans.eecs.berkeley.edu/iGAN/models/theano_dcgan/hed_shoes_64.dcgan_theano` | HED shoe sketch previews use `hed_shoes_64_real.png` and `hed_shoes_64_dcgan.png`; the model is one-channel. |

The artifact planner can emit this table as plain text or JSON and can check
whether the planned target file already exists.

```bash
python sub-skills/model-inference/scripts/igan_artifact_urls.py outdoor_64 --check-existing
python sub-skills/model-inference/scripts/igan_artifact_urls.py --all --json
python sub-skills/model-inference/scripts/igan_artifact_urls.py hed_shoes_64 --include-samples
```

If a user asks for a new model name, treat it as custom unless it exactly matches
one of the names above. For a custom model to work with `dcgan_theano.Model`, a
matching config function must exist and the model pickle must contain the
expected parameter keys described in [api-reference.md](api-reference.md).

## Artifact setup plan

1. Pick a model name from the model zoo.
2. Plan the model URL and target path:

   ```bash
   python sub-skills/model-inference/scripts/igan_artifact_urls.py shoes_64 --check-existing
   ```

3. If network access is allowed, download outside the helper using the emitted
   URL and target. Keep this as an explicit user-approved action because model
   artifacts are external files.
4. Verify the file exists at the target before attempting native generation:

   ```bash
   test -f models/shoes_64.dcgan_theano
   ```

5. Build the sample command with the model file and desired output image:

   ```bash
   python sub-skills/model-inference/scripts/build_model_command.py \
     --model_name shoes_64 \
     --model_file models/shoes_64.dcgan_theano \
     --output_image outputs/shoes_64_dcgan.png \
     --check-model
   ```

## Sample-generation command contract

The standalone generation command has these effective arguments:

| Argument | Default | Meaning |
| --- | --- | --- |
| `--model_name` | `outdoor_64` | Selects a config function and default model filename. |
| `--model_type` | `dcgan_theano` | Used by dynamic class lookup and default filename suffix. |
| `--framework` | `theano` | Informational framework argument preserved from the script. |
| `--model_file` | `./models/<model_name>.<model_type>` | Pickle-like artifact loaded by the Theano model. |
| `--output_image` | `<model_name>_<model_type>_samples.png` | Grid image written after sample generation. |

The documented generation behavior is fixed in the script: `n=196`,
`batch_size=49`, and a `14 x 14` grid assembled from generated samples. The
workflow converts output from the model's channel order into an image array and
uses OpenCV to write the final file.

## Build a command without running Theano

Use the bundled command builder whenever the caller needs a reproducible command
but the runtime may not have Theano, CUDA, cuDNN, OpenCV, or the artifact.

```bash
python sub-skills/model-inference/scripts/build_model_command.py \
  --model_name outdoor_64 \
  --output_image outdoor_64_dcgan.png \
  --check-model
```

Typical text output includes the model file, output image, environment plan,
argv vector, shell command, and model-file status. JSON output is useful for
verification scripts:

```bash
python sub-skills/model-inference/scripts/build_model_command.py \
  --model_name shoes_64 \
  --model_file models/shoes_64.dcgan_theano \
  --output_image outputs/shoes_grid.png \
  --check-model \
  --json
```

## Optional native execution

Only run the generated command when all prerequisites are intentionally
available. A conventional GPU invocation uses Theano flags similar to:

```bash
THEANO_FLAGS='device=gpu0,floatX=float32,nvcc.fastmath=True' \
python generate_samples.py --model_name outdoor_64 --output_image outdoor_64_dcgan.png
```

Native success signals:

- The process prints parsed arguments.
- It prints `LOADING...`, `load model from ...`, and `COMPILING...` messages.
- It prints `samples_shape` after generation.
- It writes the requested output image.

Native failure is expected on modern machines without a recreated legacy stack;
see [troubleshooting.md](troubleshooting.md) before changing code or claiming the
model is broken.

## Difficult synthetic cases this sub-skill supports

### shoes_64 explicit model/output command

Goal: produce a sample command without relying on defaults.

```bash
python sub-skills/model-inference/scripts/build_model_command.py \
  --model_name shoes_64 \
  --model_file models/shoes_64.dcgan_theano \
  --output_image outputs/shoes_grid.png \
  --check-model \
  --json
```

Expected assertions: `model_name` is `shoes_64`; `model_type` is
`dcgan_theano`; argv includes the explicit `--model_file` and `--output_image`;
missing/present status matches the local file system; no Theano import occurs.

### outdoor_64 missing-artifact URL plan

Goal: explain a missing artifact and provide the URL/target plan without a
network side effect.

```bash
python sub-skills/model-inference/scripts/igan_artifact_urls.py outdoor_64 --check-existing --json
```

Expected assertions: URL is the `theano_dcgan/outdoor_64.dcgan_theano` public
artifact; target is `models/outdoor_64.dcgan_theano`; status is `missing` or
`present`; the helper does not download the file.

## Handoff checklist

When handing this workflow to another agent, include:

- selected model name and whether it is a known model-zoo entry;
- model artifact URL and intended target;
- whether the model file exists locally;
- generated sample command and `THEANO_FLAGS` plan;
- output image path;
- whether native execution was attempted;
- observed native signals or unresolved blockers.
