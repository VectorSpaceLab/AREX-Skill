#!/usr/bin/env python3
"""Safe DAMO-YOLO image/video/camera demo helper.

This script adapts the repository demo inference path into a self-contained
helper for generated skills. It imports the installed ``damo`` package, validates
engine extensions and media paths, and keeps GUI display opt-in.
"""

from __future__ import annotations

import argparse
import importlib.util
import os
from pathlib import Path
import sys
from typing import Iterable, Optional, Sequence


IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
VIDEO_SUFFIXES = {".mp4", ".avi", ".mov", ".mkv", ".mpeg", ".mpg"}

# Third-party/runtime symbols are loaded lazily so ``--help`` and syntax checks
# work even before DAMO-YOLO's optional inference dependencies are installed.
np = None
torch = None
cv2 = None
Image = None
RepConv = None
parse_config = None
build_local_model = None
vis = None
postprocess = None
transform_img = None
ImageList = None
BoxList = None
onnxruntime = None
trt = None
cuda = None


class DemoError(RuntimeError):
    """User-facing demo failure with a concise recovery-oriented message."""


def str_to_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"1", "true", "t", "yes", "y", "on"}:
        return True
    if text in {"0", "false", "f", "no", "n", "off"}:
        return False
    raise argparse.ArgumentTypeError(
        f"expected boolean value, got {value!r}; use true/false or --no-save-result"
    )


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        "DAMO-YOLO safe demo",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "input_type",
        choices=("image", "video", "camera"),
        help="input type to process",
    )
    parser.add_argument(
        "-f",
        "--config-file",
        required=True,
        help="DAMO-YOLO config file matching the engine/checkpoint",
    )
    parser.add_argument(
        "-p",
        "--path",
        help="image path for input_type=image or video path for input_type=video",
    )
    parser.add_argument(
        "--camid",
        type=int,
        default=0,
        help="camera id for input_type=camera",
    )
    parser.add_argument(
        "--engine",
        required=True,
        help="engine artifact: .pth/.pt, .onnx, or .trt",
    )
    parser.add_argument(
        "--device",
        choices=("cuda", "cpu"),
        default="cuda",
        help="requested device for Torch preprocessing/model execution",
    )
    parser.add_argument(
        "--output-dir",
        default="demo",
        help="directory for saved visualization results",
    )
    parser.add_argument(
        "--output-name",
        help="optional output filename; defaults to input basename or camera_<id>.mp4",
    )
    parser.add_argument(
        "--conf",
        type=float,
        default=0.6,
        help="visualization score threshold; config NMS thresholds are unchanged",
    )
    parser.add_argument(
        "--infer-size",
        nargs=2,
        type=int,
        metavar=("H", "W"),
        help="inference resize/pad target as height width, for example --infer-size 640 640",
    )
    parser.add_argument(
        "--end2end",
        action="store_true",
        help="TensorRT engine includes NMS and returns nums/boxes/scores/classes",
    )
    parser.set_defaults(save_result=True)
    parser.add_argument(
        "--save-result",
        dest="save_result",
        action="store_true",
        help="save visualized image/video results",
    )
    parser.add_argument(
        "--no-save-result",
        dest="save_result",
        action="store_false",
        help="do not save visualization results",
    )
    parser.add_argument(
        "--save_result",
        dest="save_result",
        nargs="?",
        const=True,
        type=str_to_bool,
        help="legacy source-style alias; prefer --save-result or --no-save-result",
    )
    parser.add_argument(
        "--show-window",
        action="store_true",
        help="open cv2.imshow windows when not saving; avoid in headless jobs",
    )
    parser.add_argument(
        "--max-frames",
        type=int,
        default=0,
        help="maximum frames for video/camera; 0 means unlimited",
    )
    parser.add_argument(
        "--fps",
        type=float,
        help="override output video FPS when capture metadata is missing or wrong",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="validate arguments/imports/config for the selected engine without loading weights or media",
    )
    return parser


