#!/usr/bin/env python3
"""Run the standard-library regression suite and emit a machine-readable receipt."""
from __future__ import annotations

import argparse
import json
import sys
import time
import unittest
from pathlib import Path

from tests.support import COUNTS


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    started = time.perf_counter()
    suite = unittest.defaultTestLoader.discover(str(root / "tests"), pattern="test_*.py")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    semantic_keys = {
        "operator_value_checks",
        "checker_semantic_obligations",
        "dynamic_negative_control_sample_checks",
    }
    semantic_units = sum(COUNTS[key] for key in semantic_keys)
    report = {
        "status": "PASS" if result.wasSuccessful() else "FAIL",
        "tests_run": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skipped": len(result.skipped),
        "wall_seconds": time.perf_counter() - started,
        "counts": dict(sorted(COUNTS.items())),
        "semantic_units_this_run": semantic_units,
        "scope": "software regression; no minimization search or new scientific instance selection",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
