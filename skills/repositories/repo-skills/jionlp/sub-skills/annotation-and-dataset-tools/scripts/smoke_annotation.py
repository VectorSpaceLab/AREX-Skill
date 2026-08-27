#!/usr/bin/env python3
"""Smoke check for JioNLP annotation and dataset helpers."""

from __future__ import annotations

import jionlp as jio


def echo(tokens, **kwargs):
    return [["O"] * len(token_list) for token_list in tokens]


def main() -> int:
    chars = "胡静静在水利局工作。"
    entities = [
        {"text": "胡静静", "offset": [0, 3], "type": "Person"},
        {"text": "水利局", "offset": [4, 7], "type": "Organization"},
    ]
    assert jio.ner.entity2tag(list(chars), entities)[0] == "B-Person"
    assert jio.ner.tag2entity(list(chars), ["B-Person", "I-Person", "E-Person", "O", "B-Organization", "I-Organization", "E-Organization", "O", "O", "O"])[0]["type"] == "Person"

    assert jio.cws.word2tag(["他", "指出", "：", "近", "几", "年", "来", "，", "足球场", "风气", "差劲", "。"])[1][0] == "B"
    assert jio.cws.tag2word("他指出：近几年来，足球场风气差劲。", ["B", "B", "I", "B", "B", "B", "B", "B", "B", "B", "I", "I", "B", "I", "B", "I", "B"])[0] == "他"
    assert jio.pos.pos2tag([["他", "r"], ["指出", "v"], ["：", "w"], ["近", "a"]])[1][0] == "B-r"
    assert jio.pos.tag2pos("他指出：近", ["B-r", "B-v", "I-v", "B-w", "B-a"])[0] == ["他", "r"]

    lexicon = jio.ner.LexiconNER({"Person": ["张大山"], "Organization": ["成都市第一人民医院"]})
    assert lexicon("张大山在成都市第一人民医院工作")[0]["type"] == "Person"
    assert jio.ner.check_person_name("张三") is True
    assert jio.ner.check_person_name("办公室") is False

    split = jio.ner.TokenSplitSentence(echo, criterion="fine", max_sen_len=10, combine_sentences=True)
    assert split([list("今天，我去公园")])[0] == ["O"] * len(list("今天，我去公园"))
    break_long = jio.ner.TokenBreakLongSentence(echo, max_sen_len=10, overlap=2)
    assert break_long([list("今天我们一起去公园玩耍")])[0] == ["O"] * len(list("今天我们一起去公园玩耍"))
    bucket = jio.ner.TokenBatchBucket(echo, max_sen_len=10, batch_size=2)
    assert bucket([list("短句"), list("再短")])[0] == ["O", "O"]

    dataset_x = ["张三在北京工作", "李四在上海工作", "王五在广州工作", "赵六在成都工作"]
    dataset_y = [
        [{"type": "Person", "text": "张三", "offset": (0, 2)}, {"type": "Location", "text": "北京", "offset": (3, 5)}],
        [{"type": "Person", "text": "李四", "offset": (0, 2)}, {"type": "Location", "text": "上海", "offset": (3, 5)}],
        [{"type": "Person", "text": "王五", "offset": (0, 2)}, {"type": "Location", "text": "广州", "offset": (3, 5)}],
        [{"type": "Person", "text": "赵六", "offset": (0, 2)}, {"type": "Location", "text": "成都", "offset": (3, 5)}],
    ]
    _, _, _, _, _, _, ner_stats = jio.ner.analyse_dataset(dataset_x, dataset_y, ratio=[0.5, 0.25, 0.25], shuffle=False)
    assert set(ner_stats) == {"train", "valid", "test", "total"}
    assert jio.ner.collect_dataset_entities(dataset_y)["Person"]["张三"] == 1

    cls_x = [["好", "吃"], ["很", "差"], ["便宜"], ["糟糕"], ["满意"], ["失望"], ["干净"], ["拥挤"]]
    cls_y = ["正", "负", "正", "负", "正", "负", "正", "负"]
    _, _, _, _, _, _, cls_stats = jio.text_classification.analyse_dataset(cls_x, cls_y, ratio=[0.5, 0.25, 0.25], shuffle=False)
    assert set(cls_stats) == {"train", "valid", "test", "total"}

    print("annotation smoke: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
