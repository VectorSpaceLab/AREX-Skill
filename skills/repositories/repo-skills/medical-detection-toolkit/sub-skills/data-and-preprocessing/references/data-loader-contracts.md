# Data-loader and batchgenerators contracts

[Back to the data-and-preprocessing skill](../SKILL.md) · Related: [data formats](data-formats.md), [preprocessing](preprocessing-workflows.md), [utilities](data-utilities.md), [troubleshooting](troubleshooting.md)

The three example loaders were imported in the inspection environment with
`batchgenerators 0.19.3`. The signatures below are source-backed and were also
inspected at runtime; do not assume a newer batchgenerators release has the
same behavior.

## Public loader signatures

```text
experiments/toy_exp/data_loader.py
  get_train_generators(cf, logger)
  get_test_generator(cf, logger)
  load_dataset(cf, logger, subset_ixs=None, pp_data_path=None, pp_name=None)
  create_data_gen_pipeline(patient_data, cf, do_aug=True)
  BatchGenerator(data, batch_size, cf)
  PatientBatchIterator(data, cf)

experiments/lidc_exp/data_loader.py
  get_train_generators(cf, logger)
  get_test_generator(cf, logger)
  load_dataset(cf, logger, subset_ixs=None, pp_data_path=None, pp_name=None)
  create_data_gen_pipeline(patient_data, cf, is_training=True)
  BatchGenerator(data, batch_size, cf)
  PatientBatchIterator(data, cf)

experiments/pet_ct_tnm_classification/data_loader.py
  get_train_generators(cf, logger)
  get_test_generator(cf, logger)
  load_dataset(cf, logger, subset_ixs=None)
  create_data_gen_pipeline(patient_data, cf, is_training=True)
  BatchGenerator(data, batch_size, cf)
  PatientBatchIterator(data, cf)
```

`BatchGenerator` subclasses `SlimDataLoaderBase` and implements
`generate_train_batch`. `PatientBatchIterator` also subclasses it and cycles
its patient index back to zero after the final patient. The latter behavior is
useful for an augmenter but means a caller must bound the number of batches.

## Installed transform signatures

Observed with the historical `batchgenerators 0.19.3` API variant during
construction:

```text
batchgenerators 0.19.3
MirrorTransform(axes=(0, 1, 2), data_key='data', label_key='seg')
SpatialTransform(patch_size, patch_center_dist_from_border=30,
  do_elastic_deform=True, alpha=(0.0, 1000.0), sigma=(10.0, 13.0),
  do_rotation=True, angle_x=(0, 2*pi), angle_y=(0, 2*pi), angle_z=(0, 2*pi),
  do_scale=True, scale=(0.75, 1.25), border_mode_data='nearest',
  border_cval_data=0, order_data=3, border_mode_seg='constant',
  border_cval_seg=0, order_seg=0, random_crop=True, data_key='data',
  label_key='seg', p_el_per_sample=1, p_scale_per_sample=1, p_rot_per_sample=1)
CenterCropTransform(crop_size, data_key='data', label_key='seg')
ConvertSegToBoundingBoxCoordinates(dim, get_rois_from_seg_flag=False,
  class_specific_seg_flag=False)
Compose(transforms)
MultiThreadedAugmenter(data_loader, transform, num_processes,
  num_cached_per_queue=2, seeds=None, pin_memory=False)
```

The source constructors pass a subset of these arguments from `cf.da_kwargs`.
The PET-CT loader additionally passes `order_seg=0` and `border_cval_seg=0`
to `SpatialTransform`. It is safer to pass explicit segmentation interpolation
settings for every new medical loader.

## Pipeline order and flags

The source pattern is:

```python
data_gen = BatchGenerator(patient_data, batch_size=cf.batch_size, cf=cf)
transforms = []
if training:
    transforms.append(Mirror(...))
    transforms.append(SpatialTransform(patch_size=cf.patch_size[:cf.dim], ...))
else:
    transforms.append(CenterCropTransform(crop_size=cf.patch_size[:cf.dim]))
transforms.append(ConvertSegToBoundingBoxCoordinates(
    cf.dim,
    get_rois_from_seg_flag=..., 
    class_specific_seg_flag=cf.class_specific_seg_flag))
augmenter = MultiThreadedAugmenter(data_gen, Compose(transforms),
                                   num_processes=cf.n_workers,
                                   seeds=range(cf.n_workers))
```

- Toy uses `do_aug=False` by default in the wrapper and sets
  `get_rois_from_seg_flag=False`.
- LIDC uses `is_training=True/False` and also sets the converter flag to
  `False`, because its ROI maps already contain instance ids.
- PET-CT uses the converter flag `True`, because its segmentation is binary and
  components must be identified on the fly.
- The source comments show `SingleThreadedAugmenter` as an alternative, but the
  active path is `MultiThreadedAugmenter`. Do not increase process count as a
  first response to a shape error; first run one bounded single-threaded
  synthetic check in the caller's environment.

## Batch fields and shapes

The generator before conversion returns:

```python
{
    'data': numpy array,
    'seg': numpy array,            # toy/LIDC/PET training paths
    'pid': list or string,
    'class_target': array or list,
}
```

The converter adds `bb_target` and `roi_labels`. Patient iterators add
`patient_bb_target`, `patient_roi_labels`, and `original_img_shape`. LIDC
patient inference may additionally add `patch_crop_coords` and repeats patient
class targets for each patch. PET-CT raw patient inference has no segmentation
input and therefore should not be described as ground-truth validation.

## Config fields that are part of the contract

At minimum, a custom loader must define and review:

- `dim`, `channels`, `n_channels`, `patch_size`, `pre_crop_size`;
- `class_specific_seg_flag`, `head_classes`, and the converter's ROI mode;
- `batch_size`, `n_workers`, `batch_sample_slack`;
- `merge_2D_to_3D_preds`, `n_3D_context`;
- `da_kwargs` (`random_crop`, rotation/scale/deformation, border values and
  interpolation order); and
- input paths, `input_df_name`, `hold_out_test_set`, and fold settings.

Use `cf.patch_size[:cf.dim]` for spatial transforms. If `cf.dim == 2` but
patient inference uses z slices, retain the original volume shape and define
how slice predictions are merged. If `cf.dim == 3`, do not silently pass a 2D
patch or 2D converter.

## Import and signature check

When maintaining a checkout, import each example loader in its own experiment
module context with the dependency/API variant selected for that checkout.
This is a read-only module check: do not call a generator, read a real
manifest, or launch an augmenter. Use the bundled array validator for data
checks; a loader import alone does not validate a manifest.
