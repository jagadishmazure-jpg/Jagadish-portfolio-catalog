"""Fail if the README's generator test count differs from a real pytest collection."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def collected() -> int:
    out = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q"], cwd=ROOT, capture_output=True, text=True).stdout
    m = re.search(r"(\d+) tests? collected", out)
    if not m:
        sys.exit("could not read the pytest total:\n" + out[-500:])
    return int(m.group(1))


def main() -> int:
    n = collected()
    readme = (ROOT / "README.md").read_text()
    claims = {int(x) for x in re.findall(r"(\d+) generator tests", readme)}
    print(f"pytest collected {n}; README claims {sorted(claims)}")
    if claims != {n}:
        print("README generator test count is out of date")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
