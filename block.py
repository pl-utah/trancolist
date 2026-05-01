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


def parse_args() -> Path:
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <tranco.csv>")
        sys.exit(1)
    return Path(sys.argv[1])


def parse_blocklists(lists: Iterable[Iterable[str]]) -> Blocklist:
    flattened = itertools.chain.from_iterable(lists)
    return Blocklist(set(map(Domain, flattened))) # Create a set from all the lines


def parse_adult_list() -> Blocklist:
    with open('adult-blocklist.txt') as f:
        return parse_blocklists(itertools.repeat(f, 1))


def filter_domains(domains: Iterable[Domain], blocklist: Blocklist) -> Iterator[Domain]:
    return filter(lambda domain: not blocklist.blocks(domain), domains)


def main():
    tranco_path = parse_args()
    tranco_list = map(tranco.parse_tranco_line, open(tranco_path))
    adult_list = parse_adult_list()
    out_path = f"{tranco_path.stem}_filtered{tranco_path.suffix}"
    with open(out_path, 'w') as f:
        (f.write(domain.inner) for domain in filter_domains(tranco_list, adult_list))


if __name__ == "__main__":
    main()