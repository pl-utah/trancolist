# Copyright 2026 The University of Utah
# SPDX-License-Identifier: MIT

from dataclasses import dataclass


@dataclass(frozen=True)
class Domain:
    inner: str
