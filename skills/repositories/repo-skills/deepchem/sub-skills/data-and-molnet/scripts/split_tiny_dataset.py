#!/usr/bin/env python3
"""Create deterministic tiny DeepChem train/valid/test splits."""

import argparse


MOLECULES = [
    "CCO",
    "c1ccccc1",
    "CC(=O)O",
    "C1CCCCC1",
    "CCN(CC)CC",
    "O=C=O",
    "C#N",
    "N[C@@H](C)C(=O)O",
    "CC",
    "CCC",
    "CCCC",
    "CCCl",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--splitter", choices=["random", "scaffold"], default="random",
                        help="Use RandomSplitter or ScaffoldSplitter.")
    parser.add_argument("--seed", type=int, default=123, help="Random seed for compatible splitters.")
    parser.add_argument("--frac-train", type=float, default=0.6, help="Training fraction.")
    parser.add_argument("--frac-valid", type=float, default=0.2, help="Validation fraction.")
    parser.add_argument("--frac-test", type=float, default=0.2, help="Test fraction.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    import deepchem as dc

    featurizer = dc.feat.CircularFingerprint(size=16)
    X = featurizer.featurize(MOLECULES)
    y = [[index % 2] for index, _ in enumerate(MOLECULES)]
    dataset = dc.data.NumpyDataset(X=X, y=y, ids=MOLECULES)

    if args.splitter == "random":
        splitter = dc.splits.RandomSplitter()
    else:
        splitter = dc.splits.ScaffoldSplitter()

    train, valid, test = splitter.train_valid_test_split(
        dataset,
        frac_train=args.frac_train,
        frac_valid=args.frac_valid,
        frac_test=args.frac_test,
        seed=args.seed,
    )

    print(f"splitter={args.splitter}")
    print(f"sizes=train:{len(train)} valid:{len(valid)} test:{len(test)}")
    if min(len(train), len(valid), len(test)) == 0:
        print("warning=one split is empty; tiny scaffold/grouped datasets can be highly uneven")
    print(f"train_ids={list(train.ids)}")
    print(f"valid_ids={list(valid.ids)}")
    print(f"test_ids={list(test.ids)}")


if __name__ == "__main__":
    main()
