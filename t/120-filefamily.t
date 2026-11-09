#!/usr/bin/env perl
# 120-filefamily.t: getFileFamily() classifications, including Python.
#
# SPDX-License-Identifier: AGPL-3.0-or-later

use FindBin '$Bin';
use lib $Bin;

use Test::More;

use TestHelpers;

my $root = sibling_abs_path('..');

my $script = <<'PY';
import os
import sys
sys.path.insert(0, os.environ["ELIXIR_ROOT"])
from elixir.lib import getFileFamily

cases = {
    "foo.c": "C",
    "foo.h": "C",
    "foo.S": "C",
    "board.dts": "D",
    "board.dtsi": "D",
    "Kconfig": "K",
    "Kconfig-nommu": "K",
    "Makefile": "M",
    "subdir.mk": "M",
    "foo.py": "P",
    "FOO.PY": "P",
    "src/pkg/mod.py": "P",
    "Makefile.py": "P",
    "Kconfig.py": "P",
    "foo.pyc": None,
    "foo.pyi": None,
    "README": None,
    "notes.rst": None,
}
failed = 0
for name, expected in cases.items():
    got = getFileFamily(name)
    if got != expected:
        print(f"{name}: got {got!r}, expected {expected!r}", file=sys.stderr)
        failed += 1
sys.exit(failed)
PY

local $ENV{ELIXIR_ROOT} = $root;
my ($status, $out, $err) = run_program('python3', '-c', $script);
ok($status == 0, 'getFileFamily classifications')
    or diag "@$err";

done_testing;
