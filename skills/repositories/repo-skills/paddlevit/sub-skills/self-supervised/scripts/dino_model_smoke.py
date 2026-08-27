#!/usr/bin/env python3
"""Bounded synthetic PaddleViT DINO model/crop smoke.

No dataset, checkpoint, torch/timm package, hub access, or source mutation is
used. The script imports only the checked-out DINO implementation and uses a
small synthetic ViT. CPU is the default; ``--device gpu:0`` is an explicit
CUDA smoke.
"""
from __future__ import print_function

import argparse
import importlib
import sys
from pathlib import Path


def find_dino_dir(repo_root=None):
    candidates = []
    if repo_root:
        candidates.append(Path(repo_root) / "self_supervised_learning" / "dino")
    here = Path(__file__).resolve()
    candidates.extend(parent / "self_supervised_learning" / "dino" for parent in here.parents)
    candidates.extend(Path.cwd() / suffix for suffix in (
        Path("self_supervised_learning/dino"), Path("dino")))
    for candidate in candidates:
        if (candidate / "transformer.py").is_file() and (candidate / "config.py").is_file():
            return candidate.resolve()
    return None


def finite(tensor):
    import numpy as np
    values = tensor.numpy()
    return bool(values.size) and bool(np.isfinite(values).all())


def dino_loss(student, teacher, ncrops, student_temp=0.1, teacher_temp=0.07):
    """Small local loss equivalent for a single-process smoke."""
    import paddle
    import paddle.nn.functional as F
    import numpy as np

    student_chunks = (student / student_temp).chunk(ncrops)
    center = paddle.mean(teacher, axis=0, keepdim=True)
    teacher_chunks = F.softmax((teacher - center) / teacher_temp, axis=-1).detach().chunk(2)
    total = paddle.to_tensor(0.0, dtype="float32")
    terms = 0
    for iq, target in enumerate(teacher_chunks):
        for view, prediction in enumerate(student_chunks):
            if view == iq:
                continue
            total = total + paddle.mean(paddle.sum(-target * F.log_softmax(prediction, axis=-1), axis=-1))
            terms += 1
    if terms == 0 or not np.isfinite(float(total.numpy())):
        raise RuntimeError("DINO synthetic loss is non-finite or has no cross-view terms")
    return total / terms


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run a no-download synthetic DINO ViT and multi-crop smoke.")
    parser.add_argument("--repo-root", help="PaddleViT checkout; inferred from cwd/script when omitted")
    parser.add_argument("--device", default="cpu", help="Paddle device, e.g. cpu or gpu:0 (default: cpu)")
    parser.add_argument("--batch-size", type=int, default=2, help="synthetic per-device batch size")
    parser.add_argument("--global-size", type=int, default=32, help="synthetic global crop size")
    parser.add_argument("--local-size", type=int, default=16, help="synthetic local crop size")
    parser.add_argument("--local-crops", type=int, default=2, help="synthetic local crop count")
    args = parser.parse_args(argv)

    if args.batch_size < 1 or args.global_size < 8 or args.local_size < 8 or args.local_crops < 1:
        parser.error("batch and crop sizes/count must be positive (sizes must be >= 8)")
    dino_dir = find_dino_dir(args.repo_root)
    if dino_dir is None:
        print("ERROR: could not locate self_supervised_learning/dino; use --repo-root", file=sys.stderr)
        return 2
    try:
        import numpy as np
        import paddle
    except ImportError as exc:
        print("ERROR: Paddle and NumPy are required for the model smoke: %s" % exc, file=sys.stderr)
        return 2

    try:
        paddle.set_device(args.device)
    except Exception as exc:
        print("ERROR: could not select Paddle device %r: %s" % (args.device, exc), file=sys.stderr)
        return 2

    sys.path.insert(0, str(dino_dir))
    try:
        config_module = importlib.import_module("config")
        transformer = importlib.import_module("transformer")
    except Exception as exc:
        print("ERROR: DINO source import failed from %s: %s" % (dino_dir, exc), file=sys.stderr)
        return 1

    config = config_module.get_config()
    config.defrost()
    config.DATA.IMAGE_SIZE = args.global_size
    config.DATA.SMALL_CROP_IMAGE_SIZE = args.local_size
    config.DATA.LOCAL_CROPS_NUMBER = args.local_crops
    config.MODEL.OUT_DIM = 32
    config.MODEL.DROPPATH = 0.0
    config.MODEL.TRANS.PATCH_SIZE = 8
    config.MODEL.TRANS.IN_CHANNELS = 3
    config.MODEL.TRANS.EMBED_DIM = 32
    config.MODEL.TRANS.DEPTH = 1
    config.MODEL.TRANS.NUM_HEADS = 4
    config.MODEL.TRANS.MLP_RATIO = 2.0
    config.freeze()
    if args.global_size % 8 or args.local_size % 8:
        print("ERROR: synthetic crop sizes must be divisible by patch size 8", file=sys.stderr)
        return 1

    try:
        student_backbone = transformer.build_vit(config)
        teacher_backbone = transformer.build_vit(config)
        student = transformer.MultiCropWrapper(
            student_backbone,
            transformer.DINOHead(in_dim=32, out_dim=32, use_bn=False, norm_last_layer=True),
        )
        teacher = transformer.MultiCropWrapper(
            teacher_backbone,
            transformer.DINOHead(in_dim=32, out_dim=32, use_bn=False),
        )
        teacher.set_state_dict(student.state_dict())
        for parameter in teacher.parameters():
            parameter.stop_gradient = True

        global_views = [paddle.randn([args.batch_size, 3, args.global_size, args.global_size]) for _ in range(2)]
        local_views = [paddle.randn([args.batch_size, 3, args.local_size, args.local_size]) for _ in range(args.local_crops)]
        crops = global_views + local_views
        student.train()
        teacher.eval()
        teacher_before = [parameter.clone() for parameter in teacher.parameters()]
        with paddle.no_grad():
            teacher_output = teacher(crops[:2])
        student_output = student(crops)
        loss = dino_loss(student_output, teacher_output, len(crops))
        if not finite(student_output) or not finite(teacher_output) or not finite(loss):
            raise RuntimeError("synthetic DINO output or loss is non-finite")
        loss.backward()
        # One explicit EMA update, mirroring the source's post-optimizer step.
        with paddle.no_grad():
            for student_parameter, teacher_parameter in zip(student.parameters(), teacher.parameters()):
                teacher_parameter.set_value(0.996 * teacher_parameter + 0.004 * student_parameter.detach())
        teacher_changed = any(not bool(paddle.all(a == b).numpy()) for a, b in zip(teacher_before, teacher.parameters()))
        if not all(parameter.stop_gradient for parameter in teacher.parameters()):
            raise RuntimeError("teacher parameters are not stop_gradient")
        if not teacher_changed:
            raise RuntimeError("synthetic EMA did not change the teacher")
    except Exception as exc:
        print("ERROR: synthetic DINO smoke failed: %s" % exc, file=sys.stderr)
        return 1

    print("DINO synthetic smoke: PASS")
    print("source=%s device=%s crops=%d (2 global + %d local) student_shape=%s teacher_shape=%s loss=%.6f" %
          (dino_dir, args.device, len(crops), args.local_crops,
           tuple(student_output.shape), tuple(teacher_output.shape), float(loss.numpy())))
    print("teacher_stop_gradient=PASS ema_update=PASS network_or_dataset=NOT_USED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
