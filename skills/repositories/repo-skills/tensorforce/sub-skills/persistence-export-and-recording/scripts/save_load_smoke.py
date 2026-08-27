#!/usr/bin/env python3
"""Run a tiny Tensorforce Agent.save/Agent.load smoke using temporary files."""

import argparse
import os
import sys
from tempfile import TemporaryDirectory

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Verify Tensorforce save/load on a tiny PPO agent.")
    parser.add_argument("--format", choices=("numpy", "checkpoint"), default="numpy", help="Save format to test (default: numpy).")
    parser.add_argument("--max-timesteps", type=int, default=3, help="Max timesteps for tiny environment.")
    args = parser.parse_args(argv)
    try:
        from tensorforce import Agent, Environment
    except Exception as exc:
        print("Failed to import Tensorforce: {}: {}".format(type(exc).__name__, exc), file=sys.stderr)
        return 2

    env = Environment.create(environment="custom_cartpole", max_episode_timesteps=args.max_timesteps)
    agent = Agent.create(agent="ppo", environment=env, batch_size=2, update_frequency=1, network="auto", config=dict(device="CPU", tf_log_level=40))
    try:
        states = env.reset()
        action = agent.act(states=states)
        _states, terminal, reward = env.execute(actions=action)
        agent.observe(terminal=terminal, reward=reward)
        with TemporaryDirectory() as directory:
            save_format = None if args.format == "checkpoint" else args.format
            agent.save(directory=directory, format=save_format)
            files = sorted(os.listdir(directory))
            agent.close()
            agent = None
            restored = Agent.load(directory=directory, format=save_format, environment=env)
            action = restored.act(states=env.reset(), independent=True, deterministic=True)
            print({"format": args.format, "files": files, "restored_action": int(action)})
            restored.close()
        return 0
    except Exception as exc:
        print("Save/load smoke failed: {}: {}".format(type(exc).__name__, exc), file=sys.stderr)
        return 1
    finally:
        if agent is not None:
            agent.close()
        env.close()


if __name__ == "__main__":
    raise SystemExit(main())
