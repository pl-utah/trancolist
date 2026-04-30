# Copyright 2026 The University of Utah
# SPDX-License-Identifier: MIT

import argparse
from pathlib import Path
import sys
from tap import Tap, Positional
from tranco import Tranco
from typing import Literal

from credentials import load_credentials


class ArgParser(Tap):
    list_id: str | None = None
    """
    The list ID of an existing or pending list to get. Mutually exclusive with
    --config.
    """
    config: Path = Path("default.json")
    """
    The path to a json file that configures a new Tranco list. The json file
    should follow the schema at
    https://tranco-list.eu/api_documentation#datatypes-configuration. Mutually
    exclusive with --list-id.
    """
    creds: Path = Path("credentials.json")
    """
    The path to a json file with values for the keys "email" and "api_key".
    Environment variables `TRANCO_EMAIL` and `TRANCO_API_KEY` take precedence,
    so this option will be ignored if both are specified.
    """
    blocklists: set[Path] = {Path('adult-blocklist.txt')}
    """
    A list of files. Each file is a list of domains to exclude from the
    final list, one on each line.
    """
    top_n: int | Literal['all'] = 200
    """The number of domains to include"""
    force: bool = False
    """Overwrite `out_dir` if it already exists"""
    out_dir: Positional[Path]
    """The directory to write the list and metadata into"""

    def configure(self):
        self.add_argument('--config', action=ExplicitAction)
        self.add_argument('-b', '--blocklists')
        self.add_argument('-t', '--top-n', type=lambda s: s if s == 'all' else int(s))
        self.add_argument('-f', '--force')
    
    def process_args(self):
        # https://stackoverflow.com/a/50936474/3882118
        if self.list_id and hasattr(self, 'config_nondefault'):
            print("Cannot specify both --list-id and --config.")
            sys.exit(1)


class ExplicitAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, values)
        setattr(namespace, self.dest+'_nondefault', True)


def main():
    args = ArgParser(underscores_to_dashes=True).parse_args()


if __name__ == "__main__":
    main()