"""Test base class
"""

import pathlib
import random
import shutil
import string
import time
import unittest

import autodict

from tests import TEST_LOG


class TestBase(unittest.TestCase):
    """Test base class"""

    _TEST_ROOT = pathlib.Path.cwd().joinpath(".test").resolve()
    _DATA_ROOT = pathlib.Path(__file__).resolve().parent.joinpath("data")

    @classmethod
    def random_string(cls, length: int = 20) -> str:
        """Generate a random string a-zA-Z

        Args:
          length: Length of string to generate

        Returns:
          Random string
        """
        return "".join(random.choices(string.ascii_letters, k=length))

    def __clean_test_root(self):
        if self._TEST_ROOT.exists():
            shutil.rmtree(self._TEST_ROOT)

    def setUp(self):
        self.__clean_test_root()
        self._TEST_ROOT.mkdir(parents=True, exist_ok=True)
        self._test_start = time.perf_counter()

        # Remove sleeping by default, mainly in read hardware interaction
        self._original_sleep = time.sleep
        time.sleep = lambda *args: None

    def tearDown(self):
        duration = time.perf_counter() - self._test_start
        with autodict.JSONAutoDict(TEST_LOG) as d:
            d["methods"][self.id()] = duration
        self.__clean_test_root()

        # Restore sleeping
        time.sleep = self._original_sleep

    def log_speed(self, slow_duration, fast_duration):
        with autodict.JSONAutoDict(TEST_LOG) as d:
            d["speed"][self.id()] = {
                "slow": slow_duration,
                "fast": fast_duration,
                "increase": slow_duration / fast_duration,
            }

    @classmethod
    def setUpClass(cls):
        print(f"{cls.__module__}.{cls.__qualname__}[", end="", flush=True)
        cls._CLASS_START = time.perf_counter()

    @classmethod
    def tearDownClass(cls):
        print("]done", flush=True)
        # time.sleep(10)
        duration = time.perf_counter() - cls._CLASS_START
        with autodict.JSONAutoDict(TEST_LOG) as d:
            d["classes"][f"{cls.__module__}.{cls.__qualname__}"] = duration
