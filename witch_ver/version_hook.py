"""Module version information
"""

import pathlib
import re

__all__ = ["__version__", "version_dict"]

version_dict = {}

_semver = None


def _get_version() -> dict:
  """Get latest version

  Returns:
    Git object
  """
  global _semver
  if _semver is not None:
    return _semver
  try:
    import witch_ver  # pylint: disable=import-outside-toplevel
  except ImportError:
    _semver = version_dict
    return _semver

  try:
    # yapf: disable since witch_ver overwrites without rerunning formatter
    config = {
        "custom_str_func": witch_ver.str_func_pep440
    }
    # yapf: enable

    module_folder = pathlib.Path(__file__).parent.resolve()
    repo_folder = module_folder.parent

    g = witch_ver.fetch(repo_folder, cache=version_dict, **config)
    _semver = g.asdict(isoformat_date=True)

    # Overwrite this file with new version info
    new_file = "version_dict = {\n"
    items = []
    for k, v in _semver.items():
      if isinstance(v, str):
        items.append(f'    "{k}": "{v}"')
      else:
        items.append(f'    "{k}": {v}')
    new_file += ",\n".join(items)
    new_file += "\n}"
    with open(__file__, "rb") as file:
      buf_b = file.read()
      new_file_b = new_file.encode()
      if b"\r\n" in buf_b:
        new_file_b = new_file_b.replace(b"\n", b"\r\n")

      orig = re.search(br"version_dict = {.*?}", buf_b, flags=re.S)
      if orig[0] == new_file_b:
        return _semver
      # Modifications will occur, write (avoids over touching for systems that
      # care about modification date)
      buf_b = buf_b[:orig.start()] + new_file_b + buf_b[orig.end():]

    with open(__file__, "wb") as file:
      file.write(buf_b)
    return _semver
  except RuntimeError:
    _semver = version_dict
    return _semver


version_dict = _get_version()

__version__ = version_dict.get("pretty_str")
