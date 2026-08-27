#!/usr/bin/env python3
"""Run a tiny MuZero-style bandit demo that shows policy improvement.

This is a bundled, dependency-light adaptation of the repository example.
It uses the public Mctx API only and is safe to run on CPU.
"""

from __future__ import annotations

import argparse
import functools
from typing import Tuple

import chex
import jax
import jax.numpy as jnp
import mctx


@chex.dataclass(frozen=True)
class DemoOutput:
  prior_policy_value: chex.Array
  prior_policy_action_value: chex.Array
  selected_action_value: chex.Array
  action_weights_policy_value: chex.Array


def _make_bandit_recurrent_fn(qvalues: chex.Array):
  """Return a recurrent_fn for a deterministic bandit."""

  def recurrent_fn(params, rng_key, action, embedding):
    del params, rng_key
    reward = jnp.where(
        embedding == 0,
        qvalues[jnp.arange(action.shape[0]), action],
        0.0,
    )
    discount = jnp.ones_like(reward)
    recurrent_fn_output = mctx.RecurrentFnOutput(
        reward=reward,
        discount=discount,
        prior_logits=jnp.zeros_like(qvalues),
        value=jnp.zeros_like(reward),
    )
    next_embedding = embedding + 1
    return recurrent_fn_output, next_embedding

  return recurrent_fn


def _run_demo(
    rng_key: chex.PRNGKey,
    *,
    batch_size: int,
    num_actions: int,
    num_simulations: int,
    max_num_considered_actions: int,
) -> Tuple[chex.PRNGKey, DemoOutput]:
  """Run a search algorithm on random bandit data."""
  rng_key, logits_rng, q_rng, search_rng = jax.random.split(rng_key, 4)
  prior_logits = jax.random.normal(logits_rng, shape=[batch_size, num_actions])
  qvalues = jax.random.uniform(q_rng, shape=prior_logits.shape)
  raw_value = jnp.sum(jax.nn.softmax(prior_logits) * qvalues, axis=-1)

  root = mctx.RootFnOutput(
      prior_logits=prior_logits,
      value=raw_value,
      embedding=jnp.zeros([batch_size]),
  )
  recurrent_fn = _make_bandit_recurrent_fn(qvalues)

  policy_output = mctx.gumbel_muzero_policy(
      params=(),
      rng_key=search_rng,
      root=root,
      recurrent_fn=recurrent_fn,
      num_simulations=num_simulations,
      max_num_considered_actions=max_num_considered_actions,
      qtransform=functools.partial(
          mctx.qtransform_completed_by_mix_value,
          use_mixed_value=False,
      ),
  )

  selected_action_value = qvalues[jnp.arange(batch_size), policy_output.action]

  gumbel = policy_output.search_tree.extra_data.root_gumbel
  prior_policy_action = jnp.argmax(gumbel + prior_logits, axis=-1)
  prior_policy_action_value = qvalues[jnp.arange(batch_size), prior_policy_action]

  action_weights_policy_value = jnp.sum(
      policy_output.action_weights * qvalues,
      axis=-1,
  )

  output = DemoOutput(
      prior_policy_value=raw_value,
      prior_policy_action_value=prior_policy_action_value,
      selected_action_value=selected_action_value,
      action_weights_policy_value=action_weights_policy_value,
  )
  return rng_key, output


def _parse_args() -> argparse.Namespace:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--seed", type=int, default=42)
  parser.add_argument("--batch-size", type=int, default=256)
  parser.add_argument("--num-actions", type=int, default=82)
  parser.add_argument("--num-simulations", type=int, default=4)
  parser.add_argument("--max-num-considered-actions", type=int, default=16)
  parser.add_argument("--num-runs", type=int, default=1)
  return parser.parse_args()


def main() -> None:
  args = _parse_args()
  rng_key = jax.random.PRNGKey(args.seed)
  run_demo = jax.jit(
      functools.partial(
          _run_demo,
          batch_size=args.batch_size,
          num_actions=args.num_actions,
          num_simulations=args.num_simulations,
          max_num_considered_actions=args.max_num_considered_actions,
      ))

  for _ in range(args.num_runs):
    rng_key, output = run_demo(rng_key)
    action_value_improvement = (
        output.selected_action_value - output.prior_policy_action_value)
    weights_value_improvement = (
        output.action_weights_policy_value - output.prior_policy_value)
    print(
        "action value improvement:         %.3f (min=%.3f)"
        % (action_value_improvement.mean(), action_value_improvement.min())
    )
    print(
        "action_weights value improvement: %.3f (min=%.3f)"
        % (weights_value_improvement.mean(), weights_value_improvement.min())
    )


if __name__ == "__main__":
  main()
