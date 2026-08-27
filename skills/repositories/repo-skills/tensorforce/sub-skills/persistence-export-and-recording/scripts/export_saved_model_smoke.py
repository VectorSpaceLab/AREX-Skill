#!/usr/bin/env python3
"""Export a tiny Tensorforce PPO agent as TensorFlow SavedModel in a temp directory."""

import argparse
import os
import sys
from tempfile import TemporaryDirectory

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Verify Tensorforce SavedModel export on a tiny agent.")
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
            out = os.path.join(directory, "saved-model")
            agent.save(directory=out, format="saved-model")
            files = sorted(os.listdir(out))
            expected = {"saved_model.pb", "variables", "assets", "agent.json"}
            missing = sorted(expected.difference(files))
            if missing:
                raise RuntimeError("SavedModel export missing expected entries: {}; got {}".format(missing, files))
            print({"saved_model_entries": files})
        return 0
    except Exception as exc:
        print("SavedModel smoke failed: {}: {}".format(type(exc).__name__, exc), file=sys.stderr)
        return 1
    finally:
        agent.close()
        env.close()


if __name__ == "__main__":
    raise SystemExit(main())
