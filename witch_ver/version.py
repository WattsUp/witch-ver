"""Module version information.

Similar to version_hook but saves version_dict to a separate file _version.py
Especially for self-versioning due to importing and gitignore stuff...
"""
from __future__ import annotations

import datetime
import pathlib

__all__ = ["__version__"]


try:
    from witch_ver._version import version_dict
except ImportError:
    # Fallback
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
        "git_dir": None,
    }

_semver = {}


def _write_matching_newline(path: pathlib.Path, buf: str) -> None:
    """Write buf to path, whilst matching existing newlines if path exists.

    Args:
      path: Path to file to write
      buf: File contents to write
    """
    buf_b = buf.encode()
    if path.exists():
        with path.open("rb") as file:
            buf_b_existing = file.read()
            if b"\r\n" in buf_b_existing:
                buf_b = buf_b.replace(b"\n", b"\r\n")
        if buf_b == buf_b_existing:
            # Don't write an identical file, preserves modification time
            return
    with path.open("wb") as file:
        file.write(buf_b)


def _get_version() -> dict:
    """Get latest version.

    Returns:
      Git object
    """
    if _semver:
        return _semver
    try:
        from witch_ver import git  # pylint: disable=import-outside-toplevel
    except ImportError:
        _semver.update(**version_dict)
        return _semver

    config = {"custom_str_func": git.str_func_pep440}

    module_folder = pathlib.Path(__file__).parent.resolve()
    repo_folder = module_folder.parent

    try:
        g = git.fetch(
            repo_folder,
            cache=version_dict,
            **config,  # type: ignore[attr-defined]
        )
        _semver.update(**g.asdict(isoformat_date=True))
    except RuntimeError:
        _semver.update(**version_dict)
        return _semver

    # Overwrite the static file with new version info
    new_file = (
        '"""Static module version information."""\n'
        "from __future__ import annotations\n\n"
        "version_dict = {\n"
    )
    items = []
    for k, v in _semver.items():
        if isinstance(v, str):
            items.append(f'    "{k}": "{v}"')
        else:
            items.append(f'    "{k}": {v}')
    new_file += ",\n".join(items)
    new_file += ",\n}\n"
    path = module_folder.joinpath("_version.py")
    _write_matching_newline(path, new_file)
    return _semver


version_dict = _get_version()

__version__: str = version_dict.get("pretty_str", "0+untagged.0.g")