def detect_engine(engine_path: Path) -> str:
    suffix = engine_path.suffix.lower()
    if suffix in {".pth", ".pt"}:
        return "torch"
    if suffix == ".onnx":
        return "onnx"
    if suffix == ".trt":
        return "tensorRT"
    raise DemoError(
        f"Unsupported engine extension {suffix or '<none>'!r}. "
        "Use .pth/.pt for Torch, .onnx for ONNX Runtime, or .trt for TensorRT."
    )


def ensure_path(path: Path, label: str) -> None:
    if not path.exists():
        raise DemoError(f"{label} does not exist: {path}")


def validate_args(args: argparse.Namespace) -> str:
    config_path = Path(args.config_file)
    engine_path = Path(args.engine)
    ensure_path(config_path, "Config file")
    ensure_path(engine_path, "Engine artifact")
    engine_type = detect_engine(engine_path)

    if args.input_type in {"image", "video"}:
        if not args.path:
            raise DemoError(f"--path is required for input_type={args.input_type}")
        media_path = Path(args.path)
        ensure_path(media_path, "Input media")
        suffix = media_path.suffix.lower()
        if args.input_type == "image" and suffix and suffix not in IMAGE_SUFFIXES:
            print(
                f"WARNING: image path suffix {suffix!r} is unusual; Pillow must be able to decode it.",
                file=sys.stderr,
            )
        if args.input_type == "video" and suffix and suffix not in VIDEO_SUFFIXES:
            print(
                f"WARNING: video path suffix {suffix!r} is unusual; OpenCV must be able to decode it.",
                file=sys.stderr,
            )

    if args.infer_size is not None and any(v <= 0 for v in args.infer_size):
        raise DemoError("--infer-size values must be positive integers")
    if args.conf < 0:
        raise DemoError("--conf must be non-negative")
    if args.max_frames < 0:
        raise DemoError("--max-frames must be >= 0")
    if args.fps is not None and args.fps <= 0:
        raise DemoError("--fps must be positive when provided")
    if engine_type == "tensorRT" and args.device == "cpu":
        raise DemoError("TensorRT inference is CUDA-only in this demo path; do not use --device cpu with .trt")
    if args.end2end and engine_type != "tensorRT":
        print("WARNING: --end2end only affects TensorRT engines; it will be ignored.", file=sys.stderr)
    if not args.save_result and not args.show_window:
        print(
            "WARNING: saving and GUI display are both disabled; inference will run without visible output.",
            file=sys.stderr,
        )
    return engine_type


def require_spec(import_name: str, hint: str) -> None:
    if importlib.util.find_spec(import_name) is None:
        raise DemoError(f"Missing dependency import {import_name!r}. {hint}")


def load_runtime_modules(engine_type: str) -> None:
    """Import base and engine-specific dependencies with actionable errors."""
    global np, torch, cv2, Image, RepConv, parse_config, build_local_model
    global vis, postprocess, transform_img, ImageList, BoxList, onnxruntime, trt, cuda

    for import_name, hint in [
        ("numpy", "Install DAMO-YOLO base requirements."),
        ("torch", "Install a PyTorch build matching the desired CPU/CUDA runtime."),
        ("torchvision", "Install torchvision matching the installed torch build."),
        ("cv2", "Install opencv-python or an environment-approved OpenCV package."),
        ("PIL", "Install Pillow."),
        ("damo", "Install the DAMO-YOLO package so `damo` is importable."),
    ]:
        require_spec(import_name, hint)

    try:
        import numpy as _np
        import torch as _torch
        import cv2 as _cv2
        from PIL import Image as _Image
        from damo.base_models.core.ops import RepConv as _RepConv
        from damo.config.base import parse_config as _parse_config
        from damo.detectors.detector import build_local_model as _build_local_model
        from damo.utils import postprocess as _postprocess
        from damo.utils import vis as _vis
        from damo.utils.demo_utils import transform_img as _transform_img
        from damo.structures.bounding_box import BoxList as _BoxList
        from damo.structures.image_list import ImageList as _ImageList
    except ModuleNotFoundError as exc:
        raise DemoError(
            f"Missing DAMO-YOLO inference dependency {exc.name!r}. "
            "Install the package requirements in the active environment."
        ) from exc

    np = _np
    torch = _torch
    cv2 = _cv2
    Image = _Image
    RepConv = _RepConv
    parse_config = _parse_config
    build_local_model = _build_local_model
    postprocess = _postprocess
    vis = _vis
    transform_img = _transform_img
    BoxList = _BoxList
    ImageList = _ImageList

    if engine_type == "onnx":
        require_spec("onnxruntime", "Install onnxruntime for ONNX engines.")
        try:
            import onnxruntime as _onnxruntime
        except ModuleNotFoundError as exc:
            raise DemoError("Missing onnxruntime; install it before using a .onnx engine.") from exc
        onnxruntime = _onnxruntime

    if engine_type == "tensorRT":
        require_spec("tensorrt", "Install TensorRT Python bindings matching the target CUDA stack.")
        require_spec("cuda", "Install CUDA Python bindings importable as `from cuda import cuda`.")
        try:
            import tensorrt as _trt
            from cuda import cuda as _cuda
        except ModuleNotFoundError as exc:
            raise DemoError(
                f"Missing TensorRT/CUDA Python dependency {exc.name!r}; "
                "use Torch/ONNX or install the TensorRT stack before using .trt."
            ) from exc
        trt = _trt
        cuda = _cuda


