#!/usr/bin/env python3
"""Tiny synthetic ANN2SNN smoke cases.

This script validates the smallest useful ann2snn contracts without downloads:
rate coding, Transformer TD-equivalent conversion, STA spike-encoder conversion,
Qwen2 calibration + module-tree conversion, and an optional SpikeZIP parity
check.
"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any, Dict, List

import torch
import torch.nn as nn
import torch.nn.functional as F

from spikingjelly.activation_based import functional, neuron
from spikingjelly.activation_based.ann2snn import (
    Converter,
    ModuleConverter,
    Qwen2SNNCalibration,
    Qwen2SNNConfig,
    Qwen2SNNRecipe,
    RateCodingRecipe,
    STATransformerRecipe,
    SpikeZIPTFQANNRecipe,
    TransformerTDEquivalentRecipe,
    calibrate_qwen2_snn,
)
from spikingjelly.activation_based.ann2snn.modules import VoltageScaler
from spikingjelly.activation_based.ann2snn.operators import (
    TDGELU,
    TDLayerNorm,
    TDLinear,
    TDMultiheadAttention,
)


class TinyRateCNN(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(1, 4, kernel_size=3, padding=1),
            nn.BatchNorm2d(4),
            nn.ReLU(),
            nn.AvgPool2d(2),
            nn.Conv2d(4, 4, kernel_size=3, padding=1),
            nn.BatchNorm2d(4),
            nn.ReLU(),
            nn.AvgPool2d(2),
            nn.Flatten(),
            nn.Linear(4 * 2 * 2, 3),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class TinyTransformerBlock(nn.Module):
    def __init__(self, width: int = 8, heads: int = 2, hidden: int = 16, classes: int = 4) -> None:
        super().__init__()
        self.norm = nn.LayerNorm(width)
        self.mha = nn.MultiheadAttention(width, heads, dropout=0.0, batch_first=True)
        self.mlp = nn.Sequential(
            nn.Linear(width, hidden),
            nn.GELU(approximate="tanh"),
            nn.Linear(hidden, width),
        )
        self.head = nn.Linear(width, classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        normed = self.norm(x)
        y, _ = self.mha(normed, normed, normed, need_weights=False)
        y = y + x
        y = self.mlp(y)
        return self.head(y)


class SpikeZIPQuantizer(nn.Module):
    def __init__(self, level: int = 8, sym: bool = True, scale: float = 0.25) -> None:
        super().__init__()
        self.level = int(level)
        self.sym = bool(sym)
        self.s = nn.Parameter(torch.tensor(float(scale)))
        if self.sym:
            pos_max = self.level // 2 - 1
            neg_min = -self.level // 2
        else:
            pos_max = self.level - 1
            neg_min = 0
        self.register_buffer("pos_max", torch.tensor(float(pos_max)))
        self.register_buffer("neg_min", torch.tensor(float(neg_min)))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        q = torch.floor(x / self.s + 0.5)
        q = torch.clamp(q, min=float(self.neg_min), max=float(self.pos_max))
        return q * self.s


class TinyQRobertaSelfAttention(nn.Module):
    def __init__(self, hidden_size: int = 8, num_heads: int = 2, level: int = 8) -> None:
        super().__init__()
        if hidden_size % num_heads != 0:
            raise ValueError("hidden_size must be divisible by num_heads.")
        self.num_attention_heads = num_heads
        self.attention_head_size = hidden_size // num_heads
        self.all_head_size = hidden_size
        self.query = nn.Linear(hidden_size, hidden_size)
        self.query_quan = SpikeZIPQuantizer(level=level, sym=True)
        self.key = nn.Linear(hidden_size, hidden_size)
        self.key_quan = SpikeZIPQuantizer(level=level, sym=True)
        self.value = nn.Linear(hidden_size, hidden_size)
        self.value_quan = SpikeZIPQuantizer(level=level, sym=True)
        self.attn_quan = SpikeZIPQuantizer(level=level, sym=False, scale=0.125)
        self.after_attn_quan = SpikeZIPQuantizer(level=level, sym=True)
        self.dropout = nn.Dropout(0.0)
        self.position_embedding_type = "absolute"
        self.is_decoder = False

    def transpose_for_scores(self, x: torch.Tensor) -> torch.Tensor:
        shape = x.size()[:-1] + (self.num_attention_heads, self.attention_head_size)
        return x.view(shape).permute(0, 2, 1, 3)

    def forward(
        self,
        hidden_states: torch.Tensor,
        attention_mask: torch.Tensor | None = None,
        head_mask: torch.Tensor | None = None,
        encoder_hidden_states=None,
        encoder_attention_mask=None,
        past_key_value=None,
        output_attentions: bool = False,
    ):
        del encoder_hidden_states, encoder_attention_mask, past_key_value
        query_layer = self.transpose_for_scores(self.query_quan(self.query(hidden_states)))
        key_layer = self.transpose_for_scores(self.key_quan(self.key(hidden_states)))
        value_layer = self.transpose_for_scores(self.value_quan(self.value(hidden_states)))
        scores = torch.matmul(query_layer, key_layer.transpose(-1, -2))
        scores = scores / (self.attention_head_size**0.5)
        if attention_mask is not None:
            scores = scores + attention_mask
        attention_probs = F.softmax(scores, dim=-1)
        attention_probs = self.dropout(attention_probs)
        attention_probs = self.attn_quan(attention_probs)
        if head_mask is not None:
            attention_probs = attention_probs * head_mask
        context = torch.matmul(attention_probs, value_layer)
        context = self.after_attn_quan(context)
        context = context.permute(0, 2, 1, 3).contiguous()
        context = context.view(context.size()[:-2] + (self.all_head_size,))
        return (context, attention_probs) if output_attentions else (context,)


class TinyQRobertaClassifier(nn.Module):
    def __init__(
        self,
        vocab_size: int = 32,
        hidden_size: int = 8,
        num_heads: int = 2,
        level: int = 8,
    ) -> None:
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, hidden_size)
        self.attention = TinyQRobertaSelfAttention(hidden_size, num_heads, level)
        self.norm = nn.LayerNorm(hidden_size)
        self.classifier = nn.Linear(hidden_size, 2)

    def forward(
        self,
        tokens: torch.Tensor,
        attention_mask: torch.Tensor | None = None,
    ) -> torch.Tensor:
        hidden = self.embedding(tokens)
        hidden = self.attention(hidden, attention_mask=attention_mask)[0]
        hidden = self.norm(hidden)
        return self.classifier(hidden[:, 0])


def first_real_then_zero_sequence(x: torch.Tensor, time_steps: int) -> torch.Tensor:
    seq = torch.zeros((time_steps, *x.shape), dtype=x.dtype, device=x.device)
    seq[0] = x
    return seq


def repeat_sequence(x: torch.Tensor, time_steps: int) -> torch.Tensor:
    return x.unsqueeze(0).repeat(time_steps, *([1] * x.dim()))


def stack_single_step_calls(module: nn.Module, sequence: torch.Tensor, **kwargs: Any) -> torch.Tensor:
    functional.set_step_mode(module, "s")
    functional.reset_net(module)
    outputs = [module(step, **kwargs) for step in sequence]
    return torch.stack(outputs, dim=0)


def run_multi_step_sequence(module: nn.Module, sequence: torch.Tensor, **kwargs: Any) -> torch.Tensor:
    functional.set_step_mode(module, "m")
    functional.reset_net(module)
    return module(sequence, **kwargs)


def repeated_single_step_calls(module: nn.Module, time_steps: int, *args: Any, **kwargs: Any) -> torch.Tensor:
    functional.set_step_mode(module, "s")
    functional.reset_net(module)
    outputs = [module(*args, **kwargs) for _ in range(time_steps)]
    return torch.stack(outputs, dim=0)


def run_rate_case(device: torch.device, time_steps: int, seed: int) -> Dict[str, Any]:
    torch.manual_seed(seed)
    model = TinyRateCNN().to(device).eval()
    x = torch.randn(2, 1, 8, 8, device=device)
    dense = model(x)
    recipe = RateCodingRecipe(
        dataloader=[(x, torch.zeros(x.shape[0], dtype=torch.long, device=device))],
        mode="Max",
        fuse_flag=True,
    )
    converted = Converter(recipe=recipe, device=device).convert(copy.deepcopy(model)).eval()
    seq = repeat_sequence(x, time_steps)
    multi = run_multi_step_sequence(converted, seq)
    loop = repeated_single_step_calls(converted, time_steps, x)
    torch.testing.assert_close(loop, multi, atol=1e-6, rtol=1e-6)
    readout = multi.sum(dim=0)
    assert readout.shape == dense.shape
    assert torch.isfinite(readout).all()
    assert any(isinstance(module, neuron.IFNode) for module in converted.modules())
    assert any(isinstance(module, VoltageScaler) for module in converted.modules())
    assert not any(isinstance(module, nn.BatchNorm2d) for module in converted.modules())
    return {
        "status": "passed",
        "dense_shape": list(dense.shape),
        "sequence_shape": list(multi.shape),
        "readout_shape": list(readout.shape),
        "step_mode_equivalence": True,
        "has_ifnode": True,
        "has_voltage_scaler": True,
        "bn_fused": True,
    }


def run_transformer_td_case(device: torch.device, time_steps: int, seed: int) -> Dict[str, Any]:
    torch.manual_seed(seed + 1)
    model = TinyTransformerBlock().to(device).eval()
    x = torch.randn(2, 3, 8, device=device)
    dense = model(x)
    converted = Converter(
        recipe=TransformerTDEquivalentRecipe(time_steps=time_steps),
        device=device,
    ).convert(copy.deepcopy(model)).eval()
    seq = first_real_then_zero_sequence(x, time_steps)
    multi = run_multi_step_sequence(converted, seq)
    loop = stack_single_step_calls(converted, seq)
    torch.testing.assert_close(loop, multi, atol=1e-6, rtol=1e-6)
    readout = multi.sum(dim=0)
    torch.testing.assert_close(readout, dense, atol=1e-5, rtol=1e-5)
    assert any(isinstance(module, TDLayerNorm) for module in converted.modules())
    assert any(isinstance(module, TDMultiheadAttention) for module in converted.modules())
    assert any(isinstance(module, TDGELU) for module in converted.modules())
    assert any(isinstance(module, TDLinear) for module in converted.modules())
    return {
        "status": "passed",
        "dense_shape": list(dense.shape),
        "sequence_shape": list(multi.shape),
        "readout_shape": list(readout.shape),
        "step_mode_equivalence": True,
        "dense_equivalence": True,
    }


def run_sta_case(device: torch.device, time_steps: int, seed: int) -> Dict[str, Any]:
    torch.manual_seed(seed + 2)
    model = TinyTransformerBlock().to(device).eval()
    x = torch.randn(2, 3, 8, device=device)
    dense = model(x)
    recipe = STATransformerRecipe(
        dataloader=[x],
        time_steps=time_steps,
        mode="spiking_encoder",
        threshold_mode="mse",
        threshold_scale=0.5,
        num_calibration_batches=1,
        show_progress=False,
    )
    converted = Converter(recipe=recipe, device=device).convert(copy.deepcopy(model)).eval()
    seq = first_real_then_zero_sequence(x, time_steps)
    multi = run_multi_step_sequence(converted, seq)
    loop = stack_single_step_calls(converted, seq)
    torch.testing.assert_close(loop, multi, atol=1e-5, rtol=1e-5)
    assert multi.shape == (time_steps, *dense.shape)
    assert torch.isfinite(multi).all()
    assert any(module.__class__.__name__ == "_STASpikeEncoder" for module in converted.modules())
    assert any(isinstance(module, TDMultiheadAttention) for module in converted.modules())
    return {
        "status": "passed",
        "dense_shape": list(dense.shape),
        "sequence_shape": list(multi.shape),
        "step_mode_equivalence": True,
        "has_sta_spike_encoder": True,
        "has_td_mha": True,
        "calibrated": True,
    }


def run_qwen2_case(device: torch.device, time_steps: int, seed: int) -> Dict[str, Any]:
    try:
        import transformers
    except ImportError:
        return {"status": "skipped", "reason": "transformers is not installed"}

    torch.manual_seed(seed + 3)
    config = transformers.Qwen2Config(
        vocab_size=32,
        hidden_size=8,
        intermediate_size=16,
        num_hidden_layers=1,
        num_attention_heads=2,
        num_key_value_heads=1,
        head_dim=4,
        max_position_embeddings=32,
        tie_word_embeddings=True,
    )
    model = transformers.Qwen2ForCausalLM(config).to(device).eval()
    inputs = {
        "input_ids": torch.tensor([[0, 3, 4, 5], [0, 0, 6, 7]], device=device),
        "attention_mask": torch.tensor([[0, 1, 1, 1], [0, 0, 1, 1]], device=device),
    }
    dense = model(**inputs).logits
    qwen2_cfg = Qwen2SNNConfig(
        time_steps=time_steps,
        calibration_levels=2,
        calibration_reservoir_size=16,
        neuron_backend="torch",
    )
    calibration = calibrate_qwen2_snn(model, [inputs], qwen2_cfg)
    restored = Qwen2SNNCalibration.from_state_dict(calibration.state_dict())
    converted = ModuleConverter(Qwen2SNNRecipe(restored, qwen2_cfg), device=device).convert(
        copy.deepcopy(model)
    ).eval()
    assert converted.lm_head.weight is converted.embed_tokens.weight
    assert restored.valid_token_count > 0
    assert converted.structure_summary()["converted_decoder_count"] == 1
    assert [record["name"] for record in converted.encoder_statistics()] == [
        "model.input",
        "layer.0.query",
        "layer.0.key",
        "layer.0.value",
        "layer.0.mlp",
    ]
    functional.reset_net(converted)
    exact_td = converted(**inputs, encoding_mode="exact_td").logits
    torch.testing.assert_close(exact_td, dense, atol=1e-5, rtol=1e-5)
    functional.reset_net(converted)
    signed_if = converted(**inputs, encoding_mode="signed_if").logits
    assert signed_if.shape == dense.shape
    assert torch.isfinite(signed_if).all()
    prompt = inputs["input_ids"][:, :3]
    prompt_mask = inputs["attention_mask"][:, :3]
    functional.reset_net(converted)
    prefill = converted(
        input_ids=prompt,
        attention_mask=prompt_mask,
        encoding_mode="exact_td",
        use_cache=True,
    )
    functional.reset_net(converted)
    cached = converted(
        input_ids=inputs["input_ids"][:, 3:],
        attention_mask=inputs["attention_mask"],
        encoding_mode="exact_td",
        past_key_values=prefill.past_key_values,
        use_cache=True,
    )
    functional.reset_net(converted)
    full = converted(**inputs, encoding_mode="exact_td")
    torch.testing.assert_close(cached.logits[:, -1], full.logits[:, -1], atol=1e-5, rtol=1e-5)
    return {
        "status": "passed",
        "dense_shape": list(dense.shape),
        "exact_td_close": True,
        "signed_if_finite": True,
        "cached_decode_close": True,
        "decoder_count": 1,
        "encoder_count": len(converted.signed_encoders()),
        "valid_token_count": int(restored.valid_token_count),
        "tied_embeddings": True,
    }


def run_spikezip_case(device: torch.device, seed: int) -> Dict[str, Any]:
    torch.manual_seed(seed + 4)
    model = TinyQRobertaClassifier(level=8).to(device).eval()
    tokens = torch.randint(0, 32, (3, 5), device=device)
    attention_mask = torch.zeros(3, 1, 1, 5, device=device)
    attention_mask[:, :, :, -1] = -10000.0
    qann_logits = model(tokens, attention_mask=attention_mask)
    converted = ModuleConverter(
        recipe=SpikeZIPTFQANNRecipe(time_steps=8, model_family="roberta"),
        device=device,
    ).convert(copy.deepcopy(model)).eval()
    assert any(isinstance(module, neuron.STBIFNeuron) for module in converted.modules())
    functional.set_step_mode(converted, "s")
    functional.reset_net(converted)
    accumulated = None
    for _ in range(8):
        step_logits = converted(tokens, attention_mask=attention_mask)
        accumulated = step_logits if accumulated is None else accumulated + step_logits
    diff = (accumulated - qann_logits).abs()
    max_abs_diff = float(diff.max().cpu())
    torch.testing.assert_close(accumulated, qann_logits, atol=1e-3, rtol=1e-5)
    return {
        "status": "passed",
        "max_abs_diff": max_abs_diff,
        "time_steps": 8,
        "batch_size": int(tokens.shape[0]),
        "seq_len": int(tokens.shape[1]),
        "has_stbif_neuron": True,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run tiny synthetic smoke cases for ann2snn conversion paths."
    )
    parser.add_argument(
        "--case",
        choices=["all", "rate", "transformer_td", "sta", "qwen2", "spikezip"],
        default="all",
        help="Which smoke case to run.",
    )
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--time-steps", type=int, default=6)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument(
        "--include-spikezip",
        action="store_true",
        help="Include the optional SpikeZIP parity case when --case=all.",
    )
    parser.add_argument("--output", default=None, help="Optional JSON output path.")
    return parser.parse_args()


def write_output(path: str | None, payload: Dict[str, Any]) -> None:
    if path is None:
        return
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def main() -> int:
    args = parse_args()
    device = torch.device(args.device)
    torch.manual_seed(args.seed)
    if device.type == "cuda" and torch.cuda.is_available():
        torch.cuda.manual_seed_all(args.seed)

    case_order: List[str]
    if args.case == "all":
        case_order = ["rate", "transformer_td", "sta", "qwen2"]
        if args.include_spikezip:
            case_order.append("spikezip")
    else:
        case_order = [args.case]

    runners = {
        "rate": lambda: run_rate_case(device, args.time_steps, args.seed),
        "transformer_td": lambda: run_transformer_td_case(device, args.time_steps, args.seed),
        "sta": lambda: run_sta_case(device, args.time_steps, args.seed),
        "qwen2": lambda: run_qwen2_case(device, args.time_steps, args.seed),
        "spikezip": lambda: run_spikezip_case(device, args.seed),
    }

    results: Dict[str, Any] = {
        "device": str(device),
        "seed": args.seed,
        "time_steps": args.time_steps,
        "cases": {},
    }

    for case in case_order:
        payload = runners[case]()
        results["cases"][case] = payload
        print(json.dumps({case: payload}, sort_keys=True), flush=True)

    write_output(args.output, results)
    print(json.dumps(results, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
