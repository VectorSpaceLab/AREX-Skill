"""Reusable subprocess vector-env helper for on-policy classic-control workflows.

This is adapted from the OpenAI baselines vec-env helper and tuned for the
repo's old Gym-style APIs. Future agents can import ``SubprocVecEnv`` from here
instead of reopening the original repository.
"""

import multiprocessing as mp

import numpy as np


def _reset_env(env, seed=None):
    """Reset an env and normalize old/new Gym return shapes."""
    if seed is not None:
        try:
            result = env.reset(seed=seed)
        except TypeError:
            if hasattr(env, "seed"):
                env.seed(seed)
            result = env.reset()
    else:
        result = env.reset()

    if isinstance(result, tuple) and len(result) == 2:
        obs, _info = result
        return obs
    return result


def _step_env(env, action):
    """Step an env and normalize old/new Gym return shapes."""
    result = env.step(action)
    if len(result) == 5:
        obs, reward, terminated, truncated, info = result
        done = bool(terminated or truncated)
        return obs, reward, done, info

    obs, reward, done, info = result
    return obs, reward, done, info


def worker(remote, parent_remote, env_fn_wrapper):
    parent_remote.close()
    env = env_fn_wrapper.x()
    while True:
        cmd, data = remote.recv()
        if cmd == "step":
            ob, reward, done, info = _step_env(env, data)
            if done:
                ob = _reset_env(env)
            remote.send((ob, reward, done, info))
        elif cmd == "reset":
            seed = data if isinstance(data, int) else None
            remote.send(_reset_env(env, seed=seed))
        elif cmd == "reset_task":
            if not hasattr(env, "reset_task"):
                raise AttributeError("env does not define reset_task()")
            remote.send(env.reset_task())
        elif cmd == "close":
            remote.close()
            break
        elif cmd == "get_spaces":
            remote.send((env.observation_space, env.action_space))
        else:
            raise NotImplementedError(cmd)


class VecEnv(object):
    """Minimal vector-env interface used by the repo's A2C example."""

    def __init__(self, num_envs, observation_space, action_space):
        self.num_envs = num_envs
        self.observation_space = observation_space
        self.action_space = action_space

    def reset(self):
        raise NotImplementedError

    def step_async(self, actions):
        raise NotImplementedError

    def step_wait(self):
        raise NotImplementedError

    def close(self):
        raise NotImplementedError

    def step(self, actions):
        self.step_async(actions)
        return self.step_wait()


class CloudpickleWrapper(object):
    """Serialize env factories that ordinary pickle cannot handle."""

    def __init__(self, x):
        self.x = x

    def __getstate__(self):
        import cloudpickle

        return cloudpickle.dumps(self.x)

    def __setstate__(self, ob):
        import pickle

        self.x = pickle.loads(ob)


class SubprocVecEnv(VecEnv):
    def __init__(self, env_fns, start_method=None, spaces=None):
        """Launch one subprocess per env factory.

        ``spaces`` is accepted for source compatibility with the original helper
        but is unused.
        """
        self.waiting = False
        self.closed = False
        self._ctx = mp.get_context(start_method) if start_method else mp

        nenvs = len(env_fns)
        self.nenvs = nenvs
        self.remotes, self.work_remotes = zip(*[self._ctx.Pipe() for _ in range(nenvs)])
        self.ps = [
            self._ctx.Process(
                target=worker,
                args=(work_remote, remote, CloudpickleWrapper(env_fn)),
            )
            for (work_remote, remote, env_fn) in zip(self.work_remotes, self.remotes, env_fns)
        ]
        for p in self.ps:
            p.daemon = True
            p.start()
        for remote in self.work_remotes:
            remote.close()

        self.remotes[0].send(("get_spaces", None))
        observation_space, action_space = self.remotes[0].recv()
        VecEnv.__init__(self, len(env_fns), observation_space, action_space)

    def step_async(self, actions):
        for remote, action in zip(self.remotes, actions):
            remote.send(("step", action))
        self.waiting = True

    def step_wait(self):
        results = [remote.recv() for remote in self.remotes]
        self.waiting = False
        obs, rews, dones, infos = zip(*results)
        return np.stack(obs), np.stack(rews), np.stack(dones), infos

    def reset(self):
        for remote in self.remotes:
            remote.send(("reset", None))
        return np.stack([remote.recv() for remote in self.remotes])

    def reset_task(self):
        for remote in self.remotes:
            remote.send(("reset_task", None))
        return np.stack([remote.recv() for remote in self.remotes])

    def close(self):
        if self.closed:
            return
        if self.waiting:
            for remote in self.remotes:
                remote.recv()
        for remote in self.remotes:
            remote.send(("close", None))
        for p in self.ps:
            p.join()
        self.closed = True

    def __len__(self):
        return self.nenvs


def make_subproc_vec_env(env_fns, start_method=None):
    """Convenience wrapper for the repo's A2C-style vector env setup."""
    return SubprocVecEnv(env_fns, start_method=start_method)
