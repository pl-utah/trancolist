# Copyright 2026 The University of Utah
# SPDX-License-Identifier: MIT

"""Filters adult websites out of a Tranco CSV"""
from collections.abc import Iterator, Iterable
from dataclasses import dataclass
import itertools
from pathlib import Path
import sys

from core import Domain 
import tranco


@dataclass(frozen=True)
class Blocklist:
    inner: set[Domain]

    def blocks(self, domain: Domain) -> bool:
        [domain_part, _sep, tld] = domain.inner.rpartition('.') # a.b.example.com -> [a.b.example, com]
        while domain_part:
            if f"{domain_part}.{tld}" in self.inner:
                return True
            [_, _sep, domain_part] = domain_part.partition('.') # a.b.example -> b.example
        return False


def parse_args() -> tuple[list[Path], Path]:
    """Returns (blocklists, tranco_list)"""
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} [blocklist1.txt ...] <trancolist.txt>")
        sys.exit(1)
    return (list(map(Path, sys.argv[1:-1])), Path(sys.argv[-1]))


def parse_blocklists(lists: Iterable[Iterable[str]]) -> Blocklist:
    flattened = itertools.chain.from_iterable(lists)
    return Blocklist(set(map(Domain, flattened))) # Create a set from all the lines


def filter_domains(domains: Iterable[Domain], blocklist: Blocklist) -> Iterator[Domain]:
    return filter(lambda domain: not blocklist.blocks(domain), domains)


def main():
    block_paths, tranco_path = parse_args()
    tranco_list = map(tranco.parse_tranco_line, open(tranco_path))
    blocklists = map(open, block_paths)
    blocklist = parse_blocklists(blocklists)
    out_path = f"{tranco_path.stem}_filtered{tranco_path.suffix}"
    with open(out_path, 'w') as f:
        (f.write(domain.inner) for domain in filter_domains(tranco_list, blocklist))


if __name__ == "__main__":
    main()