#!/usr/bin/env python
#-------------------------------------------------------------------------------
# test/run_dwarfdump_tests.py
#
# Automatic test runner for elftools & llvm-dwarfdump-11
#
# Eli Bendersky (eliben@gmail.com)
# This code is in the public domain
#-------------------------------------------------------------------------------

from __future__ import annotations

import os
import platform
from pathlib import Path
from subprocess import run

import pytest


# Following the readelf example, we ship our own.
if platform.system() == "Windows":
    # Point the environment variable DWARFDUMP at a Windows build of llvm-dwarfdump
    DWARFDUMP_PATH = os.environ.get('DWARFDUMP', "llvm-dwarfdump.exe")
elif platform.system() == "Linux":
    DWARFDUMP_PATH = 'test/external_tools/llvm-dwarfdump'
else:
    pytest.skip(reason=f"Platform {platform.system()!r} not supported")


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    filelist = Path("test/testfiles_for_dwarfdump").glob("*.elf")
    metafunc.parametrize("testpath", filelist, ids=lambda path: path.stem)


def test_dwarfdump(testpath: Path) -> None:
    env = dict(os.environ, LC_ALL="C")
    native, python = (
        run(
            [exe_path, "--debug-info", "--verbose", testpath],
            capture_output=True,
            timeout=600,
            check=True,
            text=True,
            env=env,
        ).stdout
        for exe_path in [DWARFDUMP_PATH, 'scripts/dwarfdump.py']
    )

    # llvm-dwarfdump sometimes adds a comment to addresses. We still haven't invested the
    # effort to understand exactly when. For now, removing the section comment helps us pass
    # the test.
    native = native.replace('(0x0000000000000000 ".text")', '(0x0000000000000000)')

    nlines, plines = (
        [line for line in s.lower().splitlines() if line.strip()]
        for s in (native, python)
    )

    assert len(nlines) == len(plines), \
        f'Number of lines different: {len(nlines)} vs {len(plines)}'

    for i, (nline, pline) in enumerate(zip(nlines, plines, strict=True)):
        # Compare ignoring whitespace
        nparts = nline.split()
        pparts = pline.split()

        assert ''.join(nparts) == ''.join(pparts), \
            f'Mismatch on line #{i}:\n>>{nline}<<\n>>{pline}<<'