class SafeDAMOInfer:
    """DAMO-YOLO demo inference wrapper with validated engine/device behavior."""

    def __init__(
        self,
        config,
        infer_size: Optional[Sequence[int]],
        device: str,
        output_dir: Path,
        engine_path: Path,
        end2end: bool = False,
    ) -> None:
        self.engine_path = Path(engine_path)
        self.engine_type = detect_engine(self.engine_path)
        self.end2end = bool(end2end)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.config = config
        self.device = self._select_device(device)
        self.class_names = self._resolve_class_names(config)
        self.infer_size = self._resolve_infer_size(config, infer_size)
        self.config.dataset.size_divisibility = 0
        self.model = self._build_engine()

    def _select_device(self, requested: str) -> str:
        if requested == "cuda" and torch.cuda.is_available():
            return "cuda"
        if requested == "cuda":
            if self.engine_type == "tensorRT":
                raise DemoError("TensorRT engine requested but Torch reports CUDA unavailable.")
            print("WARNING: CUDA requested but unavailable; using CPU for Torch preprocessing/model path.", file=sys.stderr)
        return "cpu"

    @staticmethod
    def _resolve_class_names(config) -> tuple[str, ...]:
        configured = getattr(config.dataset, "class_names", None)
        if configured:
            return tuple(str(name) for name in configured)
        num_classes = int(config.model.head.num_classes)
        return tuple(str(i) for i in range(num_classes))

    @staticmethod
    def _resolve_infer_size(config, infer_size: Optional[Sequence[int]]) -> list[int]:
        if infer_size is not None:
            return [int(infer_size[0]), int(infer_size[1])]
        transform = getattr(getattr(config.test, "augment", None), "transform", None)
        config_size = getattr(transform, "image_max_range", None) if transform is not None else None
        if config_size is None:
            raise DemoError("--infer-size is required because config.test.augment.transform.image_max_range is missing")
        return [int(config_size[0]), int(config_size[1])]

    def _pad_image(self, img, target_size: Sequence[int]):
        n, c, h, w = img.shape
        if n != 1:
            raise DemoError(f"demo wrapper expects batch size 1, got {n}")
        target_h, target_w = int(target_size[0]), int(target_size[1])
        if h > target_h or w > target_w:
            raise DemoError(
                f"transformed image shape {(h, w)} exceeds infer_size {(target_h, target_w)}; "
                "increase --infer-size or use the engine's exported input shape"
            )
        pad_imgs = img.new_zeros((n, c, target_h, target_w))
        pad_imgs[:, :c, :h, :w].copy_(img)
        return ImageList(pad_imgs, [img.shape[-2:]], [pad_imgs.shape[-2:]])

    def _build_engine(self):
        print(f"Inference with {self.engine_type} engine")
        if self.engine_type == "torch":
            return self._build_torch_engine()
        if self.engine_type == "onnx":
            return self._build_onnx_engine()
        if self.engine_type == "tensorRT":
            return self._build_tensorrt_engine()
        raise DemoError(f"Unsupported engine type: {self.engine_type}")

    def _build_torch_engine(self):
        model = build_local_model(self.config, self.device)
        ckpt = torch.load(str(self.engine_path), map_location=self.device)
        if not isinstance(ckpt, dict) or "model" not in ckpt:
            raise DemoError("Torch checkpoint must be a dict containing key 'model'")
        model.load_state_dict(ckpt["model"], strict=True)
        for layer in model.modules():
            if isinstance(layer, RepConv):
                layer.switch_to_deploy()
        model.eval()
        return model

    def _build_onnx_engine(self):
        session = onnxruntime.InferenceSession(str(self.engine_path))
        self.input_name = session.get_inputs()[0].name
        input_shape = session.get_inputs()[0].shape
        shape_hw = input_shape[2:]
        if len(shape_hw) == 2 and all(isinstance(v, int) and v > 0 for v in shape_hw):
            self.infer_size = [int(shape_hw[0]), int(shape_hw[1])]
        elif self.infer_size is None:
            raise DemoError("ONNX input has dynamic H/W; provide --infer-size")
        providers = session.get_providers()
        print(f"ONNX Runtime providers: {providers}")
        if self.device == "cuda" and "CUDAExecutionProvider" not in providers:
            print(
                "WARNING: CUDA was requested, but this ONNX Runtime session does not report CUDAExecutionProvider.",
                file=sys.stderr,
            )
        return session

    def _build_tensorrt_engine(self):
        logger = trt.Logger(trt.Logger.INFO)
        trt.init_libnvinfer_plugins(logger, "")
        runtime = trt.Runtime(logger)
        with open(self.engine_path, "rb") as handle:
            engine = runtime.deserialize_cuda_engine(handle.read())
        if engine is None:
            raise DemoError("TensorRT failed to deserialize the engine; check version/GPU compatibility")
        context = engine.create_execution_context()

        allocations = []
        inputs = []
        outputs = []
        for binding_index in range(context.engine.num_bindings):
            is_input = context.engine.binding_is_input(binding_index)
            name = context.engine.get_binding_name(binding_index)
            dtype = context.engine.get_binding_dtype(binding_index)
            shape = list(context.engine.get_binding_shape(binding_index))
            size = np.dtype(trt.nptype(dtype)).itemsize
            for dim in shape:
                size *= int(dim)
            allocation = cuda.cuMemAlloc(size)
            if allocation[0] != cuda.CUresult.CUDA_SUCCESS:
                raise DemoError(f"CUDA allocation failed for TensorRT binding {name!r}: {allocation[0]}")
            binding = {
                "index": binding_index,
                "name": name,
                "dtype": np.dtype(trt.nptype(dtype)),
                "shape": shape,
                "allocation": allocation,
                "size": size,
            }
            allocations.append(allocation[1])
            if is_input:
                inputs.append(binding)
            else:
                outputs.append(binding)
        if not inputs:
            raise DemoError("TensorRT engine has no input bindings")
        trt_out = [np.zeros(output["shape"], output["dtype"]) for output in outputs]

        def predict(batch):
            cuda.cuMemcpyHtoD(inputs[0]["allocation"][1], np.ascontiguousarray(batch), int(inputs[0]["size"]))
            context.execute_v2(allocations)
            for output_array, output_binding in zip(trt_out, outputs):
                cuda.cuMemcpyDtoH(output_array, output_binding["allocation"][1], output_binding["size"])
            return trt_out

        return predict

    def preprocess(self, origin_img):
        img = transform_img(
            origin_img,
            0,
            **self.config.test.augment.transform,
            infer_size=self.infer_size,
        )
        original_h, original_w = origin_img.shape[:2]
        img = self._pad_image(img.tensors, self.infer_size)
        img = img.to(self.device)
        return img, (original_w, original_h)

    def postprocess(self, preds, image, origin_shape):
        if self.engine_type == "torch":
            output = preds
        elif self.engine_type == "onnx":
            scores = torch.Tensor(preds[0])
            bboxes = torch.Tensor(preds[1])
            output = postprocess(
                scores,
                bboxes,
                self.config.model.head.num_classes,
                self.config.model.head.nms_conf_thre,
                self.config.model.head.nms_iou_thre,
                image,
            )
        elif self.engine_type == "tensorRT":
            if self.end2end:
                nums, boxes, scores, pred_classes = preds[:4]
                batch_size = boxes.shape[0]
                output = [None for _ in range(batch_size)]
                for i in range(batch_size):
                    img_h, img_w = image.image_sizes[i]
                    count = int(nums[i][0])
                    boxlist = BoxList(torch.Tensor(boxes[i][:count]), (img_w, img_h), mode="xyxy")
                    boxlist.add_field("objectness", torch.Tensor(np.ones_like(scores[i][:count])))
                    boxlist.add_field("scores", torch.Tensor(scores[i][:count]))
                    boxlist.add_field("labels", torch.Tensor(pred_classes[i][:count] + 1))
                    output[i] = boxlist
            else:
                cls_scores = torch.Tensor(preds[0])
                bbox_preds = torch.Tensor(preds[1])
                output = postprocess(
                    cls_scores,
                    bbox_preds,
                    self.config.model.head.num_classes,
                    self.config.model.head.nms_conf_thre,
                    self.config.model.head.nms_iou_thre,
                    image,
                )
        else:
            raise DemoError(f"Unsupported engine type: {self.engine_type}")

        if not output or output[0] is None:
            return self._empty_detections()
        boxlist = output[0]
        if len(boxlist) == 0 or getattr(boxlist, "size", None) == (0, 0):
            return self._empty_detections()
        boxlist = boxlist.resize(origin_shape)
        return (
            boxlist.bbox.detach().cpu(),
            boxlist.get_field("scores").detach().cpu(),
            boxlist.get_field("labels").detach().cpu(),
        )

    @staticmethod
    def _empty_detections():
        return torch.empty((0, 4)), torch.empty((0,)), torch.empty((0,), dtype=torch.long)

    def forward(self, origin_image):
        image, origin_shape = self.preprocess(origin_image)
        if self.engine_type == "torch":
            with torch.no_grad():
                output = self.model(image)
        elif self.engine_type == "onnx":
            image_np = np.asarray(image.tensors.cpu())
            output = self.model.run(None, {self.input_name: image_np})
        elif self.engine_type == "tensorRT":
            image_np = np.asarray(image.tensors.cpu()).astype(np.float32)
            output = self.model(image_np)
        else:
            raise DemoError(f"Unsupported engine type: {self.engine_type}")
        return self.postprocess(output, image, origin_shape=origin_shape)

    def _validate_class_labels(self, cls_inds) -> None:
        if len(cls_inds) == 0:
            return
        labels = [int(v) for v in cls_inds.detach().cpu().tolist()]
        bad = sorted({label for label in labels if label < 0 or label >= len(self.class_names)})
        if bad:
            raise DemoError(
                f"Class label(s) {bad} do not fit class_names length {len(self.class_names)}. "
                "Check config.dataset.class_names, model.head.num_classes, and export class indexing."
            )

    def visualize(self, image, bboxes, scores, cls_inds, conf: float):
        self._validate_class_labels(cls_inds)
        return vis(image.copy(), bboxes, scores, cls_inds, conf, self.class_names)


