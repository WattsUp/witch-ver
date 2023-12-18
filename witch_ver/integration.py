"""Integration into various automated tools."""
from __future__ import annotations

import ast
import inspect
import pathlib
import re
import textwrap
import typing as t
from typing import TYPE_CHECKING

from witch_ver import git

if TYPE_CHECKING:
    import setuptools


# Boolean
# Or a configuration
# Or a function to produce a configuration
UseWitchVerValue = t.Union[bool, t.Dict[str, t.Any], t.Callable[[], t.Dict[str, t.Any]]]


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


def use_witch_ver(
    dist: setuptools.Distribution,
    _,
    value: UseWitchVerValue,
) -> None:
    """Entrypoint for setuptools.

    Args:
        dist: setuptools distribution
        keyword: Keyword used in entrypoint
        value: True, or a dictionary (or callable that produces a dictionary) of
            configuration properties
    """
    config: t.Dict[str, t.Any] = {"custom_str_func": git.str_func_pep440}
    if not value:
        return
    if callable(value):
        config.update(value())
    elif isinstance(value, dict):
        config.update(value)
    elif not isinstance(value, bool):
        msg = (
            "Expected boolean, a dictionary, or a function to produce a dictionary. "
            f"Got: {type(value)}"
        )
        raise TypeError(msg)

    # custom_str_func may be a discrete function or a member of git
    f = config["custom_str_func"]
    if isinstance(f, str):
        # Expect to be a function of witch_ver.git
        config["custom_str_func"] = getattr(git, f)
    elif not callable(f):
        msg = "custom_str_func is not callable nor a member of witch_ver.git"
        raise TypeError(msg)

    packages = []
    for v in dist.packages:
        v: str
        package = v.split(".", maxsplit=1)[0]
        if package not in packages:
            packages.append(package)

    # Catch not being in a git repo anymore and return first cached version from
    # version.py
    repo_folder = pathlib.Path().resolve()
    try:
        g = git.fetch(repo_folder, **config)  # type: ignore[attr-defined]
    except RuntimeError as e:
        dst = repo_folder.joinpath(packages[0], "version.py")
        if dst.exists():
            with dst.open(encoding="utf-8") as file:
                buf = file.read()
                buf = re.search(r"version_dict = ({.*?})", buf, flags=re.S)
                if buf is None:  # pragma: no cover
                    # Don't need coverage on debug code
                    msg = "Regex found to find version_dict"
                    raise ValueError(msg) from e
                cache = ast.literal_eval(buf[1])
                g = git.GitVer(**cache)
        else:
            msg = "Unable to fetch version from git nor cache"
            raise RuntimeError(msg) from e

    src = pathlib.Path(__file__).with_name("version_hook.py").resolve()
    with src.open(encoding="utf-8") as file:
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
    version_dict += ",\n}"
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
    config_str += ",\n}"
    config_str = textwrap.indent(config_str, "    ")
    version_py = re.sub(r" *config = {.*?}", config_str, buf, count=1, flags=re.S)

    for v in packages:
        # Copy version_hook
        dst = repo_folder.joinpath(v, "version.py")
        _write_matching_newline(dst, version_py)

        # Install import directive to __init__
        dst = repo_folder.joinpath(v, "__init__.py")
        with dst.open(encoding="utf-8") as file:
            buf = file.read()

        import_str = f"from {v}.version import __version__\n"
        if import_str in buf:
            continue

        # Find the first import of the module (EOF if not present)
        # and append import_str
        header = re.search(
            rf'^"""(?:.|\n)*?"""(?:(?!(?:from {v}|import {v})).*\n|\n)*',
            buf,
        )
        if header is None:
            buf = buf + "\n" + import_str
        else:
            buf = buf[: header.end()] + import_str + "\n" + buf[header.end() :]

        _write_matching_newline(dst, buf)

    dist.metadata.version = str(g)
