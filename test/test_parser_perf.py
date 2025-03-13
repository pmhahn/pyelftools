#!/usr/bin/env python
#-------------------------------------------------------------------------------
# test/run_examples_test.py
#
# Run the examples and compare their output to a reference
#
# Seva Alekseyev (sevaa@sprynet.com)
# This code is in the public domain
#
# This runs and times in-memory firehose DWARF parsing on all files from the dwarfdump autotest.
# The idea was to isolate the performance of the struct parsing logic alone.
#-------------------------------------------------------------------------------

from __future__ import annotations

from argparse import Namespace
from io import BytesIO
from pathlib import Path
from typing import IO

from elftools.elf.elffile import ELFFile
from elftools.dwarf.locationlists import LocationParser

import pytest
from pytest_benchmark.fixture import BenchmarkFixture


def parse_dwarf(ef: ELFFile, args: Namespace) -> None:
    di = ef.get_dwarf_info()
    llp = LocationParser(di.location_lists())
    ranges = di.range_lists()
    for cu in di.iter_CUs():
        ver = cu.header.version
        if args.lineprog:
            # No way to isolate lineprog parsing :(
            lp = di.line_program_for_CU(cu)
            assert lp is not None
            lp.get_entries()
        for die in cu.iter_DIEs():
            for (_, attr) in die.attributes.items():
                if args.locs and LocationParser.attribute_has_location(attr, ver):
                    llp.parse_from_attribute(attr, ver, die)
                elif args.ranges and attr.name == "DW_AT_ranges":
                    assert ranges is not None
                    if ver >= 5:
                        ranges.get_range_list_at_offset_ex(attr.value)
                    else:
                        ranges.get_range_list_at_offset(attr.value)


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    filelist = Path("test/testfiles_for_dwarfdump").glob("*.elf")
    metafunc.parametrize("testpath", filelist, ids=lambda path: path.stem)


def test_perf(testpath: Path, benchmark: BenchmarkFixture) -> None:
    args = Namespace(locs=False, ranges=False, lineprog=False)
    stream = BytesIO(testpath.read_bytes())
    benchmark.pedantic(parse_dwarf, args=(ELFFile(stream), args), iterations=1, rounds=1)