def save_image(output_dir: Path, save_name: str, image_rgb) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    save_path = output_dir / save_name
    ok = cv2.imwrite(str(save_path), image_rgb[:, :, ::-1])
    if not ok:
        raise DemoError(f"cv2.imwrite failed for {save_path}")
    print(f"Saved visualization results at {save_path}")
    return save_path


def maybe_show(window_name: str, frame, wait_ms: int = 0) -> None:
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.imshow(window_name, frame)
    cv2.waitKey(wait_ms)


def run_image(args: argparse.Namespace, infer_engine: SafeDAMOInfer) -> None:
    input_path = Path(args.path)
    origin_img = np.asarray(Image.open(input_path).convert("RGB"))
    bboxes, scores, cls_inds = infer_engine.forward(origin_img)
    vis_res = infer_engine.visualize(origin_img, bboxes, scores, cls_inds, conf=args.conf)
    if args.save_result:
        save_name = args.output_name or input_path.name
        save_image(Path(args.output_dir), save_name, vis_res)
    if args.show_window:
        maybe_show("DAMO-YOLO", vis_res[:, :, ::-1], wait_ms=0)
        cv2.destroyAllWindows()


def writer_path_for_stream(args: argparse.Namespace) -> Path:
    output_dir = Path(args.output_dir)
    if args.output_name:
        return output_dir / args.output_name
    if args.input_type == "video":
        return output_dir / Path(args.path).name
    return output_dir / f"camera_{args.camid}.mp4"


