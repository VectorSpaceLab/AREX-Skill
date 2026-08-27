# Segmentation and Label API Reference

This reference distills the ANTsPy source and live `antspyx` API inspection. Import with `import ants`.

## Segmentation Signatures and Return Contracts

| Function | Verified signature | Return contract | Notes |
| --- | --- | --- | --- |
| `ants.atropos` | `(a, x, i='Kmeans[3]', m='[0.2,1x1]', c='[5,0]', priorweight=0.25, **kwargs)` | `dict`: `segmentation`, `probabilityimages` | `a` is one image or a list/tuple of images; `x` is a mask. `i` accepts an ANTs initialization string such as `Kmeans[3]` or a list of prior probability images. Classes follow the first image intensity order for k-means initialization, or prior-list order when priors are used. |
| `ants.kmeans_segmentation` | `(image, k, kmask=None, mrf=0.1)` | `dict`: `segmentation`, `probabilityimages` | Normalizes the image, builds/fills a mask when `kmask` is omitted, calls `atropos` with `i='kmeans[k]'`, then clones the segmentation to the input image pixel type. |
| `ants.otsu_segmentation` | `(image, k, mask=None)` | `ANTsImage` | Fast threshold-based label image. Adds a background class, so `k=3` can yield labels `0..3`. Does not return probability maps. |
| `ants.prior_based_segmentation` | `(image, priors, mask, priorweight=0.25, mrf=0.1, iterations=25)` | `dict`: `segmentation`, `probabilityimages` | Wrapper around `atropos`; `image` may be an `ANTsImage` or list/tuple of `ANTsImage` feature images. `priors` must be one probability image per class in the intended class order. |
| `ants.fuzzy_spatial_cmeans_segmentation` | `(image, mask=None, number_of_clusters=4, m=2, p=1, q=1, radius=2, max_number_of_iterations=20, convergence_threshold=0.02, verbose=False)` | `dict`: `segmentation_image`, `probability_images` | Pure Python iterative fuzzy spatial c-means. If `mask` is omitted, all voxels are used. Convergence uses Dice overlap between iterations. |
| `ants.functional_lung_segmentation` | `(image, mask=None, number_of_iterations=2, number_of_atropos_iterations=5, mrf_parameters='[0.7,2x2x2]', number_of_clusters=6, cluster_centers=None, bias_correction='n4', verbose=True)` | `dict`: `segmentation_image`, `probability_images`, `processed_image` | 3-D only and requires `mask`. Alternates bias correction and Atropos. Intended for ventilation-class lung segmentation; not a generic 2-D quick segmenter. |
| `ants.joint_label_fusion` | `(target_image, target_image_mask, atlas_list, beta=4, rad=2, label_list=None, rho=0.01, usecor=False, r_search=3, nonnegative=False, no_zeroes=False, max_lab_plus_one=False, output_prefix=None, verbose=False)` | `ANTsImage` without labels; `dict` with `segmentation`, `intensity`, `probabilityimages`, `segmentation_numbers` with labels | Atlas intensity images and label images must already be in target space. `rad` may be scalar or dimension-length list. With `max_lab_plus_one=True`, extra keys include `segmentation_raw` and `background_prob`, and source label images may be modified. |
| `ants.local_joint_label_fusion` | `(target_image, which_labels, target_mask, initial_label, atlas_list, label_list, submask_dilation=10, type_of_transform='SyN', aff_metric='meansquares', syn_metric='mattes', syn_sampling=32, reg_iterations=(40, 20, 0), aff_iterations=(500, 50, 0), grad_step=0.2, flow_sigma=3, total_sigma=0, beta=4, rad=2, rho=0.1, usecor=False, r_search=3, nonnegative=False, no_zeroes=False, max_lab_plus_one=False, local_mask_transform='Similarity', output_prefix=None, verbose=False)` | `dict`: `ljlf`, `croppedImage`, `croppedmappedImages`, `croppedmappedSegs` | Crops around selected labels, performs local registrations, applies label-safe nearest-neighbor transforms, then calls `joint_label_fusion`. Potentially expensive. |
| `ants.kelly_kapowski` | `(s, g, w, its=45, r=0.025, m=1.5, gm_label=2, wm_label=3, **kwargs)` | `ANTsImage` | DiReCT cortical thickness from a segmentation image plus gray/white matter probability images. `s` is cloned to `unsigned int`; failure raises if the output remains all zeros. |

## Label, Cluster, Centroid, and Matrix Signatures

