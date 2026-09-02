from pope_protocol_builder import build_pope_questions, format_question


def records():
    return [
        {"image": "i1", "objects": ["cat", "sofa", "lamp"]},
        {"image": "i2", "objects": ["dog", "ball", "tree"]},
        {"image": "i3", "objects": ["apple", "plate", "fork"]},
    ]


def test_build_balanced_questions():
    questions = build_pope_questions(records(), sample_num=2, strategy="popular", seed=1)
    assert len(questions) == 12
    assert sum(q["label"] == "yes" for q in questions) == 6
    assert sum(q["label"] == "no" for q in questions) == 6
    assert [q["question_id"] for q in questions] == list(range(1, 13))


def test_negative_objects_are_absent():
    by_image = {record["image"]: set(record["objects"]) for record in records()}
    questions = build_pope_questions(records(), sample_num=2, strategy="adversarial", seed=2)
    for question in questions:
        if question["label"] == "no":
            assert question["object"] not in by_image[question["image"]]


def test_article_template():
    assert format_question("Is there a {} in the image?", "apple") == "Is there an apple in the image?"


def test_filters_images_with_too_few_objects():
    small = [{"image": "skip", "objects": ["cat"]}] + records()
    questions = build_pope_questions(small, sample_num=2, strategy="popular", seed=3)
    assert all(question["image"] != "skip" for question in questions)
