#!/usr/bin/env python3
"""Generate a safe minimal auto-sklearn custom component skeleton.

The generated module contains no training code. It is intended as a starting
point for implementing a classifier, regressor, feature preprocessor, or data
preprocessor contract.
"""

import argparse
import re
import sys
import textwrap
from pathlib import Path

_CLASS_RE = re.compile(r"^[A-Z_][A-Za-z0-9_]*$")


def _validate_class_name(value):
    if not _CLASS_RE.match(value):
        raise argparse.ArgumentTypeError(
            "class name must be a valid Python class identifier and should start with an uppercase letter"
        )
    return value


def _common_header():
    return '''\
"""Minimal auto-sklearn custom component skeleton.

Fill in the wrapped estimator or transformer implementation before using this
component in a real AutoML run. The class includes required properties and a
ConfigSpace placeholder but intentionally performs no training.
"""

from typing import Optional

from ConfigSpace.configuration_space import ConfigurationSpace

from autosklearn.askl_typing import FEAT_TYPE_TYPE
from autosklearn.pipeline.constants import (
    DENSE,
    SIGNED_DATA,
    UNSIGNED_DATA,
    PREDICTIONS,
    INPUT,
)
'''


def _classifier(class_name):
    return _common_header() + f'''
from autosklearn.pipeline.components.base import AutoSklearnClassificationAlgorithm


class {class_name}(AutoSklearnClassificationAlgorithm):
    def __init__(self, random_state=None):
        self.random_state = random_state
        self.estimator = None

    def fit(self, X, y):
        """Create and fit the wrapped classifier, then return self."""
        raise NotImplementedError("Replace with wrapped classifier training code")

    def predict(self, X):
        if self.estimator is None:
            raise NotImplementedError("predict called before fit initialized self.estimator")
        return self.estimator.predict(X)

    def predict_proba(self, X):
        if self.estimator is None:
            raise NotImplementedError("predict_proba called before fit initialized self.estimator")
        return self.estimator.predict_proba(X)

    @staticmethod
    def get_properties(dataset_properties=None):
        return {{
            "shortname": "{class_name}",
            "name": "{class_name}",
            "handles_regression": False,
            "handles_classification": True,
            "handles_multiclass": False,  # set True only if supported
            "handles_multilabel": False,
            "handles_multioutput": False,
            "is_deterministic": True,  # set False for stochastic estimators without seed control
            "input": (DENSE, SIGNED_DATA, UNSIGNED_DATA),  # add SPARSE only if supported
            "output": (PREDICTIONS,),
        }}

    @staticmethod
    def get_hyperparameter_search_space(
        feat_type: Optional[FEAT_TYPE_TYPE] = None,
        dataset_properties=None,
    ):
        cs = ConfigurationSpace()
        # Add ConfigSpace hyperparameters here. Each hyperparameter name must be
        # stored as an attribute in __init__ so auto-sklearn can set it.
        return cs


# Registration example; run before constructing AutoSklearnClassifier:
# from autosklearn.pipeline.components.classification import add_classifier
# add_classifier({class_name})
# include={{"classifier": ["{class_name}"]}}
'''


def _regressor(class_name):
    return _common_header() + f'''
from autosklearn.pipeline.components.base import AutoSklearnRegressionAlgorithm


class {class_name}(AutoSklearnRegressionAlgorithm):
    def __init__(self, random_state=None):
        self.random_state = random_state
        self.estimator = None

    def fit(self, X, y):
        """Create and fit the wrapped regressor, then return self."""
        raise NotImplementedError("Replace with wrapped regressor training code")

    def predict(self, X):
        if self.estimator is None:
            raise NotImplementedError("predict called before fit initialized self.estimator")
        return self.estimator.predict(X)

    @staticmethod
    def get_properties(dataset_properties=None):
        return {{
            "shortname": "{class_name}",
            "name": "{class_name}",
            "handles_regression": True,
            "handles_classification": False,
            "handles_multiclass": False,
            "handles_multilabel": False,
            "handles_multioutput": False,  # set True only if supported
            "is_deterministic": True,
            "input": (DENSE, SIGNED_DATA, UNSIGNED_DATA),  # add SPARSE only if supported
            "output": (PREDICTIONS,),
        }}

    @staticmethod
    def get_hyperparameter_search_space(
        feat_type: Optional[FEAT_TYPE_TYPE] = None,
        dataset_properties=None,
    ):
        cs = ConfigurationSpace()
        # Add ConfigSpace hyperparameters here. Each hyperparameter name must be
        # stored as an attribute in __init__ so auto-sklearn can set it.
        return cs


# Registration example; run before constructing AutoSklearnRegressor:
# from autosklearn.pipeline.components.regression import add_regressor
# add_regressor({class_name})
# include={{"regressor": ["{class_name}"]}}
'''


def _preprocessor(class_name):
    return _common_header() + f'''
from autosklearn.pipeline.components.base import AutoSklearnPreprocessingAlgorithm


class {class_name}(AutoSklearnPreprocessingAlgorithm):
    def __init__(self, random_state=None):
        self.random_state = random_state
        self.preprocessor = None

    def fit(self, X, y=None):
        """Create and fit the wrapped transformer, then return self."""
        raise NotImplementedError("Replace with wrapped transformer fitting code")

    def transform(self, X):
        if self.preprocessor is None:
            raise NotImplementedError("transform called before fit initialized self.preprocessor")
        return self.preprocessor.transform(X)

    @staticmethod
    def get_properties(dataset_properties=None):
        return {{
            "shortname": "{class_name}",
            "name": "{class_name}",
            "handles_regression": True,  # narrow to False if classification-only
            "handles_classification": True,  # narrow to False if regression-only
            "handles_multiclass": True,
            "handles_multilabel": False,
            "handles_multioutput": False,
            "is_deterministic": True,
            "input": (DENSE, SIGNED_DATA, UNSIGNED_DATA),  # add SPARSE only if supported
            "output": (INPUT,),  # use DENSE/SPARSE and sign constants if representation changes
        }}

    @staticmethod
    def get_hyperparameter_search_space(
        feat_type: Optional[FEAT_TYPE_TYPE] = None,
        dataset_properties=None,
    ):
        cs = ConfigurationSpace()
        # Add ConfigSpace hyperparameters here. Each hyperparameter name must be
        # stored as an attribute in __init__ so auto-sklearn can set it.
        return cs


# Feature preprocessor registration example:
# from autosklearn.pipeline.components.feature_preprocessing import add_preprocessor
# add_preprocessor({class_name})
# include={{"feature_preprocessor": ["{class_name}"]}}

# Data preprocessor registration example:
# from autosklearn.pipeline.components.data_preprocessing import add_preprocessor
# add_preprocessor({class_name})
# include={{"data_preprocessor": ["{class_name}"]}}
'''


_GENERATORS = {
    "classifier": _classifier,
    "regressor": _regressor,
    "preprocessor": _preprocessor,
}


def build_parser():
    parser = argparse.ArgumentParser(
        description="Generate a no-training auto-sklearn custom component skeleton.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--kind",
        required=True,
        choices=sorted(_GENERATORS),
        help="component skeleton kind to generate",
    )
    parser.add_argument(
        "--class-name",
        required=True,
        type=_validate_class_name,
        help="Python class name and custom include/exclude ID",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="optional file path to write; stdout is used when omitted",
    )
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    rendered = _GENERATORS[args.kind](args.class_name)
    rendered = textwrap.dedent(rendered).lstrip() + "\n"

    if args.output is None:
        sys.stdout.write(rendered)
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
        print(f"Wrote {args.kind} skeleton for {args.class_name} to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
