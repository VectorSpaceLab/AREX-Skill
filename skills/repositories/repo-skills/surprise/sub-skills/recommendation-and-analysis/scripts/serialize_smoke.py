"""Tiny temp-file serialization smoke test."""

from pathlib import Path
from tempfile import TemporaryDirectory

from surprise import Dataset, Reader, SVD, dump


def main():
    ratings = "\n".join(
        [
            "u1,i1,5",
            "u1,i2,4",
            "u1,i3,3",
            "u2,i1,2",
            "u2,i3,4",
            "u2,i4,5",
        ]
    )

    with TemporaryDirectory() as tmpdir:
        ratings_path = Path(tmpdir) / "ratings.csv"
        ratings_path.write_text(ratings + "\n", encoding="utf-8")

        reader = Reader(line_format="user item rating", sep=",", rating_scale=(1, 5))
        data = Dataset.load_from_file(str(ratings_path), reader=reader)
        trainset = data.build_full_trainset()

        algo = SVD(random_state=0, n_factors=1, n_epochs=1)
        algo.fit(trainset)

        testset = trainset.build_testset()
        predictions = algo.test(testset)
        assert predictions
        assert predictions[0].details["was_impossible"] is False

        dump_path = Path(tmpdir) / "surprise_dump.pkl"
        dump.dump(str(dump_path), predictions=predictions, algo=algo)
        loaded_predictions, loaded_algo = dump.load(str(dump_path))

        assert predictions == loaded_predictions
        assert loaded_algo.test(testset) == predictions

        print("dump_path:", dump_path)
        print("prediction_count:", len(predictions))
        print("sample_prediction:", predictions[0])


if __name__ == "__main__":
    main()
