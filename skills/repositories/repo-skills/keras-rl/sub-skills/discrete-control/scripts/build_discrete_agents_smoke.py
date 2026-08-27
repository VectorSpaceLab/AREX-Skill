#!/usr/bin/env python
"""Build/compile smoke helper for keras-rl discrete-control agents.

The helper imports keras-rl from the active Python environment and does not
require the original source checkout. It defaults to compile/build only; pass a
small --train-steps value only when an in-process lifecycle probe is desired.
"""
from __future__ import print_function

import argparse
import os
import sys
import traceback


AGENT_ORDER = ("dqn", "double-dqn", "dueling-dqn", "sarsa", "cem")


BACKEND_GUIDANCE = """\
Backend guidance:
  keras-rl is legacy Keras 2.x code. Use a Keras-2-compatible backend stack and
  set KERAS_BACKEND before importing keras. If a TensorFlow-backed stack raises
  symbolic Tensor length or _keras_shape errors while constructing DQNAgent,
  use a compatible legacy backend or patch that compatibility issue before
  training.
"""


def build_parser():
    parser = argparse.ArgumentParser(
        description="Compile/build smoke helper for keras-rl DQN, Double DQN, Dueling DQN, SARSA, and CEM agents."
    )
    parser.add_argument(
        "--agent",
        choices=AGENT_ORDER + ("all",),
        default="all",
        help="Which agent to build. Default: all.",
    )
    parser.add_argument(
        "--backend",
        choices=("theano", "tensorflow"),
        default=None,
        help="Set KERAS_BACKEND before importing Keras in this process. Omit to use the current environment.",
    )
    parser.add_argument(
        "--backend-note",
        action="store_true",
        help="Print legacy backend guidance and the backend detected after Keras import.",
    )
    parser.add_argument("--nb-actions", type=int, default=2, help="Discrete action count. Default: 2.")
    parser.add_argument("--observation-dim", type=int, default=4, help="Vector observation width. Default: 4.")
    parser.add_argument("--window-length", type=int, default=1, help="Replay/episode memory window length. Default: 1.")
    parser.add_argument("--memory-limit", type=int, default=1000, help="Memory limit for smoke agents. Default: 1000.")
    parser.add_argument("--hidden-units", type=int, default=16, help="Hidden Dense layer width. Default: 16.")
    parser.add_argument(
        "--policy",
        choices=("boltzmann", "eps-greedy"),
        default="boltzmann",
        help="Training policy for DQN/SARSA. Default: boltzmann.",
    )
    parser.add_argument("--eps", type=float, default=0.1, help="Epsilon for --policy eps-greedy. Default: 0.1.")
    parser.add_argument(
        "--dueling-type",
        choices=("avg", "max", "naive"),
        default="avg",
        help="Dueling DQN aggregation type. Default: avg.",
    )
    parser.add_argument("--batch-size", type=int, default=4, help="Small smoke batch size. Default: 4.")
    parser.add_argument("--warmup", type=int, default=1, help="Small smoke warmup step count. Default: 1.")
    parser.add_argument(
        "--target-model-update",
        type=float,
        default=1e-2,
        help="DQN target_model_update value. Float <1 is soft update; >=1 is hard period. Default: 1e-2.",
    )
    parser.add_argument("--train-steps", type=int, default=0, help="Optional tiny fit() steps. Default: 0 (compile/build only).")
    parser.add_argument("--max-episode-steps", type=int, default=5, help="Tiny env episode length when --train-steps > 0. Default: 5.")
    parser.add_argument("--verbose", action="store_true", help="Print tracebacks for failures.")
    return parser


def import_runtime():
    try:
        import numpy as np
        import keras
        import keras.backend as K
        from keras.models import Sequential
        from keras.layers import Dense, Activation, Flatten
        from keras.optimizers import Adam
        from rl.agents.dqn import DQNAgent
        from rl.agents.sarsa import SARSAAgent
        from rl.agents.cem import CEMAgent
        from rl.memory import SequentialMemory, EpisodeParameterMemory
        from rl.policy import BoltzmannQPolicy, EpsGreedyQPolicy
    except ImportError as exc:
        raise RuntimeError(
            "Import failed: {0}\n\n"
            "Action: install keras-rl and a legacy Keras 2.x-compatible backend in the active Python environment. "
            "Avoid importing rl.callbacks unless optional logging dependencies such as wandb are installed.".format(exc)
        )
    except Exception as exc:
        raise RuntimeError(
            "Keras/keras-rl import failed before agent construction: {0}\n\n{1}".format(exc, classify_exception(exc))
        )
    return {
        "np": np,
        "keras": keras,
        "K": K,
        "Sequential": Sequential,
        "Dense": Dense,
        "Activation": Activation,
        "Flatten": Flatten,
        "Adam": Adam,
        "DQNAgent": DQNAgent,
        "SARSAAgent": SARSAAgent,
        "CEMAgent": CEMAgent,
        "SequentialMemory": SequentialMemory,
        "EpisodeParameterMemory": EpisodeParameterMemory,
        "BoltzmannQPolicy": BoltzmannQPolicy,
        "EpsGreedyQPolicy": EpsGreedyQPolicy,
    }


