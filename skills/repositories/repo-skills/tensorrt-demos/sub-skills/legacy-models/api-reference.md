# Legacy model API reference

This reference records the contracts implemented by `trt_googlenet.py`,
`trt_mtcnn.py`, `utils/mtcnn.py`, `pytrt.pyx`, and `pytrt.pxd` in this checkout.
Shapes omit the batch dimension unless noted.

## GoogLeNet

| Item | Contract |
|---|---|
| Engine | `googlenet/deploy.engine` |
| Caffe input | `data`, `(3, 224, 224)` |
| Caffe output | `prob`, `(1000, 1, 1)` per batch item |
| Python wrapper | `PyTrtGooglenet(engine_path, (3,224,224), (1000,1,1))` |
| Batch | exactly 1; `pytrt.pyx` asserts `np_imgs.shape[0] == 1` |
| Preprocess | OpenCV BGR HWC; optional center square crop; resize 224×224; float32 minus `[104,117,123]`; transpose HWC→CHW |
| Labels | `np.loadtxt('googlenet/synset_words.txt', str, delimiter='\t')`; exactly 1000 rows expected |
| Display | top 3 indices from descending `prob`; label row is shown as text |

The C++ builder explicitly marks the `prob` tensor because Caffe has no output
notion. The C++ runtime checks exactly two bindings and validates input/output
dimensions before allocating CUDA buffers. The Python output is a dictionary:
`{'prob': np_prob}`, where `np_prob.shape == (1,1000,1,1)`.

### GoogLeNet CLI

`trt_googlenet.py` and `trt_googlenet_async.py` share camera arguments from
`utils.camera.add_camera_args`:

- `--image PATH`: repeat a still image.
- `--video PATH`: read a video; `--video_looping` restarts at EOF.
- `--rtsp URI`: RTSP H.264 stream; `--rtsp_latency` defaults to 200 ms.
- `--usb INTEGER`: `/dev/videoINTEGER`.
- `--gstr STRING`: format a GStreamer string with `{width}` and `{height}`.
- `--onboard INTEGER`: Jetson onboard camera selector (the implementation
  uses the onboard source; the integer is accepted by the shared CLI).
- `--width`/`--height`: defaults 640×480 for camera pipelines.
- `--copy_frame`: clone live frames before annotation/inference.
- `--do_resize`: resize image/video source frames to requested dimensions.
- `--crop`: center-crop a square before the model resize.

The source must select one input mode. `Camera.read()` returns `None` on input
failure/end-of-stream; a still image returns a fresh copy each time.

## MTCNN stages

`TrtMtcnn` constructs these wrappers and fixed engine paths:

| Stage | Wrapper call | Input | Output bindings | Max batch |
|---|---|---|---|---:|
| PNet | `PyTrtMtcnn('mtcnn/det1.engine', (3,710,384), (2,350,187), (4,350,187))` | stacked scaled image | `prob1`, `boxes` (`conv4-2`) | 1 |
| RNet | `PyTrtMtcnn('mtcnn/det2.engine', (3,24,24), (2,1,1), (4,1,1))` | 24×24 crops | `prob1`, `boxes` (`conv5-2`) | 256 |
| ONet | `PyTrtMtcnn('mtcnn/det3.engine', (3,48,48), (2,1,1), (4,1,1), (10,1,1))` | 48×48 crops | `prob1`, `boxes`, `landmarks` (`conv6-2`, `conv6-3`) | 64 |

The extension chooses the C++ initializer by checking whether the engine path
contains the substring `det1`, `det2`, or `det3`; another path raises
`ValueError`. `set_batchsize(n)` is required before each RNet/ONet forward and
must match the input array's batch dimension. The C++ implementation allocates
GPU buffers for the selected batch and copies outputs back synchronously.

### MTCNN preprocessing

- Input from OpenCV is BGR; `_detect_1280x720` reverses channels to RGB because
  the MATLAB-trained model expects RGB.
- PNet normalizes `(img.astype(float32) - 127.5) * 0.0078125` (equivalent to
  division by 128 after centering), creates a scale pyramid, and stacks up to
  nine images in `(1,3,710,384)`.
- PNet crop/output offsets are fixed for scales based on `factor=0.709`:
  input H offsets `(0,216,370,478,556,610,648,676,696)` and output offsets
  `(0,108,185,239,278,305,324,338,348)`.
- RNet and ONet crop boxes are squared with `convert_to_1x1`, padded with zero,
  resized to 24×24 or 48×48, transposed with `cv2.transpose`, then converted
  NHWC→NCHW and normalized using the same mean/scale.

## Thresholds, NMS, and outputs

| Operation | Default / rule |
|---|---|
| Public `--minsize` | 40 pixels; values below 40 raise `ValueError` in PNet |
| PNet confidence | `0.7` |
| PNet per-scale NMS | Union IoU threshold `0.5` |
| PNet combined NMS | Union IoU threshold `0.7` |
| RNet confidence | `0.6` |
| RNet NMS | Union IoU threshold `0.7` |
| ONet confidence | `0.7` |
| ONet NMS | Min-overlap threshold `0.7` |
| Pyramid factor | `0.709`; values above 0.709 raise `ValueError` |
| PNet scales | generated while scaled short side is at least 12; >9 raises |
| Large-frame policy | resize to ≤1280×720; scale `min(720/H,1280/W)`; restore coordinates |

`TrtPNet.detect` returns an `(N,5)` float array `[x1,y1,x2,y2,score]`.
`TrtRNet.detect` returns the same shape. `TrtONet.detect` returns
`(dets, landmarks)`, with detections `(N,5)` and landmarks `(N,10)` ordered as
`[x1..x5, y1..y5]`. Empty ONet results are `(0,5)` and `(0,10)` float arrays.
Coordinates are fixed/rounded and clipped to image bounds before returning.
`trt_mtcnn.py` draws rectangles and five points and prints the face count.

## C++/TensorRT compatibility branches

`googlenet/create_engine.cpp`, `mtcnn/create_engines.cpp`, and `trtNet.cpp`
use compile-time `NV_TENSORRT_MAJOR` branches:

- `<4`: legacy `DimsCHW` and `setHalf2Mode`.
- `4–5`: `Dims3`, `setFp16Mode`, and legacy builder APIs.
- `6`: newer `IHostMemory` signatures while still using legacy APIs.
- `7`: `createNetworkV2(0)`, `IBuilderConfig`, `setFlag(kFP16)`, and
  `buildEngineWithConfig`.
- `<8` versus `>=8`: `NOEXCEPT` declaration handling in `trtNet.h`.

Do not use these branches as evidence that every branch builds on a modern
TensorRT release. See [compatibility.md](compatibility.md).
