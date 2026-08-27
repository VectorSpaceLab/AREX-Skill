#!/usr/bin/env python3
"""Check an installed Tensorforce runtime without reading a source checkout."""

import argparse
import inspect
import os
import sys

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Verify Tensorforce import and optional tiny API smokes.")
    parser.add_argument("--smoke-agent", action="store_true", help="Also create a tiny environment and agent and run one action.")
    parser.add_argument("--agent", default="random", choices=("random", "ppo"), help="Agent alias for --smoke-agent (default: random).")
    parser.add_argument("--max-timesteps", type=int, default=5, help="Tiny environment max timesteps (default: 5).")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    try:
        import tensorforce
        from tensorforce import Agent, Environment, Runner
    except Exception as exc:
        print("Tensorforce import failed: {}: {}".format(type(exc).__name__, exc), file=sys.stderr)
        return 2

    print("tensorforce_version={}".format(getattr(tensorforce, "__version__", "unknown")))
    print("Agent.create={}".format(inspect.signature(Agent.create)))
    print("Environment.create={}".format(inspect.signature(Environment.create)))
    print("Runner.__init__={}".format(inspect.signature(Runner.__init__)))

    if not args.smoke_agent:
        return 0

    env = None
    agent = None
    try:
        env = Environment.create(environment="custom_cartpole", max_episode_timesteps=args.max_timesteps)
        print("states={}".format(env.states()))
        print("actions={}".format(env.actions()))
        if args.agent == "random":
            agent = Agent.create(agent="random", environment=env, config=dict(device="CPU", tf_log_level=40))
        else:
            agent = Agent.create(
                agent="ppo", environment=env, batch_size=2, update_frequency=1,
                network="auto", learning_rate=1e-3,
                config=dict(device="CPU", tf_log_level=40),
            )
        states = env.reset()
        action = agent.act(states=states)
        _next_states, terminal, reward = env.execute(actions=action)
        if args.agent != "random":
            updates = agent.observe(terminal=terminal, reward=reward)
        else:
            updates = 0
        print("smoke_action={} terminal={} reward={} updates={}".format(action, terminal, float(reward), updates))
        return 0
    except Exception as exc:
        print("Tensorforce smoke failed: {}: {}".format(type(exc).__name__, exc), file=sys.stderr)
        return 1
    finally:
        if agent is not None:
            agent.close()
        if env is not None:
            env.close()


if __name__ == "__main__":
    raise SystemExit(main())
