from __future__ import annotations
import subprocess
import logging
from pathlib import Path
import shutil

RUBY_BUNDLE = shutil.which("bundle")
EXE = shutil.which("github-linguist")
if not EXE and not RUBY_BUNDLE:
    raise ImportError("GitHub Linguist not found, did you install it per README?")

EXEC_COMMAND = []
if not EXE and RUBY_BUNDLE:
    EXE = RUBY_BUNDLE
    EXEC_COMMAND = ["exec", "github-linguist"]

GIT = shutil.which("git")
if not GIT:
    raise ImportError("Git not found")


def linguist(path: Path, rtype: bool = False) -> str | list[tuple[str, str]]:
    """runs GitHub Linguist Ruby script"""

    path = Path(path).expanduser()

    if not checkrepo(path):
        return None

    command = [EXE] + EXEC_COMMAND + [str(path)]
    ret = subprocess.check_output(command, text=True).split("\n")

    # %% parse percentage
    lpct = []

    for line in ret:
        L = line.split()
        if not L:  # EOF
            break

        lang = L[-1]
        # Loop backwards from len(L)-2 and prepend elements until we reach a string that is only made of digits
        for i in range(len(L) - 2, -1, -1):
            if L[i].isdigit():
                break
            lang = L[i] + " " + lang

        lpct.append((lang, L[0][:-1]))

    if rtype:
        return lpct[0][0] if lpct and lpct[0] else "None"

    return lpct


def checkrepo(path: Path) -> bool:
    """basic check for healthy Git repo ready for Linguist to analyze"""

    path = Path(path).expanduser()

    if not (path / ".git").is_dir():
        logging.error(
            f'{path} does not seem to be a Git repository, and Linguist only works on files after "git commit"'
        )
        return False

    # %% detect uncommitted (dirty)
    ret = subprocess.check_output([GIT, "-C", str(path), "status", "--porcelain"], text=True)

    ADD = {"A", "?"}
    MOD = "M"

    for line in ret.split("\n"):
        L = line.split()
        if not L:
            continue

        if ADD.intersection(L[0]) or (MOD in L[0] and L[1] == ".gitattributes"):
            logging.warning(
                f' {path} has uncommitted changes: \n\n{ret}\n Linguist only works on files after "git commit"'
            )
            return False

    return True
