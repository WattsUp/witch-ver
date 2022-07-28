"""Integration into various automated tools
"""

import inspect
import pathlib
import re
import textwrap
import setuptools
from typing import Dict, Union, Any, Callable

from witch_ver import git


def use_witch_ver(
    dist: setuptools.Distribution,
    _: str,
    value: Union[bool, Dict[str, Any], Callable[[], Dict[str, Any]]],
) -> None:
  """Entrypoint for setuptools

  Args:
    dist: setuptools distribution
    keyword: Keyword used in entrypoint
    value: True, or a dictionary (or callable that produces a dictionary) of
      configuration properties
  """
  config = {"custom_str_func": git.str_func_pep440}
  if not value:
    return
  elif callable(value):
    config.update(value())
  elif isinstance(value, dict):
    config.update(value)

  # custom_str_func may be a discrete function or a member of git
  f = config["custom_str_func"]
  if isinstance(f, str):
    # Expect to be a function of witch_ver.git
    config["custom_str_func"] = getattr(git, f)
  elif not callable(f):
    raise TypeError("custom_str_func is not callable nor a member of "
                    "witch_ver.git")

  g = git.fetch(**config)
  src = pathlib.Path(__file__).with_name("version_hook.py").resolve()
  with open(src, "r", encoding="utf-8") as file:
    buf = file.read()

  # Generate initial cache
  version_dict = "version_dict = {\n"
  items = []
  for k, v in g.asdict(isoformat_date=True).items():
    if isinstance(v, str):
      items.append(f'    "{k}": "{v}"')
    else:
      items.append(f'    "{k}": {v}')
  version_dict += ",\n".join(items)
  version_dict += "\n}"
  buf = re.sub(r"version_dict = {.*?}", version_dict, buf, count=1, flags=re.S)

  # Save config to version_hook
  config_str = "config = {\n"
  items = []
  for k, v in config.items():
    if isinstance(v, str):
      items.append(f'    "{k}": "{v}"')
    elif callable(v):
      if v.__module__ == "witch_ver.git":
        items.append(f'    "{k}": witch_ver.{v.__name__}')
      else:
        # Copy source to a local function
        lines = textwrap.dedent(inspect.getsource(v).strip())
        config_str = lines + "\n\n" + config_str
        items.append(f'    "{k}": {v.__name__}')
    else:
      items.append(f'    "{k}": {v}')
  config_str += ",\n".join(items)
  config_str += "\n}"
  config_str = textwrap.indent(config_str, "    ")
  buf = re.sub(r" *config = {.*?}", config_str, buf, count=1, flags=re.S)

  root = pathlib.Path(".").resolve()
  for v in dist.packages:
    # TODO (WattsUp) Add installation into __init__ for
    # from version import __version__
    dst = root.joinpath(v, "version.py")
    with open(dst, "w", encoding="utf-8") as file:
      file.write(buf)

  dist.metadata.version = str(g)
