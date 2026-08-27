#!/usr/bin/env python3
"""Safe pytorch-yolo-v3 image pipeline smoke check.

This helper validates image preprocessing, IoU, and postprocessing with a tiny
synthetic image and tensor. It never downloads weights, loads YOLO weights,
opens a GUI/camera, or writes outside a temporary directory unless the user
passes --image, which is read-only.

Examples:
  python scripts/check_image_pipeline.py --reso 64
  python scripts/check_image_pipeline.py --repo-root <repo-root> --reso 64
  python scripts/check_image_pipeline.py --image <image-file.png> --reso 64
"""

from __future__ import annotations

import argparse
import contextlib
import importlib
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from typing import Callable, Iterable, Tuple

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
NUM_CLASSES = 80


class CheckFailure(RuntimeError):
    """Raised for actionable validation failures."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run a deterministic no-weight pytorch-yolo-v3 image pipeline smoke "
            "check. By default it uses bundled fallback implementations; pass "
            "--repo-root to import and inspect a user's checkout modules."
        )
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Optional path to a pytorch-yolo-v3 checkout whose preprocess/bbox/util modules should be imported.",
    )
    parser.add_argument(
        "--reso",
        type=int,
        default=64,
        help="Network input resolution for the smoke image; must be >32 and divisible by 32. Default: 64.",
    )
    parser.add_argument(
        "--confidence",
        type=float,
        default=0.5,
        help="Synthetic object-confidence threshold to pass to write_results. Default: 0.5.",
    )
    parser.add_argument(
        "--nms-thresh",
        type=float,
        default=0.4,
        help="Synthetic NMS IoU threshold to pass as nms_conf. Default: 0.4.",
    )
    parser.add_argument(
        "--image",
        type=Path,
        default=None,
        help="Optional existing .jpg/.jpeg/.png image to read instead of creating a temporary tiny image.",
    )
    parser.add_argument(
        "--device",
        choices=("cpu", "cuda", "auto"),
        default="cpu",
        help="Tensor device for IoU/postprocessing checks. Default is safe CPU; use cuda only when available.",
    )
    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> None:
    if args.reso <= 32 or args.reso % 32 != 0:
        raise CheckFailure(
            f"invalid --reso {args.reso}: pytorch-yolo-v3 requires a value greater than 32 and divisible by 32"
        )
    if not (0.0 <= args.confidence < 1.0):
        raise CheckFailure("--confidence must be >= 0 and < 1 for the synthetic positive-box check")
    if not (0.0 <= args.nms_thresh <= 1.0):
        raise CheckFailure("--nms-thresh must be between 0 and 1")
    if args.image is not None:
        if args.image.suffix.lower() not in IMAGE_EXTENSIONS:
            raise CheckFailure(
                f"unsupported --image extension {args.image.suffix!r}; use .jpg, .jpeg, or .png"
            )
        if not args.image.is_file():
            raise CheckFailure(f"--image does not point to a readable file: {args.image}")
    if args.repo_root is not None and not args.repo_root.is_dir():
        raise CheckFailure(f"--repo-root does not point to a directory: {args.repo_root}")


def import_required_modules():
    try:
        import cv2  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on environment
        raise CheckFailure(
            "OpenCV import failed. Install an environment with cv2/opencv-python before using image preprocessing."
        ) from exc
    try:
        import numpy as np  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on environment
        raise CheckFailure("NumPy import failed; it is required for image preprocessing checks.") from exc
    try:
        import torch  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on environment
        raise CheckFailure("PyTorch import failed; it is required for tensor postprocessing checks.") from exc
    return cv2, np, torch


@contextlib.contextmanager
def force_torch_cuda_available(torch_module, value: bool):
    """Temporarily force torch.cuda.is_available for repo helpers that branch on it."""

    original = torch_module.cuda.is_available
    torch_module.cuda.is_available = lambda: value
    try:
        yield
    finally:
        torch_module.cuda.is_available = original


def fallback_letterbox_image(cv2, np):
    def letterbox_image(img, inp_dim: Tuple[int, int]):
        img_w, img_h = img.shape[1], img.shape[0]
        w, h = inp_dim
        scale = min(w / img_w, h / img_h)
        new_w = int(img_w * scale)
        new_h = int(img_h * scale)
        resized_image = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
        canvas = np.full((inp_dim[1], inp_dim[0], 3), 128, dtype=img.dtype)
        y0 = (h - new_h) // 2
        x0 = (w - new_w) // 2
        canvas[y0 : y0 + new_h, x0 : x0 + new_w, :] = resized_image
        return canvas

    return letterbox_image


def fallback_prep_image(cv2, np, torch_module):
    letterbox_image = fallback_letterbox_image(cv2, np)

    def prep_image(img: str, inp_dim: int):
        orig_im = cv2.imread(img)
        if orig_im is None:
            raise ValueError(f"OpenCV could not read image: {img}")
        dim = (orig_im.shape[1], orig_im.shape[0])
        img_arr = letterbox_image(orig_im, (inp_dim, inp_dim))
        img_arr = img_arr[:, :, ::-1].transpose((2, 0, 1)).copy()
        tensor = torch_module.from_numpy(img_arr).float().div(255.0).unsqueeze(0)
        return tensor, orig_im, dim

    return prep_image


def fallback_bbox_iou(torch_module):
    def bbox_iou(box1, box2):
        b1_x1, b1_y1, b1_x2, b1_y2 = box1[:, 0], box1[:, 1], box1[:, 2], box1[:, 3]
        b2_x1, b2_y1, b2_x2, b2_y2 = box2[:, 0], box2[:, 1], box2[:, 2], box2[:, 3]
        inter_rect_x1 = torch_module.max(b1_x1, b2_x1)
        inter_rect_y1 = torch_module.max(b1_y1, b2_y1)
        inter_rect_x2 = torch_module.min(b1_x2, b2_x2)
        inter_rect_y2 = torch_module.min(b1_y2, b2_y2)
        zeros = torch_module.zeros(inter_rect_x2.shape, device=inter_rect_x2.device, dtype=inter_rect_x2.dtype)
        inter_area = torch_module.max(inter_rect_x2 - inter_rect_x1 + 1, zeros) * torch_module.max(
            inter_rect_y2 - inter_rect_y1 + 1, zeros
        )
        b1_area = (b1_x2 - b1_x1 + 1) * (b1_y2 - b1_y1 + 1)
        b2_area = (b2_x2 - b2_x1 + 1) * (b2_y2 - b2_y1 + 1)
        return inter_area / (b1_area + b2_area - inter_area)

    return bbox_iou


def fallback_write_results(torch_module, bbox_iou_fn: Callable):
    def unique(tensor):
        tensor_np = tensor.detach().cpu().numpy()
        unique_np = sorted(set(tensor_np.tolist()))
        return tensor.new_tensor(unique_np)

    def write_results(prediction, confidence, num_classes, nms=True, nms_conf=0.4):
        conf_mask = (prediction[:, :, 4] > confidence).float().unsqueeze(2)
        prediction = prediction * conf_mask
        if torch_module.nonzero(prediction[:, :, 4]).numel() == 0:
            return 0

        box_a = prediction.new(prediction.shape)
        box_a[:, :, 0] = prediction[:, :, 0] - prediction[:, :, 2] / 2
        box_a[:, :, 1] = prediction[:, :, 1] - prediction[:, :, 3] / 2
        box_a[:, :, 2] = prediction[:, :, 0] + prediction[:, :, 2] / 2
        box_a[:, :, 3] = prediction[:, :, 1] + prediction[:, :, 3] / 2
        prediction[:, :, :4] = box_a[:, :, :4]

        outputs = []
        for ind in range(prediction.size(0)):
            image_pred = prediction[ind]
            max_conf, max_conf_score = torch_module.max(image_pred[:, 5 : 5 + num_classes], 1)
            image_pred = torch_module.cat(
                (image_pred[:, :5], max_conf.float().unsqueeze(1), max_conf_score.float().unsqueeze(1)), 1
            )
            non_zero_ind = torch_module.nonzero(image_pred[:, 4]).squeeze()
            if non_zero_ind.numel() == 0:
                continue
            image_pred_ = image_pred[non_zero_ind].view(-1, 7)
            img_classes = unique(image_pred_[:, -1])

            for cls in img_classes:
                cls_mask = image_pred_ * (image_pred_[:, -1] == cls).float().unsqueeze(1)
                class_mask_ind = torch_module.nonzero(cls_mask[:, -2]).squeeze()
                if class_mask_ind.numel() == 0:
                    continue
                image_pred_class = image_pred_[class_mask_ind].view(-1, 7)
                conf_sort_index = torch_module.sort(image_pred_class[:, 4], descending=True)[1]
                image_pred_class = image_pred_class[conf_sort_index]

                if nms:
                    keep_rows = []
                    while image_pred_class.size(0):
                        current = image_pred_class[0:1]
                        keep_rows.append(current)
                        if image_pred_class.size(0) == 1:
                            break
                        ious = bbox_iou_fn(current, image_pred_class[1:])
                        image_pred_class = image_pred_class[1:][ious < nms_conf]
                    image_pred_class = torch_module.cat(keep_rows, 0)

                batch_ind = image_pred_class.new_full((image_pred_class.size(0), 1), ind)
                outputs.append(torch_module.cat((batch_ind, image_pred_class), 1))

        if not outputs:
            return 0
        return torch_module.cat(outputs, 0)

    return write_results


def load_pipeline(args: argparse.Namespace, cv2, np, torch_module) -> SimpleNamespace:
    if args.repo_root is None:
        bbox_iou_fn = fallback_bbox_iou(torch_module)
        return SimpleNamespace(
            source="bundled fallback implementations",
            prep_image=fallback_prep_image(cv2, np, torch_module),
            bbox_iou=bbox_iou_fn,
            write_results=fallback_write_results(torch_module, bbox_iou_fn),
            uses_repo=False,
        )

    repo_root = args.repo_root.expanduser().resolve()
    sys.path.insert(0, str(repo_root))
    for module_name in ("preprocess", "bbox", "util"):
        sys.modules.pop(module_name, None)
    try:
        preprocess = importlib.import_module("preprocess")
        bbox = importlib.import_module("bbox")
        util = importlib.import_module("util")
    except Exception as exc:
        raise CheckFailure(
            "Could not import preprocess, bbox, and util from --repo-root. "
            "Check that the path is a pytorch-yolo-v3 checkout and that OpenCV, PyTorch, NumPy, matplotlib, and other imports are installed."
        ) from exc

    for module, attr in ((preprocess, "prep_image"), (bbox, "bbox_iou"), (util, "write_results")):
        if not hasattr(module, attr):
            raise CheckFailure(f"Imported module {module.__name__!r} is missing expected API {attr!r}")

    return SimpleNamespace(
        source="repo modules imported via --repo-root",
        prep_image=preprocess.prep_image,
        bbox_iou=bbox.bbox_iou,
        write_results=util.write_results,
        uses_repo=True,
    )


def select_device(args: argparse.Namespace, torch_module) -> str:
    if args.device == "cuda":
        if not torch_module.cuda.is_available():
            raise CheckFailure("--device cuda was requested, but torch.cuda.is_available() is false")
        return "cuda"
    if args.device == "auto":
        return "cuda" if torch_module.cuda.is_available() else "cpu"
    return "cpu"


def create_temporary_image(cv2, np):
    tmpdir = tempfile.TemporaryDirectory(prefix="pytorch_yolov3_image_check_")
    path = Path(tmpdir.name) / "tiny.png"
    image = np.zeros((24, 32, 3), dtype=np.uint8)
    image[:, :, 0] = 64
    image[:, :, 1] = 128
    image[:, :, 2] = 192
    ok = cv2.imwrite(str(path), image)
    if not ok:
        tmpdir.cleanup()
        raise CheckFailure("OpenCV could not write the temporary tiny image used for the smoke check")
    return tmpdir, path


def tensor_shape(tensor) -> Tuple[int, ...]:
    return tuple(int(x) for x in tensor.shape)


def run_prep_check(pipeline: SimpleNamespace, image_path: Path, reso: int, torch_module) -> None:
    try:
        tensor, orig_im, dim = pipeline.prep_image(str(image_path), reso)
    except Exception as exc:
        raise CheckFailure(
            "prep_image failed. Check that OpenCV can read the image, the path is correct, and the image is a supported .jpg/.jpeg/.png file."
        ) from exc

    expected = (1, 3, reso, reso)
    if tensor_shape(tensor) != expected:
        raise CheckFailure(f"prep_image returned tensor shape {tensor_shape(tensor)}, expected {expected}")
    if orig_im is None or len(getattr(orig_im, "shape", ())) != 3:
        raise CheckFailure("prep_image did not return a valid original HWC image array")
    expected_dim = (int(orig_im.shape[1]), int(orig_im.shape[0]))
    if tuple(dim) != expected_dim:
        raise CheckFailure(f"prep_image returned dim {dim}, expected width/height {expected_dim}")
    if not hasattr(tensor, "dtype") or not torch_module.is_floating_point(tensor):
        raise CheckFailure("prep_image tensor is not floating point")

    print(f"PASS prep_image: tensor shape {expected}, original shape {tuple(orig_im.shape)}, dim {tuple(dim)}")


def run_bbox_check(pipeline: SimpleNamespace, torch_module, device: str) -> None:
    box1 = torch_module.tensor([[0.0, 0.0, 10.0, 10.0]], device=device)
    box2 = torch_module.tensor([[5.0, 5.0, 15.0, 15.0], [20.0, 20.0, 30.0, 30.0]], device=device)
    context = force_torch_cuda_available(torch_module, False) if device == "cpu" else contextlib.nullcontext()
    try:
        with context:
            iou = pipeline.bbox_iou(box1, box2)
    except Exception as exc:
        raise CheckFailure("bbox_iou failed on synthetic corner-coordinate boxes") from exc

    if tensor_shape(iou) != (2,):
        raise CheckFailure(f"bbox_iou returned shape {tensor_shape(iou)}, expected (2,)")
    if not bool(torch_module.isfinite(iou).all().item()):
        raise CheckFailure("bbox_iou returned non-finite values")
    iou_cpu = [round(float(x), 6) for x in iou.detach().cpu().tolist()]
    print(f"PASS bbox_iou: finite IoU values {iou_cpu} on {device}")


def run_write_results_check(pipeline: SimpleNamespace, torch_module, device: str, confidence: float, nms_thresh: float) -> None:
    prediction = torch_module.zeros((1, 1, 5 + NUM_CLASSES), device=device)
    prediction[0, 0, 0:4] = torch_module.tensor([10.0, 10.0, 4.0, 4.0], device=device)
    prediction[0, 0, 4] = min(0.9999, max(0.9, confidence + 0.01))
    prediction[0, 0, 5] = 0.8

    context = force_torch_cuda_available(torch_module, False) if device == "cpu" else contextlib.nullcontext()
    try:
        with context:
            output = pipeline.write_results(prediction, confidence, NUM_CLASSES, nms=True, nms_conf=nms_thresh)
    except Exception as exc:
        raise CheckFailure("write_results failed on a synthetic positive prediction tensor") from exc

    if isinstance(output, int):
        raise CheckFailure("write_results returned 0 for a synthetic prediction that should survive confidence filtering")
    if tensor_shape(output) != (1, 8):
        raise CheckFailure(f"write_results returned shape {tensor_shape(output)}, expected (1, 8)")
    if not bool(torch_module.isfinite(output).all().item()):
        raise CheckFailure("write_results returned non-finite values")
    row = [round(float(x), 6) for x in output.detach().cpu().view(-1).tolist()]
    print(f"PASS write_results: output shape (1, 8), row {row}")


def main() -> int:
    args = parse_args()
    try:
        validate_args(args)
        cv2, np, torch_module = import_required_modules()
        pipeline = load_pipeline(args, cv2, np, torch_module)
        device = select_device(args, torch_module)

        temp_handle = None
        if args.image is None:
            temp_handle, image_path = create_temporary_image(cv2, np)
            print("INFO image: created temporary 24x32 PNG fixture")
        else:
            image_path = args.image.expanduser().resolve()
            print("INFO image: using user-provided image read-only")

        try:
            print(f"INFO pipeline: {pipeline.source}")
            print(f"INFO device: {device}")
            run_prep_check(pipeline, image_path, args.reso, torch_module)
            run_bbox_check(pipeline, torch_module, device)
            run_write_results_check(pipeline, torch_module, device, args.confidence, args.nms_thresh)
        finally:
            if temp_handle is not None:
                temp_handle.cleanup()

    except CheckFailure as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        cause = exc.__cause__
        if cause is not None:
            print(f"CAUSE {type(cause).__name__}: {cause}", file=sys.stderr)
        return 1

    print("PASS image pipeline smoke check completed without weights, downloads, CUDA requirements, GUI, camera, or sample images")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
