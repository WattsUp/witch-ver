"""Command runner
"""

import os
import subprocess
from typing import List, Tuple, Union


def run(cmd: str,
        args: List[str],
        cwd: Union[str, bytes, os.PathLike] = None) -> Tuple[str, int]:
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
