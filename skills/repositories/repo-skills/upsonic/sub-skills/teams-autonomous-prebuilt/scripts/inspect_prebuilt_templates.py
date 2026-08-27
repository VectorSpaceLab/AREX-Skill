#!/usr/bin/env python3
from __future__ import annotations

import importlib.resources as resources
import inspect


def main() -> int:
    from upsonic.prebuilt.applied_scientist.agent import AppliedScientist
    from upsonic.prebuilt.prebuilt_agent_base import PrebuiltAutonomousAgentBase
    from upsonic.agent.autonomous_agent.autonomous_agent import AutonomousAgent
    from upsonic.ralph.loop import RalphLoop
    from upsonic.simulation.simulation import Simulation
    from upsonic.team.team import Team

    template_root = resources.files('upsonic.prebuilt.applied_scientist.template')
    print(f'AppliedScientist.AGENT_REPO={AppliedScientist.AGENT_REPO}')
    print(f'AppliedScientist.AGENT_FOLDER={AppliedScientist.AGENT_FOLDER}')
    print(f'PrebuiltAutonomousAgentBase: {inspect.signature(PrebuiltAutonomousAgentBase.__init__)}')
    print(f'AutonomousAgent: {inspect.signature(AutonomousAgent.__init__)}')
    print(f'Team: {inspect.signature(Team.__init__)}')
    print(f'RalphLoop: {inspect.signature(RalphLoop.__init__)}')
    print(f'Simulation: {inspect.signature(Simulation.__init__)}')
    print('template_files:')
    for name in sorted(p.name for p in template_root.iterdir()):
        print(f'  - {name}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
