#!/usr/bin/env python3
"""No-network smoke check for installed TLLib vision data/model APIs."""

from __future__ import annotations

import argparse
import importlib
import json
import tempfile
from pathlib import Path
from typing import Dict, List, Sequence


def _record(results: Dict[str, object], name: str, value: object = "ok") -> None:
    results[name] = value


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def smoke_imagelist_and_transforms(results: Dict[str, object]) -> None:
    from PIL import Image
    import torch
    import torchvision.transforms as TVT
    from tllib.vision.datasets.imagelist import ImageList, MultipleDomainsDataset
    from tllib.vision.transforms import Denormalize, MultipleApply, RandomErasing, ResizeImage

    with tempfile.TemporaryDirectory(prefix="tllib-vision-smoke-") as tmp:
        root = Path(tmp)
        image_dir = root / "domain_a"
        image_dir.mkdir()
        image_path = image_dir / "sample.png"
        Image.new("RGB", (12, 10), color=(10, 20, 30)).save(str(image_path))
        list_file = root / "train.txt"
        list_file.write_text("domain_a/sample.png 0\n", encoding="utf-8")

        dataset = ImageList(root=str(root), classes=["sample"], data_list_file=str(list_file))
        _require(len(dataset) == 1, "ImageList length mismatch")
        image, label = dataset[0]
        _require(label == 0, "ImageList label mismatch")
        _require(tuple(image.size) == (12, 10), "ImageList did not load the tiny PIL image")

        resized = ResizeImage(8)(image)
        _require(tuple(resized.size) == (8, 8), "ResizeImage failed")

        multi_apply = MultipleApply([ResizeImage(6), ResizeImage(4)])
        outputs = multi_apply(image)
        _require([tuple(item.size) for item in outputs] == [(6, 6), (4, 4)], "MultipleApply failed")

        tensor = TVT.ToTensor()(image)
        erased = RandomErasing(probability=1.0, sl=0.1, sh=0.2, r1=0.5)(tensor.clone())
        _require(tuple(erased.shape) == tuple(tensor.shape), "RandomErasing changed tensor shape")

        denorm = Denormalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
        denormed = denorm(torch.zeros(3, 2, 2))
        _require(tuple(denormed.shape) == (3, 2, 2), "Denormalize failed")

        multi_domain = MultipleDomainsDataset([dataset], ["domain_a"], [7])
        md_item = multi_domain[0]
        _require(md_item[-1] == 7, "MultipleDomainsDataset did not append domain id")

    _record(results, "imagelist_and_transforms")


def smoke_models(results: Dict[str, object], include_heavy_models: bool) -> None:
    import torch
    from tllib.vision.models import lenet, resnet18

    torch.set_num_threads(1)

    digit_model = lenet(num_classes=10).eval()
    with torch.no_grad():
        digit_features = digit_model(torch.randn(2, 1, 28, 28))
    _require(tuple(digit_features.shape) == (2, 500), "lenet feature shape mismatch")
    _require(digit_model.copy_head().out_features == 10, "lenet copy_head class count mismatch")

    resnet = resnet18(pretrained=False).eval()
    with torch.no_grad():
        fmap = resnet(torch.randn(1, 3, 64, 64))
    _require(fmap.dim() == 4 and fmap.size(1) == resnet.out_features, "resnet18 feature map mismatch")

    from tllib.vision.models.segmentation.deeplabv2 import deeplabv2_resnet101
    deeplab = deeplabv2_resnet101(num_classes=3, pretrained_backbone=False).eval()
    _require(getattr(deeplab, "num_classes", None) == 3, "deeplabv2 num_classes mismatch")

    from tllib.vision.models.keypoint_detection.loss import JointsKLLoss, JointsMSELoss
    heatmap = torch.zeros(2, 3, 4, 4)
    heatmap[:, :, 1, 1] = 1.0
    mse = JointsMSELoss()(heatmap, heatmap)
    kl = JointsKLLoss(epsilon=1e-6)(heatmap, heatmap)
    _require(torch.isfinite(mse).item(), "JointsMSELoss returned non-finite value")
    _require(torch.isfinite(kl).item(), "JointsKLLoss returned non-finite value")

    from tllib.vision.models.keypoint_detection.pose_resnet import pose_resnet101
    _require(callable(pose_resnet101), "pose_resnet101 import is not callable")

    if include_heavy_models:
        pose_model = pose_resnet101(num_keypoints=3, pretrained_backbone=False).eval()
        with torch.no_grad():
            pose_out = pose_model(torch.randn(1, 3, 64, 64))
        _require(pose_out.size(1) == 3, "pose_resnet101 heatmap channel mismatch")

        from tllib.vision.models.reid.resnet import reid_resnet18
        reid_backbone = reid_resnet18(pretrained=False).eval()
        with torch.no_grad():
            reid_out = reid_backbone(torch.randn(1, 3, 64, 64))
        _require(reid_out.dim() == 4, "reid_resnet18 output should be a feature map")
        _record(results, "heavy_models", "pose_resnet101 and reid_resnet18 forward checks passed")

    _record(results, "models", "lenet/resnet18/deeplab/keypoint-loss checks passed")


