#!/usr/bin/env python3
"""Smoke-check the installed pyts package.

Purpose: run small, deterministic checks for the main public pyts workflows
without depending on the original repository checkout.

Prerequisites: pyts plus its runtime dependencies must already be installed in
an isolated Python environment. The script uses only tiny in-memory arrays and
cached toy datasets.

Examples:
  python pyts_smoke.py --mode core
  python pyts_smoke.py --mode datasets
  python pyts_smoke.py --mode all
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Callable

import numpy as np


def _fmt_shape(value):
    return tuple(np.asarray(value).shape)


def smoke_core() -> None:
    from pyts import __version__
    from pyts.approximation import PiecewiseAggregateApproximation
    from pyts.metrics import dtw

    paa = PiecewiseAggregateApproximation(window_size=2).transform([[0, 1, 2, 3]])
    dist = float(dtw([0, 1, 2], [2, 0, 1]))
    print(f"pyts {__version__}")
    print(f"core: paa={np.asarray(paa).tolist()} dtw={dist:.6f}")


def smoke_datasets() -> None:
    from pyts.datasets import (
        fetch_ucr_dataset,
        fetch_uea_dataset,
        load_basic_motions,
        load_coffee,
        load_gunpoint,
        load_pig_central_venous_pressure,
        make_cylinder_bell_funnel,
        ucr_dataset_list,
        uea_dataset_list,
    )

    X_train, X_test, y_train, y_test = load_gunpoint(return_X_y=True)
    X_cbf, y_cbf = make_cylinder_bell_funnel(n_samples=12, random_state=0)
    print(
        "datasets: gunpoint=%s/%s labels=%s/%s cbf=%s/%s ucr=%d uea=%d"
        % (
            _fmt_shape(X_train),
            _fmt_shape(X_test),
            _fmt_shape(y_train),
            _fmt_shape(y_test),
            _fmt_shape(X_cbf),
            _fmt_shape(y_cbf),
            len(ucr_dataset_list()),
            len(uea_dataset_list()),
        )
    )
    # Local packaged datasets should be available without network access.
    local_shapes = []
    for loader in (load_coffee, load_pig_central_venous_pressure, load_basic_motions):
        data = loader(return_X_y=True)
        local_shapes.append(tuple(_fmt_shape(part) for part in data))
    print(f"datasets-local: {local_shapes}")
    # Keep remote fetch helpers importable without forcing a network download.
    _ = fetch_ucr_dataset
    _ = fetch_uea_dataset


def smoke_symbolic() -> None:
    from pyts.approximation import (
        DiscreteFourierTransform,
        PiecewiseAggregateApproximation,
        SymbolicAggregateApproximation,
    )
    from pyts.bag_of_words import BagOfWords, WordExtractor
    from pyts.preprocessing import (
        InterpolationImputer,
        KBinsDiscretizer,
        MaxAbsScaler,
        MinMaxScaler,
        PowerTransformer,
        QuantileTransformer,
        RobustScaler,
        StandardScaler,
    )

    missing = np.array([[1.0, 2.0, np.nan, 4.0], [4.0, 4.0, 4.0, 4.0]], dtype=float)
    clean = np.array([[0.0, 1.0, 2.0, 3.0], [3.0, 2.0, 1.0, 0.0]], dtype=float)
    print(f"symbolic-scale: {StandardScaler().fit_transform(clean).round(3).tolist()}")
    print(f"symbolic-minmax: {MinMaxScaler().fit_transform(clean).round(3).tolist()}")
    print(f"symbolic-maxabs: {MaxAbsScaler().fit_transform(clean).round(3).tolist()}")
    print(f"symbolic-robust: {RobustScaler().fit_transform(clean).round(3).tolist()}")
    print(f"symbolic-power: {PowerTransformer().fit_transform(clean).round(3).tolist()}")
    print(f"symbolic-quantile: {QuantileTransformer(n_quantiles=4, random_state=0).fit_transform(clean).round(3).tolist()}")
    print(f"symbolic-imputer: {InterpolationImputer().fit_transform(missing).round(3).tolist()}")
    print(f"symbolic-kbins: {KBinsDiscretizer(n_bins=3).fit_transform(clean).tolist()}")
    paa = PiecewiseAggregateApproximation(window_size=2).fit_transform(clean)
    sax = SymbolicAggregateApproximation(n_bins=3, strategy="uniform").fit_transform(clean)
    dft = DiscreteFourierTransform(n_coefs=2).fit_transform(clean)
    words = WordExtractor(window_size=2).fit_transform([["a", "a", "b", "c"]])
    bow = BagOfWords(window_size=2, word_size=2, n_bins=3, strategy="uniform").fit_transform(clean)
    print(f"symbolic-paa: {np.asarray(paa).round(3).tolist()}")
    print(f"symbolic-sax: {np.asarray(sax).tolist()}")
    print(f"symbolic-dft: {np.asarray(dft).round(3).tolist()}")
    print(f"symbolic-words: {np.asarray(words).tolist()}")
    print(f"symbolic-bow: {np.asarray(bow).tolist()}")


def smoke_features() -> None:
    from pyts.decomposition import SingularSpectrumAnalysis
    from pyts.image import GramianAngularField, MarkovTransitionField, RecurrencePlot
    from pyts.transformation import BagOfPatterns, BOSS, ROCKET, ShapeletTransform, WEASEL

    X = np.array(
        [
            [0.0, 2.0, 3.0, 4.0, 3.0, 2.0, 1.0],
            [0.0, 1.0, 3.0, 4.0, 3.0, 4.0, 5.0],
            [2.0, 1.0, 0.0, 2.0, 1.0, 5.0, 4.0],
            [1.0, 2.0, 2.0, 1.0, 0.0, 3.0, 5.0],
        ]
    )
    y = np.array([0, 0, 1, 1])
    print(f"features-bop: {_fmt_shape(BagOfPatterns(window_size=0.5, word_size=0.5, n_bins=3, strategy='uniform', sparse=False).fit_transform(X))}")
    print(f"features-boss: {_fmt_shape(BOSS(window_size=4, word_size=2, n_bins=3, strategy='uniform', sparse=False).fit_transform(X))}")
    print(f"features-rocket: {_fmt_shape(ROCKET(n_kernels=16, kernel_sizes=(3, 5, 7), random_state=0).fit_transform(X))}")
    print(f"features-shapelet: {_fmt_shape(ShapeletTransform(n_shapelets=1, window_sizes=[3], random_state=0, n_jobs=1).fit_transform(X, y))}")
    print(f"features-weasel: {_fmt_shape(WEASEL(word_size=2, n_bins=2, strategy='uniform', window_sizes=[0.5], drop_sum=False, chi2_threshold=1, sparse=False).fit_transform(X, y))}")
    print(f"image-gaf: {_fmt_shape(GramianAngularField(image_size=4).transform([[0, 1, 2, 3]]))}")
    print(f"image-mtf: {_fmt_shape(MarkovTransitionField(image_size=4).fit_transform([[0, 1, 2, 3]]))}")
    print(f"image-rp: {_fmt_shape(RecurrencePlot(dimension=2, time_delay=1, flatten=True).transform([[0, 1, 2, 3]]))}")
    print(f"decomp-ssa: {_fmt_shape(SingularSpectrumAnalysis(window_size=2).transform([[0, 1, 2, 3]]))}")


def smoke_metrics() -> None:
    from pyts.classification import KNeighborsClassifier, SAXVSM
    from pyts.datasets import load_gunpoint
    from pyts.metrics import (
        boss,
        dtw,
        itakura_parallelogram,
        lower_bound_improved,
        lower_bound_keogh,
        lower_bound_kim,
        lower_bound_yi,
        sakoe_chiba_band,
        show_options,
    )

    x = np.array([0.0, 1.0, 2.0])
    y = np.array([2.0, 0.0, 1.0])
    result = dtw(x, y, return_cost=True, return_accumulated=True, return_path=True)
    print(f"metrics-dtw: {result[0]:.6f} cost={_fmt_shape(result[1])} acc={_fmt_shape(result[2])} path={_fmt_shape(result[3])}")
    print(f"metrics-sakoe: {_fmt_shape(sakoe_chiba_band(3))}")
    print(f"metrics-itakura: {_fmt_shape(itakura_parallelogram(3))}")
    train = np.array([[0.0, 1.0, 2.0], [2.0, 0.0, 1.0], [1.0, 1.0, 1.0]])
    test = np.array([[0.0, 1.0, 2.0]])
    region = sakoe_chiba_band(train.shape[1], test.shape[1], window_size=1)
    print(
        "metrics-bounds: kim=%s yi=%s keogh=%s improved=%s boss=%s"
        % (
            np.asarray(lower_bound_kim(train, test)).round(3).tolist(),
            np.asarray(lower_bound_yi(train, test)).round(3).tolist(),
            np.asarray(lower_bound_keogh(train, test, region)).round(3).tolist(),
            np.asarray(lower_bound_improved(train, test, region)).round(3).tolist(),
            float(boss(x, y)),
        )
    )
    show_text = show_options('classic', disp=False)
    show_line = next((line for line in show_text.splitlines() if line.strip()), "")
    print(f"metrics-show: {show_line}")
    X_train, X_test, y_train, y_test = load_gunpoint(return_X_y=True)
    knn = KNeighborsClassifier(metric='dtw', n_neighbors=1)
    knn.fit(X_train[:10], y_train[:10])
    pred = knn.predict(X_test[:2])
    saxvsm = SAXVSM(window_size=0.5, word_size=0.5, n_bins=3, strategy='uniform', numerosity_reduction=False, use_idf=False)
    saxvsm.fit(X_train[:10], y_train[:10])
    sax_pred = saxvsm.predict(X_test[:2])
    print(f"metrics-knn: pred={pred.tolist()}")
    print(f"metrics-saxvsm: pred={sax_pred.tolist()}")


def smoke_multivariate() -> None:
    from pyts.classification import BOSSVS
    from pyts.datasets import load_basic_motions
    from pyts.image import GramianAngularField
    from pyts.multivariate.classification import MultivariateClassifier
    from pyts.multivariate.image import JointRecurrencePlot
    from pyts.multivariate.transformation import MultivariateTransformer, WEASELMUSE
    from pyts.multivariate.utils import check_3d_array

    X_train, X_test, y_train, y_test = load_basic_motions(return_X_y=True)
    X_small = X_train[:8]
    y_small = y_train[:8]
    check_3d_array(X_small)
    mt = MultivariateTransformer(GramianAngularField(image_size=0.5), flatten=False)
    X_mt = mt.fit_transform(X_small)
    print(f"multivariate-transformer: {_fmt_shape(X_mt)}")
    jrp = JointRecurrencePlot(dimension=2, time_delay=1, threshold=None, percentage=10)
    print(f"multivariate-jrp: {_fmt_shape(jrp.fit_transform(X_small))}")
    wm = WEASELMUSE(window_sizes=[0.5], sparse=False)
    X_wm = wm.fit_transform(X_small, y_small)
    print(f"multivariate-weasel-muse: {_fmt_shape(X_wm)}")
    clf = MultivariateClassifier(BOSSVS(window_size=10))
    clf.fit(X_small, y_small)
    score = clf.score(X_test[:4], y_test[:4])
    print(f"multivariate-classifier: score={score:.3f}")


MODES: dict[str, Callable[[], None]] = {
    "core": smoke_core,
    "datasets": smoke_datasets,
    "symbolic": smoke_symbolic,
    "features": smoke_features,
    "metrics": smoke_metrics,
    "multivariate": smoke_multivariate,
}


@dataclass(frozen=True)
class Args:
    mode: str


def parse_args(argv: list[str] | None = None) -> Args:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        choices=sorted(MODES) + ["all"],
        default="core",
        help="Which smoke workflow to run (default: core).",
    )
    ns = parser.parse_args(argv)
    return Args(mode=ns.mode)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.mode == "all":
        for name in sorted(MODES):
            print(f"== {name} ==")
            MODES[name]()
    else:
        MODES[args.mode]()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
