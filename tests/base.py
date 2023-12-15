from __future__ import annotations

import importlib.util
import random
import shutil
import string
import time
import unittest
from pathlib import Path
from typing import TYPE_CHECKING

import autodict

from tests import TEST_LOG

if TYPE_CHECKING:
    from types import ModuleType


class TestBase(unittest.TestCase):
    _TEST_ROOT = Path.cwd().joinpath(".test").resolve()
    _DATA_ROOT = Path(__file__).resolve().parent.joinpath("data")

    @classmethod
    def random_string(cls, length: int = 20) -> str:
        """Generate a random string a-zA-Z.

        Args:
            length: Length of string to generate

        Returns:
            Random string
        """
        # Not cryptographic
        return "".join(random.choices(string.ascii_letters, k=length))  # noqa: S311

    @classmethod
    def random_int(cls, min_: int, max_: int) -> int:
        # Not cryptographic
        return random.randint(min_, max_)  # noqa: S311

    @classmethod
    def random_sha(cls) -> str:
        return f"{random.getrandbits(64):X}"

    @classmethod
    def import_file(cls, path: Path) -> ModuleType:
        name = path.name.strip(".py")
        spec = importlib.util.spec_from_file_location(name, path)
        if spec is None or spec.loader is None:
            msg = f"Failed to create spec for {path}"
            raise ImportError(msg)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def __clean_test_root(self) -> None:
        if self._TEST_ROOT.exists():
            shutil.rmtree(self._TEST_ROOT)

    def setUp(self) -> None:
        self.__clean_test_root()
        self._TEST_ROOT.mkdir(parents=True, exist_ok=True)
        self._test_start = time.perf_counter()

        # Remove sleeping by default, mainly in read hardware interaction
        self._original_sleep = time.sleep
        time.sleep = lambda *_: None

    def tearDown(self) -> None:
        duration = time.perf_counter() - self._test_start
        with autodict.JSONAutoDict(str(TEST_LOG)) as d:
            d["methods"][self.id()] = duration
        self.__clean_test_root()

        # Restore sleeping
        time.sleep = self._original_sleep

    def log_speed(self, slow_duration: float, fast_duration: float) -> None:
        with autodict.JSONAutoDict(str(TEST_LOG)) as d:
            d["speed"][self.id()] = {
                "slow": slow_duration,
                "fast": fast_duration,
                "increase": slow_duration / fast_duration,
            }

    @classmethod
    def setUpClass(cls) -> None:
        print(f"{cls.__module__}.{cls.__qualname__}[", end="", flush=True)
        cls._CLASS_START = time.perf_counter()

    @classmethod
    def tearDownClass(cls) -> None:
        print("]done", flush=True)
        duration = time.perf_counter() - cls._CLASS_START
        with autodict.JSONAutoDict(str(TEST_LOG)) as d:
            d["classes"][f"{cls.__module__}.{cls.__qualname__}"] = duration
