#!/usr/bin/env python3
"""Deterministic EasyR1 core API smoke test.

The script validates CPU-safe support APIs only. Passing it means DataProto,
dynamic batching, and small algorithm helpers are importable and internally
consistent; it does not prove full EasyR1 training readiness.
"""

from __future__ import annotations

import argparse
import sys
from typing import Sequence


def _build_proto():
    import numpy as np
    import torch

    from verl.protocol import DataProto

    tensors = {
        "input_ids": torch.tensor(
            [
                [11, 12, 0, 0],
                [21, 22, 23, 0],
                [31, 0, 0, 0],
                [41, 42, 43, 44],
            ],
            dtype=torch.long,
        ),
        "attention_mask": torch.tensor(
            [
                [1, 1, 0, 0],
                [1, 1, 1, 0],
                [1, 0, 0, 0],
                [1, 1, 1, 1],
            ],
            dtype=torch.long,
        ),
    }
    non_tensors = {"sample_id": np.array(["p0", "p1", "p2", "p3"], dtype=object)}
    return DataProto.from_dict(tensors=tensors, non_tensors=non_tensors, meta_info={"purpose": "smoke"})


def _assert_proto_equal(left, right, context: str) -> None:
    import numpy as np
    import torch

    assert len(left) == len(right), f"{context}: length mismatch {len(left)} != {len(right)}"
    if left.batch is None or right.batch is None:
        assert left.batch is right.batch, f"{context}: one proto has tensor batch and the other does not"
    else:
        assert set(left.batch.keys()) == set(right.batch.keys()), f"{context}: tensor keys differ"
        for key in left.batch.keys():
            torch.testing.assert_close(left.batch[key], right.batch[key], msg=f"{context}: tensor key {key}")
    assert set(left.non_tensor_batch.keys()) == set(right.non_tensor_batch.keys()), f"{context}: non-tensor keys differ"
    for key in left.non_tensor_batch.keys():
        assert np.array_equal(left.non_tensor_batch[key], right.non_tensor_batch[key]), (
            f"{context}: non-tensor key {key} differs"
        )
    assert left.meta_info == right.meta_info, f"{context}: meta_info differs"


