"""Module version information."""

from __future__ import annotations

import re
from pathlib import Path

__all__ = ["__version__"]

version_dict = {}

_semver = {}


def _get_version() -> dict:
    """Get latest version.

    Returns:
        Git object
    """
    if _semver:
        return _semver
    try:
        import witch_ver  # pylint: disable=import-outside-toplevel
    except ImportError:
        _semver.update(**version_dict)
        return _semver

    config = {
        "custom_str_func": witch_ver.str_func_pep440,
    }

    module_folder = Path(__file__).parent.resolve()
    repo_folder = module_folder.parent

    try:
        g = witch_ver.fetch(
            repo_folder,
            cache=version_dict,
            **config,  # type: ignore[attr-defined]
        )
        _semver.update(**g.asdict(isoformat_date=True))

    except RuntimeError:
        _semver.update(**version_dict)
        return _semver

    # Overwrite this file with new version info
    new_file = "version_dict = {\n"
    items = []
    for k, v in _semver.items():
        if isinstance(v, str):
            items.append(f'    "{k}": "{v}"')
        else:
            items.append(f'    "{k}": {v}')
    new_file += ",\n".join(items)
    new_file += ",\n}"

    path_self = Path(__file__)
    with path_self.open("rb") as file:
        buf_b = file.read()
        new_file_b = new_file.encode()
        if b"\r\n" in buf_b:
            new_file_b = new_file_b.replace(b"\n", b"\r\n")

        orig = re.search(rb"version_dict = {.*?}", buf_b, flags=re.S)
        if orig is None:
            msg = f"Could not find version_dict in {path_self}"
            raise ValueError(msg)
        if orig[0] == new_file_b:
            return _semver
        # Modifications will occur, write (avoids over touching for systems that
        # care about modification date)
        buf_b = buf_b[: orig.start()] + new_file_b + buf_b[orig.end() :]

    with path_self.open("wb") as file:
        file.write(buf_b)
    return _semver


version_dict = _get_version()

__version__: str = version_dict.get("pretty_str", "0+untagged.0.g")
