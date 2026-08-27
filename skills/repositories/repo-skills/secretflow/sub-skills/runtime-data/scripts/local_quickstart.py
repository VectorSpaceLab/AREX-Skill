#!/usr/bin/env python3
"""Minimal SecretFlow local-runtime smoke helper.

This script uses debug mode so it can prove the basic runtime path without a
multi-node Ray deployment. It creates a party device, moves a small value onto
it, reveals the value, and shuts the runtime down.
"""

import secretflow as sf


def main() -> int:
    sf.shutdown()
    try:
        sf.init(parties=["alice", "bob", "carol"], address="local", debug_mode=True)
        alice = sf.PYU("alice")
        message = alice(lambda x: x)("Hello World!")
        print(sf.reveal(message))
    finally:
        sf.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
