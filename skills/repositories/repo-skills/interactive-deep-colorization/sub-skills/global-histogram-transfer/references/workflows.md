# Global Histogram Transfer Workflows

## Purpose

Read this to reproduce the repository's global histogram transfer logic conceptually or to adapt it in an environment where PyCaffe and the global model files are available. This reference distills the notebook workflow into self-contained steps; it does not require the original notebook.

## Workflow summary

Global histogram transfer uses a target grayscale image plus a separate reference color image. A Caffe global statistics network extracts a 313-bin color histogram from the reference image. The global colorization model then consumes that histogram through a global conditioning blob while colorizing the target image.

The workflow is Caffe-only in this repository. Use the setup sub-skill to prepare Caffe and model files before execution.

## Required inputs and assets

| Item | Role |
| --- | --- |
| Target image path | Grayscale or color source image to colorize; the notebook example uses a bird image fixture. |
| Reference image path | Color image whose global color distribution guides the output. |
| `models/global_model/deploy_nodist.prototxt` | Caffe colorization network definition with global histogram input. |
| `models/global_model/global_model.caffemodel` | Weights for the global colorization network. |
| `models/global_model/global_stats.prototxt` | Caffe network that extracts global color statistics from a reference image. |
| `models/global_model/dummy.caffemodel` | Dummy weights for the global statistics network. |
| PyCaffe | Provides `caffe.Net`, `caffe.io.load_image`, and `caffe.io.resize_image`. |

Run [../scripts/check_global_histogram_assets.py](../scripts/check_global_histogram_assets.py) before execution to verify expected filenames.

## Distilled recipe

The notebook's logic can be expressed as follows once Caffe and assets exist:

1. Import Caffe, NumPy, Matplotlib, `data.colorize_image as CI`, and image/color helpers.
2. Choose `Xd = 256` and a Caffe `gpu_id` or CPU-compatible Caffe mode.
3. Create the global colorization model:

   ```python
   cid = CI.ColorizeImageCaffeGlobDist(Xd)
   cid.prep_net(
       gpu_id,
       prototxt_path="models/global_model/deploy_nodist.prototxt",
       caffemodel_path="models/global_model/global_model.caffemodel",
   )
   ```

4. Create the global statistics net:

   ```python
   gt_glob_net = caffe.Net(
       "models/global_model/global_stats.prototxt",
       "models/global_model/dummy.caffemodel",
       caffe.TEST,
   )
   ```

5. Load the target image through the wrapper and prepare no local user points:

   ```python
   cid.load_image(target_path)
   input_ab = np.zeros((2, Xd, Xd))
   input_mask = np.zeros((1, Xd, Xd))
   ```

6. For automatic colorization without a reference histogram:

   ```python
   cid.net_forward(input_ab, input_mask)
   automatic_rgb = cid.get_img_fullres()
   ```

7. Extract the reference image histogram:

   ```python
   ref_img_fullres = caffe.io.load_image(reference_path)
   img_glob_dist = (255 * caffe.io.resize_image(ref_img_fullres, (Xd, Xd))).astype("uint8")
   gt_glob_net.blobs["img_bgr"].data[...] = img_glob_dist[:, :, ::-1].transpose((2, 0, 1))
   gt_glob_net.forward()
   glob_dist_ref = gt_glob_net.blobs["gt_glob_ab_313_drop"].data[0, :-1, 0, 0].copy()
   ```

8. Run colorization with the reference histogram:

   ```python
   cid.net_forward(input_ab, input_mask, glob_dist_ref)
   reference_conditioned_rgb = cid.get_img_fullres()
   ```

9. Compare grayscale, automatic, reference-conditioned, and reference images as needed.

## Relationship to local hints

The global workflow still uses `input_ab` and `input_mask`, but the notebook example initializes them to zero. The global conditioning comes from `glob_dist_ref`, not from user clicks. If a task mixes local user points and global histogram conditioning, preserve both inputs: local points through `input_ab`/`input_mask` and global reference distribution through `glob_dist`.

## Verification limitations

Construction did not run this workflow because PyCaffe and downloaded global weights were absent. Static source evidence verifies the method names, blob names, and data flow, but native execution requires a prepared Caffe environment and model artifacts.
