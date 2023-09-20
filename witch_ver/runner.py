"""Command runner
"""

import os
import subprocess
import typing as t


def run(
    cmd: str, args: t.List[str], cwd: t.Union[str, bytes, os.PathLike] = None
) -> t.Tuple[str, int]:
    """Run a command and capture its output and return code

    Args:
      cmd: Command to run
      args: Arguments to add to command
      cwd: Current working directory to run the command from

    Returns:
      stdout, return code
    """
    cmd = [cmd] + args
    try:
        result = subprocess.run(cmd, capture_output=True, cwd=cwd, check=False)
    except OSError:
        cmd_str = " ".join(cmd)
        print(f"Failed to run '{cmd_str}'")
        return None, None
    return result.stdout.strip().decode(), result.returncode
