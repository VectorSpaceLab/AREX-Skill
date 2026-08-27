# Model and asset overview

This reference records source-observed contracts only. Names are the paths resolved
under the plug-in's `baseLoc + "weights/"` directory; an operator should supply a
generic weights root to the asset checker rather than relying on a machine-specific
path. The repository's weight files were absent during inspection.

## Checkpoint inventory

| Operation | Expected relative asset(s) | Source-observed loader/device behavior | Pre/post-processing and output |
|---|---|---|---|
| Deblur | `deblur/best_fpn.h5`, `deblur/mymodel.pth` | `Predictor` receives `best_fpn.h5`; its inspected generator helper also loads sibling `mymodel.pth`, and the state loader uses a CPU `map_location`. The plug-in passes `cf` from **Force CPU**. | Drops alpha; helper scales/pads image to a multiple of 32 and crops back. Result is a same-size RGB result layer named with a `deblur_` prefix. |
| Dehaze | `deepdehaze/dehazer.pth` | Builds `net.dehaze_net`; CUDA path moves model/input to CUDA, CPU/forced path uses `torch.device("cpu")` for checkpoint loading. | Converts `uint8` RGB to float `[0,1]`, CHW, batch; converts result back to clipped `uint8` HWC RGB. Result layer is `new_output`. |
| Denoise | `deepdenoise/net.pth`, `deepdenoise/est_net.pth` | Loads both checkpoints; CPU/forced path uses CPU `map_location`; CUDA is selected when available unless forced. `module.` prefixes are stripped from state-dict keys. | Removes alpha, reverses channel order in the helper, applies configured scale/patch processing (`wbin=512`, `ps_scale=2`), then reverses output channels. Result layer is `new_output`. Exact runtime behavior is unverified. |
| Enlighten | `enlightening/200_net_G_A.pth` | The options set `checkpoints_dir` to the weights root, model name `enlightening`, epoch `200`, and pass `cFlag`; the model loader uses CPU `map_location` when CUDA is unavailable or forced. | Converts RGB input to BGR for the transform and converts output back to RGB. Uses a 256 fine size and no flip in the observed options. Result layer is `new_output`. |
| Monocular depth | `MiDaS/model.pt` | Calls `run_depth(..., f=ForceCPU)`; the helper moves model/input to CUDA only when available and not forced. | Normalizes input to `[0,1]`; resizes for a target width of 640 and model-compatible multiples of 32, normalizes the predicted depth to 8-bit, resizes to the scaled target, repeats the map to 3 channels, then resizes back to the source size. Result layer is `new_output`. |
| Semantic segmentation | `deeplabv3/deeplabv3+model.pt` | `torch.load` is used directly in the entry point. CUDA moves model and batch to `cuda` when available and not forced; the source does not show an explicit CPU `map_location`. | PIL tensor preprocessing with ImageNet mean/std; argmax over model `out`; class map is resized to input size and repeated into three channels, multiplied by 10. Result layer is `new_output`. The exact checkpoint object schema is unverified. |
| Face parsing | `faceparse/79999_iter.pth` | Creates a 19-class `BiSeNet`; CUDA path loads normally after `.cuda()`, CPU/forced path uses a storage-preserving CPU map location. | Removes alpha; resizes to 512x512, normalizes with ImageNet mean/std, predicts 19 labels, resizes labels to the original size, then colorizes with the source's fixed palette. Portrait-only input is documented. Result layer is `new_output`. |
| Super-resolution | `super_resolution/model_srresnet.pth` | Loads the checkpoint's `"model"` entry; CPU path uses `torch.device('cpu')`; CUDA is enabled only when available and not forced. | Removes alpha; CHW float input in `[0,1]`; requested scale is a slider from 1 to 4 in 0.5 steps. Model path is a 4x SR model. Filter mode tiles with `wbin=300`; after model output, resizes by `scale/4`. At scale 1 it adds a result layer; otherwise it opens a new GIMP image. |
| Frame interpolation | `interpolateframes/contextnet.pkl`, `interpolateframes/flownet.pkl`, `interpolateframes/unet.pkl` | `RIFE.Model(c_flag)` selects CPU/CUDA; each checkpoint is loaded with CPU `map_location`, then the networks are placed on the selected device. | Removes alpha from both frames; converts to CHW `[0,1]`, pads both to multiples of 32, performs four interpolation rounds (`exp=4`), and writes 17 PNG files (`img0.png` through `img16.png`) to the requested output folder. Output uses BGR ordering for OpenCV writing and crops padding back. |

## Evidence boundary

The contracts above were distilled from the project's manual, the nine filter
entry points, the weight manifest, and selected model/helper loaders. That evidence
establishes the relative asset names, plugin controls, preprocessing, device flags,
layer-size guards, and intended outputs; it does not establish model quality or
runtime compatibility. Third-party model implementations are intentionally not
reproduced here. The manifest's download behavior is not part of this skill and must
not be invoked by an operator.

## Interpretation limits

- A checkpoint filename is not proof of its framework version, architecture
  compatibility, quality, or safe provenance. Do not substitute a same-named file.
- The segmentation entry point's `colors` tensor is computed but not applied to the
  returned map; preserve this as observed behavior rather than promising a colored
  palette.
- The denoiser's source contains an apparent `file_name`/progress dependency in an
  automatic-scale branch; use the fixed observed settings only as source evidence and
  treat that branch as unverified.
- No weights, GIMP host, Python 2 runtime, or successful CUDA allocation were present
  for a model-backed execution check.
