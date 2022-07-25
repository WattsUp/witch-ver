"""Module version information

Similar to version_hook but saves version_dict to a separate file _version.py
Especially for self-versioning due to importing and gitignore stuff...
"""

__all__ = ["__version__", "version_dict"]

try:
  from witch_ver._version import version_dict
except ImportError:
  # Fallback
  import datetime  # pylint: disable=import-outside-toplevel
  version_dict = {
      "tag": None,
      "tag_prefix": "v",
      "sha": "",
      "sha_abbrev": "",
      "branch": "master",
      "date": datetime.datetime.now(),
      "dirty": False,
      "distance": 0,
      "pretty_str": "0+untagged.0.g",
      "git_dir": None
  }

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
    from witch_ver import git  # pylint: disable=import-outside-toplevel
  except ImportError:
    _semver = version_dict
    return version_dict

  try:
    import pathlib  # pylint: disable=import-outside-toplevel
    # TODO (WattsUp) read options and configure
    g = git.fetch(custom_str_func=git.str_func_pep440, cache=version_dict)
    _semver = g.asdict(isoformat_date=True)

    # Overwrite the static file with new version info
    new_file = '"""Static module version information\n"""\n\nversion_dict = {\n'
    items = []
    for k, v in _semver.items():
      if isinstance(v, str):
        items.append(f'    "{k}": "{v}"')
      else:
        items.append(f'    "{k}": {v}')
    new_file += ",\n".join(items)
    new_file += "\n}\n"
    path = pathlib.Path(__file__).with_name("_version.py")
    if path.exists():
      with open(path, "r", encoding="utf-8") as file:
        buf = file.read()
        if buf == new_file:
          return version_dict

    with open(path, "w", encoding="utf-8") as file:
      file.write(new_file)
    return _semver
  except RuntimeError:
    _semver = version_dict
    return version_dict


version_dict = _get_version()

__version__ = version_dict.get("pretty_str")
