# Engine-building troubleshooting

Classify the failure before changing code. Preserve the first error, full
TensorRT version, GPU/compute capability, input hashes, and exact command.
Never solve a missing dependency by silently running an installer or mutating
the host.

## Environment and build prerequisites

| Symptom | Likely cause | Safe next action |
|---|---|---|
| `ModuleNotFoundError: onnx` on `yolo_to_onnx.py --help` | ONNX is absent from the active Python environment | Prepare/activate an approved isolated environment; rerun help; do not infer ONNX conversion behavior from the traceback |
| `ModuleNotFoundError: tensorrt` on an engine help command | TensorRT Python bindings are absent or bound to another Python | Check interpreter/package ABI and the target TensorRT install; classify CUDA/TensorRT verification blocked |
| `ModuleNotFoundError: uff` or `graphsurgeon` | legacy SSD dependency variant absent | Use a separate legacy environment or stop the UFF path; do not install TensorFlow 1 into a modern environment without approval |
| `nvcc: command not found` / missing `NvInfer.h` | CUDA toolkit or TensorRT development files unavailable | Report plugin/Caffe compile blocked and identify include/library paths; do not invoke make repeatedly |
| `cannot find -lnvinfer` / `-lnvparsers` | Makefile paths do not match installed TensorRT or removed legacy library | Inspect `common/Makefile.config`, `plugins/Makefile`, `setup.py`; adapt paths only in a reviewed build configuration |
| `gpu_cc.py` prints no architecture | CUDA driver cannot be loaded/initialized or no visible GPU | Check driver/container device visibility and run `nvidia-smi`; no CPU substitute exists for CUDA/plugin claims |
| plugin compile emits unsupported `sm_XX`/toolchain errors | CUDA toolkit does not support the requested architecture or compiler | Pick a supported `computes` value for the actual target or use a compatible toolkit; do not ship a plugin compiled only for another GPU |
| compiler warnings become ABI/link errors after TensorRT upgrade | legacy API/header/library mismatch | Rebuild all C++/CUDA pieces against one exact TensorRT installation; inspect `NV_TENSORRT_MAJOR` branches |

## Caffe GoogLeNet / MTCNN

| Symptom | Likely cause | Safe next action |
|---|---|---|
| Caffe parser returns null / assertion at `parse` | missing/corrupt prototxt, caffemodel, parser incompatibility, or wrong cwd | validate both artifacts, run from `googlenet/` or `mtcnn/`, capture parser log; do not replace outputs blindly |
| `find("prob")`/output tensor is null | model's output names differ from repository contract | inspect prototxt graph and update marked output plus binding expectation together; record model variant |
| MTCNN fails on PReLU | wrong original files were used instead of `_relu` workaround files | use the exact `det*_relu` pairs or separately port/test the graph |
| compile fails around `createNetworkV2`, `buildEngineWithConfig`, or `destroy` | TensorRT major does not match source branch/deprecations | select the matching historical branch or make a deliberate API port; do not mix headers and runtime |
| engine serializes but immediate verification fails | engine built with a different runtime/driver, binding count changed, or output mark is wrong | deserialize with the same stack, print binding names/dims, compare expected 2 or 3/4 counts; rebuild only after diagnosis |
| output works but accuracy differs | FP16 numerics, preprocessing, or model mismatch | compare FP32/FP16 and input preprocessing, then task-level accuracy; do not attribute to build speed |

## UFF SSD

| Symptom | Likely cause | Safe next action |
|---|---|---|
| `No conversion function registered for AddV2` | graph was not rewritten or GraphSurgeon variant differs | verify `replace_addv2()` ran and inspect graph ops; use a compatible legacy package rather than patching system packages implicitly |
| `FusedBatchNormV3` conversion failure | TensorFlow graph op is newer than UFF support | verify `replace_fusedbnv3()` and the TF/UFF compatibility pair; stop if parser still rejects it |
| `GridAnchor_TRT`, `NMS_TRT`, or `FlattenConcat_TRT` creator missing | `init_libnvinfer_plugins`/custom plugin not loaded, wrong plugin ABI, or removed API | check plugin library version and registration logs; rebuild/use a matching legacy TensorRT stack |
| `Could not register plugin creator: FlattenConcat_TRT` | duplicate registration warning known in repo's TensorRT 6 note, or a real conflicting/missing creator | determine whether parsing/build continues. If it continues, record warning; if creator lookup/build fails, treat as blocked |
| UFF output or `MarkOutput_0` is missing | namespace collapse/output graph differs by model | inspect graph outputs and model spec; do not assume all frozen graphs have identical node names |
| builder rejects `fp16_mode`, `max_batch_size`, or `build_cuda_engine` | modern TensorRT removed legacy builder API | use an isolated legacy TensorRT path or port the graph to a supported ONNX/explicit-batch workflow; this skill does not claim the port |
| `.bin` cannot deserialize later | engine is tied to TensorRT/CUDA/GPU and plugin ABI | rebuild on deployment stack; retain build metadata and do not copy old binaries as universal artifacts |

## YOLO conversion, plugin, and parser

