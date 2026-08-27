"""Shared helpers for the perceptual-similarity skill.

These helpers are safe to import from bundled scripts regardless of the current
working directory. They use the installed `lpips` package and the skill's own
bundled assets rather than depending on the original repository checkout.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Tuple

import numpy as np
from PIL import Image
import torch

import lpips


SKILL_ROOT = Path(__file__).resolve().parents[1]
BUNDLED_EXAMPLES = SKILL_ROOT / "assets" / "examples"


def resolve_example_path(*parts: str) -> Path:
    """Return a path inside the bundled example asset tree."""

    return BUNDLED_EXAMPLES.joinpath(*parts)


def ensure_exists(path: str | Path) -> Path:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"missing path: {path}")
    return path


def choose_device(use_gpu: bool) -> torch.device:
    """Select CPU or CUDA, falling back to CPU if CUDA is unavailable."""

    if use_gpu and torch.cuda.is_available():
        return torch.device("cuda:0")
    return torch.device("cpu")


def load_rgb_image(path: str | Path) -> np.ndarray:
    """Load an image as an RGB uint8 numpy array."""

    path = Path(path)
    return np.asarray(Image.open(path).convert("RGB"))


def image_to_tensor(image_or_path: str | Path | np.ndarray) -> torch.Tensor:
    """Convert an RGB image or path to the LPIPS tensor format."""

    if isinstance(image_or_path, (str, Path)):
        image = load_rgb_image(image_or_path)
    else:
        image = np.asarray(image_or_path)
    if image.dtype != np.uint8:
        image = np.clip(image, 0, 255).astype(np.uint8)
    return lpips.im2tensor(image)


def tensor_to_pil(image_tensor: torch.Tensor) -> Image.Image:
    """Convert an LPIPS tensor back to a PIL image."""

    return Image.fromarray(lpips.tensor2im(image_tensor))


def save_tensor_image(image_tensor: torch.Tensor, path: str | Path) -> None:
    """Save an LPIPS tensor as an RGB PNG or JPEG."""

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tensor_to_pil(image_tensor).save(path)


def make_lpips_model(
    *,
    model: str = "lpips",
    net: str = "alex",
    version: str = "0.1",
    use_gpu: bool = False,
    pnet_rand: bool = False,
    pnet_tune: bool = False,
    spatial: bool = False,
    model_path: str | None = None,
    verbose: bool = False,
):
    """Create a LPIPS-compatible model and the device it should run on."""

    model_key = model.lower()
    if model_key not in {"lpips", "baseline"}:
        raise ValueError(f"unsupported LPIPS model kind: {model}")

    device = choose_device(use_gpu)
    if use_gpu and device.type != "cuda":
        print("[lpips] CUDA requested but unavailable; using CPU instead.")

    net_model = lpips.LPIPS(
        pretrained=True,
        net=net,
        version=version,
        lpips=(model_key == "lpips"),
        spatial=spatial,
        pnet_rand=pnet_rand,
        pnet_tune=pnet_tune,
        use_dropout=True,
        model_path=model_path,
        eval_mode=True,
        verbose=verbose,
    )
    net_model.eval()
    if device.type == "cuda":
        net_model = net_model.to(device)
    return net_model, device


def lpips_distance(model, img0: torch.Tensor, img1: torch.Tensor) -> torch.Tensor:
    """Run a model under `torch.no_grad()` and return its output tensor."""

    with torch.no_grad():
        return model(img0, img1)


def _iterate_pairs(img0: torch.Tensor, img1: torch.Tensor):
    for item0, item1 in zip(img0.split(1, dim=0), img1.split(1, dim=0)):
        yield item0, item1


def l2_distance_batch(
    img0: torch.Tensor,
    img1: torch.Tensor,
    *,
    colorspace: str = "Lab",
    use_gpu: bool = False,
) -> torch.Tensor:
    """Compute L2 distances with the stock LPIPS convention.

    The stock `lpips.L2` helper only supports batch size 1, so this wrapper
    iterates safely over larger batches when needed.
    """

    metric = lpips.L2(use_gpu=use_gpu and torch.cuda.is_available(), colorspace=colorspace)
    results = []
    for item0, item1 in _iterate_pairs(img0, img1):
        with torch.no_grad():
            value = metric(item0, item1).view(-1)
        results.append(value)
    return torch.cat(results, dim=0)


def ssim_distance_batch(
    img0: torch.Tensor,
    img1: torch.Tensor,
    *,
    colorspace: str = "RGB",
    use_gpu: bool = False,
) -> torch.Tensor:
    """Compute a DSSIM-style distance using a modern SSIM implementation."""

    try:
        from skimage.metrics import structural_similarity as structural_similarity
    except Exception:  # pragma: no cover - compatibility fallback
        from skimage.measure import compare_ssim as structural_similarity

    def one_pair(pair0: torch.Tensor, pair1: torch.Tensor) -> torch.Tensor:
        if colorspace.upper() == "LAB":
            arr0 = lpips.tensor2np(lpips.tensor2tensorlab(pair0.data, to_norm=False))
            arr1 = lpips.tensor2np(lpips.tensor2tensorlab(pair1.data, to_norm=False))
            data_range = 100.0
        else:
            arr0 = lpips.tensor2im(pair0.data).astype("float")
            arr1 = lpips.tensor2im(pair1.data).astype("float")
            data_range = 255.0

        try:
            score = structural_similarity(arr0, arr1, data_range=data_range, channel_axis=-1)
        except TypeError:  # older API
            score = structural_similarity(arr0, arr1, data_range=data_range, multichannel=True)
        return torch.tensor([(1.0 - score) / 2.0], dtype=torch.float32)

    results = [one_pair(item0, item1) for item0, item1 in _iterate_pairs(img0, img1)]
    return torch.cat(results, dim=0)


def write_scalar_lines(path: str | Path, lines: Iterable[str]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(lines), encoding="utf-8")
