from paired_data import validate_paired_records

def test_validate_records_emits_diagonal_labels():
    batch = validate_paired_records([
        {"image_id":"a","caption":"a photo of a cat","class_name":"cat","image_features":[1,0],"text_features":[1,0]},
        {"image_id":"b","caption":"a photo of a dog","class_name":"dog","image_features":[0,1],"text_features":[0,1]},
    ])
    assert batch["labels"] == [0, 1]
    assert batch["feature_dim"] == 2

def test_duplicate_ids_are_rejected():
    try:
        validate_paired_records([
            {"image_id":"a","caption":"x","class_name":"x","image_features":[1],"text_features":[1]},
            {"image_id":"a","caption":"y","class_name":"y","image_features":[1],"text_features":[1]},
        ])
    except ValueError as exc:
        assert "duplicate" in str(exc)
    else:
        raise AssertionError("duplicate id was accepted")
