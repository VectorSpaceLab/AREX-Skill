#!/usr/bin/env python3
"""Safe 3D StarDist file predictor.

This adapted helper imports the installed package only after parsing and path
checks. Consequently ``--help`` works from an arbitrary working directory and
does not depend on a source checkout.
"""
import argparse
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Set, Tuple


def build_parser():
    p = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="Predict 3D StarDist instances and write integer label TIFFs.",
    )
    p.add_argument("-i", "--input", nargs="+", required=True, metavar="PATH",
                   help="input TIFF volume(s), rank 3 ZYX or rank 4 with one C axis")
    p.add_argument("-m", "--model", required=True, metavar="SPEC",
                   help="existing model directory or registered pretrained name")
    p.add_argument("-o", "--outdir", default=".", metavar="DIR",
                   help="output directory")
    p.add_argument("--outname", default="{img}.stardist.tif", metavar="TEMPLATE",
                   help="one .tif/.tiff filename; {img} is replaced by input stem")
    p.add_argument("--axes", default=None, metavar="AXES",
                   help="input axes, e.g. ZYX, ZYXC, XYZ, or CZYX")
    p.add_argument("--n-tiles", "--n_tiles", dest="n_tiles", type=int,
                   nargs=3, metavar=("NZ", "NY", "NX"), default=None,
                   help="tile counts for the three spatial axes")
    p.add_argument("--pnorm", type=float, nargs=2, metavar=("PMIN", "PMAX"),
                   default=(1.0, 99.8), help="normalization percentiles")
    p.add_argument("--prob-thresh", "--prob_thresh", dest="prob_thresh",
                   type=float, default=None, metavar="VALUE",
                   help="object probability threshold; model default if omitted")
    p.add_argument("--nms-thresh", "--nms_thresh", dest="nms_thresh",
                   type=float, default=None, metavar="VALUE",
                   help="NMS threshold; model default if omitted")
    p.add_argument("-v", "--verbose", action="store_true")
    p.add_argument("--overwrite", action="store_true",
                   help="allow replacing an existing output after checking it")
    return p


def _path_like(spec):
    p = Path(spec).expanduser()
    return (p.is_absolute() or len(p.parts) > 1 or spec.startswith((".", "~"))
            or "\\" in spec or p.suffix.lower() in (".zip", ".h5", ".json"))


def _load_model(cls, spec):
    selected = Path(spec).expanduser()
    if selected.exists():
        if not selected.is_dir():
            raise ValueError("model selector is a file, not a directory: %s" % selected)
        model_dir = selected.resolve()
        if not (model_dir / "config.json").is_file():
            raise FileNotFoundError("local model lacks config.json: %s" % model_dir)
        if not any(model_dir.glob("*.h5")):
            raise FileNotFoundError("local model has no .h5 weights: %s" % model_dir)
        return cls(None, name=model_dir.name, basedir=str(model_dir.parent))
    if _path_like(spec):
        raise FileNotFoundError("missing path-like model selector: %s" % selected)
    try:
        # A plain name deliberately enters StarDist's registered pretrained
        # route, which can download/cache a model and therefore needs approval.
        return cls.from_pretrained(spec)
    except Exception as exc:
        raise RuntimeError("could not load pretrained 3D model %r; check its name and network/cache access" % spec) from exc


def _axes(value, ndim):
    value = value.upper()
    required = set("ZYX") if ndim == 3 else set("ZYXC")
    if len(value) != ndim or len(set(value)) != ndim or set(value) != required:
        raise ValueError("rank %d input requires exactly axes %s, got %r" %
                         (ndim, "".join(sorted(required)), value))
    return value


def _percentiles(values):
    low, high = [float(x) for x in values]
    if not 0 <= low < high <= 100:
        raise ValueError("pnorm must satisfy 0 <= pmin < pmax <= 100")
    return low, high


def _jobs(inputs: Iterable[str], outdir, template, overwrite):
    directory = Path(outdir).expanduser()
    if directory.exists() and not directory.is_dir():
        raise NotADirectoryError("output path is not a directory: %s" % directory)
    directory.mkdir(parents=True, exist_ok=True)
    directory = directory.resolve()
    if not template or Path(template).is_absolute() or any(c in template for c in "/\\"):
        raise ValueError("--outname must be one filename, not an absolute/nested path")
    result = []
    seen = set()
    for item in inputs:
        source = Path(item).expanduser()
        if not source.is_file():
            raise FileNotFoundError("input is not a regular file: %s" % source)
        if source.suffix.lower() not in (".tif", ".tiff"):
            raise ValueError("3D prediction accepts only .tif/.tiff input: %s" % source)
        source = source.resolve()
        try:
            name = template.format(img=source.stem)
        except (KeyError, ValueError) as exc:
            raise ValueError("--outname may use only {img}") from exc
        target = (directory / name).resolve()
        try:
            target.relative_to(directory)
        except ValueError:
            raise ValueError("resolved output escapes --outdir (including through a symlink)")
        if target.name != name or target.suffix.lower() not in (".tif", ".tiff"):
            raise ValueError("--outname must resolve to one .tif/.tiff filename")
        if target in seen:
            raise ValueError("multiple inputs map to the same output: %s" % target)
        seen.add(target)
        if target == source:
            raise ValueError("refusing to overwrite input: %s" % source)
        if target.exists() and not overwrite:
            raise FileExistsError("output exists; pass --overwrite after checking it: %s" % target)
        result.append((source, target))
    return result


def main(argv: Optional[Sequence[str]] = None):
    args = build_parser().parse_args(argv)
    try:
        pmin, pmax = _percentiles(args.pnorm)
        jobs = _jobs(args.input, args.outdir, args.outname, args.overwrite)
        # Delayed imports keep parser help independent of TensorFlow and source paths.
        import numpy as np
        from csbdeep.utils import normalize
        from stardist.models import StarDist3D
        from tifffile import imread, imwrite
        model = _load_model(StarDist3D, args.model)
        if args.verbose:
            print("loaded 3D model: %s" % model.name)
        for source, target in jobs:
            image = np.asarray(imread(str(source)))
            if image.ndim not in (3, 4):
                raise ValueError("3D input must have rank 3 or 4, got %s" % (image.shape,))
            axes = _axes(args.axes or {3: "ZYX", 4: "ZYXC"}[image.ndim], image.ndim)
            if args.verbose:
                print("reading %s axes=%s shape=%s" % (source, axes, image.shape))
            image = normalize(image, pmin, pmax)
            labels, _ = model.predict_instances(
                image, axes=axes,
                n_tiles=tuple(args.n_tiles) if args.n_tiles is not None else None,
                prob_thresh=args.prob_thresh, nms_thresh=args.nms_thresh,
                show_tile_progress=args.verbose, verbose=args.verbose,
            )
            labels = np.asarray(labels)
            if labels.ndim != 3 or not np.issubdtype(labels.dtype, np.integer):
                raise TypeError("prediction is not an integer 3D label array: shape=%s dtype=%s" %
                                (labels.shape, labels.dtype))
            imwrite(str(target), labels)
            if args.verbose:
                print("wrote %s shape=%s dtype=%s" % (target, labels.shape, labels.dtype))
    except (FileNotFoundError, FileExistsError, NotADirectoryError, TypeError,
            ValueError, RuntimeError, ImportError, OSError) as exc:
        raise SystemExit("predict3d: error: %s" % exc)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
