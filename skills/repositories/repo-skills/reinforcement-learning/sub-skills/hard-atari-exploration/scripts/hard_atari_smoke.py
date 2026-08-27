#!/usr/bin/env python3
"""Self-contained smoke checks for the hard-atari-exploration sub-skill.

The checks intentionally avoid Atari ROMs, envpool execution, raw ALE restore,
W&B, real demo artifacts, and full benchmark runs. They validate distilled
interfaces and invariants for PPO+RND, Go-Explore archive/log data structures,
demo pickle schema, robustification model/curriculum shape, and final.json
summary records.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import pickle
import statistics
import sys
import tempfile
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import numpy as np


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _torch():
    try:
        import torch
        import torch.nn as nn
    except Exception as exc:  # pragma: no cover - message path depends on env
        raise RuntimeError(
            "PyTorch is required for --section rnd and --section robustify. "
            "Install torch, or run data-only sections such as --section go-explore, "
            "--section demo, or --section final-json."
        ) from exc
    return torch, nn


# ---------------------------------------------------------------------------
# PPO + RND distilled checks
# ---------------------------------------------------------------------------


class RunningMeanStd:
    """Welford/Chan running mean/variance used for RND obs and int returns."""

    def __init__(self, shape: Sequence[int] | Tuple[int, ...] = ()):  # noqa: D401
        self.mean = np.zeros(shape, dtype=np.float64)
        self.var = np.ones(shape, dtype=np.float64)
        self.count = 1e-4

    def update(self, batch: np.ndarray) -> None:
        batch = np.asarray(batch, dtype=np.float64)
        _require(batch.shape[0] > 0, "RunningMeanStd.update needs a non-empty batch")
        bm = batch.mean(axis=0)
        bv = batch.var(axis=0)
        bc = batch.shape[0]
        delta = bm - self.mean
        total = self.count + bc
        new_mean = self.mean + delta * bc / total
        m_a = self.var * self.count
        m_b = bv * bc
        m2 = m_a + m_b + delta * delta * self.count * bc / total
        self.mean = new_mean
        self.var = m2 / total
        self.count = total


def normalize_obs_for_rnd(frame: np.ndarray, obs_rms: RunningMeanStd) -> np.ndarray:
    """Normalize newest 84x84 frame(s), clip to [-5, 5], return float32."""

    x = np.asarray(frame, dtype=np.float32)
    x = (x - obs_rms.mean) / np.sqrt(obs_rms.var + 1e-8)
    x = np.clip(x, -5.0, 5.0)
    return x.astype(np.float32)


def compute_gae(
    rewards: np.ndarray,
    values: np.ndarray,
    nonterminals: np.ndarray,
    last_value: np.ndarray,
    gamma: float,
    lam: float,
) -> Tuple[np.ndarray, np.ndarray]:
    rewards = np.asarray(rewards, dtype=np.float32)
    values = np.asarray(values, dtype=np.float32)
    nonterminals = np.asarray(nonterminals, dtype=np.float32)
    last_value = np.asarray(last_value, dtype=np.float32)
    advantages = np.zeros_like(rewards, dtype=np.float32)
    gae = np.zeros_like(last_value, dtype=np.float32)
    for t in reversed(range(len(rewards))):
        next_v = last_value if t == len(rewards) - 1 else values[t + 1]
        delta = rewards[t] + gamma * next_v * nonterminals[t] - values[t]
        gae = delta + gamma * lam * nonterminals[t] * gae
        advantages[t] = gae
    return advantages, advantages + values


def _make_rnd_models():
    torch, nn = _torch()

    def _ortho(layer, gain):
        nn.init.orthogonal_(layer.weight, gain)
        nn.init.zeros_(layer.bias)
        return layer

    class ActorCriticRND(nn.Module):
        def __init__(self, n_actions: int):
            super().__init__()
            self.conv = nn.Sequential(
                _ortho(nn.Conv2d(4, 32, kernel_size=8, stride=4), 2**0.5), nn.ReLU(),
                _ortho(nn.Conv2d(32, 64, kernel_size=4, stride=2), 2**0.5), nn.ReLU(),
                _ortho(nn.Conv2d(64, 64, kernel_size=3, stride=1), 2**0.5), nn.ReLU(),
                nn.Flatten(),
                _ortho(nn.Linear(64 * 7 * 7, 512), 2**0.5), nn.ReLU(),
            )
            self.policy = _ortho(nn.Linear(512, n_actions), 0.01)
            self.value_ext = _ortho(nn.Linear(512, 1), 1.0)
            self.value_int = _ortho(nn.Linear(512, 1), 1.0)

        def forward(self, x):
            h = self.conv(x.float() / 255.0)
            return self.policy(h), self.value_ext(h).squeeze(-1), self.value_int(h).squeeze(-1)

    def _rnd_conv():
        return nn.Sequential(
            nn.Conv2d(1, 32, kernel_size=8, stride=4), nn.LeakyReLU(),
            nn.Conv2d(32, 64, kernel_size=4, stride=2), nn.LeakyReLU(),
            nn.Conv2d(64, 64, kernel_size=3, stride=1), nn.LeakyReLU(),
            nn.Flatten(),
        )

    class RNDTarget(nn.Module):
        def __init__(self):
            super().__init__()
            self.conv = _rnd_conv()
            self.fc = nn.Linear(64 * 7 * 7, 512)

        def forward(self, x):
            return self.fc(self.conv(x))

    class RNDPredictor(nn.Module):
        def __init__(self):
            super().__init__()
            self.conv = _rnd_conv()
            self.head = nn.Sequential(
                nn.Linear(64 * 7 * 7, 512), nn.ReLU(),
                nn.Linear(512, 512), nn.ReLU(),
                nn.Linear(512, 512),
            )

        def forward(self, x):
            return self.head(self.conv(x))

    return torch, ActorCriticRND, RNDTarget, RNDPredictor


def check_rnd(verbose: bool = False) -> None:
    torch, ActorCriticRND, RNDTarget, RNDPredictor = _make_rnd_models()
    torch.manual_seed(0)
    try:
        torch.set_num_threads(1)
    except Exception:
        pass

    n_actions = 18
    model = ActorCriticRND(n_actions).eval()
    obs = torch.randint(0, 256, (2, 4, 84, 84), dtype=torch.uint8)
    with torch.no_grad():
        logits, value_ext, value_int = model(obs)
    _require(tuple(logits.shape) == (2, n_actions), f"policy logits shape mismatch: {tuple(logits.shape)}")
    _require(tuple(value_ext.shape) == (2,), f"external value shape mismatch: {tuple(value_ext.shape)}")
    _require(tuple(value_int.shape) == (2,), f"intrinsic value shape mismatch: {tuple(value_int.shape)}")
    _require(torch.isfinite(logits).all().item(), "policy logits contain non-finite values")

    obs_rms = RunningMeanStd(shape=(84, 84))
    frames = np.stack([
        np.zeros((84, 84), dtype=np.uint8),
        np.full((84, 84), 128, dtype=np.uint8),
        np.full((84, 84), 255, dtype=np.uint8),
    ])
    obs_rms.update(frames)
    normalized = normalize_obs_for_rnd(frames, obs_rms)
    _require(normalized.shape == (3, 84, 84), f"normalized RND frame shape mismatch: {normalized.shape}")
    _require(normalized.dtype == np.float32, "normalized RND frames must be float32")
    _require(float(normalized.max()) <= 5.0 and float(normalized.min()) >= -5.0, "RND normalization not clipped")
    _require(obs_rms.count > 3.0, "RND observation RMS count did not update")

    target = RNDTarget().eval()
    predictor = RNDPredictor().eval()
    for param in target.parameters():
        param.requires_grad_(False)
    x = torch.as_tensor(normalized[:2]).unsqueeze(1)
    with torch.no_grad():
        intrinsic_err = (predictor(x) - target(x)).pow(2).mean(dim=-1)
    _require(tuple(intrinsic_err.shape) == (2,), f"RND error shape mismatch: {tuple(intrinsic_err.shape)}")
    _require(torch.isfinite(intrinsic_err).all().item(), "RND error contains non-finite values")
    _require((intrinsic_err >= 0).all().item(), "RND intrinsic error must be non-negative")
    _require(not any(p.requires_grad for p in target.parameters()), "RND target should be frozen for PPO+RND training")

    rewards = np.ones((4, 2), dtype=np.float32)
    values = np.zeros((4, 2), dtype=np.float32)
    last = np.zeros(2, dtype=np.float32)
    episodic_nonterm = np.array([[1, 1], [1, 0], [1, 1], [0, 1]], dtype=np.float32)
    intrinsic_nonterm = np.ones_like(episodic_nonterm)
    adv_ext, ret_ext = compute_gae(rewards, values, episodic_nonterm, last, gamma=0.999, lam=0.95)
    adv_int, ret_int = compute_gae(rewards, values, intrinsic_nonterm, last, gamma=0.99, lam=0.95)
    _require(adv_ext.shape == rewards.shape and ret_ext.shape == rewards.shape, "extrinsic GAE shape mismatch")
    _require(adv_int.shape == rewards.shape and ret_int.shape == rewards.shape, "intrinsic GAE shape mismatch")
    _require(np.isfinite(adv_ext).all() and np.isfinite(adv_int).all(), "GAE produced non-finite values")
    _require(float(adv_int[0, 1]) > float(adv_ext[0, 1]), "intrinsic GAE should chain across done when nonterminals are all ones")

    if verbose:
        print("rnd: logits", tuple(logits.shape), "err_mean", float(intrinsic_err.mean()))
    print("OK rnd: ActorCriticRND/RNDTarget/RNDPredictor/RMS/GAE checks passed")


# ---------------------------------------------------------------------------
# Go-Explore pure-data distilled checks
# ---------------------------------------------------------------------------


CELL_W, CELL_H, CELL_LEVELS = 11, 8, 8
DONE_KEY = (b"DONE", True)


def cell_key(frame: np.ndarray) -> bytes:
    """Grayscale frame -> 88-byte quantized key.

    Uses cv2.INTER_AREA when OpenCV is present. Falls back to deterministic
    coordinate sampling for smoke environments that have no cv2; the smoke then
    checks key length/range rather than exact interpolation fidelity.
    """

    frame = np.asarray(frame, dtype=np.uint8)
    _require(frame.ndim == 2, "cell_key expects a grayscale 2-D frame")
    try:
        import cv2  # type: ignore

        small = cv2.resize(frame, (CELL_W, CELL_H), interpolation=cv2.INTER_AREA)
    except Exception:
        ys = np.linspace(0, frame.shape[0] - 1, CELL_H).round().astype(int)
        xs = np.linspace(0, frame.shape[1] - 1, CELL_W).round().astype(int)
        small = frame[np.ix_(ys, xs)]
    quantized = ((small / 255.0) * CELL_LEVELS).astype(np.uint8)
    return quantized.tobytes()


@dataclass
class Cell:
    snapshot: Optional[bytes]
    score: float
    traj_len: int
    traj_last: int
    lives: int
    seen: int = 0
    chosen: int = 0
    chosen_since_new: int = 0


class ExperienceLog:
    def __init__(self, log_dir: Optional[str], chunk_size: int = 8, ancestor_dir: Optional[str] = None):
        self.dir = log_dir
        self.ancestor = ancestor_dir
        self.chunk_size = int(chunk_size)
        if self.dir:
            os.makedirs(self.dir, exist_ok=True)
        self.count = 0
        self.n_flushed = 0
        self._ram_chunks: List[Dict[str, np.ndarray]] = []
        self._cache: Dict[int, Dict[str, np.ndarray]] = {}
        self._new_chunk()

    def _new_chunk(self) -> None:
        n = self.chunk_size
        self.prev = np.empty(n, dtype=np.int64)
        self.act = np.empty(n, dtype=np.uint8)
        self.rew = np.empty(n, dtype=np.float32)
        self.done = np.empty(n, dtype=np.uint8)
        self.fill = 0

    def append(self, prev_id: int, action: int, reward: float, done: bool) -> int:
        if self.fill == self.chunk_size:
            self._flush()
        i = self.fill
        self.prev[i] = int(prev_id)
        self.act[i] = int(action)
        self.rew[i] = float(reward)
        self.done[i] = int(bool(done))
        self.fill += 1
        idx = self.count
        self.count += 1
        return idx

    def _flush(self) -> None:
        arrays = {
            "prev": self.prev[: self.fill].copy(),
            "act": self.act[: self.fill].copy(),
            "rew": self.rew[: self.fill].copy(),
            "done": self.done[: self.fill].copy(),
        }
        if self.dir:
            tmp = os.path.join(self.dir, f"chunk_{self.n_flushed:05d}.tmp")
            np.savez_compressed(tmp, **arrays)
            os.replace(f"{tmp}.npz", os.path.join(self.dir, f"chunk_{self.n_flushed:05d}.npz"))
        else:
            self._ram_chunks.append(arrays)
        self.n_flushed += 1
        self._new_chunk()

    def _chunk_path(self, chunk_idx: int) -> str:
        _require(self.dir is not None, "chunk_path requires a log directory")
        own = os.path.join(self.dir, f"chunk_{chunk_idx:05d}.npz")
        if os.path.exists(own):
            return own
        if self.ancestor:
            anc = os.path.join(self.ancestor, f"chunk_{chunk_idx:05d}.npz")
            if os.path.exists(anc):
                return anc
        raise RuntimeError(f"experience-log chunk {chunk_idx} not found")

    def _chunk(self, chunk_idx: int) -> Dict[str, np.ndarray]:
        if chunk_idx == self.n_flushed:
            return {"prev": self.prev, "act": self.act}
        if self.dir:
            if chunk_idx not in self._cache:
                z = np.load(self._chunk_path(chunk_idx))
                self._cache[chunk_idx] = {"prev": z["prev"], "act": z["act"]}
            return self._cache[chunk_idx]
        return self._ram_chunks[chunk_idx]

    def reconstruct_actions(self, last_id: int) -> List[int]:
        actions: List[int] = []
        idx = int(last_id)
        while idx >= 0:
            chunk = self._chunk(idx // self.chunk_size)
            off = idx % self.chunk_size
            actions.append(int(chunk["act"][off]))
            idx = int(chunk["prev"][off])
        return actions[::-1]

    def state(self) -> Dict[str, Any]:
        return {
            "count": self.count,
            "n_flushed": self.n_flushed,
            "chunk_size": self.chunk_size,
            "cur_prev": self.prev[: self.fill].copy(),
            "cur_act": self.act[: self.fill].copy(),
            "cur_rew": self.rew[: self.fill].copy(),
            "cur_done": self.done[: self.fill].copy(),
        }

    def load_state(self, state: Mapping[str, Any]) -> None:
        _require(int(state["chunk_size"]) == self.chunk_size, "experience-log chunk_size mismatch")
        self.count = int(state["count"])
        self.n_flushed = int(state["n_flushed"])
        if self.dir:
            for i in range(self.n_flushed):
                self._chunk_path(i)
        self._new_chunk()
        n = len(state["cur_prev"])
        self.prev[:n] = state["cur_prev"]
        self.act[:n] = state["cur_act"]
        self.rew[:n] = state["cur_rew"]
        self.done[:n] = state["cur_done"]
        self.fill = n


class Archive:
    def __init__(self):
        self.cells: Dict[Tuple[bytes, bool], Cell] = {}
        self.rooms = set()
        self.done_scores: List[float] = []

    def seed_root(self, key: bytes, snapshot: Optional[bytes], lives: int) -> None:
        self.cells[(key, False)] = Cell(snapshot, 0.0, 0, -1, int(lives))

    @property
    def best_done_score(self) -> float:
        cell = self.cells.get(DONE_KEY)
        return cell.score if cell else float("-inf")

    @property
    def max_archive_score(self) -> float:
        return max((c.score for k, c in self.cells.items() if k != DONE_KEY), default=float("-inf"))

    def sample(self, n: int, rng: np.random.Generator) -> List[Tuple[Tuple[bytes, bool], Dict[str, Any]]]:
        keys = [k for k in self.cells if k != DONE_KEY]
        _require(bool(keys), "archive has no selectable cells")
        weights = np.array([1.0 / math.sqrt(self.cells[k].seen + 1.0) for k in keys], dtype=np.float64)
        csum = np.cumsum(weights)
        picks = []
        for u in rng.random(int(n)) * csum[-1]:
            key = keys[min(int(np.searchsorted(csum, u)), len(keys) - 1)]
            cell = self.cells[key]
            cell.chosen += 1
            cell.chosen_since_new += 1
            picks.append((key, {
                "snapshot": cell.snapshot,
                "lives": cell.lives,
                "score": cell.score,
                "traj_len": cell.traj_len,
                "traj_last": cell.traj_last,
            }))
        return picks

    def update_from_trajectory(
        self,
        chosen_key: Tuple[bytes, bool],
        capture: Mapping[str, Any],
        result: Mapping[str, Any],
        explog: ExperienceLog,
    ) -> None:
        chosen = self.cells.get(chosen_key)
        cur_score = float(capture["score"])
        cur_len = int(capture["traj_len"])
        prev_id = int(capture["traj_last"])
        found_new = False
        seen_this_episode = set()
        for i in range(int(result["n_steps"])):
            done = bool(result["dones"][i])
            prev_id = explog.append(prev_id, int(result["actions"][i]), float(result["rewards"][i]), done)
            cur_score += float(result["rewards"][i])
            cur_len += 1
            key = DONE_KEY if done else (result["keys"][i], False)
            cell = self.cells.get(key)
            if cell is None:
                self.cells[key] = Cell(result["snapshots"][i], cur_score, cur_len, prev_id, int(result["lives"][i]), seen=1)
                seen_this_episode.add(key)
                found_new = True
            else:
                if key not in seen_this_episode:
                    cell.seen += 1
                    seen_this_episode.add(key)
                if cur_score > cell.score or (cur_score == cell.score and cur_len < cell.traj_len):
                    cell.snapshot = result["snapshots"][i]
                    cell.score = cur_score
                    cell.traj_len = cur_len
                    cell.traj_last = prev_id
                    cell.lives = int(result["lives"][i])
                    cell.seen = cell.chosen = cell.chosen_since_new = 0
                    found_new = True
            if done:
                self.done_scores.append(cur_score)
                break
        if found_new and chosen is not None:
            chosen.chosen_since_new = 0
        self.rooms.update(result.get("rooms", set()))

    def state(self) -> Dict[str, Any]:
        return {
            "cells": {k: vars(c).copy() for k, c in self.cells.items()},
            "rooms": sorted(self.rooms),
            "done_scores": self.done_scores[-200:],
        }

    def load_state(self, state: Mapping[str, Any]) -> None:
        self.cells = {k: Cell(**v) for k, v in state["cells"].items()}
        self.rooms = set(state["rooms"])
        self.done_scores = list(state["done_scores"])


def check_go_explore(verbose: bool = False) -> None:
    rng = np.random.default_rng(0)
    frame0 = np.zeros((210, 160), dtype=np.uint8)
    frame1 = np.full((210, 160), 255, dtype=np.uint8)
    key0, key1 = cell_key(frame0), cell_key(frame1)
    _require(len(key0) == CELL_W * CELL_H, f"cell key length should be 88, got {len(key0)}")
    _require(len(key1) == CELL_W * CELL_H, f"cell key length should be 88, got {len(key1)}")
    _require(max(key1) <= CELL_LEVELS, "quantized cell key values must be <= 8")

    archive = Archive()
    archive.seed_root(key0, b"root-state", lives=6)
    pick_key, capture = archive.sample(1, rng)[0]
    with tempfile.TemporaryDirectory(prefix="hard-atari-explog-") as tmp:
        explog = ExperienceLog(tmp, chunk_size=3)
        result = {
            "n_steps": 2,
            "actions": [1, 2],
            "rewards": [0.0, 100.0],
            "dones": [False, True],
            "keys": [key1, key1],
            "snapshots": [b"s1", b"s2"],
            "lives": [6, 5],
            "rooms": {1},
        }
        archive.update_from_trajectory(pick_key, capture, result, explog)
        _require(DONE_KEY in archive.cells, "DONE cell was not inserted")
        _require(archive.best_done_score == 100.0, f"best done score mismatch: {archive.best_done_score}")
        done_tail = archive.cells[DONE_KEY].traj_last
        _require(explog.reconstruct_actions(done_tail) == [1, 2], "experience log failed to reconstruct actions")
        log_state = explog.state()
        log2 = ExperienceLog(tmp, chunk_size=3)
        log2.load_state(log_state)
        _require(log2.reconstruct_actions(done_tail) == [1, 2], "experience log state round-trip failed")
        arch2 = Archive()
        arch2.load_state(archive.state())
        _require(arch2.best_done_score == 100.0, "archive state round-trip failed")

    if verbose:
        print("go-explore: cells", len(archive.cells), "rooms", archive.rooms)
    print("OK go-explore: cell/archive/experience-log checks passed")


# ---------------------------------------------------------------------------
# Demo pickle schema and final.json checks
# ---------------------------------------------------------------------------


REQUIRED_DEMO_KEYS = {
    "actions",
    "rewards",
    "returns",
    "checkpoints",
    "checkpoint_action_nr",
    "score",
    "env_id",
    "protocol",
}


def validate_demo_schema(demo: Mapping[str, Any]) -> Dict[str, Any]:
    missing = sorted(REQUIRED_DEMO_KEYS - set(demo))
    _require(not missing, f"demo is missing required keys: {missing}")

    actions = np.asarray(demo["actions"])
    rewards = np.asarray(demo["rewards"], dtype=np.float32)
    returns = np.asarray(demo["returns"], dtype=np.float32)
    ckpt_nr = np.asarray(demo["checkpoint_action_nr"])
    checkpoints = demo["checkpoints"]
    protocol = demo["protocol"]

    _require(actions.ndim == 1, "demo['actions'] must be 1-D")
    _require(np.issubdtype(actions.dtype, np.integer), "demo['actions'] must contain integers")
    _require(rewards.ndim == 1, "demo['rewards'] must be 1-D")
    _require(returns.ndim == 1, "demo['returns'] must be 1-D")
    _require(len(actions) > 0, "demo must contain at least one action")
    _require(len(actions) == len(rewards) == len(returns), "actions/rewards/returns lengths must match")
    _require(np.allclose(returns, np.cumsum(rewards), atol=1e-5), "returns must equal cumsum(rewards)")
    _require(math.isclose(float(demo["score"]), float(np.sum(rewards)), rel_tol=1e-6, abs_tol=1e-5), "score must equal sum(rewards)")

    _require(isinstance(checkpoints, (list, tuple)) and len(checkpoints) > 0, "checkpoints must be a non-empty list/tuple")
    _require(all(isinstance(c, (bytes, bytearray)) for c in checkpoints), "checkpoints must contain pickled ALE-state bytes")
    _require(ckpt_nr.ndim == 1, "checkpoint_action_nr must be 1-D")
    _require(len(ckpt_nr) == len(checkpoints), "checkpoint_action_nr length must match checkpoints")
    _require(np.issubdtype(ckpt_nr.dtype, np.integer), "checkpoint_action_nr must contain integers")
    _require(np.all(ckpt_nr >= 0) and np.all(ckpt_nr < len(actions)), "checkpoint indices must be within action range")
    _require(np.all(ckpt_nr[:-1] <= ckpt_nr[1:]), "checkpoint indices must be sorted")

    _require(isinstance(demo["env_id"], str) and demo["env_id"].startswith("ALE/"), "env_id should be an ALE env id string")
    _require(isinstance(protocol, Mapping), "protocol must be a mapping")
    _require(int(protocol.get("frameskip", -1)) == 4, "Phase 1 demo protocol must use frameskip 4")
    _require(float(protocol.get("sticky", -1.0)) == 0.0, "Phase 1 demo protocol must have sticky=0.0")
    _require(int(protocol.get("seed", -1)) == 0, "Phase 1 demo protocol should record seed=0")

    return {"n_actions": int(len(actions)), "score": float(demo["score"]), "n_checkpoints": int(len(checkpoints))}


def _toy_demo() -> Dict[str, Any]:
    rewards = np.array([0.0, 100.0, 0.0], dtype=np.float32)
    return {
        "actions": np.array([0, 1, 2], dtype=np.int64),
        "rewards": rewards,
        "returns": np.cumsum(rewards).astype(np.float32),
        "checkpoints": [b"pickled-ale-state-at-action-0"],
        "checkpoint_action_nr": np.array([0], dtype=np.int64),
        "score": float(np.sum(rewards)),
        "env_id": "ALE/MontezumaRevenge-v5",
        "protocol": {"frameskip": 4, "sticky": 0.0, "seed": 0},
        "source_run": "synthetic-smoke",
        "ale_py": "synthetic",
    }


def check_demo(path: Optional[str] = None, verbose: bool = False) -> None:
    if path:
        with open(path, "rb") as fh:
            demo = pickle.load(fh)
        source = path
    else:
        demo = _toy_demo()
        source = "synthetic demo"
    summary = validate_demo_schema(demo)
    if verbose:
        print("demo:", source, json.dumps(summary, sort_keys=True))
    print(f"OK demo: schema checks passed for {source} ({summary['n_actions']} actions, score {summary['score']:.1f})")


def validate_final_json_record(record: Mapping[str, Any]) -> Dict[str, Any]:
    required = {"frames_total", "frames_unit", "gate_metric", "K", "value_mean", "value_std", "episodes_counted"}
    missing = sorted(required - set(record))
    _require(not missing, f"final.json missing keys: {missing}")
    frames_total = int(record["frames_total"])
    k = int(record["K"])
    episodes = int(record["episodes_counted"])
    value_mean = float(record["value_mean"])
    value_std = float(record["value_std"])
    _require(frames_total >= 0, "frames_total must be non-negative")
    _require(record["frames_unit"] == "agent_steps", "frames_unit must be agent_steps")
    _require(isinstance(record["gate_metric"], str) and record["gate_metric"], "gate_metric must be a non-empty string")
    _require(k >= 1, "K must be positive")
    _require(episodes >= 0, "episodes_counted must be non-negative")
    _require(math.isfinite(value_mean) or episodes == 0, "value_mean must be finite when episodes are counted")
    _require(math.isfinite(value_std) and value_std >= 0.0, "value_std must be finite and non-negative")
    return {"frames_total": frames_total, "K": k, "episodes_counted": episodes}


def check_final_json(verbose: bool = False) -> None:
    returns = [10.0, 20.0, 30.0]
    record = {
        "frames_total": 12345,
        "frames_unit": "agent_steps",
        "gate_metric": "game_return_mean_lastK",
        "K": len(returns),
        "value_mean": statistics.fmean(returns),
        "value_std": statistics.pstdev(returns),
        "episodes_counted": len(returns),
    }
    summary = validate_final_json_record(record)
    if verbose:
        print("final-json:", json.dumps(record, sort_keys=True))
    print(f"OK final-json: schema checks passed ({summary['frames_total']} agent steps)")


# ---------------------------------------------------------------------------
# Robustification distilled checks
# ---------------------------------------------------------------------------


def _make_robustify_model():
    torch, nn = _torch()

    def _ortho(layer, gain):
        nn.init.orthogonal_(layer.weight, gain)
        nn.init.zeros_(layer.bias)
        return layer

    class GRUActorCritic(nn.Module):
        def __init__(self, n_actions: int, gru_dim: int = 32):
            super().__init__()
            self.conv = nn.Sequential(
                _ortho(nn.Conv2d(4, 32, 8, stride=4), 2**0.5), nn.ReLU(),
                _ortho(nn.Conv2d(32, 64, 4, stride=2), 2**0.5), nn.ReLU(),
                _ortho(nn.Conv2d(64, 64, 3, stride=1), 2**0.5), nn.ReLU(),
                nn.Flatten(),
            )
            with torch.no_grad():
                n_flat = self.conv(torch.zeros(1, 4, 105, 80)).shape[1]
            self.fc = _ortho(nn.Linear(n_flat, gru_dim), 2**0.5)
            self.ln = nn.LayerNorm(gru_dim)
            self.gru = nn.GRUCell(gru_dim, gru_dim)
            self.pi = _ortho(nn.Linear(gru_dim, n_actions), 0.01)
            self.v = _ortho(nn.Linear(gru_dim, 1), 1.0)
            self.gru_dim = gru_dim

        def features(self, obs):
            return self.ln(torch.relu(self.fc(self.conv(obs.float() / 255.0))))

        def step(self, obs, hx, inc_entropy=None):
            hx = self.gru(self.features(obs), hx)
            logits = self.pi(hx)
            if inc_entropy is not None:
                logits = torch.where(inc_entropy.unsqueeze(1), logits / 2.0, logits)
            return logits, self.v(hx).squeeze(-1), hx

        def unroll(self, obs_seq, hx0, done_seq):
            t_steps, batch = obs_seq.shape[:2]
            hx = hx0
            logits, values = [], []
            for t in range(t_steps):
                hx = hx * (1.0 - done_seq[t]).unsqueeze(1)
                hx = self.gru(self.features(obs_seq[t]), hx)
                logits.append(self.pi(hx))
                values.append(self.v(hx).squeeze(-1))
            return torch.stack(logits), torch.stack(values)

    return torch, GRUActorCritic


class ResetManager:
    def __init__(self, demo: Mapping[str, Any], n_envs: int, *, move_threshold: float = 0.1, nudge: int = 100, window: Optional[int] = None):
        self.n = len(demo["actions"])
        self.n_envs = int(n_envs)
        self.move_threshold = float(move_threshold)
        self.nudge = int(nudge)
        self.window = int(window or max(n_envs, 32))
        self.max_starting_point = self.n - 1
        self.max_max = self.n - 1
        self.success = np.zeros(self.n + 1, dtype=np.float64)

    def assign(self, envs: Sequence[Any]) -> None:
        per = max(self.window // max(self.n_envs, 1), 1)
        for i, env in enumerate(envs):
            env.starting_point = max(self.max_starting_point - i * per, 0)

    def record(self, starting_point: int, success: bool) -> None:
        self.success[min(int(starting_point), self.n)] = float(success)

    def update(self, envs: Sequence[Any]) -> int:
        tail = self.success[: self.max_starting_point + 1]
        csum = np.cumsum(tail)
        hits = np.argwhere(csum >= self.move_threshold * self.window)
        if len(hits):
            new_max = int(hits[0][0])
            self.max_starting_point = max(min(new_max, self.max_starting_point), 0)
        else:
            self.max_starting_point = min(self.max_starting_point + self.nudge, self.max_max)
        self.assign(envs)
        return self.max_starting_point


def check_robustify(verbose: bool = False) -> None:
    torch, GRUActorCritic = _make_robustify_model()
    torch.manual_seed(0)
    try:
        torch.set_num_threads(1)
    except Exception:
        pass

    n_actions = 18
    net = GRUActorCritic(n_actions=n_actions, gru_dim=32).eval()
    obs = torch.randint(0, 256, (2, 4, 105, 80), dtype=torch.uint8)
    hx0 = torch.zeros(2, net.gru_dim)
    inc = torch.tensor([True, False])
    with torch.no_grad():
        logits, value, hx1 = net.step(obs, hx0, inc_entropy=inc)
    _require(tuple(logits.shape) == (2, n_actions), f"robustification logits shape mismatch: {tuple(logits.shape)}")
    _require(tuple(value.shape) == (2,), f"robustification value shape mismatch: {tuple(value.shape)}")
    _require(tuple(hx1.shape) == (2, net.gru_dim), f"GRU hidden shape mismatch: {tuple(hx1.shape)}")
    _require(torch.isfinite(logits).all().item() and torch.isfinite(value).all().item(), "robustification model produced non-finite values")

    obs_seq = torch.randint(0, 256, (3, 2, 4, 105, 80), dtype=torch.uint8)
    done_seq = torch.zeros(3, 2)
    done_seq[1, 0] = 1.0
    with torch.no_grad():
        logits_seq, value_seq = net.unroll(obs_seq, hx0, done_seq)
    _require(tuple(logits_seq.shape) == (3, 2, n_actions), f"unroll logits shape mismatch: {tuple(logits_seq.shape)}")
    _require(tuple(value_seq.shape) == (3, 2), f"unroll value shape mismatch: {tuple(value_seq.shape)}")

    demo = _toy_demo()
    # Extend the demo to make curriculum movement visible.
    demo["actions"] = np.arange(10, dtype=np.int64)
    mgr = ResetManager(demo, n_envs=4, move_threshold=0.25, window=4)
    envs = [SimpleNamespace(starting_point=None) for _ in range(4)]
    mgr.assign(envs)
    old = mgr.max_starting_point
    mgr.record(5, True)
    new = mgr.update(envs)
    _require(new < old, f"ResetManager should move backward after success mass, got {old} -> {new}")
    progress = 1.0 - mgr.max_starting_point / max(mgr.max_max, 1)
    _require(0.0 <= progress <= 1.0, "curriculum progress should be in [0,1]")

    if verbose:
        print("robustify: logits", tuple(logits.shape), "curriculum_progress", progress)
    print("OK robustify: GRUActorCritic/ResetManager checks passed")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


SECTIONS = ("all", "rnd", "go-explore", "demo", "robustify", "final-json")


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--section",
        choices=SECTIONS,
        default="all",
        help="which smoke section to run (default: all)",
    )
    parser.add_argument(
        "--demo",
        default=None,
        help="optional demo.pkl to validate for --section demo or as part of --section all",
    )
    parser.add_argument("--verbose", action="store_true", help="print extra shape/schema details")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    order = ["rnd", "go-explore", "demo", "robustify", "final-json"] if args.section == "all" else [args.section]
    try:
        for section in order:
            if section == "rnd":
                check_rnd(args.verbose)
            elif section == "go-explore":
                check_go_explore(args.verbose)
            elif section == "demo":
                check_demo(args.demo, args.verbose)
            elif section == "robustify":
                check_robustify(args.verbose)
            elif section == "final-json":
                check_final_json(args.verbose)
            else:  # pragma: no cover
                raise AssertionError(f"unknown section: {section}")
        print("OK hard-atari-exploration smoke completed")
        return 0
    except Exception as exc:
        print(f"FAIL hard-atari-exploration smoke: {exc}", file=sys.stderr)
        if args.verbose:
            raise
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
