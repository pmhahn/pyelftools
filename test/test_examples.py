#!/usr/bin/env python
#-------------------------------------------------------------------------------
# test/run_examples_test.py
#
# Run the examples and compare their output to a reference
#
# Eli Bendersky (eliben@gmail.com)
# This code is in the public domain
#-------------------------------------------------------------------------------

from __future__ import annotations

import os
import sys
from pathlib import Path
from subprocess import run

import pytest


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    filelist = Path("examples").glob("*.py")
    metafunc.parametrize("example_path", filelist, ids=lambda path: path.stem)


def reference_output_path(path: Path) -> Path:
    """ Compute the reference output path from a given example path.
    """
    return path.parent / "reference_output" / f"{path.stem}.out"


def test_run_example_and_compare(example_path: Path) -> None:
    reference_path = reference_output_path(example_path)
    ref_str = reference_path.read_text()
    env = dict(os.environ, LC_ALL="C")
    result = run(
        [sys.executable, example_path, "--test", "./examples/sample_exe64.elf"],
        capture_output=True,
        timeout=600,
        check=True,
        text=True,
        env=env,
    )
    assert result.stdout == ref_str
