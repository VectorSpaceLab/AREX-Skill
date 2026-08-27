#!/usr/bin/env python3
"""Smoke check for JioNLP parsing and normalization helpers."""

from __future__ import annotations

from datetime import datetime

import jionlp as jio


def main() -> int:
    assert jio.parse_money("1万元")["num"] == "10000.00"
    assert jio.ner.extract_money("今天去了一趟超市，开销123元1角1分", with_parsing=False)[0]["text"] == "123元1角1分"

    time_res = jio.parse_time("2021年9月")
    assert time_res["type"] == "time_point"
    assert time_res["time"][0].startswith("2021-09")
    assert jio.ner.extract_time("他在10月22出生", with_parsing=False)[0]["text"] == "10月22"

    loc_res = jio.parse_location("湖南湘潭城塘社区", town_village=True, change2new=True)
    assert loc_res["province"] == "湖南省"
    assert loc_res["city"] == "湘潭市"
    assert jio.phone_location("电话：13288568202")["province"] == "广东"

    assert jio.parse_id_card("52010320171109002X")["province"] == "贵州省"
    assert jio.parse_motor_vehicle_licence_plate("川A·23047B")["car_type"] == "PEV"

    assert jio.pinyin("中国", formater="simple") == ["zhong1", "guo2"]
    assert jio.char_radical("河")[0]["radical"] == "水"
    idiom = jio.idiom_solitaire("道阻且长", same_pinyin=False, same_tone=True)
    assert isinstance(idiom, str) and idiom.startswith("长")
    assert jio.lunar2solar(1989, 9, 23, False).strftime("%Y-%m-%d") == "1989-10-22"
    assert jio.solar2lunar(datetime(1989, 10, 22)) == (1989, 9, 23, False)

    print("parsers smoke: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
