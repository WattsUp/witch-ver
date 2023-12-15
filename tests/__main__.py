from __future__ import annotations

import sys
import unittest

import autodict

from tests import TEST_LOG
from witch_ver.version import __version__, version_dict


def pre_tests() -> None:
    """Things to run before all tests."""
    print(f"Testing version {__version__}")
    if TEST_LOG.exists():
        TEST_LOG.unlink()
    with autodict.JSONAutoDict(str(TEST_LOG)) as d:
        d["version"] = version_dict
        d["classes"] = {}
        d["methods"] = {}


def post_tests() -> None:
    """Things to run after all tests."""
    n_slowest = 10
    with autodict.JSONAutoDict(str(TEST_LOG)) as d:
        classes = sorted(d["classes"].items(), key=lambda item: -item[1])[:n_slowest]
        methods = sorted(d["methods"].items(), key=lambda item: -item[1])[:n_slowest]

    print(f"{n_slowest} slowest classes")
    if len(classes) != 0:
        n_pad = max(len(k) for k, _ in classes) + 1
        for cls, duration in classes:
            print(f"  {cls:{n_pad}}: {duration:6.2f}s")

    print(f"{n_slowest} slowest tests")
    if len(methods) != 0:
        n_pad = max(len(k) for k, _ in methods) + 1
        for method, duration in methods:
            print(f"  {method:{n_pad}}: {duration:6.2f}s")


pre_tests()
m = unittest.main(module=None, exit=False)
all_passed = m.result.wasSuccessful()
if all_passed:
    post_tests()
    sys.exit(0)
else:
    sys.exit(1)
