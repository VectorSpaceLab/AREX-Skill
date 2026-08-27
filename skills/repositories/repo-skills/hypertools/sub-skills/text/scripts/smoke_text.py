#!/usr/bin/env python
"""Tiny smoke checks for HyperTools text workflows.

This script exercises the common sklearn text path, the text-aware plot
routing, and an optional gensim path when gensim is installed.

Examples
--------
python scripts/smoke_text.py
python scripts/smoke_text.py --require-gensim
python scripts/smoke_text.py --full-gensim
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import sys
import warnings

os.environ.setdefault("MPLBACKEND", "Agg")

import numpy as np
import matplotlib
matplotlib.use("Agg")

import hypertools as hyp
from hypertools.tools import text2mat

CORPUS = [
    "cats purr on warm windowsills and nap in the sun",
    "kittens play with yarn and toys before dinner",
    "dogs fetch balls and wag their tails at the park",
    "puppies learn sit stay and come from patient trainers",
    "stars shine in distant galaxies beyond the night sky",
    "astronomers track planets comets and nebulae with telescopes",
]


def _dense(x):
    if hasattr(x, "todense"):
        return np.asarray(x.todense())
    return np.asarray(x)


def _assert_topic_rows_sum_to_one(mat, tol=1e-6):
    row_sums = mat.sum(axis=1)
    if not np.allclose(row_sums, 1.0, atol=tol):
        raise AssertionError(f"expected row sums near 1, got {row_sums!r}")


def run_sklearn_smoke():
    print("[text] sklearn topic smoke...")

    lda = text2mat(
        [CORPUS],
        vectorizer='CountVectorizer',
        semantic='LatentDirichletAllocation',
        corpus=CORPUS,
    )[0]
    assert lda.shape == (len(CORPUS), 20), lda.shape
    _assert_topic_rows_sum_to_one(_dense(lda))

    nmf = text2mat(
        [CORPUS],
        vectorizer='TfidfVectorizer',
        semantic={
            'model': 'NMF',
            'kwargs': {
                'n_components': 3,
                'init': 'nndsvda',
                'random_state': 0,
                'max_iter': 200,
            },
        },
        corpus=CORPUS,
    )[0]
    nmf = _dense(nmf)
    assert nmf.shape == (len(CORPUS), 3), nmf.shape
    assert (nmf >= 0).all(), nmf

    fig = hyp.plot(CORPUS, '.', corpus=CORPUS, show=False, backend='matplotlib')
    assert fig is not None

    print("[text] sklearn topic smoke OK")


def _gensim_available():
    return importlib.util.find_spec('gensim') is not None


def run_gensim_smoke(full=False):
    if not _gensim_available():
        return False

    print("[text] gensim smoke...")

    word2vec = text2mat(
        [CORPUS],
        vectorizer='Word2Vec',
        semantic=None,
        corpus=CORPUS,
    )[0]
    word2vec = _dense(word2vec)
    assert word2vec.shape == (len(CORPUS), 100), word2vec.shape
    assert np.isfinite(word2vec).all()
    assert not np.allclose(word2vec, 0.0)

    lda = text2mat(
        [CORPUS],
        vectorizer='CountVectorizer',
        semantic={'model': 'LdaModel', 'kwargs': {'num_topics': 3}},
        corpus=CORPUS,
    )[0]
    lda = _dense(lda)
    assert lda.shape == (len(CORPUS), 3), lda.shape
    _assert_topic_rows_sum_to_one(lda, tol=1e-4)

    if full:
        doc2vec = text2mat(
            [CORPUS],
            vectorizer='Doc2Vec',
            semantic=None,
            corpus=CORPUS,
        )[0]
        assert _dense(doc2vec).shape == (len(CORPUS), 100)

        fasttext = text2mat(
            [CORPUS],
            vectorizer='FastText',
            semantic=None,
            corpus=CORPUS,
        )[0]
        assert _dense(fasttext).shape == (len(CORPUS), 100)

        lsi = text2mat(
            [CORPUS],
            vectorizer='CountVectorizer',
            semantic='LsiModel',
            corpus=CORPUS,
        )[0]
        assert _dense(lsi).shape[0] == len(CORPUS)

        hdp = text2mat(
            [CORPUS],
            vectorizer='CountVectorizer',
            semantic='HdpModel',
            corpus=CORPUS,
        )[0]
        assert _dense(hdp).shape[0] == len(CORPUS)

    print("[text] gensim smoke OK")
    return True


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--require-gensim',
        action='store_true',
        help='fail if gensim is unavailable',
    )
    parser.add_argument(
        '--full-gensim',
        action='store_true',
        help='also run Doc2Vec, FastText, LsiModel, and HdpModel checks',
    )
    args = parser.parse_args(argv)

    warnings.filterwarnings('ignore', category=UserWarning, module='hypertools')

    run_sklearn_smoke()

    gensim_ok = run_gensim_smoke(full=args.full_gensim)
    if not gensim_ok:
        if args.require_gensim:
            raise SystemExit('gensim is not installed; rerun with hypertools[gensim]')
        print('[text] gensim not installed; skipped optional smoke')

    print('[text] smoke_text.py OK')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
