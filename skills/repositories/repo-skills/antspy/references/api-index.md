# ANTsPy API Index

Use this index to route common public `ants.*` calls to the nearest detailed sub-skill reference.

## Image Core

Read [image-core](../sub-skills/image-core/SKILL.md) for:

- `ANTsImage`, `image_read`, `image_write`, `from_numpy`, `from_numpy_like`, `make_image`, `image_header_info`.
- `copy_image_info`, `image_physical_space_consistency`, `allclose`, `image_clone`.
- `get_ants_data`, `get_data`, metadata setters/getters, indexing, views, NumPy copies, pixel types, and component images.

## Operations and Math

Read [image-ops-math](../sub-skills/image-ops-math/SKILL.md) for:

- `smooth_image`, `resample_image`, `resample_image_to_target`, `threshold_image`, `mask_image`, `get_mask`.
- `crop_image`, `crop_indices`, `decrop_image`, `pad_image`, `slice_image`, `denoise_image`.
- `n3_bias_field_correction`, `n4_bias_field_correction`, `abp_n4`, histogram matching/equalization.
- `iMath`, `morphology`, `image_similarity`, `image_mutual_information`, neighborhoods, Hausdorff distance, average images, and quantitative helpers.

## Registration and Transforms

Read [registration-transforms](../sub-skills/registration-transforms/SKILL.md) for:

- `registration`, `motion_correction`, `label_image_registration`, `apply_transforms`, `apply_transforms_to_points`.
- `create_ants_transform`, `read_transform`, `write_transform`, affine initializer, template building, transform averaging, displacement fields, Jacobians, warped grids, landmarks, and FSL conversion.

## Segmentation and Labels

Read [segmentation-labels](../sub-skills/segmentation-labels/SKILL.md) for:

- `atropos`, `kmeans_segmentation`, `otsu_segmentation`, `prior_based_segmentation`, fuzzy spatial c-means, joint label fusion, KellyKapowski, and functional lung segmentation.
- `label_stats`, `label_overlap_measures`, `label_geometry_measures`, `label_clusters`, `labels_to_matrix`, `make_points_image`, `multi_label_morphology`, `get_centroids`, and point/label helpers.

## Visualization and Interop

Read [visualization-interop](../sub-skills/visualization-interop/SKILL.md) for:

- `plot`, `plot_ortho`, `plot_ortho_stack`, `plot_grid`, `plot_hist`, `movie`, and `plot_directory`.
- `merge_channels`, `split_channels`, RGB/vector conversions, `images_to_matrix`, `matrix_to_images`, `ndimage_to_list`, `list_to_ndimage`, nibabel, and SimpleITK conversion helpers.

## Learning and Deeplearn Helpers

Read [learning-deeplearn](../sub-skills/learning-deeplearn/SKILL.md) for:

- `sparse_decom2`, `eig_seg`, eigenanatomy initialization, patch extraction/reconstruction, random augmentation, one-hot label conversion, histogram warping, simulated bias fields, regression matching, and learning-oriented crop/pad helpers.
