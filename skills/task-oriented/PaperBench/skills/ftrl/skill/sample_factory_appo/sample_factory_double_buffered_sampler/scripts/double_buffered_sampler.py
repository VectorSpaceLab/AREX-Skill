#!/usr/bin/env python3
import argparse
import json
import math


def split_buffers(envs_per_worker):
    if envs_per_worker <= 0:
        raise ValueError("envs_per_worker must be positive")
    if envs_per_worker % 2 != 0:
        raise ValueError("envs_per_worker must be even for equal double buffers")
    midpoint = envs_per_worker // 2
    return list(range(midpoint)), list(range(midpoint, envs_per_worker))


def build_schedule(envs_per_worker, iterations):
    if iterations <= 0:
        raise ValueError("iterations must be positive")
    front, back = split_buffers(envs_per_worker)
    schedule = []
    for index in range(iterations):
        active = front if index % 2 == 0 else back
        pending = back if index % 2 == 0 else front
        schedule.append({"iteration": index, "simulate_envs": active, "policy_pending_envs": pending})
    return schedule


def idle_estimates(envs_per_worker, inference_time, env_step_time):
    if inference_time < 0:
        raise ValueError("inference_time must be non-negative")
    if env_step_time <= 0:
        raise ValueError("env_step_time must be positive")
    split_buffers(envs_per_worker)
    half = envs_per_worker / 2.0
    synchronous_idle = inference_time
    double_buffered_idle = max(0.0, inference_time - half * env_step_time)
    if synchronous_idle == 0:
        reduction = 0.0
    else:
        reduction = (synchronous_idle - double_buffered_idle) / synchronous_idle
    return {
        "synchronous_idle_time": synchronous_idle,
        "double_buffered_idle_time": double_buffered_idle,
        "idle_time_reduction_ratio": reduction,
        "minimum_half_buffer_size": math.ceil(inference_time / env_step_time),
        "overlap_window_time": half * env_step_time,
    }


def analyze(envs_per_worker, inference_time, env_step_time, iterations):
    front, back = split_buffers(envs_per_worker)
    estimates = idle_estimates(envs_per_worker, inference_time, env_step_time)
    return {
        "front_buffer": front,
        "back_buffer": back,
        "schedule": build_schedule(envs_per_worker, iterations),
        **estimates,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--envs-per-worker", type=int, required=True)
    parser.add_argument("--inference-time", type=float, required=True)
    parser.add_argument("--env-step-time", type=float, required=True)
    parser.add_argument("--iterations", type=int, default=4)
    args = parser.parse_args()
    print(json.dumps(analyze(args.envs_per_worker, args.inference_time, args.env_step_time, args.iterations), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
