# Programmatic Workflows

## When to read

Read this to write Python code that samples from an existing
`stylegan2_pytorch` checkpoint. Use the training sub-skill first if no checkpoint
has been created.

## Load latest checkpoint and save a sample grid

This mirrors the README's `ModelLoader` pattern:

```python
import torch
from torchvision.utils import save_image
from stylegan2_pytorch import ModelLoader

loader = ModelLoader(
    base_dir='/path/to/run-base',  # directory where the CLI was invoked
    name='default'                 # CLI --name value
)

noise = torch.randn(1, 512).cuda()
styles = loader.noise_to_styles(noise, trunc_psi=0.7)
images = loader.styles_to_images(styles)
save_image(images, './sample.jpg')
```

`base_dir` must contain the default checkpoint layout:

```text
base_dir/models/<name>/model_<n>.pt
base_dir/models/<name>/.config.json
```

If the training run used custom `--models_dir`, `ModelLoader` may not find it.
Either recreate the default layout under a base directory or instantiate
`Trainer` directly with the matching `models_dir`.

## Load a specific checkpoint

```python
loader = ModelLoader(base_dir='/path/to/run-base', name='my-project', load_from=12)
```

Use this when the user says an earlier checkpoint generated better samples than
the latest one.

## Generate multiple samples

```python
import torch
from torchvision.utils import save_image
from stylegan2_pytorch import ModelLoader

count = 16
loader = ModelLoader(base_dir='/path/to/run-base', name='my-project')
noise = torch.randn(count, 512).cuda()
styles = loader.noise_to_styles(noise, trunc_psi=0.75)
images = loader.styles_to_images(styles)
save_image(images, 'samples.png', nrow=4)
```

Memory scales with `count`, image size, and network capacity saved in the
checkpoint's config. Lower `count` first if sampling runs out of memory.

## Use the bundled helper

After a checkpoint exists, use:

```bash
python sub-skills/programmatic-api/scripts/sample_from_checkpoint.py \
  --base-dir /path/to/run-base \
  --name my-project \
  --output-dir /tmp/sg2-samples \
  --count 4 \
  --trunc-psi 0.75
```

The helper checks CUDA, verifies that the default checkpoint directory exists,
loads the requested checkpoint, and writes one grid image.

## Direct `Trainer` use for custom layouts

When the user trained with custom directories and cannot reshape them into the
`ModelLoader` default layout, use `Trainer` directly:

```python
from stylegan2_pytorch import Trainer

trainer = Trainer(
    name='my-project',
    base_dir='/path/to/base',
    models_dir='/path/to/custom-models',
    results_dir='/path/to/custom-results'
)
trainer.load(-1)
trainer.evaluate(num=0)
```

Direct `Trainer` use is advanced. Keep architecture settings aligned with the
checkpoint config, and prefer CLI routes for normal training/generation.

## Transparent model sampling

Transparent training writes `.png` outputs and uses RGBA tensors. When sampling
programmatically, save PNG output and verify downstream tools preserve alpha:

```python
save_image(images, 'transparent-samples.png', nrow=4)
```

Do not infer transparency only from the requested filename. The loaded
`.config.json` controls whether the trained model was transparent.
