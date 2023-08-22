"""Run yapf formatter and trim whitespace on all files
"""

import pathlib
import subprocess
import sys

import colorama
from colorama import Fore

colorama.init(autoreset=True)


def main() -> None:
  """Main program entry
  """

  cwd = pathlib.Path(__file__).parent.parent

  # Get a list of files
  files = []
  folders = ["witch_ver", "tests", "tools"]
  for folder in folders:
    path = cwd.joinpath(folder)
    if not path.is_dir():
      raise TypeError(f"{path} is not a folder")
    files.extend(path.glob("*.py"))

  # Run yapf first
  args = ([
      "yapf",
      "-p",  # Run in parallel
      "-m",  # Print modified
      "-r",  # Recursive directories
      "-i",  # Edit in place
      # "-vv",  # Print file names when processing
  ] + files)
  stdout = subprocess.check_output(args, cwd=cwd).decode()
  for line in stdout.splitlines():
    if line.startswith("Reformatting"):
      print(f"{Fore.CYAN}{line}")
    elif line.startswith("Formatted"):
      print(f"{Fore.GREEN}{line}")
    else:
      print(line)

  # Trim trailing whitespace
  for f in files:
    # Do binary to normalize line endings to LF
    with open(f, "rb") as file:
      buf = file.read()

    lines = [l.rstrip(b" ") for l in buf.splitlines()]
    buf_trimmed = b"\n".join(lines)
    # Add trailing newline to non-blank files
    if buf_trimmed != b"":
      buf_trimmed += b"\n"
    if buf == buf_trimmed:
      continue
    with open(f, "wb") as file:
      file.write(buf_trimmed)
    print(f"{Fore.GREEN}Trimmed {f}")


if __name__ == "__main__":
  sys.exit(main())