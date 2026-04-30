# Copyright 2026 The University of Utah
# SPDX-License-Identifier: MIT

"""Filters adult websites out of a Tranco CSV"""
import sys
from pathlib import Path
from collections.abc import Iterator


def parse_args() -> Path:
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <tranco.csv>")
    return Path(sys.argv[1])


def parse_adult_list() -> set[str]:
    with open('adult-blocklist.txt') as f:
        return set(f) # Create a set from all the lines


def parse_tranco_line(line: str) -> str:
    return line.split(',')[1]


def parse_tranco_list(path: Path) -> Iterator[str]:
    return map(parse_tranco_line, open(path))


def is_blocked(tranco_domain: str, blocklist: set[str]) -> bool:
    [domain, _sep, tld] = tranco_domain.rpartition('.') # a.b.example.com -> [a.b.example, com]
    while domain:
        if f"{domain}.{tld}" in blocklist:
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
                f.write(f"{domain}")


if __name__ == "__main__":
    main()