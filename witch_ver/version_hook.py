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
    g = git.fetch(custom_str_func=git.str_func_pep440)
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
    with open(__file__, "r+", encoding="utf-8") as file:
      buf = file.read()
      buf = re.sub(r"version_dict = {.*?}", new_file, buf, count=1, flags=re.S)

      file.seek(0)
      file.write(buf)
      file.truncate()
    return _semver
  except RuntimeError:
    return version_dict


if _semver is None:
  _semver = version_dict = _get_version()

__version__ = version_dict["pretty_str"]
