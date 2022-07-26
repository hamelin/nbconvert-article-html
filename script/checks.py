import subprocess as sp
import sys
from typing import *


def print_heading(heading_: str) -> None:
    heading = f"=== {heading_} "
    suffix = "=" * (88 - len(heading))
    print()
    print(heading, suffix, sep="")


def run_cmd(cmd: List[str]) -> int:
    cp = sp.run(cmd)
    return cp.returncode


CHECKS = [
    ("mypy", ["mypy", "--ignore-missing-imports", "."]),
    ("pytest", ["pytest"]),
    ("flake8", ["flake8"]),
]


for name, command in CHECKS:
    print_heading(f"Running {name} [{' '.join(command)}]")
    return_code = run_cmd(command)
    if return_code != 0:
        print(f"\n{name} FAIL")
        sys.exit(return_code)
print("\nAll checks passed.")
