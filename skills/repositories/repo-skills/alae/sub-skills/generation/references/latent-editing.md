# ALAE latent editing and principal directions

ALAE's latent editing routes operate in W/dlatent space. The interactive demo and traversal figure script both consume `principal_directions/direction_<idx>.npy` vectors and assume the vectors match the model checkpoint and latent dimensionality.

## Committed direction labels

The current demo/traversal routes use this subset of CelebA attribute classifier indices:

| Index | File | Interactive label | Traversal output label |
| ---: | --- | --- | --- |
| 0 | `principal_directions/direction_0.npy` | `gender` | `gender` |
| 1 | `principal_directions/direction_1.npy` | `smile` | `smile` |
| 2 | `principal_directions/direction_2.npy` | `attractive` | not emitted by `make_traversarls.py` |
| 3 | `principal_directions/direction_3.npy` | `wavy-hair` | `wavy-hair` |
| 4 | `principal_directions/direction_4.npy` | `young` | `young` |
| 10 | `principal_directions/direction_10.npy` | `big lips` | `big_lips` |
| 11 | `principal_directions/direction_11.npy` | `big nose` | `big_nose` |
| 17 | `principal_directions/direction_17.npy` | `chubby` | `chubby` |
| 19 | `principal_directions/direction_19.npy` | `glasses` | `glasses` |

Use the bundled checker before traversals or the GUI:

```bash
python scripts/check_principal_directions.py \
  --repo-root <ALAE-checkout> \
  --inspect-shapes
```

For FFHQ-style checkpoints, the expected committed vectors are one-dimensional 512-element arrays. A different latent size or a different model family requires regenerated vectors.

## FFHQ-model-specific warning

The repository's `principal_directions/README.md` states that the committed `direction_*.npy` files were computed for the FFHQ model `ffhq/model_157.pth`. Treat them as FFHQ-specific operating assets. They may still load for another 512-dimensional checkpoint, but the attribute semantics can be wrong because the W-space basis and generator distribution changed.

For `celeba`, `celeba-hq256`, `bedroom`, a custom trained checkpoint, or any config with a different latent space, regenerate the directions and replace or point to a separate `principal_directions` directory. Do not present non-FFHQ slider effects as validated unless regeneration was run for that checkpoint.

## Regeneration sequence

Regeneration is expensive and has network/runtime requirements. Do not run it during routine preflight. It requires a checkpoint, CUDA, TensorFlow 1.x TFRecord APIs, `dnnlib`, scikit-learn, local cache space, and access to the CelebA-HQ attribute classifier pickle files used by `principal_directions/classifier.py`.

From the ALAE repository root with `PYTHONPATH` set:

```bash
export PYTHONPATH="$PYTHONPATH:$(pwd)"

python principal_directions/generate_images.py -c <config>
python principal_directions/extract_attributes.py -c <config>
python principal_directions/find_principal_directions.py
```

What each stage does:

1. `generate_images.py` loads the selected ALAE checkpoint, samples 60,000 latents, generates images, downsamples classifier inputs to 256x256, and writes `principal_directions/generated_data.000` with image data plus `lat` and `dlat` arrays.
2. `extract_attributes.py` loads classifier networks for indices `0, 1, 2, 3, 4, 10, 11, 17, 19`, scores the generated images, and writes `principal_directions/wspace_att_<idx>.npy` for each attribute.
3. `find_principal_directions.py` fits a linear SVM for each attribute using the saved dlatents and writes `principal_directions/direction_<idx>.npy`.

The README in the source folder contains typos in the example path names (`printipal_directions` and `find_printipal_directions.py`). Use the actual filenames listed above.

## Relationship to generation scripts

- `interactive_demo.py` loads all nine committed directions and exposes sliders for them.
- `make_figures/make_traversarls.py` loads individual direction files for a fixed set of hard-coded sample images and traversal ranges.
- Style mixing, random generation, and ordinary reconstruction figures do not need principal directions.

## Managing alternate direction sets

When keeping directions for multiple checkpoints:

1. Store each set in a clearly named directory outside generated skill files, for example under the active checkout or experiment output area.
2. Before launch, copy or symlink the selected `direction_<idx>.npy` files into the checkout's `principal_directions/` directory, or adapt the native scripts to read a custom directory.
3. Record the config name, checkpoint path from `last_checkpoint`, latent size, number of generated samples, and classifier/cache source used for the regenerated set.
4. Re-run `check_principal_directions.py --inspect-shapes` after moving or replacing files.

Never bundle binary `.npy` direction vectors inside this generated skill. This sub-skill only documents expected names and provides safe file checkers.