| Function | Verified signature | Return contract | Notes |
| --- | --- | --- | --- |
| `ants.label_clusters` | `(image, min_cluster_size=50, min_thresh=1e-06, max_thresh=1, fully_connected=False)` | `ANTsImage` | Thresholds `image` to `[min_thresh, max_thresh]`, labels connected components, and removes components smaller than `min_cluster_size`. `fully_connected=True` uses a broader neighborhood. |
| `ants.image_to_cluster_images` | `(image, min_cluster_size=50, min_thresh=1e-06, max_thresh=1)` | `list[ANTsImage]` | Calls `label_clusters`, then returns one image per nonzero cluster label with all other voxels zeroed. |
| `ants.label_geometry_measures` | `(label_image, intensity_image=None)` | `pandas.DataFrame` | Requires labels representable as `uint32`. Adds `VolumeInMillimeters` from voxel volume if the backend returns only voxel counts. `Label` must be integer typed. |
| `ants.label_image_centroids` | `(image, physical=False, convex=True, verbose=False)` | `dict`: `labels`, `vertices` | 3-D only. Returns label values and voxel-space vertices. The current implementation does not convert to physical points even when `physical=True`. |
| `ants.get_centroids` | `(image, clustparam=0)` | `numpy.ndarray` | Uses `label_clusters` when `clustparam > 0`, then `label_stats`; returns columns `[x, y, z, t]`, with zeros for absent dimensions. |
| `ants.label_overlap_measures` | `(source_image, target_image)` | `pandas.DataFrame` | Clones both images to `unsigned int`; row 0 has `Label == 'All'`. Includes overlap measures such as Dice/mean overlap per label and all labels. |
| `ants.label_stats` | `(image, label_image)` | `pandas.DataFrame` | Clones `image` to float and `label_image` to `unsigned int`; rejects labels not exactly representable as `uint32`. Sorts rows by `LabelValue`. Common columns include `LabelValue`, `Mean`, `Min`, `Max`, `Variance`, `Count`, `Volume`, and coordinate columns. |
| `ants.labels_to_matrix` | `(image, mask, target_labels=None, missing_val=nan)` | `numpy.ndarray` | Matrix shape is `(number_of_labels, number_of_mask_voxels)`. Includes labels present inside `mask > 0`; if `target_labels` includes a missing label, that row is filled with `missing_val`. |
| `ants.make_points_image` | `(pts, target, radius=5)` | `ANTsImage` | Converts physical-space points to target image indices, writes labels `1..N`, and dilates them with grayscale morphology. `pts.shape[1]` must match `target.dimension`. Points outside the image are ignored. |
| `ants.multi_label_morphology` | `(image, operation, radius, dilation_mask=None, label_list=None, force=False)` | `ANTsImage` | Label-preserving morphology for positive integer labels. `operation` is one of `MD`, `ME`, `MC`, `MO`. Refuses more than 200 labels unless `force=True`. Dilation/closing preserve existing labels but collision voxels keep the lowest label intensity. |

## Common Dict-Key Pitfalls

- Use `result['segmentation']` and `result['probabilityimages']` for `atropos`, `kmeans_segmentation`, and `prior_based_segmentation`.
- Use `result['segmentation_image']` and `result['probability_images']` for `fuzzy_spatial_cmeans_segmentation` and `functional_lung_segmentation`.
- Use `result['ljlf']` first after `local_joint_label_fusion`; the nested value follows `joint_label_fusion` contracts.
- Do not expect probability images from `otsu_segmentation`; if posterior maps are needed, use Atropos/k-means/prior workflows.

## Data Type and Physical-Space Rules

- Label measures use `unsigned int` internally. Before calling `label_stats` or `label_geometry_measures`, confirm labels are nonnegative integers and fit in `uint32`.
- `label_overlap_measures` clones labels to `unsigned int` without the same explicit exactness check, so validate labels yourself when fractional values are possible.
- `labels_to_matrix` and image-mask indexing require image and mask domains to match. Validate dimension, shape, spacing, origin, and direction before indexing.
- For transformed labels, use registration-transform workflows with nearest-neighbor or label-safe interpolation; do not linearly interpolate discrete labels before computing statistics.

## Expensive or Specialized Calls

- `joint_label_fusion` and `local_joint_label_fusion` can be slow and multithreaded; bound atlas counts, radii, search radii, and registration iterations for smoke tests.
- `kelly_kapowski` is an optimization algorithm and needs meaningful gray/white probability images aligned with segmentation labels. Small synthetic arrays often fail because the thickness output remains zero.
- `functional_lung_segmentation` is 3-D, mask-required, and does bias correction; use tiny 3-D data and low iteration counts only for bounded checks.