def make_adam(Adam, lr):
    try:
        return Adam(lr=lr)
    except TypeError:
        return Adam(learning_rate=lr)


def select_policy(runtime, args):
    if args.policy == "eps-greedy":
        return runtime["EpsGreedyQPolicy"](eps=args.eps)
    return runtime["BoltzmannQPolicy"]()


def build_q_model(runtime, args, final_activation="linear"):
    Sequential = runtime["Sequential"]
    Dense = runtime["Dense"]
    Activation = runtime["Activation"]
    Flatten = runtime["Flatten"]

    model = Sequential()
    model.add(Flatten(input_shape=(args.window_length, args.observation_dim)))
    model.add(Dense(args.hidden_units))
    model.add(Activation("relu"))
    model.add(Dense(args.hidden_units))
    model.add(Activation("relu"))
    model.add(Dense(args.hidden_units))
    model.add(Activation("relu"))
    model.add(Dense(args.nb_actions))
    model.add(Activation(final_activation))
    return model


def build_agent(agent_name, runtime, args):
    np = runtime["np"]
    optimizer = make_adam(runtime["Adam"], 1e-3)

    if agent_name in ("dqn", "double-dqn", "dueling-dqn"):
        model = build_q_model(runtime, args, final_activation="linear")
        memory = runtime["SequentialMemory"](limit=args.memory_limit, window_length=args.window_length)
        policy = select_policy(runtime, args)
        kwargs = {
            "model": model,
            "nb_actions": args.nb_actions,
            "memory": memory,
            "policy": policy,
            "batch_size": args.batch_size,
            "nb_steps_warmup": args.warmup,
            "target_model_update": args.target_model_update,
            "train_interval": 1,
        }
        if agent_name == "double-dqn":
            kwargs["enable_double_dqn"] = True
        if agent_name == "dueling-dqn":
            kwargs["enable_dueling_network"] = True
            kwargs["dueling_type"] = args.dueling_type
        agent = runtime["DQNAgent"](**kwargs)
        agent.compile(optimizer, metrics=["mae"])
        return agent, model

    if agent_name == "sarsa":
        model = build_q_model(runtime, args, final_activation="linear")
        policy = select_policy(runtime, args)
        agent = runtime["SARSAAgent"](
            model=model,
            nb_actions=args.nb_actions,
            policy=policy,
            nb_steps_warmup=args.warmup,
            train_interval=1,
        )
        agent.compile(optimizer, metrics=["mae"])
        return agent, model

    if agent_name == "cem":
        model = build_q_model(runtime, args, final_activation="softmax")
        memory = runtime["EpisodeParameterMemory"](limit=args.memory_limit, window_length=args.window_length)
        elite_frac = 0.5 if args.batch_size < 20 else 0.05
        agent = runtime["CEMAgent"](
            model=model,
            nb_actions=args.nb_actions,
            memory=memory,
            batch_size=args.batch_size,
            nb_steps_warmup=args.warmup,
            train_interval=1,
            elite_frac=elite_frac,
        )
        agent.compile()
        return agent, model

    raise ValueError("Unknown agent: {0}".format(agent_name))


def tiny_fit(agent, runtime, args):
    np = runtime["np"]

    class DiscreteSpace(object):
        def __init__(self, n):
            self.n = n

        def sample(self):
            return int(np.random.randint(self.n))

    class ObservationSpace(object):
        def __init__(self, shape):
            self.shape = shape

    class TinyDiscreteEnv(object):
        def __init__(self):
            self.action_space = DiscreteSpace(args.nb_actions)
            self.observation_space = ObservationSpace((args.observation_dim,))
            self.steps = 0

        def seed(self, seed=None):
            if seed is not None:
                np.random.seed(seed)

        def reset(self):
            self.steps = 0
            return np.zeros((args.observation_dim,), dtype="float32")

        def step(self, action):
            self.steps += 1
            obs = np.ones((args.observation_dim,), dtype="float32") * (float(self.steps) / float(args.max_episode_steps))
            reward = 1.0 if int(action) == (self.steps % args.nb_actions) else 0.0
            done = self.steps >= args.max_episode_steps
            return obs, reward, done, {}

        def render(self, mode="human"):
            return None

        def close(self):
            return None

    env = TinyDiscreteEnv()
    env.seed(123)
    agent.fit(env, nb_steps=args.train_steps, visualize=False, verbose=0, nb_max_episode_steps=args.max_episode_steps)


