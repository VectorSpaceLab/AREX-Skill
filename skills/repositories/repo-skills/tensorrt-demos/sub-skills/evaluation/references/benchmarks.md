# Historical benchmarks and interpretation

These values are reproduced from this repository's README tables and
`README_mAP.md`. They are historical observations, not acceptance thresholds.
The reported systems used specific Jetson devices, JetPack/TensorRT versions,
engines, preprocessing, and COCO `val2017`; a different build or dataset is
not directly comparable.

## SSD COCO mAP and FPS

The main README reports the following comparison, measured with
`trt_ssd_async.py` on a Jetson Nano with JetPack-4.3:

| TensorRT/TF variant | AP IoU 0.50:0.95 | AP IoU 0.50 | FPS on Nano |
|---|---:|---:|---:|
| mobilenet_v1 TF | 0.232 | 0.351 | -- |
| mobilenet_v1 TRT (FP16) | 0.232 | 0.351 | 27.7 |
| mobilenet_v2 TF | 0.248 | 0.375 | -- |
| mobilenet_v2 TRT (FP16) | 0.248 | 0.375 | 22.7 |

`README_mAP.md` shows example COCOeval summaries whose primary AP values are
rounded as `0.232` and `0.248` for the two TRT models. Its prose also says
“overall mAP” `0.230` and `0.246`; retain the full COCOeval output and do not
invent precision from the prose. Compare like-for-like primary AP and AP50,
with identical annotation revision, image set, mode, and model.

The useful historical conclusion is that these particular FP16 TensorRT SSD
engines matched their corresponding frozen TensorFlow graphs in the reported
run. It is not proof that any TensorRT version preserves accuracy for a newly
built engine.

## YOLO COCO mAP and FPS on Nano

The README reports these TensorRT results on a Jetson Nano with JetPack-4.4
(TensorRT 7):

| Engine (FP16) | AP 0.50:0.95 | AP50 | FPS |
|---|---:|---:|---:|
| yolov3-tiny-288 | 0.077 | 0.158 | 35.8 |
| yolov3-tiny-416 | 0.096 | 0.202 | 25.5 |
| yolov3-288 | 0.331 | 0.601 | 8.16 |
| yolov3-416 | 0.373 | 0.664 | 4.93 |
| yolov3-608 | 0.376 | 0.665 | 2.53 |
| yolov3-spp-288 | 0.339 | 0.594 | 8.16 |
| yolov3-spp-416 | 0.391 | 0.664 | 4.82 |
| yolov3-spp-608 | 0.410 | 0.685 | 2.49 |
| yolov4-tiny-288 | 0.179 | 0.344 | 36.6 |
| yolov4-tiny-416 | 0.196 | 0.387 | 25.5 |
| yolov4-288 | 0.376 | 0.591 | 7.93 |
| yolov4-416 | 0.459 | 0.700 | 4.62 |
| yolov4-608 | 0.488 | 0.736 | 2.35 |
| yolov4-csp-256 | 0.336 | 0.502 | 12.8 |
| yolov4-csp-512 | 0.436 | 0.630 | 4.26 |
| yolov4x-mish-320 | 0.400 | 0.581 | 4.79 |
| yolov4x-mish-640 | 0.470 | 0.668 | 1.46 |

The supported model examples in the README additionally include
`yolov4-csp-512`, `yolov4x-mish-320`, `yolov4x-mish-640`, and custom forms such
as `yolov4-416x256`. A model string alone does not prove that its `.trt` file
or compatible plugin exists on the current checkout.

## INT8 and DLA historical comparison

On a Jetson Xavier NX under a stated “15W 6CORE” mode with clocks maximized,
the README reports the following FPS values:

| Engine | FP16 | INT8 | DLA0 | DLA1 |
|---|---:|---:|---:|---:|
| yolov3-tiny-416 | 58 | 65 | 42 | 42 |
| yolov3-608 | 15.2 | 23.1 | 14.9 | 14.9 |
| yolov3-spp-608 | 15.0 | 22.7 | 14.7 | 14.7 |
| yolov4-tiny-416 | 57 | 60 | X | X |
| yolov4-608 | 13.8 | 20.5 | 8.97 | 8.97 |
| yolov4-csp-512 | 19.8 | 27.8 | -- | -- |
| yolov4x-mish-640 | 9.01 | 14.1 | -- | -- |

The corresponding AP/AP50 pairs were:

| Engine | FP16 | INT8 | DLA0 | DLA1 |
|---|---|---|---|---|
| yolov3-tiny-416 | 0.096 / 0.202 | 0.094 / 0.198 | 0.096 / 0.199 | 0.096 / 0.199 |
| yolov3-608 | 0.376 / 0.665 | 0.378 / 0.670 | 0.378 / 0.670 | 0.378 / 0.670 |
| yolov3-spp-608 | 0.410 / 0.685 | 0.407 / 0.681 | 0.404 / 0.676 | 0.404 / 0.676 |
| yolov4-tiny-416 | 0.196 / 0.387 | 0.190 / 0.376 | X | X |
| yolov4-608 | 0.488 / 0.736 | *0.317 / 0.507* | 0.474 / 0.727 | 0.473 / 0.726 |
| yolov4-csp-512 | 0.436 / 0.630 | 0.391 / 0.577 | -- | -- |
| yolov4x-mish-640 | 0.470 / 0.668 | 0.434 / 0.631 | -- | -- |

`X` means the reported configuration was not available/tested; `--` means no
value was reported in that table. The README explicitly flags the yolov4-608
INT8 AP loss as unexplained. Do not “correct” it by averaging, dropping the
row, or attributing it to a particular TensorRT node without new evidence.
The README also cautions that TensorRT 7.1's Python API did not specifically
select a DLA core at inference time, so the DLA labels are historical claims
with a documented uncertainty.

## How to compare a new run

Use this order:

1. Compare primary AP (`IoU=0.50:0.95`, all areas, maxDets=100) and AP50 from
   the same evaluator, not a display-demo confidence score or FPS alone.
2. Check AP75 and small/medium/large AP to distinguish localization and scale
   effects. A change only in small-object AP may not indicate a general engine
   regression.
3. Inspect AR at maxDets 1, 10, and 100 for recall/candidate-limit effects.
4. Confirm image IDs, category mapping, letterbox setting, engine precision,
   TensorRT version, and GPU before diagnosing numerical degradation.
5. Treat historical FPS as hardware/context data. FPS was measured by a
   separate async demo for SSD and on fixed Nano/Xavier configurations, not by
   the mAP evaluator itself.

COCO AP is the mean over IoU thresholds 0.50 through 0.95 for the summary's
primary row, while AP50 is the single IoU=0.50 row. Never label AP50 as “mAP”
without stating the IoU threshold.
