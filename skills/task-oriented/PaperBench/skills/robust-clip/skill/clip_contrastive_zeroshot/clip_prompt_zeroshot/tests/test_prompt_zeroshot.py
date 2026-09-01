from prompt_zeroshot import classify, class_vectors


def test_prompt_classifier_ranks_matching_vector():
    classes = ["cat", "dog"]
    prompt_embeddings = {"cat":[[1,0],[0.9,0.1]], "dog":[[0,1],[0.1,0.9]]}
    out = classify([[1,0],[0,1]], classes, prompt_embeddings, 10)
    assert [x["prediction"] for x in out] == ["cat", "dog"]


def test_class_vectors_are_normalized():
    vectors = class_vectors(["cat"], {"cat":[[2,0],[3,0]]})
    assert vectors["cat"] == [1.0, 0.0]
