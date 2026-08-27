# Workflows

## Purpose

Use this reference to choose the right data generator and to understand what each generator yields before you hand the data to a model.

## Workflow selection matrix

| User goal | Recommended generator | Why |
| --- | --- | --- |
| Train pairwise registration from two scans | `scan_to_scan` | Simplest random source/target pairing. |
| Train against a fixed atlas | `scan_to_atlas` | Reuses a single atlas batch across source scans. |
| Add label supervision to registration | `semisupervised` | Converts discrete labels to probability volumes. |
| Build an unconditional template | `template_creation` | Produces a single scan input plus template-style outputs. |
| Build a conditional template | `conditional_template_creation` | Adds phenotype vectors alongside atlas and scan data. |
| Learn from surface distances and point clouds | `surf_semisupervised` | Produces signed-distance volumes and surface point samples. |
| Train without real scans using label maps | `synthmorph` | Emits paired label maps and ignores a dummy target. |

## Common preprocessing flow

1. Load or prepare local volume files.
2. Verify the file shape and key layout with `scripts/validate_vxm_npz.py` when the inputs are `.npz`.
3. Decide whether the downstream consumer expects:
   - only image tensors,
   - image plus segmentation tensors,
   - one-hot/probability label stacks,
   - surface point clouds,
   - or synthesized label maps.
4. Pick the generator whose output list already matches that consumer.
5. Convert the NumPy outputs to the downstream framework only after the generator choice is fixed.

## Copyable recipes

### 1) Scan-to-scan

Use this when you want random moving/fixed scan pairs.

```python
from voxelmorph.py import generators

gen = generators.scan_to_scan(volume_list, batch_size=2, bidir=True)
invols, outvols = next(gen)
# invols: [scan1, scan2]
# outvols: [scan2, scan1, zero_flow]
```

Notes:

- `prob_same` can force identical source/target pairs with a chosen probability.
- `no_warp=True` removes the zero-flow output, which is useful for affine-only experiments.

### 2) Scan-to-atlas

Use this when all scans should align to a fixed atlas.

```python
from voxelmorph.py import generators

atlas = atlas_array[np.newaxis, ..., np.newaxis]
gen = generators.scan_to_atlas(volume_list, atlas, batch_size=2)
invols, outvols = next(gen)
# invols: [scan_batch, atlas_batch]
# outvols: [atlas_batch, zero_flow]
```

If you also supply segmentations, the target output becomes the segmentation batch.

### 3) Semisupervised registration

Use this when each scan has a discrete segmentation and you want those labels to contribute to the loss.

```python
from voxelmorph.py import generators

labels = [0, 1, 2, 3]
gen = generators.semisupervised(volume_list, seg_list, labels=labels, downsize=2)
invols, outvols = next(gen)
# invols: [src_vol, trg_vol, src_seg_prob]
# outvols: [trg_vol, zero_flow, trg_seg_prob]
```

Notes:

- The segmentation stack is label-probability style, not a raw integer label map.
- The current implementation downsamples the label stack with three explicit spatial slices, so treat it as a 3D workflow.
- Use `atlas_file=` when you want atlas-target supervision instead of sampling both source and target from the list.

### 4) Template creation

Use this when the output is a template or atlas estimate rather than a warped target.

```python
from voxelmorph.py import generators

gen = generators.template_creation(volume_list, batch_size=1)
invols, outvols = next(gen)
# invols: [scan]
# outvols: [scan, zeros, zeros]
```

Notes:

- The generator emits zero-filled auxiliary outputs that the template loss can ignore.
- Keep batch size small unless you adapt the zero-cache shape yourself.

### 5) Conditional template creation

Use this when template learning is conditioned on phenotype attributes.

```python
from voxelmorph.py import generators

attributes = {
    "case01.npz": [21.0, 0.73],
    "case02.npz": [19.0, 0.68],
}
gen = generators.conditional_template_creation(volume_names, atlas_batch, attributes, batch_size=1)
invols, outvols = next(gen)
# invols: [pheno, atlas_batch, scan_batch]
```

Notes:

- The attribute dictionary keys must match the exact file names used in `vol_names`.
- The attribute vectors are stacked into a dense matrix before entering the model.

### 6) Surface semisupervised learning

Use this when the loss needs surface distances or point clouds from label maps.

```python
from voxelmorph.py import generators

gen = generators.surf_semisupervised(
    volume_names,
    atlas_vol,
    atlas_seg,
    nb_surface_pts=2048,
    labels=[1, 2, 3],
    batch_size=1,
    surf_bidir=True,
)
inputs, outputs = next(gen)
```

Notes:

- `nb_surface_pts` must be greater than zero.
- The generator currently asserts `batch_size == 1`.
- `align_segs=True` is only supported for a single label.
- Surface point arrays end with the label index in the last column.
- Surface extraction uses `clean_seg`, signed distance transforms, and point sampling around the surface boundary.

### 7) SynthMorph

Use this when training from synthesized label maps instead of real scans.

```python
from voxelmorph.py import generators

label_maps = [label_map_a, label_map_b, label_map_c]
gen = generators.synthmorph(label_maps, batch_size=1, same_subj=True, flip=True)
(inputs, dummy_target) = next(gen)
```

Notes:

- The generator returns paired label maps and a dummy empty target.
- `same_subj=True` forces both halves of the batch to use the same source label map.
- `flip=True` applies the same random flips to both members of the pair.

## When to run the bundled validator

Run `scripts/validate_vxm_npz.py` before any of the workflows above when the inputs are `.npz` files and you want to catch schema issues early.

Good checks include:

- missing `vol` or `seg` keys
- wrong `.npz` file type or a missing path
- inconsistent volume shapes across a list
- label maps that are not integer typed
- NaNs or infinities
- unexpected label values

## Hand-off to other sub-skills

- Once the generator choice is clear, hand the resulting arrays to `../pairwise-registration/SKILL.md` if the next step is model construction or a training smoke test.
- If the task is tensor warping, field composition, or Jacobian math, stop here and route to `transform-ops`.
