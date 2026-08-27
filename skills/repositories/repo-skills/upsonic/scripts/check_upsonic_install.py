#!/usr/bin/env python3
from __future__ import annotations

import argparse
import inspect
import json
import sys
from typing import Any


def build_report(include_extended: bool = False) -> dict[str, Any]:
    import upsonic

    from upsonic import Agent, Chat, Direct, KnowledgeBase, Task, Team

    report: dict[str, Any] = {
        'version': getattr(upsonic, '__version__', 'unknown'),
        'exports': list(getattr(upsonic, '__all__', [])),
        'core_signatures': {
            'Task': str(inspect.signature(Task.__init__)),
            'Agent': str(inspect.signature(Agent.__init__)),
            'Direct': str(inspect.signature(Direct.__init__)),
            'Chat': str(inspect.signature(Chat.__init__)),
            'Team': str(inspect.signature(Team.__init__)),
            'KnowledgeBase': str(inspect.signature(KnowledgeBase.__init__)),
        },
    }

    if include_extended:
        extended: dict[str, str] = {}
        for dotted_name in [
            'upsonic.agent.autonomous_agent.autonomous_agent.AutonomousAgent',
            'upsonic.prebuilt.prebuilt_agent_base.PrebuiltAutonomousAgentBase',
            'upsonic.simulation.simulation.Simulation',
            'upsonic.ralph.loop.RalphLoop',
        ]:
            module_name, class_name = dotted_name.rsplit('.', 1)
            try:
                module = __import__(module_name, fromlist=[class_name])
                extended[class_name] = str(inspect.signature(getattr(module, class_name).__init__))
            except Exception as exc:  # pragma: no cover - best effort only
                extended[class_name] = f'UNAVAILABLE: {exc}'
        report['extended_signatures'] = extended

    return report


def main() -> int:
    parser = argparse.ArgumentParser(description='Check that Upsonic imports and signatures resolve.')
    parser.add_argument('--json', action='store_true', help='Print a JSON report instead of text.')
    parser.add_argument('--extended', action='store_true', help='Try a few heavier top-level exports too.')
    parser.add_argument('--cli-help', action='store_true', help='Also invoke the CLI help route.')
    args = parser.parse_args()

    try:
        report = build_report(include_extended=args.extended)
        if args.cli_help:
            from upsonic.cli.main import main as cli_main
            report['cli_help_exit_code'] = cli_main(['--help'])
        if args.json:
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            print(f"upsonic {report['version']}")
            print('exports:', ', '.join(report['exports']))
            for name, signature in report['core_signatures'].items():
                print(f'{name}: {signature}')
            if 'extended_signatures' in report:
                print('extended:')
                for name, signature in report['extended_signatures'].items():
                    print(f'  {name}: {signature}')
            if 'cli_help_exit_code' in report:
                print(f"cli_help_exit_code: {report['cli_help_exit_code']}")
        return 0
    except Exception as exc:  # pragma: no cover - smoke helper
        print(f'ERROR: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
