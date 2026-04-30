# Copyright 2026 The University of Utah
# SPDX-License-Identifier: MIT

"""Filters adult websites out of a Tranco CSV"""
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
import sys

from . import Domain


@dataclass
class Blocklist:
    inner: set[str]


def parse_args() -> Path:
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <tranco.csv>")
    return Path(sys.argv[1])


def parse_adult_list() -> Blocklist:
    with open('adult-blocklist.txt') as f:
        return Blocklist(set(f)) # Create a set from all the lines


def parse_tranco_line(line: str) -> Domain:
    return Domain(line.split(',')[1])


def parse_tranco_list(path: Path) -> Iterator[Domain]:
    return map(parse_tranco_line, open(path))


def is_blocked(tranco_domain: Domain, blocklist: Blocklist) -> bool:
    [domain, _sep, tld] = tranco_domain.inner.rpartition('.') # a.b.example.com -> [a.b.example, com]
    while domain:
        if f"{domain}.{tld}" in blocklist.inner:
            return True
        [_, _sep, domain] = domain.partition('.') # a.b.example -> b.example
    return False


def main():
    tranco_path = parse_args()
    tranco_list = parse_tranco_list(tranco_path)
    adult_list = parse_adult_list()
    out_path = f"{tranco_path.stem}_filtered{tranco_path.suffix}"
    with open(out_path, 'w') as f:
        for domain in tranco_list:
            if not is_blocked(domain, adult_list):
                f.write(domain.inner)


if __name__ == "__main__":
    main()