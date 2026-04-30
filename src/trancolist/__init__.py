# Copyright 2026 The University of Utah
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

@dataclass
class Domain:
    inner: str


def parse_tranco_line(line: str) -> Domain:
    return Domain(line.split(',')[1])


def parse_tranco_list(path: Path) -> Iterator[Domain]:
    return map(parse_tranco_line, open(path))