def smoke_metrics_and_utils(results: Dict[str, object]) -> None:
    import numpy as np
    import torch
    from torch.utils.data import DataLoader, TensorDataset
    from tllib.utils.data import CombineDataset, ForeverDataIterator, concatenate, send_to_device
    from tllib.utils.meter import AverageMeter, Meter, ProgressMeter
    from tllib.utils.metric import ConfusionMatrix, accuracy
    from tllib.utils.metric import keypoint_detection as keypoint_metric
    from tllib.utils.metric.reid import cmc, mean_ap
    from tllib.vision.models.reid.loss import pairwise_euclidean_distance

    logits = torch.tensor([[0.1, 0.9, 0.0], [2.0, 0.0, 0.1]])
    targets = torch.tensor([1, 0])
    top1 = accuracy(logits, targets, topk=(1,))[0]
    _require(float(top1) == 100.0, "classification accuracy mismatch")

    cm = ConfusionMatrix(num_classes=3)
    cm.update(torch.tensor([[0, 1], [2, 1]]), torch.tensor([[0, 2], [2, 1]]))
    acc_global, _, iu = cm.compute()
    _require(torch.isfinite(acc_global).item(), "ConfusionMatrix global accuracy non-finite")
    _require(torch.isfinite(iu[:3]).all().item(), "ConfusionMatrix IoU non-finite")

    heatmaps = np.zeros((1, 2, 4, 4), dtype=np.float32)
    heatmaps[0, 0, 2, 2] = 1.0
    heatmaps[0, 1, 3, 2] = 1.0
    _, avg_acc, count, preds = keypoint_metric.accuracy(heatmaps, heatmaps)
    _require(count == 2 and avg_acc == 1.0 and preds.shape == (1, 2, 2), "keypoint metric mismatch")

    feat_a = torch.tensor([[0.0, 0.0], [1.0, 1.0]])
    feat_b = torch.tensor([[0.0, 1.0], [2.0, 2.0]])
    dist_features = pairwise_euclidean_distance(feat_a, feat_b)
    _require(tuple(dist_features.shape) == (2, 2), "re-id pairwise distance shape mismatch")

    dist = torch.tensor([[0.1, 0.8, 0.9], [0.7, 0.2, 0.6]])
    query_ids = [1, 2]
    gallery_ids = [1, 2, 3]
    query_cams = [0, 0]
    gallery_cams = [1, 1, 2]
    rank_curve = cmc(dist, query_ids, gallery_ids, query_cams, gallery_cams, topk=3)
    map_value = mean_ap(dist, query_ids, gallery_ids, query_cams, gallery_cams)
    _require(rank_curve.shape[0] == 3 and np.isfinite(map_value), "re-id CMC/mAP mismatch")

    loader = DataLoader(TensorDataset(torch.arange(4)), batch_size=2)
    iterator = ForeverDataIterator(loader)
    batch_a = next(iterator)[0]
    batch_b = next(iterator)[0]
    batch_c = next(iterator)[0]
    _require(batch_a.numel() == 2 and batch_b.numel() == 2 and batch_c.numel() == 2, "ForeverDataIterator failed")

    combined = CombineDataset([TensorDataset(torch.tensor([1, 2])), TensorDataset(torch.tensor([3, 4]))])
    _require(combined[0] == [torch.tensor(1), torch.tensor(3)], "CombineDataset splice mismatch")

    nested = send_to_device({"x": [torch.tensor([1])]}, torch.device("cpu"))
    _require(nested["x"][0].device.type == "cpu", "send_to_device failed")
    cat = concatenate([torch.ones(1, 2), torch.zeros(1, 2)])
    _require(tuple(cat.shape) == (2, 2), "concatenate failed")

    meter = AverageMeter("loss", ":.2f")
    meter.update(1.0, n=2)
    meter.update(3.0, n=2)
    _require(abs(meter.avg - 2.0) < 1e-6, "AverageMeter average mismatch")
    simple_meter = Meter("epoch")
    simple_meter.update(3)
    ProgressMeter(1, [simple_meter], prefix="smoke:").display(0)

    _record(results, "metrics_and_utils")


def smoke_optional_object_detection(results: Dict[str, object]) -> None:
    try:
        importlib.import_module("tllib.vision.models.object_detection")
    except ModuleNotFoundError as exc:
        if exc.name and exc.name.startswith("detectron2"):
            _record(results, "object_detection", "optional-skip: detectron2 is not installed")
            return
        raise
    except Exception as exc:
        message = str(exc)
        if "detectron2" in message.lower():
            _record(results, "object_detection", f"optional-skip: {message}")
            return
        raise
    _record(results, "object_detection", "imported")


def main(argv: Sequence[str] = None) -> int:
    parser = argparse.ArgumentParser(description="Run a local no-network TLLib vision API smoke check.")
    parser.add_argument(
        "--include-heavy-models",
        action="store_true",
        help="Also forward through PoseResNet and re-id ResNet. This is still no-network but slower on CPU.",
    )
    args = parser.parse_args(argv)

    results: Dict[str, object] = {}

    import tllib  # type: ignore
    import torch
    import torchvision

    _record(results, "tllib_version", getattr(tllib, "__version__", "unknown"))
    _record(results, "torch_version", torch.__version__)
    _record(results, "torchvision_version", torchvision.__version__)

    smoke_imagelist_and_transforms(results)
    smoke_models(results, include_heavy_models=args.include_heavy_models)
    smoke_metrics_and_utils(results)
    smoke_optional_object_detection(results)

    print(json.dumps({"status": "ok", "checks": results}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
