# Generation workflows

Run commands from an environment where the installed `mattergen` package and
its optional runtime dependencies are available. These examples are intentionally
small enough to use as smoke-test templates; the model still performs a real
sampling job when invoked.

## Validate without running

The bundled helper is the first stop because it does not import MatterGen,
contact the Hub, load a checkpoint, or start a diffusion job unless `--run` is
present:

```bash
python <mattergen-skill-root>/sub-skills/generation/scripts/generate_materials.py \
  --pretrained-name mattergen_base \
  --batch-size 1 --num-batches 1
```

It prints normalized JSON and warnings. Add `--help` to see the helper's
options. The helper uses hyphenated option names; the native Fire CLI uses the
function's underscore names.

## Native CLI: unconditional

The installed console entry point is `mattergen-generate` and its required first
argument is the output directory:

```bash
mattergen-generate results/base \
  --pretrained-name=mattergen_base --batch_size=1 --num_batches=1
```

The source CLI uses `fire.Fire(main)`. In particular, mappings need shell
quoting and Fire's dictionary syntax must not contain whitespace around the
colon. A safe native example is:

```bash
mattergen-generate results/mag \
  --pretrained-name=dft_mag_density --batch_size=1 --num_batches=1 \
  --properties_to_condition_on="{'dft_mag_density':0.15}" \
  --diffusion_guidance_factor=2.0
```

For a local checkpoint directory, replace the named model with
`--model_path=/path/to/checkpoint-dir`; do not pass both flags.

## Multi-property conditioning

The selected model must have been trained with every requested property. For the
catalog's jointly trained examples:

```bash
mattergen-generate results/ehull \
  --pretrained-name=chemical_system_energy_above_hull \
  --batch_size=1 --num_batches=1 \
  --properties_to_condition_on="{'energy_above_hull':0.05,'chemical_system':'Li-O'}" \
  --diffusion_guidance_factor=2.0

mattergen-generate results/mag-hhi \
  --pretrained-name=dft_mag_density_hhi_score \
  --batch_size=1 --num_batches=1 \
  --properties_to_condition_on="{'dft_mag_density':0.15,'hhi_score':0.5}" \
  --diffusion_guidance_factor=2.0
```

A condition key accepted by the package registry can still fail at runtime if it
is not in the chosen model's condition embeddings. Treat a checkpoint config as
the source of truth for local/fine-tuned models.

## CSP composition targeting

CSP models do not denoise element identities. The composition list is therefore
not a general-purpose filter for a normal MatterGen checkpoint. The native
source CLI expects a Fire list of JSON strings and the CSP sampling config:

```bash
mattergen-generate results/na-cl \
  --model_path=/path/to/csp-checkpoint-dir \
  --batch_size=1 --num_batches=1 \
  --target_compositions='[{"Na":1,"Cl":1}]' \
  --sampling-config-name=csp
```

The exact Fire option is `--target_compositions`; the helper offers repeated
`--target-composition` / `--target-compositions` mapping options for easier
validation. Each composition must be a non-empty mapping of valid-looking
chemical symbols to positive integer counts. Keep the requested total within
the model's supported atom-count regime (the released MatterGen models were
trained/evaluated up to 20 atoms per unit cell).

## Explicit safe-helper execution

After a dry validation, `--run` deliberately invokes the installed public
MatterGen API. A named model may download from Hugging Face at this point:

```bash
python <mattergen-skill-root>/sub-skills/generation/scripts/generate_materials.py \
  --pretrained-name mattergen_base --output-dir results/base \
  --batch-size 1 --num-batches 1 --no-record-trajectories --run
```

For a local checkpoint:

```bash
python <mattergen-skill-root>/sub-skills/generation/scripts/generate_materials.py \
  --model-path /path/to/checkpoint-dir --output-dir results/local \
  --batch-size 1 --num-batches 1 --checkpoint-epoch last --run
```

The helper refuses conflicting checkpoint flags, malformed mappings, missing
local checkpoint directories, nonpositive sizes, CSP without `csp`, and property
conditioning without a mapping. It does not pretend that a CUDA device or an
installed Python import proves that checkpoint assets are present.

## Python API pattern

```python
from mattergen.common.utils.data_classes import MatterGenCheckpointInfo
from mattergen.generator import CrystalGenerator

checkpoint = MatterGenCheckpointInfo.from_hf_hub(
    "mattergen_base", config_overrides=[]
)
generator = CrystalGenerator(
    checkpoint_info=checkpoint,
    batch_size=1,
    num_batches=1,
    diffusion_guidance_factor=0.0,
    record_trajectories=False,
)
structures = generator.generate(output_dir="results/api")
```

For a local checkpoint, construct `MatterGenCheckpointInfo(model_path=...,` with
`load_epoch="last"` (or `"best"`/an integer), then pass it to the same
constructor. For CSP, pass `target_compositions_dict=[{"Na": 1, "Cl": 1}]`,
`sampling_config_name="csp"`, and a CSP-compatible checkpoint.

## Overrides and reproducibility

- `config_overrides` change model config composition; use them sparingly and
  keep the element-mask override behavior of the native CLI when filtering
  unsupported elements.
- `sampling_config_overrides` change sampler/condition-loader settings. Examples
  include `condition_loader_partial.batch_size=1`, but the generator itself
  appends its batch and sample count overrides for normal sampling.
- `sampling_config_path` must be a directory; `sampling_config_name` is a file
  basename. The shipped `default.yaml` includes atomic-number denoising and the
  shipped `csp.yaml` does not.
- Record model name/path (without exposing private host paths in a published
  report), checkpoint epoch, config overrides, sampling config name/path,
  sampling overrides, guidance, batch counts, trajectory choice, device, and
  output file hashes in an experiment record.
