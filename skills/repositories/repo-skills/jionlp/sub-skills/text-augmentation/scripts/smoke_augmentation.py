#!/usr/bin/env python3
"""Smoke check for JioNLP text augmentation helpers."""

from __future__ import annotations

import jionlp as jio


class EchoApi:
    lang_pool = ["zh", "en"]

    def __call__(self, text, from_lang=None, to_lang=None):
        return f"{text}:{from_lang}->{to_lang}"


def main() -> int:
    back = jio.BackTranslation([])
    assert set(back.filter_results("abc", ["abc", "abcd", "a", "abcdefghijk"])) == {"abc", "abcd", "a"}

    assert jio.swap_char_position("民盟发言人：昂山素季目前情况良好", augmentation_num=2, swap_ratio=0.2, seed=1, scale=1.0)
    assert jio.random_add_delete("孙俪晒11年对比照庆领证纪念日，邓超被指沧桑。", augmentation_num=1, seed=1, add_ratio=0.01, delete_ratio=0.01)
    assert jio.homophone_substitution(
        "中国驻英记者一向恪守新闻职业道德，为增进中英两国人民之间的了解和沟通发挥了积极作用。",
        augmentation_num=1,
        homo_ratio=0.01,
        allow_mispronounce=False,
        seed=1,
    )

    replace = jio.ReplaceEntity({
        "Person": {"马成宇": 1},
        "Company": {"百度": 4, "国力教育公司": 1},
        "Organization": {"延平区人民法院": 1},
    })
    texts, entities = replace(
        "腾讯致力于解决冲突，阿里巴巴致力于玩。小马爱玩。",
        [
            {"type": "Company", "text": "腾讯", "offset": (0, 2)},
            {"type": "Company", "text": "阿里巴巴", "offset": (10, 14)},
            {"type": "Person", "text": "小马", "offset": (19, 21)},
        ],
    )
    assert len(texts) == 3
    assert len(entities) == 3

    print("augmentation smoke: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