def model_shape(model):
    return getattr(model, "output_shape", "unknown")


def classify_exception(exc):
    msg = "{0}".format(exc)
    low = msg.lower()
    hints = []

    if "one dimension for each action" in msg or "invalid shape" in low:
        hints.append("The model's final output must be exactly nb_actions. Check Dense(nb_actions), action-space sizing, and single-output model construction.")
    if "more than one output" in msg:
        hints.append("DQNAgent accepts a single-output model only; merge or choose one output before constructing the agent.")
    if "symbolic" in low and ("len" in low or "_keras_shape" in low):
        hints.append("This looks like a legacy Keras/TensorFlow symbolic-output incompatibility. Use a Keras-2-compatible backend stack or patch the output-shape check.")
    if "_keras_shape" in low:
        hints.append("keras-rl expects legacy Keras tensors with _keras_shape. Modern Keras stacks may be incompatible without patches.")
    if "unexpected keyword" in low and ("lr" in low or "learning_rate" in low):
        hints.append("Optimizer keyword mismatch: legacy Keras often uses lr; newer Keras uses learning_rate. Confirm the stack is compatible with keras-rl.")
    if "compile" in low and "positional" in low:
        hints.append("CEMAgent.compile() takes no optimizer; DQNAgent/SARSAAgent.compile() require an optimizer.")
    if "not enough entries" in low or "not enough" in low and "memory" in low:
        hints.append("Replay memory has too few entries. Increase warmup/train steps or reduce batch size/window length for the smoke.")
    if "wandb" in low:
        hints.append("rl.callbacks imports wandb at module import time. Avoid callbacks for this smoke or install the optional logging dependency.")
    if "gym" in low and ("reset" in low or "step" in low or "values" in low):
        hints.append("keras-rl expects legacy Gym reset/step signatures. Wrap newer Gym/Gymnasium environments.")
    if not hints:
        hints.append("Run with --verbose for a traceback, verify nb_actions/model shape, and confirm the active environment is legacy Keras 2.x-compatible.")

    return "\n".join("Action: " + hint for hint in hints)


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.nb_actions < 2:
        parser.error("--nb-actions must be at least 2 for this discrete smoke.")
    if args.observation_dim < 1:
        parser.error("--observation-dim must be positive.")
    if args.window_length < 1:
        parser.error("--window-length must be positive.")
    if args.batch_size < 1:
        parser.error("--batch-size must be positive.")
    if args.warmup < 0:
        parser.error("--warmup must be non-negative.")
    if args.train_steps < 0:
        parser.error("--train-steps must be non-negative.")

    if args.backend:
        os.environ["KERAS_BACKEND"] = args.backend

    try:
        runtime = import_runtime()
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        if args.verbose:
            traceback.print_exc()
        return 2

    if args.backend_note:
        print(BACKEND_GUIDANCE.rstrip())
        try:
            print("Detected Keras backend: {0}".format(runtime["K"].backend()))
        except Exception as exc:
            print("Detected Keras backend: unavailable ({0})".format(exc))

    selected = AGENT_ORDER if args.agent == "all" else (args.agent,)
    failures = []

    for agent_name in selected:
        try:
            agent, model = build_agent(agent_name, runtime, args)
            if args.train_steps:
                tiny_fit(agent, runtime, args)
            print("OK {0}: compiled={1}, model_output_shape={2}".format(agent_name, getattr(agent, "compiled", None), model_shape(model)))
        except Exception as exc:
            failures.append((agent_name, exc))
            print("FAIL {0}: {1}".format(agent_name, exc), file=sys.stderr)
            print(classify_exception(exc), file=sys.stderr)
            if args.verbose:
                traceback.print_exc()

    if failures:
        print("\n{0} agent smoke(s) failed.".format(len(failures)), file=sys.stderr)
        return 1

    print("All requested discrete-agent smoke checks passed. No training was run." if args.train_steps == 0 else "All requested discrete-agent smoke checks passed, including tiny fit().")
    return 0


if __name__ == "__main__":
    sys.exit(main())
