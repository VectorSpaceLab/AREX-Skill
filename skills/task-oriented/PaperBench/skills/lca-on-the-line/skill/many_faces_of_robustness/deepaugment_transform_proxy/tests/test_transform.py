from transform import augment_examples

def test_labels_preserved_and_features_change():
    data=[{"id":"a","label":"cat","features":[1.0,0.2,0.1]}]
    aug, log=augment_examples(data, seed=3)
    assert aug[0]["label"] == "cat"
    assert aug[0]["features"] != data[0]["features"]
    assert log[0]["label_preserved"] is True
    assert "texture_noise" in log[0]["perturbations"]


def test_rendition_anchor_matches_labels():
    data=[{"id":"a","label":"cat","features":[1.0,0.0,0.0]},{"id":"b","label":"dog","features":[-1.0,0.0,0.0]}]
    aug, log=augment_examples(data, strength=0.9, seed=5)
    assert aug[0]["features"][1] > 0
    assert aug[1]["features"][1] < 0
    assert all("rendition_style_anchor" in item["perturbations"] for item in log)