| Symptom | Likely cause | Safe next action |
|---|---|---|
| `file (<model>.cfg) not found` or weights missing | wrong cwd/stem or acquisition step not performed | confirm approved files and run from `yolo/`; do not invoke `download_yolo.sh` implicitly |
| ONNX checker fails | malformed cfg, unsupported DarkNet layer/shape, incomplete weights, or dependency mismatch | preserve generated graph only if approved, inspect cfg parse/output shapes, validate weight size; regenerate after fixing source inputs |
| `failed to load ../plugins/libyolo_layer.so` | plugin not built, wrong cwd, missing dependent library, or wrong architecture | build/load-test the plugin with matching TensorRT/CUDA and verify path; no ONNX→TRT build yet |
| `cannot get YoloLayer_TRT plugin creator` | shared object did not register, plugin namespace/ABI mismatch, or TensorRT registry changed | load plugin before registry lookup, compare creator name/version, rebuild against exact headers; do not substitute a similarly named plugin |
| `bad number of network outputs` / anchors / scales | cfg and ONNX do not describe the same model or PAN ordering differs | use one exact cfg/weights/ONNX stem; inspect `get_output_convs`, masks, `scale_x_y`, and `new_coords` |
| ONNX parses but TensorRT plugin insertion fails | plugin only accepts one linear FLOAT input/output and old IPluginV2 API is unsupported | check TensorRT version and tensor formats; on newer TRT, port to a supported plugin interface as a separate change |
| build killed by Linux kernel | memory pressure during engine tactics/build | stop and inspect memory/swap/container limits; reduce model/workspace only with an explicit accuracy/performance decision; do not retry in a loop |
| output engine is zero/absent | build returned `None`, parser errors, or output directory not writable | inspect the first TensorRT error and path permissions; do not treat a shell exit from a wrapper as success |

## INT8 and calibration

| Symptom | Likely cause | Safe next action |
|---|---|---|
| `INT8 not supported on this platform` | no fast INT8 capability or incompatible GPU/runtime | skip INT8 or choose an approved capable target; FP16 is not an INT8 substitute |
| calibrator says directory missing / no usable images | wrong cwd or calibration set not staged | create/populate an approved set explicitly; preserve data provenance |
| fewer than 500 images warning | small calibration population | decide whether deployment coverage is adequate; warning is not an automatic failure, but record the rationale |
| `bad net shape` | calibration shape not 2D or not divisible by 32 | use the exact cfg H/W and confirm model profile; do not resize only calibration while building another shape |
| OpenCV cannot read a JPEG | corrupt/unsupported image | remove or repair the specific input after review; never let a failed read silently become zeros |
| stale cache is reused | cache filename matches stem but model/preprocess changed | quarantine/rebuild cache after checking exact hashes; never assume same stem means same calibration |
| INT8 mAP collapses | calibration distribution, plugin/concat precision, or model-specific numerical sensitivity | compare FP16 baseline, inspect calibration coverage, evaluate per-layer/output differences; repository records YOLOv4-608 as unresolved historical example |

## DLA

| Symptom | Likely cause | Safe next action |
|---|---|---|
| `DLA core not supported by old API` | TensorRT major <7 branch | stop; DLA requires the documented newer path and compatible hardware |
| no DLA device/core | non-Xavier target, wrong JetPack/driver, or hidden device | verify hardware/runtime; GPU fallback does not create a DLA |
| DLA build rejects a layer | unsupported DLA operator/format or strict type constraint | inspect verbose log; allow documented GPU fallback only if the deployment accepts mixed placement |
| engine builds but performance is GPU-like | fallback or inference core selection is not what was expected | use target runtime device/engine inspection; TensorRT 7.1 Python limitation means placement was historically uncertain |
| `yolov4-tiny-416` DLA build fails | known historical repository limitation | record as expected candidate-specific block; do not weaken checks to force serialization |

## MODNet

| Symptom | Likely cause | Safe next action |
|---|---|---|
| script exits `TensorRT version < 7` | unsupported historical runtime | use TensorRT 7+ or stop; do not bypass the guard |
| `UNSUPPORTED_NODE` / dynamic InstanceNormalization on 7.1 | documented TensorRT 7.1 ONNX-TensorRT limitation | use the separately approved onnx-tensorrt 7.1 workaround or move to 7.2+ |
| `--int8` or `--dla_core` raises not implemented | source explicitly does not implement those MODNet modes | use FP16/GPU fallback path; do not report flags as supported |
| profile input `Input` not found | ONNX input name differs or model is not the repository contract | inspect ONNX inputs and adapt profile name/dimensions deliberately |
| output engine deserializes but matting is wrong | input size/preprocessing or InstanceNorm behavior differs | compare the ONNX model's input contract, image normalization, and a reference matte; engine existence is insufficient |

## Modern TensorRT (8.5-like) triage

If a legacy script fails on a modern runtime:

1. capture the exact `trt.__version__` and first API error;
2. decide whether the failure is package absence, removed API, plugin ABI, parser
   format, or model-specific unsupported op;
3. rebuild custom plugins against the same headers/libs before changing Python;
4. prefer a documented port to explicit-batch/modern builder and plugin APIs over
   ad-hoc compatibility shims;
5. keep old UFF/Caffe paths isolated and do not claim modern support without a
   successful target-stack build and deserialization check.
