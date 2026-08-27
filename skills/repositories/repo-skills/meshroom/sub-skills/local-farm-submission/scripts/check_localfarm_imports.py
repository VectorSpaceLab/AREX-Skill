#!/usr/bin/env python3
"""Import-check Meshroom LocalFarm modules without starting a daemon or creating a farm root."""

from __future__ import annotations

import argparse
import platform


def main() -> int:
    parser = argparse.ArgumentParser(description="Check LocalFarm client/submitter imports without side effects.")
    parser.parse_args()

    import localfarm.localFarmClient
    import localfarm.localFarmLauncher
    import meshroom.submitters.localFarm.localFarmSubmitter

    print(f"platform: {platform.system()}")
    print("localfarm imports: ok")
    if platform.system() == "Windows":
        print("warning: full LocalFarm daemon is currently Unix-oriented")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