def run_stream(args: argparse.Namespace, infer_engine: SafeDAMOInfer) -> None:
    source = str(args.path) if args.input_type == "video" else int(args.camid)
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        raise DemoError(f"cv2.VideoCapture could not open {source!r}")

    writer = None
    processed = 0
    try:
        ok, frame = cap.read()
        if not ok:
            raise DemoError(f"No frames could be read from {source!r}")
        height, width = frame.shape[:2]
        fps = args.fps or cap.get(cv2.CAP_PROP_FPS) or 30.0
        if fps <= 0:
            fps = 30.0
        if args.save_result:
            save_path = writer_path_for_stream(args)
            save_path.parent.mkdir(parents=True, exist_ok=True)
            writer = cv2.VideoWriter(
                str(save_path),
                cv2.VideoWriter_fourcc(*"mp4v"),
                float(fps),
                (int(width), int(height)),
            )
            if not writer.isOpened():
                raise DemoError(f"cv2.VideoWriter could not open {save_path}")
            print(f"Inference result will be saved at {save_path}")

        while ok:
            bboxes, scores, cls_inds = infer_engine.forward(frame)
            result_frame = infer_engine.visualize(frame, bboxes, scores, cls_inds, conf=args.conf)
            if writer is not None:
                writer.write(result_frame)
            if args.show_window:
                cv2.namedWindow("DAMO-YOLO", cv2.WINDOW_NORMAL)
                cv2.imshow("DAMO-YOLO", result_frame)
                key = cv2.waitKey(1)
                if key in {27, ord("q"), ord("Q")}:
                    break
            processed += 1
            if args.max_frames and processed >= args.max_frames:
                break
            ok, frame = cap.read()
    finally:
        cap.release()
        if writer is not None:
            writer.release()
        if args.show_window:
            cv2.destroyAllWindows()
    print(f"Processed {processed} frame(s)")


def summarize_config(config) -> str:
    num_classes = getattr(config.model.head, "num_classes", "unknown")
    names = getattr(config.dataset, "class_names", None)
    names_len = len(names) if names is not None else "missing"
    return f"num_classes={num_classes}, class_names={names_len}"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = make_parser()
    args = parser.parse_args(argv)
    try:
        engine_type = validate_args(args)
        load_runtime_modules(engine_type)
        config = parse_config(args.config_file)
        if args.check_only:
            print(f"Selected engine: {engine_type}")
            print(f"Config summary: {summarize_config(config)}")
            print("Check-only completed without loading weights or media.")
            return 0
        infer_engine = SafeDAMOInfer(
            config=config,
            infer_size=args.infer_size,
            device=args.device,
            output_dir=Path(args.output_dir),
            engine_path=Path(args.engine),
            end2end=args.end2end,
        )
        if args.input_type == "image":
            run_image(args, infer_engine)
        else:
            run_stream(args, infer_engine)
        return 0
    except (DemoError, FileNotFoundError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
