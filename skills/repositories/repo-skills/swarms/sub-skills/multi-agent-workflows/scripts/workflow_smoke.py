#!/usr/bin/env python3
"""Offline smoke check for Swarms multi-agent workflow classes."""

from __future__ import annotations

from dataclasses import dataclass

from swarms import (
    AgentRearrange,
    ConcurrentWorkflow,
    SequentialWorkflow,
    SwarmRouter,
)


@dataclass
class EchoAgent:
    agent_name: str
    system_prompt: str = ""

    def run(self, task, *args, **kwargs):
        return f"{self.agent_name}: {task}"


def _namespaced_result(result):
    return str(result)[:120]


def main() -> None:
    agents = [EchoAgent("Alpha"), EchoAgent("Beta")]

    seq = SequentialWorkflow(
        agents=agents,
        max_loops=1,
        autosave=False,
        verbose=False,
    )
    print("Sequential:", _namespaced_result(seq.run("plan")))

    conc = ConcurrentWorkflow(
        agents=agents,
        max_loops=1,
        autosave=False,
        verbose=False,
    )
    print("Concurrent:", _namespaced_result(conc.run("plan")))

    rearrange = AgentRearrange(
        agents=agents,
        flow="Alpha -> Beta",
        max_loops=1,
        autosave=False,
        verbose=False,
    )
    print("AgentRearrange:", _namespaced_result(rearrange.run("plan")))

    router = SwarmRouter(
        agents=agents,
        swarm_type="SequentialWorkflow",
        autosave=False,
        verbose=False,
    )
    print("SwarmRouter:", _namespaced_result(router.run("plan")))

    print("workflow smoke ok")


if __name__ == "__main__":
    main()
