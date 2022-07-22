"""Module version information
"""

__all__ = ["__version__", "version_dict"]

version_dict = {}

_semver = None


def _get_version() -> dict:
  """Get latest version

  Returns:
    Git object
  """
  global _semver
  try:
    from witch_ver import git  # pylint: disable=import-outside-toplevel
  except ImportError:
    return version_dict

  try:
    import re  # pylint: disable=import-outside-toplevel
    # TODO (WattsUp) read options and configure
    g = git.fetch(custom_str_func=git.str_func_pep440, cache=version_dict)
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
    with open(__file__, "r", encoding="utf-8") as file:
      buf = file.read()
      orig = re.search(r"version_dict = {.*?}", buf, flags=re.S)
      if orig[0] == new_file:
        return version_dict
      # Modifications will occur, write (avoids over touching for systems that
      # care about modification date)
      buf = buf[:orig.start()] + new_file + buf[orig.end():]

    with open(__file__, "w", encoding="utf-8") as file:
      file.write(buf)
    return _semver
  except RuntimeError:
    return version_dict


if _semver is None:
  _semver = version_dict = _get_version()
else:
  # Subsequent imports should use the already loaded/cached module in
  # sys.modules
  pass  # pragma: no cover

__version__ = version_dict.get("pretty_str")
