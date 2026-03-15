#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys


COMMANDS = [
    ["pytest", "tests/deploy", "-m", "deploy"],
    ["pytest", "tests/integration", "-m", "integration"],
]


def main() -> int:
    for cmd in COMMANDS:
        print(f"\n==> Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=False)
        if result.returncode != 0:
            print(f"Command failed: {' '.join(cmd)}")
            return result.returncode
    print("\nDeployment validation succeeded.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
