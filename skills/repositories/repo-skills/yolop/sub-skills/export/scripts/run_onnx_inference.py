#!/usr/bin/env python3
"""Run YOLOP ONNXRuntime inference with explicit model/image/output paths.

Example:
  python run_onnx_inference.py --repo-root /path/to/YOLOP --onnx /tmp/yolop.onnx \
    --image /path/to/image.jpg --output-dir /tmp/yolop-onnx-output
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import cv2
import numpy as np
import onnxruntime as ort
import torch


def resize_unscale(img: np.ndarray, new_shape: tuple[int, int], color: int = 114):
    shape = img.shape[:2]
    canvas = np.zeros((new_shape[0], new_shape[1], 3), dtype=np.float32)
    canvas.fill(color)
    r = min(new_shape[0] / shape[0], new_shape[1] / shape[1])
    new_unpad_w = int(round(shape[1] * r))
    new_unpad_h = int(round(shape[0] * r))
    dw = (new_shape[1] - new_unpad_w) // 2
    dh = (new_shape[0] - new_unpad_h) // 2
    if shape[::-1] != (new_unpad_w, new_unpad_h):
        img = cv2.resize(img, (new_unpad_w, new_unpad_h), interpolation=cv2.INTER_AREA)
    canvas[dh : dh + new_unpad_h, dw : dw + new_unpad_w, :] = img
    return canvas, r, dw, dh, new_unpad_w, new_unpad_h


def _static_hw(session: ort.InferenceSession, fallback: int) -> tuple[int, int]:
    shape = session.get_inputs()[0].shape
    try:
        h = int(shape[2])
        w = int(shape[3])
        return h, w
    except Exception:
        return fallback, fallback


def main() -> int:
    parser = argparse.ArgumentParser(description="YOLOP ONNXRuntime inference helper")
    parser.add_argument("--repo-root", required=True, help="Path to a YOLOP checkout, used for NMS implementation")
    parser.add_argument("--onnx", required=True, help="Path to YOLOP ONNX model")
    parser.add_argument("--image", required=True, help="Input image path")
    parser.add_argument("--output-dir", required=True, help="Directory for detect/drivable/lane/merged outputs")
    parser.add_argument("--input-size", type=int, default=640, help="Fallback square input size for dynamic ONNX shapes")
    parser.add_argument("--conf-thres", type=float, default=0.25, help="NMS confidence threshold")
    parser.add_argument("--iou-thres", type=float, default=0.45, help="NMS IoU threshold")
    parser.add_argument("--dry-run", action="store_true", help="Only print ONNX inputs/outputs")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    if not (repo_root / "lib" / "core" / "general.py").is_file():
        print(f"ERROR: not a YOLOP checkout: {repo_root}", file=sys.stderr)
        return 2
    sys.path.insert(0, str(repo_root))
    from lib.core.general import non_max_suppression

    onnx_path = Path(args.onnx).expanduser().resolve()
    image_path = Path(args.image).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()
    if not onnx_path.is_file():
        print(f"ERROR: ONNX model not found: {onnx_path}", file=sys.stderr)
        return 3
    if not image_path.is_file():
        print(f"ERROR: image not found: {image_path}", file=sys.stderr)
        return 4

    ort.set_default_logger_severity(4)
    session = ort.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"])
    print(f"onnx_inputs={[(i.name, i.shape) for i in session.get_inputs()]}")
    print(f"onnx_outputs={[(o.name, o.shape) for o in session.get_outputs()]}")
    if args.dry_run:
        return 0
    output_names = [o.name for o in session.get_outputs()]
    required = ["det_out", "drive_area_seg", "lane_line_seg"]
    missing = [name for name in required if name not in output_names]
    if missing:
        print(f"ERROR: ONNX model missing expected outputs: {missing}", file=sys.stderr)
        return 5

    h_in, w_in = _static_hw(session, args.input_size)
    img_bgr = cv2.imread(str(image_path))
    if img_bgr is None:
        print(f"ERROR: cv2 could not read image: {image_path}", file=sys.stderr)
        return 6
    height, width = img_bgr.shape[:2]
    img_rgb = img_bgr[:, :, ::-1].copy()
    canvas, r, dw, dh, new_unpad_w, new_unpad_h = resize_unscale(img_rgb, (h_in, w_in))

    arr = canvas.copy().astype(np.float32) / 255.0
    arr[:, :, 0] = (arr[:, :, 0] - 0.485) / 0.229
    arr[:, :, 1] = (arr[:, :, 1] - 0.456) / 0.224
    arr[:, :, 2] = (arr[:, :, 2] - 0.406) / 0.225
    arr = np.expand_dims(arr.transpose(2, 0, 1), 0)

    det_out, da_seg_out, ll_seg_out = session.run(required, {session.get_inputs()[0].name: arr})
    boxes = non_max_suppression(torch.from_numpy(det_out).float(), conf_thres=args.conf_thres, iou_thres=args.iou_thres)[0]
    boxes_np = boxes.cpu().numpy().astype(np.float32)
    if boxes_np.shape[0]:
        boxes_np[:, 0] -= dw
        boxes_np[:, 1] -= dh
        boxes_np[:, 2] -= dw
        boxes_np[:, 3] -= dh
        boxes_np[:, :4] /= r

    da_seg_out = da_seg_out[:, :, dh : dh + new_unpad_h, dw : dw + new_unpad_w]
    ll_seg_out = ll_seg_out[:, :, dh : dh + new_unpad_h, dw : dw + new_unpad_w]
    da_seg_mask = np.argmax(da_seg_out, axis=1)[0].astype(np.uint8)
    ll_seg_mask = np.argmax(ll_seg_out, axis=1)[0].astype(np.uint8)

    color_area = np.zeros((new_unpad_h, new_unpad_w, 3), dtype=np.uint8)
    color_area[da_seg_mask == 1] = [0, 255, 0]
    color_area[ll_seg_mask == 1] = [255, 0, 0]
    color_seg = color_area[:, :, ::-1]
    color_mask = np.mean(color_seg, axis=2)
    img_merge = canvas[dh : dh + new_unpad_h, dw : dw + new_unpad_w, :][:, :, ::-1]
    img_merge[color_mask != 0] = img_merge[color_mask != 0] * 0.5 + color_seg[color_mask != 0] * 0.5
    img_merge = cv2.resize(img_merge.astype(np.uint8), (width, height), interpolation=cv2.INTER_LINEAR)

    img_det = img_bgr.copy()
    for row in boxes_np:
        x1, y1, x2, y2, conf, label = row
        cv2.rectangle(img_det, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2, 2)
        cv2.rectangle(img_merge, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2, 2)

    da_vis = cv2.resize((da_seg_mask * 255).astype(np.uint8), (width, height), interpolation=cv2.INTER_LINEAR)
    ll_vis = cv2.resize((ll_seg_mask * 255).astype(np.uint8), (width, height), interpolation=cv2.INTER_LINEAR)
    output_dir.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output_dir / "detect.jpg"), img_det)
    cv2.imwrite(str(output_dir / "drivable.png"), da_vis)
    cv2.imwrite(str(output_dir / "lane.png"), ll_vis)
    cv2.imwrite(str(output_dir / "merged.jpg"), img_merge)
    print(f"boxes={boxes_np.shape[0]} output_dir={output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
