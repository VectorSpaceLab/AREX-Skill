#!/usr/bin/env python3
"""Tiny custom-model smoke check for Asteroid blocks and helpers."""

from __future__ import annotations

import argparse

import torch

from asteroid.complex_nn import ComplexSingleRNN
from asteroid.dsp.overlap_add import LambdaOverlapAdd
from asteroid.masknn import norms, recurrent
from asteroid.masknn.convolutional import TDConvNet
from asteroid.utils import parse_args_as_dict, prepare_parser_from_dict


def main() -> None:
    tdconv = TDConvNet(
        in_chan=20,
        n_src=2,
        n_blocks=2,
        n_repeats=2,
        bn_chan=10,
        hid_chan=11,
        skip_chan=12,
        out_chan=None,
    )
    td_out = tdconv(torch.randn(2, 20, 24))
    print(f"TDConvNet: {tuple(td_out.shape)}")

    dprnn = recurrent.DPRNN(
        in_chan=20,
        n_src=2,
        n_repeats=2,
        bn_chan=10,
        hid_size=11,
        out_chan=None,
        chunk_size=24,
        hop_size=None,
        use_mulcat=False,
    )
    dprnn_out = dprnn(torch.randn(2, 20, 78))
    print(f"DPRNN: {tuple(dprnn_out.shape)}")

    ln = norms.get("gLN")(8)
    ln_out = ln(torch.randn(4, 8, 12))
    print(f"gLN: {tuple(ln_out.shape)}")

    complex_rnn = ComplexSingleRNN("GRU", input_size=10, hidden_size=10, n_layers=1)
    complex_in = torch.randn(2, 5, 10, dtype=torch.complex64)
    complex_out = complex_rnn(complex_in)
    print(f"ComplexSingleRNN: {tuple(complex_out.shape)}")

    ola = LambdaOverlapAdd(lambda x: x.unsqueeze(1), n_src=1, window_size=128, hop_size=64)
    ola_out = ola(torch.randn(2, 1, 400))
    print(f"LambdaOverlapAdd: {tuple(ola_out.shape)}")

    parser = argparse.ArgumentParser()
    parser.add_argument("--main_arg", default="ok")
    conf = {"group": {"flag": True, "count": 3}}
    parser = prepare_parser_from_dict(conf, parser=parser)
    parsed, plain = parse_args_as_dict(parser, return_plain_args=True, args=["--flag", "false"])
    print(f"parser: {parsed['group']['flag']} / {plain.flag}")


if __name__ == "__main__":
    main()
