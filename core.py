# Copyright 2026 The University of Utah
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator


@dataclass
class Domain:
    inner: str