def run_smoke(verbose: bool = False) -> None:
    import numpy as np
    import torch

    from verl.protocol import DataProto, batch_collate, pad_dataproto_to_divisor, unpad_dataproto
    from verl.trainer.core_algos import (
        compute_grpo_outcome_advantage,
        compute_kl,
        compute_policy_loss,
        compute_rewards,
    )
    from verl.utils.seqlen_balancing import prepare_dynamic_batch, restore_dynamic_batch

    torch.manual_seed(0)
    proto = _build_proto()
    assert len(proto) == 4, "DataProto length should be 4"

    item = proto[0]
    assert item.non_tensor_batch["sample_id"] == "p0", "integer indexing should return first item metadata"

    chunks = proto.chunk(2)
    assert [len(chunk) for chunk in chunks] == [2, 2], "chunk(2) should produce two equally sized chunks"
    _assert_proto_equal(DataProto.concat(chunks), proto, "concat(chunk(proto))")

    splits = proto.split(2)
    assert [len(split) for split in splits] == [2, 2], "split(2) should produce two parts of size 2"

    padded, pad_size = pad_dataproto_to_divisor(proto, size_divisor=3)
    assert pad_size == 2, f"expected pad_size=2, got {pad_size}"
    assert len(padded) == 6, f"expected padded length 6, got {len(padded)}"
    _assert_proto_equal(unpad_dataproto(padded, pad_size), proto, "unpad(pad(proto))")

    repeated = proto.select(batch_keys=["input_ids"], non_tensor_batch_keys=["sample_id"], deepcopy=True).repeat(
        repeat_times=2, interleave=True
    )
    assert len(repeated) == 8, "repeat should double batch length"
    assert repeated.non_tensor_batch["sample_id"].tolist()[:4] == ["p0", "p0", "p1", "p1"], (
        "interleaved repeat order changed"
    )

    left = proto.select(batch_keys=["input_ids"], non_tensor_batch_keys=["sample_id"], meta_info_keys=["purpose"])
    right = proto.select(batch_keys=["attention_mask"], non_tensor_batch_keys=[], meta_info_keys=[])
    left.union(right)
    assert set(left.batch.keys()) == {"input_ids", "attention_mask"}, "union did not merge disjoint tensor keys"

    collated = batch_collate([{"a": 1, "b": "x"}, {"a": 2, "b": "y"}])
    assert collated == {"a": [1, 2], "b": ["x", "y"]}, "batch_collate result changed"

    micro_batches, batch_idx_list = prepare_dynamic_batch(proto, max_token_len=5)
    assert len(micro_batches) >= 1, "dynamic batching returned no micro-batches"
    dynamic_input_ids = torch.cat([micro.batch["input_ids"] for micro in micro_batches], dim=0)
    restored_input_ids = restore_dynamic_batch(dynamic_input_ids, batch_idx_list)
    torch.testing.assert_close(restored_input_ids, proto.batch["input_ids"], msg="dynamic batch restore mismatch")

    old_log_probs = torch.log(torch.tensor([[0.50, 0.40], [0.60, 0.30]], dtype=torch.float32))
    log_probs = torch.log(torch.tensor([[0.55, 0.35], [0.50, 0.40]], dtype=torch.float32))
    ref_log_probs = torch.log(torch.tensor([[0.45, 0.45], [0.55, 0.35]], dtype=torch.float32))
    response_mask = torch.tensor([[1.0, 1.0], [1.0, 0.0]], dtype=torch.float32)
    advantages = torch.tensor([[0.2, -0.1], [0.3, 0.0]], dtype=torch.float32)
    token_level_scores = torch.tensor([[1.0, 0.0], [0.5, 0.0]], dtype=torch.float32)

    kl = compute_kl(log_probs, ref_log_probs, kl_penalty="kl")
    torch.testing.assert_close(kl, log_probs - ref_log_probs, msg="KL helper mismatch")
    rewards = compute_rewards(token_level_scores, log_probs, ref_log_probs, kl_ratio=0.1)
    assert torch.isfinite(rewards).all(), "reward helper produced non-finite values"

    policy_loss, metrics = compute_policy_loss(
        old_log_probs=old_log_probs,
        log_probs=log_probs,
        advantages=advantages,
        response_mask=response_mask,
        clip_ratio_low=0.2,
        clip_ratio_high=0.2,
        clip_ratio_dual=3.0,
        tau_positive=1.0,
        tau_negative=1.0,
        loss_type="default",
        loss_avg_mode="token",
    )
    assert policy_loss.ndim == 0 and torch.isfinite(policy_loss), "policy loss should be a finite scalar"
    assert {"ppo_kl", "entropy_loss", "pg_clipfrac_higher", "pg_clipfrac_lower"}.issubset(metrics), (
        f"policy metrics missing expected keys: {sorted(metrics)}"
    )

    grouped_rewards = torch.tensor([[1.0, 0.0], [2.0, 0.0], [0.0, 1.0], [0.0, 2.0]], dtype=torch.float32)
    grouped_mask = torch.ones_like(grouped_rewards)
    # Core GRPO functions group rows with Python dictionary keys. A NumPy array
    # keeps index[i] as reusable scalar keys for direct API calls.
    grouped_index = np.array([0, 0, 1, 1], dtype=np.int64)
    grpo_adv, grpo_returns = compute_grpo_outcome_advantage(
        token_level_rewards=grouped_rewards,
        response_mask=grouped_mask,
        index=grouped_index,
    )
    assert grpo_adv.shape == grouped_rewards.shape, "GRPO advantage shape mismatch"
    assert grpo_returns.shape == grouped_rewards.shape, "GRPO returns shape mismatch"

    if verbose:
        print(f"DataProto rows: {len(proto)}")
        print(f"Dynamic micro-batches: {[len(micro) for micro in micro_batches]}")
        print(f"Policy loss: {float(policy_loss):.6f}")
        print(f"Policy metric keys: {sorted(metrics)}")

    print("easy-r1 core API smoke: success")


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run a deterministic CPU-safe EasyR1 core API smoke test for DataProto, "
            "dynamic batching, KL/reward helpers, and policy loss."
        )
    )
    parser.add_argument("--verbose", action="store_true", help="Print intermediate smoke-test details.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        run_smoke(verbose=args.verbose)
    except Exception as exc:  # pragma: no cover - CLI diagnostic path
        print(f"easy-r1 core API smoke: FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
